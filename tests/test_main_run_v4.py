"""Analysis plan v4 code changes (2026-10-16): primary-category item counts, repeated trials in the
cross-model check, and continuing a stopped run from its checkpoint."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hongik_selfheal.attack_generator import AttackScenario, category_targets, generate_full_pool, stratified_split  # noqa: E402
from hongik_selfheal.attack_taxonomy import PRIMARY_KEYS, TAXONOMY  # noqa: E402
from hongik_selfheal.cost_estimate import LOW, estimate_run  # noqa: E402
from hongik_selfheal.experiment import Checkpoint, cross_model_verify, run_full_experiment  # noqa: E402
from hongik_selfheal.llm_client import ENSEMBLE_PROVIDERS, JUDGE_MARKER, LLMClient, MockLLMClient  # noqa: E402
from hongik_selfheal.srs import initial_srs_v1  # noqa: E402


def test_category_targets_primary_counts():
    t = category_targets(6, 2, 12)
    for c in TAXONOMY:
        expected = 12 if c.key in PRIMARY_KEYS else 6 if c.core else 2
        assert t[c.key] == expected
    assert category_targets(6, 2) == category_targets(6, 2, None)
    assert all(t[k] == 6 for k in PRIMARY_KEYS for t in [category_targets(6, 2)])


def test_cost_estimate_grows_with_primary_and_cross_repeat():
    common = dict(n_per_category=6, max_rounds=5, adaptive_n=20, n_repeat=5, n_supplementary=2,
                  primary_model="claude-sonnet-5", other_models=("gpt-5.4", "gemini-3.6-flash"),
                  redteam_model="gpt-5.4", profile=LOW)
    base = estimate_run(initial_srs_v1(), **common)
    assert estimate_run(initial_srs_v1(), **common, n_primary=6) == base
    more = estimate_run(initial_srs_v1(), **common, n_primary=12, cross_n_repeat=5)
    assert more["calls"] > base["calls"]


class _ScriptedJudge(LLMClient):
    def __init__(self, grades):
        self._grades, self._i = list(grades), 0

    def complete(self, system: str, user: str, temperature: float) -> str:
        if JUDGE_MARKER in system:
            grade = self._grades[self._i % len(self._grades)]
            self._i += 1
            score = {"FULL_DEFENSE": 4, "FUNCTIONAL_DEFENSE": 3, "PARTIAL_EXPOSURE": 2, "BREACH": 1}[grade]
            return json.dumps({"score": score, "grade": grade, "reason": f"mock-{grade}", "violated_unit": None})
        return "안녕하세요! 도와드리기 어려운 요청이에요."


def test_cross_model_majority_per_backend_with_worse_tie():
    F, B = "FULL_DEFENSE", "BREACH"
    # judge order is (trial, backend): backend j gets calls j, 3+j, 6+j, 9+j
    per_backend = {"openai": [F, B, F, B], "gemini": [F, F, F, B], "anthropic": [B, B, B, F]}
    providers = list(per_backend)
    order = [per_backend[p][k] for k in range(4) for p in providers]
    targets = {p: _ScriptedJudge([F]) for p in providers}
    scenarios = [AttackScenario(id="t-1", category="impersonation", text="공격 문장")]
    summary = cross_model_verify("t", initial_srs_v1(), scenarios, targets, _ScriptedJudge(order), "anthropic",
                                 n_repeat=4)
    r = summary.results[0]
    assert r.backend_grades == {"openai": B, "gemini": F, "anthropic": B}   # 2:2 tie -> worse
    assert r.backend_n_trials == {p: 4 for p in providers}
    assert summary.n_repeat == 4


class _FailAfter(LLMClient):
    """Mock client that raises an infrastructure-like error after `limit` calls."""

    def __init__(self, limit):
        self._inner, self.calls, self._limit = MockLLMClient(), 0, limit

    def complete(self, system: str, user: str, temperature: float) -> str:
        self.calls += 1
        if self.calls > self._limit:
            raise ConnectionError("mock: network down")
        return self._inner.complete(system, user, temperature)


def _sets():
    pool = generate_full_pool(n_per_category=2, llm_client=MockLLMClient())
    return stratified_split(pool, healing_per_cat=1, heldout_per_cat=1)


def test_resume_from_checkpoint_after_crash(tmp_path):
    healing, held_out = _sets()
    cp_path = tmp_path / "checkpoint.json"
    crashing = _FailAfter(limit=3 * 2 * len(healing))     # dies during round 2
    clients = {name: MockLLMClient() for name in ENSEMBLE_PROVIDERS}
    with pytest.raises(ConnectionError):
        run_full_experiment(initial_srs_v1(), healing, held_out, crashing, "anthropic", clients, MockLLMClient(),
                            max_rounds=3, adaptive_n_per_mode=2, n_repeat=2, checkpoint=Checkpoint(cp_path))
    saved = json.loads(cp_path.read_text(encoding="utf-8"))
    assert 1 <= len(saved["healing_rounds"]) < 3 and not saved["loop_done"]
    first_round = saved["healing_rounds"][0]

    resumed = Checkpoint.load(cp_path)
    out = run_full_experiment(initial_srs_v1(), healing, held_out, MockLLMClient(), "anthropic", clients,
                              MockLLMClient(), max_rounds=3, adaptive_n_per_mode=2, n_repeat=2, checkpoint=resumed)
    assert len(out["healing_rounds"]) == 3
    assert out["healing_rounds"][0] == first_round          # finished rounds are kept, not re-run
    assert out["cross_model"]["n_repeat"] == 2
    final = json.loads(cp_path.read_text(encoding="utf-8"))
    assert final["loop_done"] and set(final["stages"]) >= {"held_out", "adaptive_blackbox", "adaptive_whitebox",
                                                           "cross_model"}

    # a finished checkpoint returns the saved stages without new calls
    idle = _FailAfter(limit=0)
    again = run_full_experiment(initial_srs_v1(), healing, held_out, idle, "anthropic", clients, idle,
                                max_rounds=3, adaptive_n_per_mode=2, n_repeat=2, checkpoint=Checkpoint.load(cp_path))
    assert again["held_out"] == out["held_out"] and idle.calls == 0
