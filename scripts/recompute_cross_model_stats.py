#!/usr/bin/env python3
"""Recompute the cross-model tests of existing runs as repeated-measures tests.

The same held-out items are answered by all three backends, so the backends are
related samples (program review 2026-10-11, 2.2). Scores go to Friedman, the
top-grade indicator (PASS in 3-level runs, FULL_DEFENSE in 4-level runs) goes to
Cochran's Q. The old Kruskal-Wallis / chi-square values are printed next to them.
No API call is made; only data/results/*.json is read.

    PYTHONPATH=src python3 scripts/recompute_cross_model_stats.py
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hongik_selfheal.stats import cochran_q, friedman  # noqa: E402

RUNS = [
    ("7차", "experiment_real_20260804_060902.json"),
    ("8차", "experiment_real_20260804_082642.json"),
    ("9차", "experiment_real_20260804_102353.json"),
    ("10차 (baseline)", "ablation_baseline.json"),
    ("11차 (5W1H)", "ablation_5w1h.json"),
    ("12차 (baseline)", "pilot_5w1h_baseline.json"),
    ("13차 (5W1H)", "pilot_5w1h_5w1h.json"),
]
TOP = {"PASS", "FULL_DEFENSE"}


def recompute(label: str, path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    cm = d["cross_model"]
    items = cm["results"]
    backends = list(items[0]["backend_scores"])
    complete = [r for r in items if all(r["backend_scores"].get(b) is not None for b in backends)]
    scores = [[r["backend_scores"][b] for r in complete] for b in backends]
    tops = [[1 if r["backend_grades"][b] in TOP else 0 for r in complete] for b in backends]
    fr = friedman(*scores)
    cq = cochran_q(*tops)
    old = d.get("stats", {})
    old_kw = (old.get("kruskalwallis_cross_model_backends") or {}).get("p_value")
    old_chi = (old.get("chisquare_cross_model_backends") or {}).get("p_value")
    return {
        "run": label,
        "file": path.name,
        "srs_version": cm["srs_version"],
        "n_items": len(complete),
        "backends": backends,
        "top_grade_rate": {b: round(100 * sum(t) / len(t), 1) for b, t in zip(backends, tops)},
        "mean_score": {b: round(sum(s) / len(s), 3) for b, s in zip(backends, scores)},
        "validated_rate": cm.get("cross_model_validated_rate"),
        "friedman": asdict(fr) if fr else None,
        "cochran_q": asdict(cq) if cq else None,
        "old_kruskal_wallis_p": old_kw,
        "old_chisquare_p": old_chi,
    }


def fmt(p):
    if p is None:
        return "-"
    return f"{p:.3g}" if p >= 0.001 else f"{p:.2e}"


def main() -> None:
    out = [recompute(label, ROOT / "data" / "results" / name) for label, name in RUNS]
    dst = ROOT / "data" / "results" / "recomputed_cross_model_stats.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("| 실행 | SRS | n | 최상위 등급률 (openai/gemini/anthropic) | Friedman p | Cochran's Q p | (기존 KW p) | (기존 χ² p) |")
    print("|---|---|---|---|---|---|---|---|")
    for r in out:
        rates = " / ".join(f"{r['top_grade_rate'][b]}" for b in r["backends"])
        fp = r["friedman"]["p_value"] if r["friedman"] else None
        cp = r["cochran_q"]["p_value"] if r["cochran_q"] else None
        print(f"| {r['run']} | {r['srs_version']} | {r['n_items']} | {rates} | {fmt(fp)} | {fmt(cp)} "
              f"| {fmt(r['old_kruskal_wallis_p'])} | {fmt(r['old_chisquare_p'])} |")
    print("saved", dst)


if __name__ == "__main__":
    main()
