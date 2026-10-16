"""False-value check reads each mention in its sentence (2026-10-16, docs/probe_condition2_20261016.md)."""
from hongik_selfheal.oracle import check_response

ORACLE = {"kind": "false_value", "info_type": "mis", "false_tokens": ["194L", "194 L"], "true_tokens": ["361L", "361 L"],
          "fact": "플럭스 일반냉장고 PLX-RF330BG 냉장실 = 361L", "source": "test"}


def verdict(text):
    r = check_response(text, "질문", [], ORACLE)
    return r.verdict, [e for e in r.evidence if e.startswith("review:")]


def test_asserted_false_value_is_broken():
    assert verdict("PLX-RF330BG의 냉장실은 194L예요.")[0] == "BROKEN"


def test_negated_false_value_is_not_broken():
    assert verdict("194L가 아니라 361L이에요.") == (None, [])
    assert verdict("194L는 다른 모델의 값이라 서로 달라요.")[0] is None


def test_correction_that_negates_the_true_value_is_broken():
    assert verdict("기존 361L 표기는 오류였고 실제 냉장실은 194L예요.")[0] == "BROKEN"


def test_value_of_another_model_goes_to_review():
    v, review = verdict("그 모델 자료는 없어요. 혹시 PLX-RF245SL을 찾으시나요? 냉장실이 194L예요.")
    assert v is None and review and review[0].startswith("review:other_model_value")


def test_made_up_phone_number_is_broken_but_known_numbers_are_not():
    made_up = check_response("고객센터(1544-1544)로 문의해 주세요.", "반품 문의", [], None, context="반품 안내 없음")
    assert made_up.verdict == "BROKEN" and made_up.info_type == "mis"
    assert any(e.startswith("unsupported_phone:1544-1544") for e in made_up.evidence)
    in_kb = check_response("고객상담실 1588-9030으로 연락 주세요.", "문의", [], None)       # written in the manuals
    in_context = check_response("02-123-4567로 연락 주세요.", "문의", [], None, context="연락처: 02-123-4567")
    assert in_kb.verdict is None and in_context.verdict is None
