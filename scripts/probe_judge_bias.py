# -*- coding: utf-8 -*-
"""심판관 자기 응답 선호 편향 점검 (2026-10-16, 진단).

저장된 응답(응답 모델 3종)은 그대로 두고, 심판관만 3종(Claude, GPT-5.4, Gemini)으로 바꿔 다시 채점한다.
정답 대조 코드는 심판관과 무관하므로, 여기서는 심판관 자체의 정보 무결성 판정만 비교한다.

편향이 있다면: 어떤 심판관이 자기 벤더 응답을 다른 심판관보다 더 후하게(유지로) 판정한다.

    python3 scripts/probe_judge_bias.py --mode real \
        --cross-result data/results/probe_cross_real_20261016_141139.json:data/results/attack_pool_rag_v6_20261016.json \
        --cross-result data/results/probe_cross_real_20261016_140749.json:data/results/attack_pool_pii_templates_20261016.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hongik_selfheal.attack_generator import load_pool  # noqa: E402
from hongik_selfheal.config import load_config  # noqa: E402
from hongik_selfheal.experiment import _reference  # noqa: E402
from hongik_selfheal.judge import evaluate_responses  # noqa: E402
from hongik_selfheal.llm_client import build_ensemble_pool  # noqa: E402
from hongik_selfheal.srs import initial_srs_v1  # noqa: E402

JUDGES = ("anthropic", "openai", "gemini")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["mock", "real"], default="mock")
    ap.add_argument("--cross-result", action="append", required=True,
                    help="<probe_cross 결과 json>:<그 실행의 공격 풀 json>")
    args = ap.parse_args()

    config = load_config()
    clients = build_ensemble_pool(config, force_provider=args.mode)
    rows = []          # (scenario, responder, response)
    for pair in args.cross_result:
        res_path, pool_path = pair.split(":")
        pool = {s.id: s for s in load_pool(ROOT / pool_path)}
        for it in json.loads((ROOT / res_path).read_text(encoding="utf-8"))["items"]:
            for responder, v in it["backends"].items():
                if v.get("response"):
                    rows.append((pool[it["id"]], responder, v["response"]))
    srs_text = initial_srs_v1().render_for_judge()
    transcripts = [(s.text, resp, _reference(s), s.poison_context) for s, _, resp in rows]

    verdicts: dict[str, list] = {}
    for j in JUDGES:
        out = evaluate_responses(srs_text, transcripts, clients[j], temperature=config.judge_temperature)
        verdicts[j] = [None if isinstance(r, Exception) else (r.info_integrity or "INTACT") for r in out]
        print(f"심판관 {j}: 채점 {sum(v is not None for v in verdicts[j])}/{len(rows)}")

    # 응답 모델 x 심판관: 정보 무결성 유지 비율
    table: dict[str, dict[str, list[int]]] = {}
    for i, (_, responder, _) in enumerate(rows):
        for j in JUDGES:
            v = verdicts[j][i]
            if v is not None:
                table.setdefault(responder, {}).setdefault(j, []).append(int(v == "INTACT"))
    print("\n응답 모델 \\ 심판관 — 정보 무결성 '유지' 판정 수 / 채점 수")
    print(" " * 12 + "".join(f"{j:>14s}" for j in JUDGES))
    summary = {}
    for responder in JUDGES:
        cells = {j: (sum(table.get(responder, {}).get(j, [])), len(table.get(responder, {}).get(j, []))) for j in JUDGES}
        summary[responder] = cells
        print(f"{responder:12s}" + "".join(f"{f'{a}/{n}':>14s}" for a, n in cells.values()))
    # 심판관 쌍 일치율
    agree = {}
    for a in JUDGES:
        for b in JUDGES:
            if a < b:
                pairs = [(x, y) for x, y in zip(verdicts[a], verdicts[b]) if x and y]
                agree[f"{a}-{b}"] = (sum(x == y for x, y in pairs), len(pairs))
    print("\n심판관 쌍 정보 무결성 판정 일치:", {k: f"{a}/{n}" for k, (a, n) in agree.items()})

    run_id = f"judge_bias_{args.mode}_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}"
    out = ROOT / "data" / "results" / ("mock" if args.mode == "mock" else "") / f"{run_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "run_id": run_id, "sources": args.cross_result, "judges": list(JUDGES),
        "intact_by_responder_and_judge": summary, "judge_agreement": agree,
        "items": [{"id": s.id, "category": s.category, "responder": r, **{f"judge_{j}": verdicts[j][i] for j in JUDGES}}
                  for i, (s, r, _) in enumerate(rows)],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    main()
