"""통계 검정 (thesis.md §3.5.3).

- paired_wilcoxon: 같은 문항을 반복 측정한 경우 (예: 치유용 셋의 v1.0 점수 vs v_final 점수)
- independent_mannwhitney / chi_square_independence: 서로 다른 문항 집합을 비교하는 경우
  (예: 치유용 셋 vs 헬드아웃 셋, 블랙박스 vs 화이트박스 적응형 재공격)

같은 문항 반복 측정에 Mann-Whitney/카이제곱을 쓰거나, 서로 다른 문항 집합에
Wilcoxon을 쓰는 것은 통계적으로 부적절하므로 섞어 쓰지 않는다.
"""
from __future__ import annotations

from dataclasses import dataclass

from scipy import stats as scipy_stats


@dataclass
class TestResult:
    test_name: str
    statistic: float | None
    p_value: float | None
    note: str


def paired_wilcoxon(before_scores: list[int], after_scores: list[int]) -> TestResult:
    """같은 문항을 두 번 측정했을 때 (예: SRS v1.0 vs v_final, 동일 50개 문항)."""
    if len(before_scores) != len(after_scores):
        raise ValueError("대응표본 비교는 두 리스트의 길이가 같아야 합니다 (같은 문항 순서로 정렬).")

    diffs = [a - b for a, b in zip(after_scores, before_scores)]
    if all(d == 0 for d in diffs):
        return TestResult(
            test_name="wilcoxon_signed_rank",
            statistic=0.0,
            p_value=1.0,
            note="두 조건의 점수가 모든 문항에서 동일하여 차이가 없습니다 (변화 없음).",
        )

    result = scipy_stats.wilcoxon(after_scores, before_scores)
    return TestResult(
        test_name="wilcoxon_signed_rank",
        statistic=float(result.statistic),
        p_value=float(result.pvalue),
        note="p < 0.05이면 두 SRS 버전 간 점수 분포 차이가 통계적으로 유의합니다.",
    )


def independent_mannwhitney(group_a_scores: list[int], group_b_scores: list[int]) -> TestResult:
    """서로 다른 문항 집합 비교 (예: 치유용 셋 vs 헬드아웃 셋)."""
    result = scipy_stats.mannwhitneyu(group_a_scores, group_b_scores, alternative="two-sided")
    return TestResult(
        test_name="mann_whitney_u",
        statistic=float(result.statistic),
        p_value=float(result.pvalue),
        note="p > 0.05이면 두 집단의 점수 분포가 통계적으로 구분되지 않습니다 (일반화 근거).",
    )


def chi_square_independence(
    counts_a: tuple[int, int, int], counts_b: tuple[int, int, int]
) -> TestResult:
    """PASS/WARNING/FAIL 빈도표(2x3 분할표)에 대한 독립성 검정.

    counts_a, counts_b는 각각 (pass_count, warning_count, fail_count).
    """
    labels = ("PASS", "WARNING", "FAIL")
    # 두 집단 모두에서 0인 등급(열)은 기대빈도가 0이 되어 카이제곱 계산이
    # 불가능하므로 제외한다 (예: WARNING이 한 건도 없는 경우).
    kept_cols = [i for i in range(3) if counts_a[i] > 0 or counts_b[i] > 0]
    if len(kept_cols) < 2:
        return TestResult(
            test_name="chi_square_independence",
            statistic=None,
            p_value=None,
            note="두 집단 모두 등급이 사실상 한 가지뿐이라 카이제곱 검정을 적용할 수 없습니다.",
        )

    table = [[counts_a[i] for i in kept_cols], [counts_b[i] for i in kept_cols]]
    chi2, p, dof, _expected = scipy_stats.chi2_contingency(table)
    dropped = [labels[i] for i in range(3) if i not in kept_cols]
    dropped_note = f" (0건이라 제외된 등급: {', '.join(dropped)})" if dropped else ""
    return TestResult(
        test_name="chi_square_independence",
        statistic=float(chi2),
        p_value=float(p),
        note=(
            f"자유도={dof}.{dropped_note} p > 0.05이면 두 집단의 등급 분포가 "
            "통계적으로 독립(=차이 없음)이라는 근거가 됩니다."
        ),
    )
