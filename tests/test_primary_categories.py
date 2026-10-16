"""분석 계획 v2: H1~H3는 주 지표 범주(RAG 오염·개인정보 유출)로 계산한다 (2026-10-16)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from hongik_selfheal.attack_taxonomy import CORE_KEYS, PRIMARY_KEYS


def test_primary_keys_are_the_two_diagnosed_categories():
    assert PRIMARY_KEYS == ("rag_poisoning", "pii_leak")
    assert set(PRIMARY_KEYS) < set(CORE_KEYS)          # 중간안: 핵심 5개는 그대로, 주 지표만 2개


def test_run_experiment_uses_primary_categories_for_hypotheses():
    import run_experiment as rx
    assert rx._is_primary_category("rag_poisoning") and rx._is_primary_category("pii_leak")
    for k in ("impersonation", "misinformation", "metadata_leak"):
        assert not rx._is_primary_category(k) and rx._is_core_category(k)


def test_response_client_answers_while_primary_judges():
    """--response-provider: 챗봇 응답만 다른 모델로 만들고 채점은 주 모델이 한다 (2026-10-16)."""
    from hongik_selfheal.experiment import evaluate_set
    from hongik_selfheal.factual_attacks import rag_poisoning_scenarios
    from hongik_selfheal.llm_client import MockLLMClient
    from hongik_selfheal.srs import initial_srs_v1

    class Spy(MockLLMClient):
        def __init__(self):
            super().__init__()
            self.systems = []

        def complete(self, system_prompt, user_prompt, temperature=0.0, **kw):
            self.systems.append(system_prompt)
            return super().complete(system_prompt, user_prompt, temperature=temperature, **kw)

    judge, responder = Spy(), Spy()
    evaluate_set("t", initial_srs_v1(), rag_poisoning_scenarios(2), judge, response_client=responder)
    assert responder.systems and judge.systems
    from hongik_selfheal.llm_client import JUDGE_MARKER
    assert all(JUDGE_MARKER not in s for s in responder.systems)     # 응답 모델은 채점하지 않는다
    assert all(JUDGE_MARKER in s for s in judge.systems)             # 주 모델은 채점만 한다
