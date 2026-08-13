#!/usr/bin/env python3
"""§4.2.2 연구자 수동 검토(manual_review_hook)의 표본 기반 대체 절차.

전수 수동 검토(생성된 모든 공격 후보를 하나하나 확인)는 물리적으로 오래 걸리고,
헬드아웃/교차 모델 검증이 이미 사후적으로 "비현실적이거나 카테고리에 안 맞는
문항이 섞여 있었다면 결과가 이상하게 나왔을 것"이라는 정황 증거를 제공한다는
점에서 전수 검토의 필요성 자체가 낮다(2026-08-13, 결정 로그 항목 32). 이 스크립트는
카테고리별 층화 표본만 사람이 직접 확인하고, 그 표본의 승인율(acceptance rate)을
"전체 풀의 품질이 이 정도일 것"이라는 근거로 논문에 인용할 수 있게 만든다.

사용법:
    PYTHONPATH=src python3 scripts/manual_review_sample.py data/results/attack_pool_xxx.json --per-category 3

표본 크기(카테고리당 3개, 8개 카테고리 = 24개)는 100개 규모 전체 풀을 몇 분 안에
훑어볼 수 있는 수준으로 의도적으로 작게 잡았다 - "물리적으로 너무 오래 걸리지
않는 수준"이라는 연구자 요청(2026-08-13)을 반영한 값이며, --per-category로
조정 가능하다.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hongik_selfheal.attack_generator import load_pool  # noqa: E402


def stratified_sample(pool, per_category: int, seed: int):
    rng = random.Random(seed)
    by_category = defaultdict(list)
    for scenario in pool:
        by_category[scenario.category].append(scenario)
    sample = []
    for category, items in sorted(by_category.items()):
        rng.shuffle(items)
        sample.extend(items[:per_category])
    return sample


def run_interactive_review(sample) -> list[dict]:
    print(f"\n표본 {len(sample)}건에 대한 수동 검토를 시작합니다.")
    print("각 문항에 대해 다음 기준으로 판단하십시오:")
    print("  1) 실질적으로 동일한 공격의 표현만 다른 중복인가")
    print("  2) 대상 도메인(가전 유통)에 비현실적인 시나리오인가")
    print("  3) 카테고리 정의에 부합하지 않는 문항인가")
    print("문제가 없으면 Enter(승인), 문제가 있으면 이유를 입력(거부).\n")

    records = []
    for i, scenario in enumerate(sample, 1):
        print(f"[{i}/{len(sample)}] category={scenario.category} id={scenario.id}")
        print(f"  {scenario.text}")
        reason = input("  판정 (Enter=승인 / 이유 입력=거부): ").strip()
        records.append({
            "scenario_id": scenario.id,
            "category": scenario.category,
            "text": scenario.text,
            "approved": reason == "",
            "rejection_reason": reason or None,
        })
        print()
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pool_path", type=Path, help="save_pool()로 저장된 공격 시나리오 풀 JSON")
    parser.add_argument("--per-category", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    pool = load_pool(args.pool_path)
    sample = stratified_sample(pool, args.per_category, args.seed)
    records = run_interactive_review(sample)

    approved = sum(1 for r in records if r["approved"])
    total = len(records)
    acceptance_rate = approved / total if total else 0.0

    out_path = args.out or args.pool_path.parent / (
        f"manual_review_sample_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    )
    out_path.write_text(
        json.dumps(
            {
                "source_pool": str(args.pool_path),
                "pool_size": len(pool),
                "sample_size": total,
                "per_category": args.per_category,
                "seed": args.seed,
                "approved": approved,
                "rejected": total - approved,
                "acceptance_rate": acceptance_rate,
                "records": records,
                "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"승인 {approved}/{total} ({acceptance_rate * 100:.1f}%) -> {out_path}")
    if acceptance_rate < 0.9:
        print(
            "⚠️ 표본 승인율이 90% 미만입니다 - 자동 생성·중복제거만으로는 품질이 "
            "충분하지 않을 수 있으므로, 거부된 문항의 카테고리를 확인해 해당 "
            "카테고리는 전수 검토를 고려하십시오."
        )


if __name__ == "__main__":
    main()
