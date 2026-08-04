#!/usr/bin/env python3
"""전체 실험 실행: 공격 시나리오 생성 → 자가 치유 루프 → 헬드아웃 검증 →
적응형 재공격 → 교차 모델 검증 → 통계 검정 → 결과 저장.

사용법:
    PYTHONPATH=src python3 scripts/run_experiment.py --mode mock
    PYTHONPATH=src python3 scripts/run_experiment.py --mode real --n-per-category 10

주의: --mode mock 은 API 키 없이 파이프라인 배선만 검증하는 용도입니다.
      논문에 쓸 실제 실험 결과는 반드시 --mode real로 .env에 OpenAI/Gemini/
      Anthropic 3종 API 키를 모두 채운 뒤 실행해야 합니다.

      지도교수 피드백(thesis.md §3.5.5): 자가 치유 루프(Unit C/심판관/Meta-Rule
      생성기) → 헬드아웃 검증 → 적응형 재공격까지는 --primary-provider로 지정한
      단일 모델로만 진행합니다. 그 결과(v_final)가 특정 모델에 우연히 맞춰진
      것이 아님을 확인하기 위해, 마지막에 헬드아웃 셋을 이종 LLM 2종을 더한
      3개 백엔드로 다시 실행하고 채점은 primary 모델 심판관 하나로 고정하는
      "교차 모델 검증" 단계를 추가로 수행합니다 (3개 백엔드 중 2개 이상 PASS
      -> 검증됨).

      예외 1건: 공격 문장 자체를 생성하는 레드팀 역할은 --redteam-provider로
      별도 지정합니다 (기본값 openai). 실험 중 Claude Sonnet 5가 "우회 공격
      문장 생성" 요청 자체를 정책상 거부하는 것을 확인했고(실제 시스템 존재·
      승인 여부와 무관하게 적용되는 원칙이라고 명시함), Gemini 3.6 Flash도
      같은 요청에서 실패한 반면 GPT-5.4는 정상 생성했습니다 (thesis.md §3.5.2/§6).
"""
from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hongik_selfheal.attack_generator import generate_full_pool, stratified_split  # noqa: E402
from hongik_selfheal.call_logger import CallLogger  # noqa: E402
from hongik_selfheal.config import load_config  # noqa: E402
from hongik_selfheal.experiment import run_full_experiment, save_experiment_output  # noqa: E402
from hongik_selfheal.fake_members import FAKE_MEMBERS, MEMBERS_VERSION, save_members_snapshot  # noqa: E402
from hongik_selfheal.knowledge_base import KB_VERSION, save_kb_snapshot  # noqa: E402
from hongik_selfheal.llm_client import build_ensemble_pool  # noqa: E402
from hongik_selfheal.srs import initial_srs_v1  # noqa: E402
from hongik_selfheal.stats import (  # noqa: E402
    chi_square_independence,
    chi_square_multi_group,
    independent_mannwhitney,
    kruskal_wallis,
    paired_wilcoxon,
)

_TRACKED_PACKAGES = ["openai", "anthropic", "google-generativeai", "scipy"]


