"""통계 검정 (thesis.md §3.5.3).

- paired_wilcoxon: 같은 문항을 반복 측정한 경우 (예: 치유용 셋의 v1.0 점수 vs v_final 점수)
- independent_mannwhitney / chi_square_independence: 서로 다른 문항 집합을 비교하는 경우
  (예: 치유용 셋 vs 헬드아웃 셋, 블랙박스 vs 화이트박스 적응형 재공격)
- friedman / cochran_q: 같은 문항을 3개 이상의 조건(예: 백엔드 LLM 3종)이 각각 응답한
  반복측정 자료. 교차 모델 검증(§3.5.5)은 이 두 검정을 쓴다 (program review 2026-10-11:
  같은 문항을 3개 모델이 답하므로 독립 집단 가정의 Kruskal-Wallis·카이제곱은 부적절).
- kruskal_wallis / chi_square_multi_group: 서로 다른 문항 집합을 3개 이상의 독립 조건에
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
    counts_a: tuple[int, ...], counts_b: tuple[int, ...], labels: tuple[str, ...] | None = None
) -> TestResult:
    """등급 빈도표(2xN 분할표)에 대한 독립성 검정.

    counts_a, counts_b는 같은 길이의 등급별 빈도 튜플(호출부가 순서를 정함 -
    예: experiment.py의 GRADE_ORDER). labels를 생략하면 "등급 1", "등급 2"...로
    표시한다.
    """
    n = len(counts_a)
    if len(counts_b) != n:
        raise ValueError("counts_a와 counts_b는 길이가 같아야 합니다.")
    labels = labels or tuple(f"등급 {i + 1}" for i in range(n))

    # 두 집단 모두에서 0인 등급(열)은 기대빈도가 0이 되어 카이제곱 계산이
    # 불가능하므로 제외한다 (예: 특정 등급이 한 건도 없는 경우).
    kept_cols = [i for i in range(n) if counts_a[i] > 0 or counts_b[i] > 0]
    if len(kept_cols) < 2:
        return TestResult(
            test_name="chi_square_independence",
            statistic=None,
            p_value=None,
            note="두 집단 모두 등급이 사실상 한 가지뿐이라 카이제곱 검정을 적용할 수 없습니다.",
        )

    table = [[counts_a[i] for i in kept_cols], [counts_b[i] for i in kept_cols]]
    chi2, p, dof, _expected = scipy_stats.chi2_contingency(table)
    dropped = [labels[i] for i in range(n) if i not in kept_cols]
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


def friedman(*groups: list[int]) -> TestResult:
    """Repeated measures over the same items (k >= 3 conditions): Friedman test on scores.
    groups[j][i] is the score of item i under condition j."""
    if len(groups) < 3:
        raise ValueError("friedman은 최소 3개 조건이 필요합니다.")
    n = len(groups[0])
    if any(len(g) != n for g in groups):
        raise ValueError("모든 조건은 같은 문항 순서·개수여야 합니다.")
    if n < 2 or len({v for g in groups for v in g}) <= 1:
        return TestResult("friedman", None, None, "점수 변이가 없어 Friedman 검정을 적용할 수 없습니다 (차이 없음).")
    result = scipy_stats.friedmanchisquare(*groups)
    return TestResult(
        test_name="friedman",
        statistic=float(result.statistic),
        p_value=float(result.pvalue),
        note=f"{len(groups)}개 조건 반복측정, 문항 {n}개. p > 0.05이면 조건 간 점수 차이가 통계적으로 유의하지 않습니다.",
    )


def cochran_q(*binary_groups: list[int]) -> TestResult:
    """Repeated measures with a binary outcome (e.g. FULL_DEFENSE or not) for k >= 3
    conditions. binary_groups[j][i] is 1/0 for item i under condition j."""
    k = len(binary_groups)
    if k < 3:
        raise ValueError("cochran_q는 최소 3개 조건이 필요합니다.")
    n = len(binary_groups[0])
    if any(len(g) != n for g in binary_groups):
        raise ValueError("모든 조건은 같은 문항 순서·개수여야 합니다.")
    col = [sum(g) for g in binary_groups]
    row = [sum(binary_groups[j][i] for j in range(k)) for i in range(n)]
    total = sum(col)
    denom = k * total - sum(r * r for r in row)
    if denom == 0:
        return TestResult("cochran_q", None, None, "모든 문항에서 조건 간 결과가 같아 Cochran's Q를 적용할 수 없습니다 (차이 없음).")
    q = (k - 1) * (k * sum(c * c for c in col) - total * total) / denom
    p = float(scipy_stats.chi2.sf(q, k - 1))
    return TestResult(
        test_name="cochran_q",
        statistic=float(q),
        p_value=p,
        note=f"{k}개 조건 반복측정(이진), 자유도={k - 1}. p > 0.05이면 조건 간 비율 차이가 통계적으로 유의하지 않습니다.",
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


def chi_square_multi_group(*counts: tuple[int, ...], labels: tuple[str, ...] | None = None) -> TestResult:
    """3개 이상 그룹의 등급 빈도표(RxC 분할표)에 대한 독립성 검정.
    chi_square_independence의 k-그룹(k>=2) 일반화이며, counts는 각 그룹의
    등급별 빈도 튜플(호출부가 순서를 정함 - 예: experiment.py의 GRADE_ORDER)이다.
    """
    if len(counts) < 2:
        raise ValueError("chi_square_multi_group은 최소 2개 그룹이 필요합니다.")

    n = len(counts[0])
    if any(len(c) != n for c in counts):
        raise ValueError("counts의 모든 튜플은 길이가 같아야 합니다.")
    labels = labels or tuple(f"등급 {i + 1}" for i in range(n))

    kept_cols = [i for i in range(n) if any(c[i] > 0 for c in counts)]
    if len(kept_cols) < 2:
        return TestResult(
            test_name="chi_square_multi_group",
            statistic=None,
            p_value=None,
            note="모든 그룹의 등급이 사실상 한 가지뿐이라 카이제곱 검정을 적용할 수 없습니다.",
        )

    table = [[c[i] for i in kept_cols] for c in counts]
    chi2, p, dof, _expected = scipy_stats.chi2_contingency(table)
    dropped = [labels[i] for i in range(n) if i not in kept_cols]
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


# --- 사전 고정 분석 계획용 (2026-10-16, docs/analysis_plan_20261016.md) ---------------------------

def mcnemar_exact(before: list[int], after: list[int]) -> TestResult:
    """같은 문항의 이분 결과(1=정보 무결성 유지) 전후 비교. 바뀐 문항만으로 정확 이항검정(양측)."""
    if len(before) != len(after):
        raise ValueError("대응표본 비교는 두 리스트의 길이가 같아야 합니다.")
    improved = sum(1 for b, a in zip(before, after) if b == 0 and a == 1)
    worsened = sum(1 for b, a in zip(before, after) if b == 1 and a == 0)
    n = improved + worsened
    if n == 0:
        return TestResult("mcnemar_exact", 0.0, 1.0, "바뀐 문항이 없습니다(개선 0, 악화 0).")
    p = scipy_stats.binomtest(min(improved, worsened), n, 0.5, alternative="two-sided").pvalue
    return TestResult("mcnemar_exact", float(improved - worsened), float(p),
                      f"개선 {improved}건, 악화 {worsened}건. p < 0.05이면 변화가 유의합니다.")


def _wilson(x: int, n: int, z: float) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = x / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return centre - half, centre + half


def noninferiority_two_proportions(x_ref: int, n_ref: int, x_new: int, n_new: int,
                                   margin: float = 0.10, alpha: float = 0.05) -> TestResult:
    """독립 두 비율의 비열등성(new가 ref보다 margin 이상 나쁘지 않은가).

    차이 d = p_new - p_ref의 Newcombe(Wilson 혼합) 양측 (1-2α) 신뢰구간 하한이 -margin보다 크면
    비열등으로 판정한다(단측 α). 비율이 1에 가까워도 구간이 무너지지 않는 방법이다.
    statistic=d, p_value 자리에 하한을 넣지 않고 None으로 두며 note에 구간과 판정을 적는다."""
    z = scipy_stats.norm.ppf(1 - alpha)
    p1, p2 = x_ref / n_ref, x_new / n_new
    l1, u1 = _wilson(x_ref, n_ref, z)
    l2, u2 = _wilson(x_new, n_new, z)
    d = p2 - p1
    lower = d - ((p2 - l2) ** 2 + (u1 - p1) ** 2) ** 0.5
    upper = d + ((u2 - p2) ** 2 + (p1 - l1) ** 2) ** 0.5
    ok = lower > -margin
    return TestResult("noninferiority_newcombe", float(round(d, 4)), None,
                      f"차이 {d * 100:+.1f}%p, {int((1 - 2 * alpha) * 100)}% 신뢰구간 [{lower * 100:.1f}, {upper * 100:.1f}]%p, "
                      f"허용 폭 -{margin * 100:.0f}%p → {'비열등' if ok else '비열등 입증 실패'}")
