#!/usr/bin/env python3
"""§3.6.2 경량 표본 검토 — 연구자가 채운 블라인드 파일과 정답지를 대조해
일치율을 계산한다. spotcheck_sample.py로 만든 두 파일을 입력으로 받는다.

사용법:
    PYTHONPATH=src python3 scripts/spotcheck_compare.py \\
        data/results/spotcheck_blind_....json data/results/spotcheck_answer_key_....json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("blind_json", type=Path, help="연구자가 채점을 채워 넣은 블라인드 파일")
    parser.add_argument("answer_key_json", type=Path, help="spotcheck_sample.py가 만든 정답지")
    parser.add_argument("--output", type=Path, default=None, help="비교 결과를 저장할 경로(선택)")
    args = parser.parse_args()

    blind_items = json.loads(args.blind_json.read_text(encoding="utf-8"))
    answer_key = json.loads(args.answer_key_json.read_text(encoding="utf-8"))

    missing = [b["sample_id"] for b in blind_items if b.get("researcher_grade") is None]
    if missing:
        raise SystemExit(
            f"researcher_grade가 비어있는 항목이 {len(missing)}건 있습니다 (예: {missing[:5]}). "
            "전부 채점한 뒤 다시 실행하세요."
        )

    rows = []
    agree = 0
    for b in blind_items:
        sid = b["sample_id"]
        if sid not in answer_key:
            raise SystemExit(f"정답지에 없는 sample_id: {sid} (다른 실행의 파일을 섞어 쓴 것 아닌지 확인)")
        key = answer_key[sid]
        matched = b["researcher_grade"] == key["judge_grade"]
        agree += matched
        rows.append({
            "sample_id": sid,
            "source": b["source"],
            "category": b["category"],
            "judge_grade": key["judge_grade"],
            "researcher_grade": b["researcher_grade"],
            "match": matched,
            "judge_reason": key["judge_reason"],
            "researcher_note": b.get("researcher_note", ""),
        })

    n = len(rows)
    rate = round(agree / n * 100, 1) if n else 0.0
    print(f"[spotcheck_compare] 표본 {n}건 중 일치 {agree}건 (일치율 {rate}%)")

    mismatches = [r for r in rows if not r["match"]]
    if mismatches:
        print(f"\n불일치 {len(mismatches)}건:")
        for r in mismatches:
            print(
                f"  - [{r['source']}/{r['category']}] 심판관={r['judge_grade']} vs "
                f"연구자={r['researcher_grade']} | 심판관 근거: {r['judge_reason']}"
            )
    else:
        print("불일치 없음.")

    result = {
        "n": n,
        "agree": agree,
        "agreement_rate": rate,
        "rows": rows,
    }
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[spotcheck_compare] 결과 저장: {args.output}")


if __name__ == "__main__":
    main()
