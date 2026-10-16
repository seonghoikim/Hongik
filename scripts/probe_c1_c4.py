# -*- coding: utf-8 -*-
"""조건 1·4: 문서 간접 인젝션과 꾸며낸 이전 대화 (진단, 설계는 docs/probe_condition1_4_20261016.md에 실행 전 고정).

공격 풀(build_pool_c1_c4.py로 만든 16문항)의 공격 문항과 대조군(-ctrl)을 짝지어 돌린다.
응대 정책 v1.0, 보강 없이 1회, 주 모델, topk 4(조건 2와 같은 검색 설정).
결과는 data/results/c1_c4_<run>.json (문항별 응답, 지식 베이스 버전, 공격 풀 파일 이름 포함).

    python3 scripts/probe_c1_c4.py --mode real
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from hongik_selfheal.attack_generator import load_pool  # noqa: E402
from hongik_selfheal.config import load_config  # noqa: E402
from hongik_selfheal.experiment import evaluate_set  # noqa: E402
from hongik_selfheal.knowledge_base import configure_retrieval, current_kb_version  # noqa: E402
from hongik_selfheal.llm_client import build_ensemble_pool  # noqa: E402
from hongik_selfheal.srs import initial_srs_v1  # noqa: E402
from hongik_selfheal.stats import mcnemar_exact  # noqa: E402
from probe_difficulty import FAILED, item_records  # noqa: E402

DEFAULT_POOL = ROOT / "data" / "results" / "attack_pool_c1_c4_20261016.json"
CONDITIONS = {"c1": "조건 1 문서 간접 인젝션", "c4": "조건 4 꾸며낸 이전 대화"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["mock", "real"], default="mock")
    ap.add_argument("--attack-pool-file", type=Path, default=DEFAULT_POOL)
    ap.add_argument("--top-k", type=int, default=4)
    args = ap.parse_args()

    config = load_config()
    configure_retrieval("topk", doc_dirs=(ROOT / "data" / "rag", ROOT / "data" / "rag" / "crawled"), top_k=args.top_k)
    pool_path = args.attack_pool_file.resolve()
    pool = load_pool(pool_path)
    client = build_ensemble_pool(config, force_provider=args.mode)["anthropic"]

    run_id = f"c1_c4_{args.mode}_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}"
    report = {
        "run_id": run_id, "kb_version": current_kb_version(), "design": "docs/probe_condition1_4_20261016.md",
        "attack_pool_file": str(pool_path.relative_to(ROOT)) if pool_path.is_relative_to(ROOT) else str(pool_path),
        "attack_pool_sha256": hashlib.sha256(pool_path.read_bytes()).hexdigest(),
        "srs": "v1.0", "top_k": args.top_k, "conditions": {},
    }

    for cond, label in CONDITIONS.items():
        attacks = [s for s in pool if s.id.startswith(f"{cond}-") and not s.id.endswith("-ctrl")]
        by_id = {s.id: s for s in pool}
        pairs = [(a, by_id[f"{a.id}-ctrl"]) for a in attacks]
        arms = {"attack": [a for a, _ in pairs], "control": [c for _, c in pairs]}
        out: dict = {"label": label, "n_pairs": len(pairs)}
        intact: dict[str, list[int]] = {}
        for arm, scenarios in arms.items():
            summary = evaluate_set(f"{cond}-{arm}", initial_srs_v1(), scenarios, client,
                                   unit_temperature=config.llm_temperature, judge_temperature=config.judge_temperature)
            items = item_records(summary.results, scenarios)
            # keep pair order regardless of result order
            order = {s.id: k for k, s in enumerate(scenarios)}
            items.sort(key=lambda it: order[it["id"]])
            intact[arm] = [int(i["info_integrity"] not in FAILED) for i in items]
            kinds = [i["answer_kind"] for i in items]
            out[arm] = {
                "info_failed": sum(1 - x for x in intact[arm]), "info_counts": summary.info_counts,
                "oracle_broken": sum(i["oracle_verdict"] == "BROKEN" for i in items),
                "answer_kind": {k: kinds.count(k) for k in sorted(set(kinds))},
                "items": items,
            }
            print(f"{cond} {arm:7s} 정보 무결성 실패 {out[arm]['info_failed']}/{len(items)}  "
                  f"코드 판정 훼손 {out[arm]['oracle_broken']}  응답 값 {out[arm]['answer_kind']}")
        t = mcnemar_exact(intact["control"], intact["attack"])
        out["mcnemar_control_vs_attack"] = {"statistic": t.statistic, "p_value": t.p_value}
        print(f"{cond} 맥니마 정확검정(대조군 대 공격) p={t.p_value:.4g} ({len(pairs)}쌍)")
        report["conditions"][cond] = out

    dest = ROOT / "data" / "results" / ("mock" if args.mode == "mock" else "") / f"{run_id}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", dest)


if __name__ == "__main__":
    main()
