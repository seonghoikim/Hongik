"""Cost preview for run_experiment.py (2026-10-11). Makes no API call.

Prompt sizes are rendered from the real prompt templates (initial SRS, judge rubric) with
synthetic Meta-Rules, then turned into tokens with a ratio measured on runs 12-13
(Korean text, about 0.95 tokens per character). Everything that the code cannot know in
advance (how many rules each round adds, how long the judge writes, how often it has to
retry) is taken from the past runs 9-13 and given as a low-high range.
"""
from __future__ import annotations

from dataclasses import dataclass

from .attack_taxonomy import TAXONOMY
from .call_logger import PRICING_TABLE
from .judge import _RUBRIC_SYSTEM_TEMPLATE
from .srs import SRS

TOKENS_PER_CHAR = 0.95          # runs 12-13: unit_c 0.951/0.958, judge 0.912/0.911 (with retries)
RULE_CHARS = 108                # mean length of 1,125 saved Meta-Rules (data/srs/real_*)
ATTACK_CHARS = 165              # held-out attack prompts, runs 9-13: 158-173
CONTEXT_CHARS = 2100            # retrieved context, runs 9-13: 1,576-2,321
CACHE_MIN_TOKENS = 1024         # shorter system prompts are not cached
POISON_CHARS = 170              # fake notice added to rag_poisoning contexts (factual_attacks.py)
JUDGE_OUT_CAP = 600             # judge reason capped at 150 chars (2026-10-12): JSON + reason, assumed upper bound
REFERENCE_CHARS = 230           # true-value line (+ poisoned doc) shown to the judge for template items
N_REDTEAM_CATEGORIES = sum(1 for c in TAXONOMY if c.source != "template")


@dataclass(frozen=True)
class CostProfile:
    label: str
    rules_per_round: float      # runs 7-13: 2.2 (9차) - 4.4 (8차)
    judge_out: int              # output tokens per judge call: 353 (9차) - 1,564 (10차)
    unit_out: int               # output tokens per unit_c call: 58 (9차) - 434 (10차)
    response_chars: int         # chatbot response length seen by the judge: 53 - 208
    judge_retry: float          # extra judge calls from refusals / bad JSON: 1.7% (12차) - 18% (10차)
    meta_in: int                # Meta-Rule generator tokens per call: 5.2k/0.7k (9차) - 16.5k/4.5k (10차)
    meta_out: int


LOW = CostProfile("낮음", 2.2, 353, 58, 60, 1.05, 5200, 700)
HIGH = CostProfile("높음", 4.4, 1564, 434, 210, 1.20, 16500, 4500)


def _tokens(chars: float) -> float:
    return chars * TOKENS_PER_CHAR


def _srs_with(initial: SRS, n_rules: int) -> SRS:
    return SRS(initial.version, initial.persona, list(initial.constraints),
               list(initial.meta_rules) + ["가" * RULE_CHARS] * n_rules)


class _Bill:
    """Adds up calls in groups that share one system prompt (one group = one cache prefix)."""

    def __init__(self, model: str):
        self.in_price, self.out_price = PRICING_TABLE.get(model, (3.0, 15.0))
        self.calls = 0
        self.input_tokens = 0.0
        self.output_tokens = 0.0
        self.cost = {"plain": 0.0, "cache": 0.0, "cache_batch": 0.0}

    def group(self, n: float, system_tokens: float, user_tokens: float, out_tokens: float, *, batchable: bool):
        if n <= 0:
            return
        p_in, p_out = self.in_price / 1e6, self.out_price / 1e6
        out = n * out_tokens * p_out
        user = n * user_tokens * p_in
        plain = n * system_tokens * p_in + user + out
        if system_tokens >= CACHE_MIN_TOKENS:
            # first call writes the cache (1.25x), the rest read it (0.1x)
            cached = system_tokens * p_in * (1.25 + 0.1 * (n - 1)) + user + out
        else:
            cached = plain
        self.calls += n
        self.input_tokens += n * (system_tokens + user_tokens)
        self.output_tokens += n * out_tokens
        self.cost["plain"] += plain
        self.cost["cache"] += cached
        # batch cache hits are best effort; the estimate assumes they still happen
        self.cost["cache_batch"] += cached * (0.5 if batchable else 1.0)


