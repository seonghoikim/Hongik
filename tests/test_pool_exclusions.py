"""Template generators skip items used in earlier attack pools (2026-10-16)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hongik_selfheal.attack_generator import exclusions_from_pools, pool_overlap, save_pool  # noqa: E402
from hongik_selfheal.customer_data_attacks import pii_template_scenarios  # noqa: E402
from hongik_selfheal.factual_attacks import false_premise_scenarios, rag_poisoning_scenarios  # noqa: E402


def _old_pool(tmp_path):
    old = false_premise_scenarios(4) + rag_poisoning_scenarios(4) + pii_template_scenarios(6)
    path = save_pool(old, tmp_path / "old.json")
    return old, exclusions_from_pools([path])


def test_no_exclusions_keeps_items(tmp_path):
    assert [s.text for s in false_premise_scenarios(5)] == [s.text for s in false_premise_scenarios(5)]
    assert [s.text for s in pii_template_scenarios(6)] == [s.text for s in pii_template_scenarios(6)]


def test_new_items_skip_old_texts_facts_members(tmp_path):
    old, excl = _old_pool(tmp_path)
    new = (false_premise_scenarios(4, exclude=excl) + rag_poisoning_scenarios(4, exclude=excl)
           + pii_template_scenarios(6, exclude=excl))
    assert pool_overlap(new, excl) == []
    old_facts = {s.oracle["fact"] for s in old if s.oracle.get("fact")}
    assert not old_facts & {s.oracle["fact"] for s in new if s.oracle.get("fact")}
    old_members = {s.oracle["member_id"] for s in old if s.oracle.get("member_id")}
    assert not old_members & {s.oracle["member_id"] for s in new if s.oracle.get("member_id")}


def test_overlap_reports_old_items(tmp_path):
    old, excl = _old_pool(tmp_path)
    assert len(pool_overlap(old, excl)) == len(old)


def test_fact_matched_by_source(tmp_path):
    item = false_premise_scenarios(1)[0]
    raw = [{"id": "x", "category": "misinformation", "text": "다른 문장", "split": "unassigned",
            "oracle": {"kind": "false_value", "fact": "옛 상품명 무게 = 1kg", "source": item.oracle["source"]},
            "poison_context": None}]
    path = tmp_path / "older.json"
    path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    assert pool_overlap([item], exclusions_from_pools([path]))
