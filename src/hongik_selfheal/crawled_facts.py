"""Facts with known answers from the collected product pages (data/rag/crawled, kb_v5, 2026-10-16).

Each collected page gives structured specs (name: value). A numeric spec becomes a ProductFact whose
false values come first from a *similar model in the same group* (same spec name, different value) —
the realistic confusion between near-identical models — and otherwise from a scaled near-miss value.
Prices are left out (the response policy forbids volunteering prices).
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

from .factual_attacks import ProductFact, _num_variants

_NUM = re.compile(r"^\s*([\d,]+(?:\.\d+)?)\s*(kg|g|W|L|ml|cm|mm|m|등급|인치|RPM)\s*$")
_SKIP = ("가격", "판매가", "할인")


def _label(rec: dict) -> str:
    """How a customer would name the product: short name + model."""
    name = re.sub(r"\[[^\]]*\]", "", rec["name"]).strip()
    name = re.sub(r"\([^)]*\)", "", name).strip()
    if rec.get("model") and rec["model"] not in name:
        name = f"{name}({rec['model']})"
    return name


def _particles(attr: str) -> tuple[str, str]:
    last = attr[-1]
    code = ord(last) - 0xAC00
    has_final = 0 <= code < 11172 and code % 28 != 0
    return ("은", "이") if has_final else ("는", "가")


def _near_miss(number: str, unit: str, rng: random.Random) -> str:
    x = float(number.replace(",", ""))
    y = x * rng.choice((0.6, 1.5, 1.8))
    if unit == "등급":
        y = max(1, min(5, round(x) + rng.choice((-2, 2))))
        return f"{int(y)}등급"
    y = round(y, 1) if x < 10 else int(round(y, -1 if x >= 100 else 0))
    text = f"{y:,}" if isinstance(y, int) else f"{y}"
    return f"{text}{unit}"


def load_crawled_facts(index_path: Path, *, seed: int = 3, max_per_product: int = 2) -> list[ProductFact]:
    recs = [json.loads(line) for line in Path(index_path).read_text(encoding="utf-8").splitlines()]
    recs = [r for r in recs if r.get("selected") and r.get("props")]
    rng = random.Random(seed)
    facts: list[ProductFact] = []
    for r in recs:
        numeric = []
        for attr, values in r["props"].items():
            if len(values) != 1 or any(k in attr for k in _SKIP):
                continue
            m = _NUM.match(values[0])
            if m:
                numeric.append((attr, m.group(1), m.group(2)))
        for attr, number, unit in numeric[:max_per_product]:
            true = f"{number}{unit}"
            siblings = []
            for o in recs:
                if o is r or o.get("group") != r.get("group"):
                    continue
                v = (o["props"].get(attr) or [""])[0]
                mm = _NUM.match(v)
                if mm and mm.group(2) == unit and mm.group(1).replace(",", "") != number.replace(",", ""):
                    siblings.append(f"{mm.group(1)}{unit}")
            falses = list(dict.fromkeys(siblings))[:1]
            for _ in range(50):                      # bounded: some specs (e.g. 1등급) have few distinct near-misses
                if len(falses) >= 2:
                    break
                cand = _near_miss(number, unit, rng)
                if cand != true and cand not in falses:
                    falses.append(cand)
            if not falses:
                continue
            topic, subj = _particles(attr)
            facts.append(ProductFact(
                product=_label(r), attribute=attr, topic_particle=topic, subject_particle=subj,
                true_value=true, true_tokens=_num_variants(number, unit), false_values=tuple(falses),
                source=f"{r['url']} 구조화 사양 '{attr}: {true}' (수집 {r['fetched_at'][:10]})",
            ))
    return facts
