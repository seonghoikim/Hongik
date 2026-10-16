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
