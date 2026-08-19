#!/usr/bin/env python3
"""과거(3단계 PASS/WARNING/FAIL) 실행 기록을 현재의 4단계(Level) rubric으로
회고적으로 재채점(retrospective re-scoring)하는 진단 스크립트.

cross_judge_check.py(§3.6.2)가 "같은 rubric, 다른 심판관 벤더"로 재검증하는
것과 대칭적으로, 이 스크립트는 "같은 심판관 벤더, 새 rubric"으로 재검증한다.
이미 저장된 (SRS, 공격문, 챗봇 응답) 3종 세트는 그대로 두고 채점만 다시
받는다 — 특정 시나리오를 골라 유리한 결과만 보여주는 것을 피하기 위해
지정된 라운드에 포함된 시나리오 전수를 재채점한다(층화/선별 없음).

사용법:
    PYTHONPATH=src python3 scripts/relevel_with_4tier.py \
        data/results/experiment_real_20260804_102353.json \
        --rounds 1 14
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hongik_selfheal.config import load_config  # noqa: E402
from hongik_selfheal.judge import evaluate_response  # noqa: E402
from hongik_selfheal.llm_client import build_llm_client  # noqa: E402
from hongik_selfheal.srs import SRS  # noqa: E402

GRADE_ORDER = ["FULL_DEFENSE", "FUNCTIONAL_DEFENSE", "PARTIAL_EXPOSURE", "BREACH"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_json", type=Path)
    parser.add_argument("--srs-dir", type=Path, default=None,
                         help="기본값: data/srs/<experiment_json stem에서 run_id 추출>")
    parser.add_argument("--rounds", type=int, nargs="+", required=True,
                         help="재채점할 healing_rounds 인덱스(1-based)")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    data = json.loads(args.experiment_json.read_text(encoding="utf-8"))
    run_id = args.experiment_json.stem.replace("experiment_", "")
    srs_dir = args.srs_dir or Path("data/srs") / run_id

    config = load_config()
    client = build_llm_client(config, force_provider="anthropic")

    srs_cache: dict[str, str] = {}

    def load_srs_prompt(version: str) -> str:
        if version not in srs_cache:
            srs_cache[version] = SRS.load(srs_dir / f"{version}.json").render_system_prompt()
        return srs_cache[version]

    all_results: dict[int, list[dict]] = {}
    for round_idx in args.rounds:
        rnd = data["healing_rounds"][round_idx - 1]
        system_prompt = load_srs_prompt(rnd["srs_version"])
        print(f"\n=== 라운드 {round_idx} (SRS {rnd['srs_version']}) — 원 채점 3단계, 재채점 4단계 ===")
        round_results = []
        for r in rnd["results"]:
            judged = evaluate_response(
                system_prompt, r["attack_prompt"], r["chatbot_response"], client, temperature=0.0
            )
            round_results.append({
                "scenario_id": r["scenario_id"],
                "category": r["category"],
                "original_grade_3tier": r["grade"],
                "original_score_3tier": r["score"],
                "relevel_grade_4tier": judged.grade,
                "relevel_score_4tier": judged.score,
                "relevel_reason": judged.reason,
            })
            print(f"  {r['scenario_id']}: {r['grade']}({r['score']}) [3단계] -> "
                  f"{judged.grade}({judged.score}) [4단계]")
        all_results[round_idx] = round_results

    print("\n=== 라운드별 4단계 등급 분포 ===")
    summary = {}
    for round_idx, results in all_results.items():
        counts = {g: 0 for g in GRADE_ORDER}
        for r in results:
            counts[r["relevel_grade_4tier"]] += 1
        summary[round_idx] = counts
        print(f"라운드 {round_idx}: {counts}")

    out_path = args.output or args.experiment_json.with_name(f"relevel4tier_{run_id}.json")
    out_path.write_text(
        json.dumps({"rounds": all_results, "summary": summary}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[relevel_with_4tier] 상세 결과 저장: {out_path}")


if __name__ == "__main__":
    main()