def capture_environment_snapshot() -> dict:
    """재현성 근거 데이터(thesis.md §6): 실행 시점의 정확한 코드/라이브러리
    버전을 남긴다. 모델명 문자열만으로는 "그때 실제로 어떤 코드/SDK가
    응답했는지" 알 수 없으므로 별도로 기록한다."""
    try:
        git_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parent.parent,
            capture_output=True, text=True, timeout=5, check=True,
        ).stdout.strip()
    except Exception:
        git_commit = None

    try:
        git_dirty = bool(subprocess.run(
            ["git", "status", "--porcelain"], cwd=Path(__file__).resolve().parent.parent,
            capture_output=True, text=True, timeout=5, check=True,
        ).stdout.strip())
    except Exception:
        git_dirty = None

    package_versions = {}
    for pkg in _TRACKED_PACKAGES:
        try:
            from importlib.metadata import version
            package_versions[pkg] = version(pkg)
        except Exception:
            package_versions[pkg] = None

    return {
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "python_version": platform.python_version(),
        "package_versions": package_versions,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["mock", "real"], default=None)
    parser.add_argument(
        "--primary-provider",
        choices=["openai", "gemini", "anthropic"],
        default="anthropic",
        help="자가 치유/헬드아웃/적응형 재공격(Unit C·심판관·Meta-Rule 생성기)에 쓸 단일 주 모델",
    )
    parser.add_argument(
        "--redteam-provider",
        choices=["openai", "gemini", "anthropic"],
        default="openai",
        help="공격 시나리오/적응형 재공격 문장 생성 전용 모델 (기본 openai - "
        "Claude Sonnet 5는 정책상 이 역할을 거부함, thesis.md §3.5.2 참조)",
    )
    parser.add_argument("--n-per-category", type=int, default=10, help="치유용/헬드아웃 각 카테고리당 개수")
    parser.add_argument("--max-rounds", type=int, default=10)
    parser.add_argument("--adaptive-n", type=int, default=15, help="블랙박스/화이트박스 각각 개수")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--no-raw-log",
        dest="raw_log",
        action="store_false",
        default=True,
        help="모든 API 호출의 원문 요청/응답을 JSONL로 남기지 않음 (기본은 남김 - "
        "심판관 스팟체크·재현성 근거 데이터 확보용, thesis.md §3.6.2/§6). "
        "저장 용량이 문제되면 이 플래그로 끄거나 raw_calls_*.jsonl을 실행 후 압축/이동할 것",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()
    mode = args.mode or ("mock" if config.provider == "mock" else "real")

    run_id = f"{mode}_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}"
    results_dir = Path(__file__).resolve().parent.parent / "data" / "results"
    rag_dir = Path(__file__).resolve().parent.parent / "data" / "rag"
    kb_snapshot_path = save_kb_snapshot(rag_dir)
    print(f"[run_experiment] RAG 지식베이스 스냅샷({KB_VERSION}): {kb_snapshot_path}")
    members_snapshot_path = save_members_snapshot(rag_dir)
    print(f"[run_experiment] 회원 DB 스냅샷({MEMBERS_VERSION}, {len(FAKE_MEMBERS)}명): {members_snapshot_path}")
    call_logger = None
    if args.raw_log and mode != "mock":
        raw_log_path = results_dir / f"raw_calls_{run_id}.jsonl"
        call_logger = CallLogger(raw_log_path)
        print(f"[run_experiment] 원문 API 호출 로그: {raw_log_path}")

    # 교차 모델 검증(§3.5.5)에 3개 백엔드가 전부 필요하므로 mock이 아니면 항상 3종을 빌드한다.
    cross_model_clients = build_ensemble_pool(config, force_provider=mode, logger=call_logger)
    primary_client = cross_model_clients[args.primary_provider]
    redteam_client = cross_model_clients[args.redteam_provider]

    print(
        f"[run_experiment] mode={mode} primary={args.primary_provider} "
        f"redteam={args.redteam_provider} cross_model_backends={list(cross_model_clients)}"
    )

    pool = generate_full_pool(n_per_category=args.n_per_category * 2, llm_client=redteam_client)
    healing_set, held_out_set = stratified_split(
        pool, healing_per_cat=args.n_per_category, heldout_per_cat=args.n_per_category
    )
    print(f"[run_experiment] healing={len(healing_set)} held_out={len(held_out_set)}")

    srs_dir = Path(__file__).resolve().parent.parent / "data" / "srs"
    output = run_full_experiment(
        initial_srs_v1(),
        healing_set,
        held_out_set,
        primary_client,
        args.primary_provider,
        cross_model_clients,
        redteam_client,
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

    # 교차 모델 검증: 동일 헬드아웃 셋 x 3개 백엔드, 심판관은 고정이므로
    # k-그룹(k=3) 검정으로 "백엔드 간 점수 분포가 통계적으로 구분되지 않는가"를 본다.
    cross_model_results = output["cross_model"]["results"]
    providers = list(output["cross_model"]["per_backend_pass_rate"])
    score_groups = [[r["backend_scores"][p] for r in cross_model_results] for p in providers]
    cross_model_kw = kruskal_wallis(*score_groups)

    def _grade_counts(provider: str) -> tuple[int, int, int]:
        grades = [r["backend_grades"][provider] for r in cross_model_results]
        return (grades.count("PASS"), grades.count("WARNING"), grades.count("FAIL"))

    cross_model_chi2 = chi_square_multi_group(*(_grade_counts(p) for p in providers))

    output["stats"] = {
        "wilcoxon_v1_vs_final_healing_set": asdict(wilcoxon_result),
        "mannwhitney_healing_final_vs_held_out": asdict(mannwhitney_result),
        "chisquare_healing_final_vs_held_out": asdict(chi2_result),
        "chisquare_adaptive_blackbox_vs_whitebox": asdict(adaptive_chi2_result),
        "kruskalwallis_cross_model_backends": asdict(cross_model_kw),
        "chisquare_cross_model_backends": asdict(cross_model_chi2),
    }
    output["kb_version"] = KB_VERSION
    output["members_version"] = MEMBERS_VERSION
    output["mode"] = mode
    output["primary_provider"] = args.primary_provider
    output["redteam_provider"] = args.redteam_provider
    output["cross_model_backends"] = providers
    output["run_at_utc"] = datetime.now(timezone.utc).isoformat()
    output["environment"] = capture_environment_snapshot()

    if call_logger is not None:
        call_logger.close()
        output["usage_summary"] = call_logger.usage_summary()

    out_path = args.output or (results_dir / f"experiment_{run_id}.json")
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

    cm = output["cross_model"]
    print(f"\n[교차 모델 검증] 헬드아웃 셋, 심판관={cm['judge_provider']} 고정")
    for provider, rate in cm["per_backend_pass_rate"].items():
        print(f"  {provider:>10}: PASS율 {rate}%")
    print(f"  2/3 이상 PASS(교차 모델 검증됨) 비율: {cm['cross_model_validated_rate']}%")
    if cm["ungradable_count"]:
        print(f"  ⚠ 심판관 거부로 채점 불가(제외)한 시나리오: {cm['ungradable_count']}건")

    total_ungradable = sum(
        output[key]["ungradable_count"]
        for key in ("held_out", "adaptive_blackbox", "adaptive_whitebox")
    ) + sum(r["ungradable_count"] for r in output["healing_rounds"])
    if total_ungradable:
        print(f"\n⚠ 심판관 거부로 채점 불가(통계에서 제외)한 시나리오 총 {total_ungradable}건 (§3.6.3 참조)")

    if "usage_summary" in output:
        us = output["usage_summary"]
        print(
            f"\n[사용량/비용 요약] 총 호출 {us['total_calls']}건(오류 {us['total_errors']}건), "
            f"입력 {us['total_input_tokens']:,} / 출력 {us['total_output_tokens']:,} 토큰, "
            f"개략 비용 ${us['estimated_cost_usd']} (참고치)"
        )
        for key, bucket in sorted(us["by_provider_role"].items()):
            print(
                f"  {key:>22}: 호출 {bucket['calls']:>4}건 (오류 {bucket['errors']}), "
                f"입력 {bucket['input_tokens']:>7,} / 출력 {bucket['output_tokens']:>7,} 토큰"
            )

    print(f"\n[run_experiment] 결과 저장: {out_path}")
    if mode == "mock":
        print(
            "\n*** 주의: mock 모드 결과입니다. 파이프라인 동작 검증용일 뿐, "
            "논문에 쓸 실제 데이터가 아닙니다. ***"
        )


if __name__ == "__main__":
    main()
