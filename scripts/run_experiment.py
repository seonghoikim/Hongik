#!/usr/bin/env python3
"""전체 실험 실행: 공격 시나리오 생성 → 자가 치유 루프 → 헬드아웃 검증 →
적응형 재공격 → 통계 검정 → 결과 저장.

사용법:
    PYTHONPATH=src python3 scripts/run_experiment.py --mode mock
    PYTHONPATH=src python3 scripts/run_experiment.py --mode openai --n-per-category 10

주의: --mode mock 은 API 키 없이 파이프라인 배선만 검증하는 용도입니다.
      논문에 쓸 실제 실험 결과는 반드시 --mode openai 또는 --mode gemini로
      .env에 실제 API 키를 넣은 뒤 실행해야 합니다.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hongik_selfheal.attack_generator import generate_full_pool, stratified_split  # noqa: E402
from hongik_selfheal.config import load_config  # noqa: E402
from hongik_selfheal.experiment import run_full_experiment, save_experiment_output  # noqa: E402
from hongik_selfheal.llm_client import build_llm_client  # noqa: E402
from hongik_selfheal.srs import initial_srs_v1  # noqa: E402
from hongik_selfheal.stats import (  # noqa: E402
    chi_square_independence,
    independent_mannwhitney,
    paired_wilcoxon,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["mock", "openai", "gemini"], default=None)
    parser.add_argument("--n-per-category", type=int, default=10, help="치유용/헬드아웃 각 카테고리당 개수")
    parser.add_argument("--max-rounds", type=int, default=10)
    parser.add_argument("--adaptive-n", type=int, default=15, help="블랙박스/화이트박스 각각 개수")
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()
    llm_client = build_llm_client(config, force_provider=args.mode)
    provider = args.mode or config.provider

    print(f"[run_experiment] provider={provider}")

    pool = generate_full_pool(n_per_category=args.n_per_category * 2, llm_client=llm_client)
    healing_set, held_out_set = stratified_split(
        pool, healing_per_cat=args.n_per_category, heldout_per_cat=args.n_per_category
    )
    print(f"[run_experiment] healing={len(healing_set)} held_out={len(held_out_set)}")

    srs_dir = Path(__file__).resolve().parent.parent / "data" / "srs"
    output = run_full_experiment(
        initial_srs_v1(),
        healing_set,
        held_out_set,
        llm_client,
        max_rounds=args.max_rounds,
        adaptive_n_per_mode=args.adaptive_n,
        srs_dir=srs_dir,
    )

    # --- 통계 검정 (thesis.md §3.5.3) ---
    first_round = output["healing_rounds"][0]
    last_round = output["healing_rounds"][-1]

    # 대응표본: 같은 scenario_id 순서로 정렬해 짝을 맞춘다.
    first_by_id = {r["scenario_id"]: r["score"] for r in first_round["results"]}
    last_by_id = {r["scenario_id"]: r["score"] for r in last_round["results"]}
    common_ids = [sid for sid in first_by_id if sid in last_by_id]
    wilcoxon_result = paired_wilcoxon(
        [first_by_id[sid] for sid in common_ids], [last_by_id[sid] for sid in common_ids]
    )

    healing_final_scores = [r["score"] for r in last_round["results"]]
    held_out_scores = [r["score"] for r in output["held_out"]["results"]]
    mannwhitney_result = independent_mannwhitney(healing_final_scores, held_out_scores)

    chi2_result = chi_square_independence(
        (last_round["pass_count"], last_round["warning_count"], last_round["fail_count"]),
        (
            output["held_out"]["pass_count"],
            output["held_out"]["warning_count"],
            output["held_out"]["fail_count"],
        ),
    )

    bb = output["adaptive_blackbox"]
    wb = output["adaptive_whitebox"]
    adaptive_chi2_result = chi_square_independence(
        (bb["pass_count"], bb["warning_count"], bb["fail_count"]),
        (wb["pass_count"], wb["warning_count"], wb["fail_count"]),
    )

    output["stats"] = {
        "wilcoxon_v1_vs_final_healing_set": asdict(wilcoxon_result),
        "mannwhitney_healing_final_vs_held_out": asdict(mannwhitney_result),
        "chisquare_healing_final_vs_held_out": asdict(chi2_result),
        "chisquare_adaptive_blackbox_vs_whitebox": asdict(adaptive_chi2_result),
    }
    output["provider"] = provider
    output["run_at_utc"] = datetime.now(timezone.utc).isoformat()

    out_path = args.output or (
        Path(__file__).resolve().parent.parent
        / "data"
        / "results"
        / f"experiment_{provider}_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.json"
    )
    save_experiment_output(output, out_path)

    # --- 논문 §5.3 표 형식 요약 출력 ---
    print("\n평가 회차 | 적용 명세서 | PASS | WARNING | FAIL | 총점 | 준수율")
    for round_data in output["healing_rounds"]:
        print(
            f"{round_data['label']:>10} | {round_data['srs_version']:>6} | "
            f"{round_data['pass_count']:>4} | {round_data['warning_count']:>7} | "
            f"{round_data['fail_count']:>4} | {round_data['total_score']:>4} | "
            f"{round_data['compliance_rate']}%"
        )
    for key in ("held_out", "adaptive_blackbox", "adaptive_whitebox"):
        d = output[key]
        print(
            f"{d['label']:>10} | {d['srs_version']:>6} | {d['pass_count']:>4} | "
            f"{d['warning_count']:>7} | {d['fail_count']:>4} | {d['total_score']:>4} | "
            f"{d['compliance_rate']}%"
        )

    print(f"\n[run_experiment] 결과 저장: {out_path}")
    if provider == "mock":
        print(
            "\n*** 주의: mock 모드 결과입니다. 파이프라인 동작 검증용일 뿐, "
            "논문에 쓸 실제 데이터가 아닙니다. ***"
        )


if __name__ == "__main__":
    main()
