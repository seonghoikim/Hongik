#!/usr/bin/env python3
"""교차 심판관 재검증(cross-judge check) — "방어가 실제로 잘된 건지, 심판관이
후한 건지"를 구분하기 위한 진단 스크립트.

기존 cross_model_verify(§3.5.5)는 응답 생성 모델을 바꾸고 심판관은 고정해서
"응답 모델 차이"만 격리한다. 이 스크립트는 반대로 이미 저장된 (공격문, 챗봇
응답) 쌍은 그대로 두고 심판관만 다른 벤더 모델로 바꿔서 다시 채점시킨다.
등급이 그대로면 원래 채점이 신뢰할 만하다는 근거가 되고, 다른 심판관이
등급을 낮추면 원래 심판관(anthropic)이 후하게 채점했을 가능성을 시사한다.

사용법:
    PYTHONPATH=src python3 scripts/cross_judge_check.py \
        data/results/experiment_real_20260803_135419.json \
        --judges openai gemini
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hongik_selfheal.config import load_config  # noqa: E402
from hongik_selfheal.judge import evaluate_response  # noqa: E402
from hongik_selfheal.llm_client import LLMRefusalError, build_ensemble_pool  # noqa: E402
from hongik_selfheal.srs import SRS  # noqa: E402

_GRADE_RANK = {"FAIL": 1, "WARNING": 2, "PASS": 3}


def load_srs_prompt(srs_dir: Path, version: str, cache: dict[str, str]) -> str:
    if version not in cache:
        cache[version] = SRS.load(srs_dir / f"{version}.json").render_system_prompt()
    return cache[version]


def collect_transcripts(data: dict, srs_dir: Path) -> list[dict]:
    cache: dict[str, str] = {}
    items: list[dict] = []

    stages = [("healing_final", data["healing_rounds"][-1])]
    for key in ("held_out", "adaptive_blackbox", "adaptive_whitebox"):
        stages.append((key, data[key]))

    for stage_name, summary in stages:
        system_prompt = load_srs_prompt(srs_dir, summary["srs_version"], cache)
        for r in summary["results"]:
            items.append({
                "stage": stage_name,
                "scenario_id": r["scenario_id"],
                "category": r["category"],
                "system_prompt": system_prompt,
                "attack_prompt": r["attack_prompt"],
                "chatbot_response": r["chatbot_response"],
                "original_score": r["score"],
                "original_grade": r["grade"],
            })
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_json", type=Path)
    parser.add_argument("--srs-dir", type=Path, default=Path("data/srs"))
    parser.add_argument("--judges", nargs="+", default=["openai", "gemini"])
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    data = json.loads(args.experiment_json.read_text(encoding="utf-8"))
    original_judge = data["primary_provider"]
    transcripts = collect_transcripts(data, args.srs_dir)
    print(f"[cross_judge_check] 원 판정 {len(transcripts)}건, 원 심판관={original_judge}")

    config = load_config()
    pool = build_ensemble_pool(config, force_provider="real")

    results: list[dict] = []
    tally = defaultdict(lambda: {"agree": 0, "downgrade": 0, "upgrade": 0, "ungradable": 0})

    for judge_name in args.judges:
        if judge_name == original_judge:
            continue
        client = pool[judge_name]
        for t in transcripts:
            try:
                judged = evaluate_response(
                    t["system_prompt"], t["attack_prompt"], t["chatbot_response"], client, temperature=0.0
                )
            except LLMRefusalError as e:
                tally[judge_name]["ungradable"] += 1
                results.append({**t, "alt_judge": judge_name, "alt_grade": None, "alt_score": None, "error": str(e)})
                continue

            orig_rank = _GRADE_RANK[t["original_grade"]]
            new_rank = _GRADE_RANK[judged.grade]
            if new_rank == orig_rank:
                tally[judge_name]["agree"] += 1
            elif new_rank < orig_rank:
                tally[judge_name]["downgrade"] += 1
            else:
                tally[judge_name]["upgrade"] += 1

            results.append({
                **t,
                "alt_judge": judge_name,
                "alt_grade": judged.grade,
                "alt_score": judged.score,
                "alt_reason": judged.reason,
            })
            print(
                f"  [{judge_name}] {t['stage']}:{t['scenario_id']} "
                f"{t['original_grade']}({t['original_score']}) -> {judged.grade}({judged.score})"
                + ("  <<< 등급 하락" if new_rank < orig_rank else "")
            )

    print("\n=== 교차 심판관 재검증 요약 ===")
    for judge_name, counts in tally.items():
        total = sum(counts.values())
        agree_rate = round(counts["agree"] / total * 100, 1) if total else 0.0
        print(
            f"{judge_name}: 총 {total}건 중 동의 {counts['agree']}건({agree_rate}%), "
            f"등급 하락(더 엄격) {counts['downgrade']}건, 등급 상승(더 후함) {counts['upgrade']}건, "
            f"채점불가 {counts['ungradable']}건"
        )
    if any(c["downgrade"] for c in tally.values()):
        print("\n-> 다른 벤더 심판관이 등급을 낮춘 사례가 있음: 원 심판관(anthropic)이 후하게 채점했을 가능성 있음.")
    else:
        print("\n-> 모든 대안 심판관이 동의하거나 더 엄격했음: 원래 채점이 관대해서가 아니라 실제로 방어가 된 것이라는 근거.")

    out_path = args.output or args.experiment_json.with_name(
        args.experiment_json.stem.replace("experiment_", "cross_judge_") + ".json"
    )
    out_path.write_text(json.dumps({"tally": tally, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[cross_judge_check] 상세 결과 저장: {out_path}")


if __name__ == "__main__":
    main()
