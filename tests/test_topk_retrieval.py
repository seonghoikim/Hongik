"""kb_v5 top-k retrieval (2026-10-16): similar-model documents can be retrieved together."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hongik_selfheal import knowledge_base as kb  # noqa: E402


def test_topk_mixes_sources_and_keeps_keyword_default(tmp_path):
    (tmp_path / "A21.txt").write_text("드럼 세탁기 PLX-W21 용량 21kg 소비전력 300W", encoding="utf-8")
    (tmp_path / "A24.txt").write_text("드럼 세탁기 PLX-W24 용량 24kg 소비전력 350W", encoding="utf-8")
    kb.configure_retrieval("topk", doc_dirs=(tmp_path,), top_k=2)
    try:
        ctx = kb.retrieve("드럼 세탁기 용량 알려줘")
        assert "A21.txt" in ctx and "A24.txt" in ctx      # near-identical models come back together
        assert kb.current_kb_version() == "kb_v5"
        assert kb.snapshot_dict()["retrieval"]["top_k"] == 2
    finally:
        kb.configure_retrieval("keyword")
    assert kb.current_kb_version() == kb.KB_VERSION
