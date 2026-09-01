"""정보 불일치성(Information Disorderness) 3분류 기준 재집계 스크립트 (thesis.md F.6 TODO 항목 1).

기존 8개 공격 카테고리별 raw 채점 결과(data/results/*.json)를 새 실험 없이 다시 읽어,
Dis-/Mis-/Malinformation 3유형 기준으로 재집계한다. 원자료의 점수·등급은 전혀 수정하지
않는다 — 어떤 카테고리를 어느 유형으로 묶어서 보여줄지만 바꾸는 순수 집계 스크립트다.

카테고리↔유형 매핑 근거는 thesis.md §2.5-⑧·§4.2.1 참조. 8개 중 4개만 3유형에 직접
대응한다고 판단했으므로(결정 로그 항목 59), 나머지 4개는 "보완적 보안 위협"으로 따로 묶어
보여준다 — 억지로 3유형에 끼워 넣지 않는다.

사용법:
    python scripts/aggregate_by_disorderness_type.py data/results/experiment_real_20260804_102353.json
    python scripts/aggregate_by_disorderness_type.py data/results/*.json
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

# 결정 로그 항목 59의 정밀 분석 결과. 4개는 3유형에 직접 대응(핵심 실증),
# 나머지 4개는 정보 진위와 무관한 보완적 보안 위협이라 "supplementary"로 분리한다.
CATEGORY_TO_TYPE: dict[str, str] = {
    "impersonation": "Disinformation",       # 사칭 — "imposter content" (Wardle-Derakhshan)
    "misinformation": "Misinformation",      # 허위사실 동조 유도 — Dis/Mis 경계, 카테고리 자체 명칭 존중
    "metadata_leak": "Malinformation",       # 내부 메타데이터·시스템 프롬프트 유출
    "pii_leak": "Malinformation",            # 개인정보 유출 — 마크롱 이메일 유출 사례와 동일 구조
    "encoding_bypass": "supplementary",      # 필터 우회 "기법" — 정보 진위 문제가 아님
    "tone_gaslighting": "supplementary",     # 역할·톤 위반 — 정보 진위 문제가 아님
    "cross_product_leak": "supplementary",   # 정책 위반에 더 가까움 (약한 Malinformation 후보)
    "price_probing": "supplementary",        # 정책 위반에 더 가까움 (약한 Malinformation 후보)
}

# 원래 8개 카테고리에 속하지 않는 것으로 확인된 값(집계에서 의도적으로 제외, 오류 아님).
# "adaptive": §5.4 적응형 재공격 시나리오는 라운드마다 새로 생성되어 8개 카테고리 태그가
# 없다(attack_generator.py::generate_adaptive_attacks) — 정보 불일치성 3유형 재집계 범위 밖.
KNOWN_EXCLUDED_CATEGORIES = {"adaptive"}

TYPE_ORDER = ["Disinformation", "Misinformation", "Malinformation", "supplementary"]


def _norm(entry: dict) -> dict | None:
    """3-tier(grade/score)와 4-tier(relevel_grade_4tier/relevel_score_4tier) 스키마를
    모두 흡수해 {scenario_id, category, grade, score, tier}로 정규화한다."""
    category = entry.get("category")
    if category is None:
        return None
    if "relevel_grade_4tier" in entry:
        grade, score, tier = entry["relevel_grade_4tier"], entry["relevel_score_4tier"], "4tier"
    elif "grade" in entry:
        grade, score, tier = entry["grade"], entry.get("score"), "3tier"
    else:
        return None
    return {
        "scenario_id": entry.get("scenario_id"),
        "category": category,
        "grade": grade,
        "score": score,
        "tier": tier,
    }


def iter_scenario_results(path: Path):
    """실험 결과 JSON의 알려진 모든 위치(healing_rounds/held_out/adaptive_*/cross_model,
    또는 relevel4tier의 rounds 딕셔너리)를 순회하며 정규화된 시나리오 결과를 낸다."""
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        # 예: pilot_5w1h_pool.json — 채점 전 원시 시나리오 풀 목록. 이 스크립트는
        # 채점 결과(grade)가 있는 파일만 다루므로 조용히 건너뛴다.
        return

    def from_results_list(results, label):
        for entry in results or []:
            norm = _norm(entry)
            if norm:
                norm["source_file"] = path.name
                norm["label"] = label
                yield norm

    if "healing_rounds" in data:
        for round_ in data["healing_rounds"]:
            yield from from_results_list(round_.get("results"), round_.get("label", "healing"))
    for key in ("held_out", "adaptive_blackbox", "adaptive_whitebox"):
        block = data.get(key)
        if isinstance(block, dict):
            yield from from_results_list(block.get("results"), block.get("label", key))
    if "cross_model" in data and isinstance(data["cross_model"], dict):
        for backend, block in data["cross_model"].get("backends", {}).items():
            if isinstance(block, dict):
                yield from from_results_list(block.get("results"), f"cross_model:{backend}")
    if "rounds" in data and isinstance(data["rounds"], dict):
        # relevel4tier_*.json 형태: {"1": [...], "2": [...]}
        for round_label, results in data["rounds"].items():
            yield from from_results_list(results, f"relevel_round_{round_label}")


def aggregate(paths: list[Path]) -> dict:
    # agg[type][tier][grade] = count
    agg: dict[str, dict[str, dict[str, int]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    category_seen: dict[str, int] = defaultdict(int)
    unmapped_categories: set[str] = set()
    total = 0
    for path in paths:
        for result in iter_scenario_results(path):
            category = result["category"]
            category_seen[category] += 1
            type_ = CATEGORY_TO_TYPE.get(category)
            if type_ is None:
                if category not in KNOWN_EXCLUDED_CATEGORIES:
                    unmapped_categories.add(category)
                continue
            agg[type_][result["tier"]][result["grade"]] += 1
            total += 1
    return {
        "agg": agg,
        "category_seen": dict(category_seen),
        "unmapped_categories": sorted(unmapped_categories),
        "total": total,
    }


def print_report(result: dict) -> None:
    agg = result["agg"]
    print(f"총 {result['total']}건 시나리오 결과를 정보 불일치성 3유형(+보완)으로 재집계했습니다.\n")
    print("카테고리별 원자료 건수(변경 없음, 확인용):")
    for cat, n in sorted(result["category_seen"].items()):
        if cat in KNOWN_EXCLUDED_CATEGORIES:
            type_ = "(집계 범위 밖 — 8개 카테고리 아님)"
        else:
            type_ = CATEGORY_TO_TYPE.get(cat, "?")
        print(f"  - {cat:20s} → {type_:15s} ({n}건)")
    if result["unmapped_categories"]:
        print(f"\n⚠️ 매핑표에 없는 카테고리 발견(스크립트 갱신 필요): {result['unmapped_categories']}")
    print()

    for type_ in TYPE_ORDER:
        tiers = agg.get(type_, {})
        if not tiers:
            continue
        label = "보완적 보안 위협 (정보 불일치성 3유형 밖)" if type_ == "supplementary" else type_
        print(f"### {label}")
        for tier, grades in tiers.items():
            total_t = sum(grades.values())
            print(f"  [{tier}] 총 {total_t}건")
            for grade, n in sorted(grades.items(), key=lambda kv: -kv[1]):
                pct = 100 * n / total_t if total_t else 0
                print(f"    - {grade:20s} {n:4d}건 ({pct:5.1f}%)")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    paths = [Path(p) for p in sys.argv[1:]]
    missing = [p for p in paths if not p.exists()]
    if missing:
        print(f"파일을 찾을 수 없습니다: {missing}")
        sys.exit(1)
    result = aggregate(paths)
    print_report(result)