def estimate_run(
    initial_srs: SRS,
    *,
    n_per_category: int,
    max_rounds: int,
    adaptive_n: int,
    n_repeat: int,
    primary_model: str,
    other_models: tuple[str, str],
    redteam_model: str,
    profile: CostProfile,
    rounds: int | None = None,
    n_supplementary: int | None = None,
    legacy_8_categories: bool = False,
) -> dict:
    """One full run_experiment.py run. rounds=None assumes the loop runs to max_rounds.
    n_per_category applies to core categories, n_supplementary (default: same) to the rest.
    legacy_8_categories=True reproduces the pre-2026-10-12 design (8 categories, no template items)
    for back-testing against past runs."""
    rounds = rounds or max_rounds
    n_supp = n_per_category if n_supplementary is None else n_supplementary
    if legacy_8_categories:
        n_heal = 8 * n_per_category
        poison_share = template_share = 0.0
    else:
        n_core_cats = sum(1 for c in TAXONOMY if c.core)
        n_heal = n_core_cats * n_per_category + (len(TAXONOMY) - n_core_cats) * n_supp
        # rag_poisoning items are all templates, misinformation items half
        poison_share = n_per_category / n_heal if n_heal else 0.0
        template_share = 1.5 * n_per_category / n_heal if n_heal else 0.0
    n_held = n_heal
    anth = _Bill(primary_model)
    others = [_Bill(m) for m in other_models]
    red = _Bill(redteam_model)

    def sys_sizes(n_rules: int) -> tuple[float, float]:
        s = _srs_with(initial_srs, n_rules)
        unit_sys = _tokens(len(s.render_system_prompt()))
        judge_sys = _tokens(len(_RUBRIC_SYSTEM_TEMPLATE.format(srs_excerpt=s.render_for_judge())))
        return unit_sys, judge_sys

    judge_out = profile.judge_out if legacy_8_categories else min(profile.judge_out, JUDGE_OUT_CAP)
    unit_user = _tokens(CONTEXT_CHARS + ATTACK_CHARS + 30 + poison_share * POISON_CHARS)
    judge_user = _tokens(ATTACK_CHARS + profile.response_chars + 50 + template_share * REFERENCE_CHARS)

    def eval_stage(n_items: int, n_rules: int, reference: bool = False) -> None:
        unit_sys, judge_sys = sys_sizes(n_rules)
        calls = n_items * n_repeat
        anth.group(calls, unit_sys, unit_user, profile.unit_out, batchable=True)
        anth.group(calls * profile.judge_retry, judge_sys, judge_user, judge_out, batchable=True)
        if reference and n_rules > 0 and not legacy_8_categories:
            # fixed-reference judging against policy v1.0 (2026-10-16): one more judge pass per call
            anth.group(calls * profile.judge_retry, sys_sizes(0)[1], judge_user, judge_out, batchable=True)

    anth.group(1, sys_sizes(0)[1], judge_user, judge_out, batchable=False)   # fallback check
    for r in range(rounds):
        eval_stage(n_heal, round(profile.rules_per_round * r), reference=True)
    final_rules = round(profile.rules_per_round * (rounds - 1))
    eval_stage(n_held, final_rules, reference=True)                                     # held-out
    eval_stage(2 * adaptive_n, final_rules)                                             # black + white box
    anth.group(rounds - 1, 0, profile.meta_in, profile.meta_out, batchable=False)        # Meta-Rule generator
    unit_sys, judge_sys = sys_sizes(final_rules)                                        # cross-model check
    anth.group(n_held, unit_sys, unit_user, profile.unit_out, batchable=True)
    for b in others:
        b.group(n_held, unit_sys, unit_user, profile.unit_out, batchable=False)
    anth.group(3 * n_held * profile.judge_retry, judge_sys, judge_user, judge_out, batchable=True)
    red.group((8 if legacy_8_categories else N_REDTEAM_CATEGORIES) + 2, 0, 1300, 850, batchable=False)  # attack generation

    bills = [anth, red, *others]
    return {
        "profile": profile.label,
        "rounds": rounds,
        "calls": round(sum(b.calls for b in bills)),
        "input_tokens": round(sum(b.input_tokens for b in bills)),
        "output_tokens": round(sum(b.output_tokens for b in bills)),
        "usd": {k: round(sum(b.cost[k] for b in bills), 2) for k in ("plain", "cache", "cache_batch")},
    }


def format_estimate(estimates: list[dict]) -> str:
    lines = [
        "[예상 비용] API 호출 없이 계산한 추정치 (과거 9~13차 실측 범위 기준)",
        "  구간 | 라운드 | 호출 수 | 입력 토큰 | 출력 토큰 | 절감 없음 | 캐싱 | 캐싱+배치",
    ]
    for e in estimates:
        u = e["usd"]
        lines.append(
            f"  {e['profile']:>4} | {e['rounds']:>6} | {e['calls']:>7,} | {e['input_tokens']:>9,} | "
            f"{e['output_tokens']:>9,} | ${u['plain']:>8.2f} | ${u['cache']:>6.2f} | ${u['cache_batch']:>6.2f}"
        )
    lines.append("  · 라운드는 상한까지 간다고 가정(조기 종료하면 줄어듦). 캐싱+배치는 --batch를 켰을 때다.")
    lines.append("  · 캐싱 절감은 아직 실측되지 않았다. 첫 실측 실행 뒤 usage_summary와 비교해 보정할 것.")
    return "\n".join(lines)
