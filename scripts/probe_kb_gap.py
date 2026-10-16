# -*- coding: utf-8 -*-
"""조건 2: 지식 베이스 공백에서의 허위 전제 (진단, 설계는 docs/probe_condition2_20261016.md에 실행 전 고정).

같은 허위 전제 문항 12개를 두 조건으로 짝지어 돌린다.
  present: 지금과 같은 검색(정답 문서 포함 가능)
  absent : 해당 상품 문서를 검색 대상에서 뺌(비슷한 모델 문서는 그대로)
응대 정책 v1.0, 보강 없이 1회, 주 모델. 결과는 data/results/kb_gap_<run>.json (문항별 응답 포함).

    python3 scripts/probe_kb_gap.py --mode real
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from hongik_selfheal.attack_generator import AttackScenario  # noqa: E402
from hongik_selfheal.config import load_config  # noqa: E402
from hongik_selfheal.crawled_facts import load_crawled_facts  # noqa: E402
from hongik_selfheal.experiment import evaluate_set  # noqa: E402
from hongik_selfheal.factual_attacks import _FALSE_PREMISE, _fill, _oracle, value_in_name  # noqa: E402
from hongik_selfheal.knowledge_base import configure_retrieval, current_kb_version, set_retrieval_exclusions  # noqa: E402
from hongik_selfheal.llm_client import build_ensemble_pool  # noqa: E402
from hongik_selfheal.srs import initial_srs_v1  # noqa: E402
from hongik_selfheal.stats import mcnemar_exact  # noqa: E402
from probe_difficulty import FAILED, item_records  # noqa: E402

CONDITIONS = ("present", "absent")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["mock", "real"], default="mock")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=21)
    ap.add_argument("--top-k", type=int, default=4)
    args = ap.parse_args()

    config = load_config()
    configure_retrieval("topk", doc_dirs=(ROOT / "data" / "rag", ROOT / "data" / "rag" / "crawled"), top_k=args.top_k)
    manifest = json.loads((ROOT / "data" / "rag" / "crawled" / "manifest.json").read_text(encoding="utf-8"))
    doc_of_url = {m["url"]: f"crawled/{m['file']}" for m in manifest}
    facts = [f for f in load_crawled_facts(ROOT / "data" / "rag" / "crawled" / "scan_index.jsonl")
             if not value_in_name(f) and f.source.split()[0] in doc_of_url]
    random.Random(args.seed).shuffle(facts)
    facts = facts[:args.n]
    scenarios, own_doc = [], {}
    for i, f in enumerate(facts):
        false = f.false_values[0]
        text = _fill(_FALSE_PREMISE[i % len(_FALSE_PREMISE)], f, false)
        scenarios.append(AttackScenario(id=f"misinformation-gap-{i + 1}", category="misinformation", text=text,
                                        oracle=_oracle(f, false, "mis")))
        own_doc[text] = doc_of_url[f.source.split()[0]]
    client = build_ensemble_pool(config, force_provider=args.mode)["anthropic"]

    run_id = f"kb_gap_{args.mode}_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}"
    report = {"run_id": run_id, "kb_version": current_kb_version(), "design": "docs/probe_condition2_20261016.md",
              "n": len(scenarios), "conditions": {}}
    intact: dict[str, list[int]] = {}
    for cond in CONDITIONS:
        set_retrieval_exclusions({t: {d} for t, d in own_doc.items()} if cond == "absent" else {})
        summary = evaluate_set(f"kb-gap-{cond}", initial_srs_v1(), scenarios, client,
                               unit_temperature=config.llm_temperature, judge_temperature=config.judge_temperature)
        items = item_records(summary.results, scenarios)
        for it, sc in zip(items, scenarios):
            ctx = it["retrieved_context"].replace(" ", "").replace(",", "")
            it["own_doc"] = own_doc[sc.text]
            it["own_doc_retrieved"] = f"[출처:{own_doc[sc.text]}]" in ctx
            it["false_value_in_context"] = any(t.replace(" ", "").replace(",", "") in ctx for t in sc.oracle["false_tokens"])
            it["true_value_in_context"] = any(t.replace(" ", "").replace(",", "") in ctx for t in sc.oracle["true_tokens"])
        intact[cond] = [int(i["info_integrity"] not in FAILED) for i in items]
        kinds = [i["answer_kind"] for i in items]
        report["conditions"][cond] = {
            "info_failed": sum(1 - x for x in intact[cond]), "info_counts": summary.info_counts,
            "answer_kind": {k: kinds.count(k) for k in sorted(set(kinds))},
            "own_doc_retrieved": sum(i["own_doc_retrieved"] for i in items),
            "false_value_in_context": sum(i["false_value_in_context"] for i in items),
            "items": items,
        }
        c = report["conditions"][cond]
        print(f"{cond:7s} 정보 무결성 실패 {c['info_failed']}/{len(items)}  응답 값 {c['answer_kind']}  "
              f"정답 문서 검색 {c['own_doc_retrieved']}  맥락에 틀린 값 {c['false_value_in_context']}")
    set_retrieval_exclusions({})
    t = mcnemar_exact(intact["present"], intact["absent"])
    report["mcnemar_present_vs_absent"] = {"statistic": t.statistic, "p_value": t.p_value}
    print(f"맥니마 정확검정(정답 있음 대 없음) p={t.p_value:.4g}")
    out = ROOT / "data" / "results" / ("mock" if args.mode == "mock" else "") / f"{run_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    main()
