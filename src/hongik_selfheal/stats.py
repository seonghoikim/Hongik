"""통계 검정 (thesis.md §3.5.3).

- paired_wilcoxon: 같은 문항을 반복 측정한 경우 (예: 치유용 셋의 v1.0 점수 vs v_final 점수)
- independent_mannwhitney / chi_square_independence: 서로 다른 문항 집합을 비교하는 경우
  (예: 치유용 셋 vs 헬드아웃 셋, 블랙박스 vs 화이트박스 적응형 재공격)
- kruskal_wallis / chi_square_multi_group: 같은 문항 집합을 3개 이상의 독립 조건에
  적용한 경우 (예: 동일 헬드아웃 셋을 3개 백엔드 LLM에 각각 통과시킨 교차 모델 검증,
  §3.5.5). Mann-Whitney/카이제곱의 k-그룹(k>=2) 일반화이며 k=2일 때는 각각과 동치.

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


def kruskal_wallis(*groups: list[int]) -> TestResult:
    """같은 문항 집합을 3개 이상의 독립 조건(예: 백엔드 LLM 3종)에 적용했을 때
    Action Matrix 점수 분포 차이를 검정한다. Mann-Whitney U의 k-그룹 일반화.
    """
    if len(groups) < 2:
        raise ValueError("kruskal_wallis는 최소 2개 그룹이 필요합니다.")

    all_values = {v for group in groups for v in group}
    if len(all_values) <= 1:
        return TestResult(
            test_name="kruskal_wallis",
            statistic=None,
            p_value=None,
            note="모든 그룹의 점수가 완전히 동일(분산 0)하여 검정을 적용할 수 없습니다 (차이 없음으로 해석).",
        )

    result = scipy_stats.kruskal(*groups)
    return TestResult(
        test_name="kruskal_wallis",
        statistic=float(result.statistic),
        p_value=float(result.pvalue),
        note=(
            f"{len(groups)}개 그룹 비교. p > 0.05이면 그룹 간 점수 분포가 "
            "통계적으로 구분되지 않습니다 (교차 모델 일관성 근거)."
        ),
    )


def chi_square_multi_group(*counts: tuple[int, int, int]) -> TestResult:
    """3개 이상 그룹의 PASS/WARNING/FAIL 빈도표(RxC 분할표)에 대한 독립성 검정.
    chi_square_independence의 k-그룹(k>=2) 일반화이며, counts는 각 그룹의
    (pass_count, warning_count, fail_count) 튜플이다.
    """
    if len(counts) < 2:
        raise ValueError("chi_square_multi_group은 최소 2개 그룹이 필요합니다.")

    labels = ("PASS", "WARNING", "FAIL")
    kept_cols = [i for i in range(3) if any(c[i] > 0 for c in counts)]
    if len(kept_cols) < 2:
        return TestResult(
            test_name="chi_square_multi_group",
            statistic=None,
            p_value=None,
            note="모든 그룹의 등급이 사실상 한 가지뿐이라 카이제곱 검정을 적용할 수 없습니다.",
        )

    table = [[c[i] for i in kept_cols] for c in counts]
    chi2, p, dof, _expected = scipy_stats.chi2_contingency(table)
    dropped = [labels[i] for i in range(3) if i not in kept_cols]
    dropped_note = f" (0건이라 제외된 등급: {', '.join(dropped)})" if dropped else ""
    return TestResult(
        test_name="chi_square_multi_group",
        statistic=float(chi2),
        p_value=float(p),
        note=(
            f"{len(counts)}개 그룹, 자유도={dof}.{dropped_note} p > 0.05이면 그룹 간 "
            "등급 분포가 통계적으로 독립(=차이 없음)이라는 근거가 됩니다."
        ),
    )
