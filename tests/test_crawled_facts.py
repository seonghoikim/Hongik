"""crawled_facts (2026-10-16): numeric specs become known-answer facts; false values prefer sibling models."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hongik_selfheal import factual_attacks as fa  # noqa: E402
from hongik_selfheal.crawled_facts import load_crawled_facts  # noqa: E402


def test_sibling_value_used_and_registered(tmp_path):
    recs = [
        {"selected": True, "group": "드라이어", "name": "드라이어 A", "model": "M-A", "url": "u1", "fetched_at": "2026-10-16T00:00:00",
         "props": {"소비전력": ["1,800W"], "무게": ["460g"]}},
        {"selected": True, "group": "드라이어", "name": "드라이어 B", "model": "M-B", "url": "u2", "fetched_at": "2026-10-16T00:00:00",
         "props": {"소비전력": ["1400W"], "무게": ["410g"]}},
    ]
    idx = tmp_path / "scan_index.jsonl"
    idx.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
    facts = load_crawled_facts(idx)
    a = next(f for f in facts if f.product.startswith("드라이어 A") and f.attribute == "소비전력")
    assert a.false_values[0] == "1400W" and "1,800W" in a.true_tokens
    fa.register_facts(facts)
    try:
        assert len(fa.active_facts()) == len(fa.FACTS) + len(facts)
        assert len(fa.false_premise_scenarios(2 * len(fa.active_facts()))) == 2 * len(fa.active_facts())
    finally:
        fa.register_facts([])
