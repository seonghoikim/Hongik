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


def test_question_label_hides_the_answer_but_keeps_model_codes():
    from hongik_selfheal.factual_attacks import ProductFact, question_label, value_in_name

    def fact(product, value):
        return ProductFact(product, "용량", "은", "이", value, (value,), ("1L",), "test")

    leaked = fact("플럭스 160L 스탠드 냉동고 PLX-FF160SL", "160L")
    assert value_in_name(leaked) and question_label(leaked).product == "플럭스 스탠드 냉동고 PLX-FF160SL"
    dryer = fact("건조기 9kg 이하 삼성전자((R)DA9SS4N_00001)", "9kg")
    assert question_label(dryer).product == "건조기 삼성전자((R)DA9SS4N_00001)"
    code_only = fact("플럭스 고음질 사운드 스피커 PLX-BTS10WRBK", "10W")
    assert not value_in_name(code_only) and question_label(code_only) is code_only
