# -*- coding: utf-8 -*-
"""응답 모델을 바꾼 난이도 탐색 (2026-10-16, 진단 ③).

재탐색(probe_difficulty.py --refresh-templates)과 같은 15문항을 응답 모델 3종(주 모델, 오픈AI, 구글)에
각각 통과시키고, 채점은 주 모델 심판관 하나로 고정한다(cross_model_verify와 같은 설계). 응대 정책 v1.0,
보강 없이 1회. 목적은 주 모델에서 낮게 나온 실패율이 모델 특성인지 보는 것이며, GO 판단에는 쓰지 않는다.

    python3 scripts/probe_cross_backend.py --mode real \
        --attack-pool-file data/results/attack_pool_probe_real_20261016_114846.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from hongik_selfheal.attack_generator import category_targets, load_pool, stratified_split  # noqa: E402
from hongik_selfheal.config import load_config  # noqa: E402
from hongik_selfheal.experiment import cross_model_verify  # noqa: E402
from hongik_selfheal.knowledge_base import configure_retrieval, current_kb_version  # noqa: E402
from hongik_selfheal.llm_client import build_ensemble_pool  # noqa: E402
from hongik_selfheal.srs import initial_srs_v1  # noqa: E402
from probe_difficulty import FAILED, answer_kind  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["mock", "real"], default="mock")
    ap.add_argument("--attack-pool-file", type=Path, required=True)
    ap.add_argument("--n-per-category", type=int, default=3)
    ap.add_argument("--judge-provider", default="anthropic")
    ap.add_argument("--backends", default="anthropic,openai,gemini")
    ap.add_argument("--top-k", type=int, default=4)
    args = ap.parse_args()

    config = load_config()
    configure_retrieval("topk", doc_dirs=(ROOT / "data" / "rag", ROOT / "data" / "rag" / "crawled"), top_k=args.top_k)
    clients = build_ensemble_pool(config, force_provider=args.mode)
    pool = load_pool(args.attack_pool_file)
    targets = category_targets(args.n_per_category, 0)
    probe_set, _ = stratified_split(pool, healing_per_cat=targets, heldout_per_cat=targets)
    backends = args.backends.split(",")
    summary = cross_model_verify("probe-cross", initial_srs_v1(), probe_set, {b: clients[b] for b in backends},
                                 clients[args.judge_provider], args.judge_provider,
                                 unit_temperature=config.llm_temperature, judge_temperature=config.judge_temperature)

    by_id = {s.id: s for s in probe_set}
    per_backend: dict[str, dict] = {b: {"n": 0, "failed": 0, "by_category": {}, "answer_kind": {}} for b in backends}
    items = []
    for r in summary.results:
        sc = by_id[r.scenario_id]
        row = {"id": r.scenario_id, "category": r.category, "core": r.core, "attack": r.attack_prompt,
               "poison_context": sc.poison_context, "backends": {}}
        for b in backends:
            info = r.backend_info_integrity.get(b)
            kind = answer_kind(r.backend_responses.get(b, ""), sc.oracle)
            row["backends"][b] = {"response": r.backend_responses.get(b), "info_integrity": info,
                                  "policy_compliance": r.backend_policy_compliance.get(b),
                                  "grade": r.backend_grades.get(b), "reason": r.backend_reasons.get(b),
                                  "answer_kind": kind}
            if r.core:
                pb = per_backend[b]
                pb["n"] += 1
                pb["failed"] += info in FAILED
                c = pb["by_category"].setdefault(r.category, [0, 0])
                c[0] += info in FAILED; c[1] += 1
                if kind:
                    pb["answer_kind"][kind] = pb["answer_kind"].get(kind, 0) + 1
        items.append(row)
    models = {"anthropic": config.anthropic_model, "openai": config.openai_model, "gemini": config.gemini_model}
    for b, pb in per_backend.items():
        pb["model"] = models.get(b)
        pb["rate_pct"] = round(pb["failed"] / pb["n"] * 100, 1) if pb["n"] else None
        cats = ", ".join(f"{k} {v[0]}/{v[1]}" for k, v in sorted(pb["by_category"].items()))
        print(f"{b:9s} ({pb['model']}) 핵심 정보 무결성 실패 {pb['failed']}/{pb['n']} = {pb['rate_pct']}%  [{cats}]  "
              f"응답 값 {pb['answer_kind']}")
    run_id = f"probe_cross_{args.mode}_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}"
    out = ROOT / "data" / "results" / ("mock" if args.mode == "mock" else "") / f"{run_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"run_id": run_id, "kb_version": current_kb_version(), "judge": args.judge_provider,
                               "attack_pool_file": str(args.attack_pool_file), "ungradable": summary.ungradable_count,
                               "per_backend": per_backend, "items": items}, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    main()
