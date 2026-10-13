#!/usr/bin/env python3
"""Power of the cross-model Cochran's Q test by number of held-out items (no API call).

Backends answer the same items, so items share a difficulty term: each item is "easy" or "hard"
with probability 1/2 and shifts every backend's pass probability by +rho/2 or -rho/2.
Pass rates come from the pilot runs (7차, 8차, 11차, data/results/recomputed_cross_model_stats.json).
Used in the thesis summary v8, §4.5 and Table 10.

    PYTHONPATH=src python3 scripts/power_simulation_cross_model.py
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from hongik_selfheal.stats import cochran_q  # noqa: E402

SEED, SIMS, RHO, ALPHA = 1, 1000, 0.3, 0.05
PATTERNS = {"7차형 (60.9/60.9/52.2)": [0.609, 0.609, 0.522],
            "8차형 (68.2/50.0/31.8)": [0.682, 0.500, 0.318],
            "11차형 (100/77.3/22.7)": [1.0, 0.773, 0.227]}
SIZES = (24, 38, 40, 80)


def power(rates, n, rng):
    hits = 0
    for _ in range(SIMS):
        groups = [[], [], []]
        for _ in range(n):
            shift = RHO / 2 if rng.random() < 0.5 else -RHO / 2
            for k, p in enumerate(rates):
                groups[k].append(1 if rng.random() < min(1.0, max(0.0, p + shift)) else 0)
        r = cochran_q(*groups)
        if r and r.p_value is not None and r.p_value < ALPHA:
            hits += 1
    return hits / SIMS


def main():
    rng = random.Random(SEED)
    out = {"seed": SEED, "sims": SIMS, "rho": RHO, "alpha": ALPHA, "power": {}}
    for name, rates in PATTERNS.items():
        out["power"][name] = {n: power(rates, n, rng) for n in SIZES}
        print(name, out["power"][name])
    dst = ROOT / "data" / "results" / "power_simulation_cross_model.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", dst)


if __name__ == "__main__":
    main()
