"""Regression tests for the fixes in docs/program_review_20261011.md."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from scipy import stats as scipy_stats

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hongik_selfheal.attack_generator import AttackScenario, stratified_split
from hongik_selfheal.experiment import evaluate_set, self_healing_loop
from hongik_selfheal.judge import evaluate_response
from hongik_selfheal.llm_client import JUDGE_MARKER, META_RULE_MARKER, LLMClient
from hongik_selfheal.srs import initial_srs_v1
from hongik_selfheal.stats import cochran_q, friedman


class _ScriptedClient(LLMClient):
    """Judge always answers with a fixed payload; the Meta-Rule generator always adds a new rule."""

    def __init__(self, judge_payload):
        self.judge_payload = judge_payload
        self.rule_calls = 0

    def complete(self, system, user, temperature):
        if JUDGE_MARKER in system:
            return self.judge_payload if isinstance(self.judge_payload, str) else json.dumps(self.judge_payload)
        if META_RULE_MARKER in system:
            self.rule_calls += 1
            return json.dumps({"new_rules": [f"rule-{self.rule_calls}"]})
        return "안녕하세요, 제품 안내를 도와드리는 상담원이에요."


def _scenarios(n, category="impersonation"):
    return [AttackScenario(id=f"{category}-{i}", category=category, text=f"공격 문장 {i} {'가' * i}") for i in range(n)]


def test_v_final_is_the_last_evaluated_version_when_round_cap_is_hit():
    client = _ScriptedClient({"score": 3, "grade": "FUNCTIONAL_DEFENSE", "reason": "형식 이탈"})
    rounds, final_srs = self_healing_loop(initial_srs_v1(), _scenarios(3), client, max_rounds=3)
    assert [r.srs_version for r in rounds] == ["v1.0", "v1.1", "v1.2"]
    assert final_srs.version == rounds[-1].srs_version          # no unevaluated v1.3
    assert client.rule_calls == 2                                # no rule generation after the last round


def test_stratified_split_raises_when_a_set_would_be_empty():
    with pytest.raises(ValueError):
        stratified_split(_scenarios(1), healing_per_cat=3, heldout_per_cat=3)


def test_stratified_split_keeps_a_held_out_share_when_short(capsys):
    healing, held_out = stratified_split(_scenarios(4), healing_per_cat=3, heldout_per_cat=3)
    assert len(healing) == 2 and len(held_out) == 2
    assert "경고" in capsys.readouterr().out


def test_judge_score_is_derived_from_grade():
    client = _ScriptedClient({"score": 4, "grade": "breach", "reason": "유출"})
    result = evaluate_response("SRS", "공격", "응답", client)
    assert result.grade == "BREACH" and result.score == 1


def test_invalid_judge_grade_is_recorded_as_ungradable_not_a_crash():
    client = _ScriptedClient({"score": 3, "grade": "PASS", "reason": "3단계 등급"})
    summary = evaluate_set("held_out", initial_srs_v1(), _scenarios(2), client)
    assert summary.results == [] and summary.ungradable_count == 2


def test_friedman_matches_scipy():
    a, b, c = [4, 3, 4, 2, 4, 3], [3, 3, 2, 2, 4, 1], [4, 4, 4, 3, 4, 3]
    expected = scipy_stats.friedmanchisquare(a, b, c)
    got = friedman(a, b, c)
    assert got.p_value == pytest.approx(expected.pvalue)


def test_cochran_q_hand_computed_example():
    # 4 items x 3 conditions; column totals 3, 1, 4; row totals 3, 2, 2, 1
    a, b, c = [1, 1, 0, 1], [1, 0, 0, 0], [1, 1, 1, 1]
    got = cochran_q(a, b, c)
    # Q = (k-1)[k*sum(C^2) - N^2] / (k*N - sum(R^2)) = 2*(3*26 - 64)/(3*8 - 18) = 28/6
    assert got.statistic == pytest.approx(28 / 6)
    assert got.p_value == pytest.approx(scipy_stats.chi2.sf(28 / 6, 2))


def test_run_experiment_help_does_not_crash():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_experiment.py"), "--help"],
        capture_output=True, text=True, env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 0, proc.stderr[-500:]
