#!/usr/bin/env python3
"""§3.6.2 경량 표본 검토(Lightweight Spot-Check)용 블라인드 표본 추출.

실험 결과 JSON(run_experiment.py 산출물)에서 채점 대상을 전부 모아 등급이
골고루 섞이도록 층화추출한 뒤, 점수를 가린 "블라인드 검토 파일"과 정답이 담긴
"정답지"를 분리해서 저장한다. 연구자는 블라인드 파일만 보고 직접 채점하고,
다 채우면 spotcheck_compare.py로 정답지와 대조해 일치율을 계산한다.

사용법:
    PYTHONPATH=src python3 scripts/spotcheck_sample.py data/results/experiment_real_....json --n 20
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def _collect_candidates(output: dict) -> list[dict]:
    candidates: list[dict] = []

    single_judgment_sources = [
        ("healing_final", output["healing_rounds"][-1]["results"]),
        ("held_out", output["held_out"]["results"]),
        ("adaptive_blackbox", output["adaptive_blackbox"]["results"]),
        ("adaptive_whitebox", output["adaptive_whitebox"]["results"]),
    ]
    for source, results in single_judgment_sources:
        for r in results:
            candidates.append({
                "sample_id": f"{source}:{r['scenario_id']}",
                "source": source,
                "category": r["category"],
                "attack_prompt": r["attack_prompt"],
                "chatbot_response": r["chatbot_response"],
                "_judge_score": r["score"],
                "_judge_grade": r["grade"],
                "_judge_reason": r["reason"],
            })

    for r in output["cross_model"]["results"]:
        for backend in r["backend_scores"]:
            candidates.append({
                "sample_id": f"cross_model:{backend}:{r['scenario_id']}",
                "source": f"cross_model:{backend}",
                "category": r["category"],
                "attack_prompt": r["attack_prompt"],
                "chatbot_response": r["backend_responses"][backend],
                "_judge_score": r["backend_scores"][backend],
                "_judge_grade": r["backend_grades"][backend],
                "_judge_reason": r["backend_reasons"][backend],
            })

    return candidates


def _stratified_sample(candidates: list[dict], n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    # 4단계 Level 체계(thesis.md §4.1.1) - 등급별 균등 배분을 목표로 하되,
    # 실제로 등장한 등급만 키로 삼는다(호출부가 어떤 grade 문자열 집합을 쓰는지
    # 여기서 미리 알 필요가 없도록 일반화).
    by_grade: dict[str, list[dict]] = {}
    for c in candidates:
        by_grade.setdefault(c["_judge_grade"], []).append(c)
    for bucket in by_grade.values():
        rng.shuffle(bucket)

    # 등급별 균등 배분을 목표로 하되, 특정 등급의 표본이 적으면(예: BREACH가 희귀)
    # 있는 만큼만 가져오고 남는 몫은 다른 등급에서 채운다.
    grades = list(by_grade)
    quota = {g: n // len(grades) for g in grades}
    remainder = n - sum(quota.values())
    for g in grades[:remainder]:
        quota[g] += 1

    sample: list[dict] = []
    leftover: list[dict] = []
    for g in grades:
        take = min(quota[g], len(by_grade[g]))
        sample.extend(by_grade[g][:take])
        leftover.extend(by_grade[g][take:])

    if len(sample) < n:
        rng.shuffle(leftover)
        sample.extend(leftover[: n - len(sample)])

    rng.shuffle(sample)
    return sample


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_json", type=Path, help="run_experiment.py가 저장한 결과 JSON 경로")
    parser.add_argument("--n", type=int, default=20, help="추출할 표본 수 (기본 20)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    output = json.loads(args.results_json.read_text(encoding="utf-8"))
    candidates = _collect_candidates(output)
    if not candidates:
        raise SystemExit("채점 대상이 결과 파일에 없습니다.")

    sample = _stratified_sample(candidates, args.n, args.seed)

    out_dir = args.output_dir or args.results_json.parent
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    blind_path = out_dir / f"spotcheck_blind_{run_id}.json"
    answer_key_path = out_dir / f"spotcheck_answer_key_{run_id}.json"

    blind_items = [
        {
            "sample_id": c["sample_id"],
            "source": c["source"],
            "category": c["category"],
            "attack_prompt": c["attack_prompt"],
            "chatbot_response": c["chatbot_response"],
            "researcher_score": None,  # 1|2|3|4 직접 채점해서 채울 것
            "researcher_grade": None,  # "FULL_DEFENSE"|"FUNCTIONAL_DEFENSE"|"PARTIAL_EXPOSURE"|"BREACH"
            "researcher_note": "",
        }
        for c in sample
    ]
    answer_key = {
        c["sample_id"]: {
            "judge_score": c["_judge_score"],
            "judge_grade": c["_judge_grade"],
            "judge_reason": c["_judge_reason"],
        }
        for c in sample
    }

    blind_path.write_text(json.dumps(blind_items, ensure_ascii=False, indent=2), encoding="utf-8")
    answer_key_path.write_text(json.dumps(answer_key, ensure_ascii=False, indent=2), encoding="utf-8")

    grade_counts: dict[str, int] = {}
    for c in sample:
        grade_counts[c["_judge_grade"]] = grade_counts.get(c["_judge_grade"], 0) + 1
    print(f"[spotcheck_sample] 전체 채점 대상 {len(candidates)}건 중 {len(sample)}건 추출 (등급 분포: {grade_counts})")
    print(f"[spotcheck_sample] 블라인드 검토 파일: {blind_path}")
    print(f"[spotcheck_sample] 정답지 (검토 끝나기 전엔 열어보지 말 것): {answer_key_path}")
    print(
        "\n다음 단계: blind 파일을 열어 각 항목의 attack_prompt/chatbot_response만 보고 "
        "researcher_score(1~4)/researcher_grade(FULL_DEFENSE|FUNCTIONAL_DEFENSE|PARTIAL_EXPOSURE|BREACH)를 "
        "직접 채운 뒤, spotcheck_compare.py로 정답지와 대조하세요."
    )


if __name__ == "__main__":
    main()
