"""유닛 B(RAG 검색)용 초소형 지식 베이스.

실제 벡터 DB 대신 키워드 매칭 기반의 단순 검색으로 구현한다. 본 연구의
초점은 검색 정확도가 아니라 '가드레일 구조 자체의 방어력'이므로, RAG는
오염된 외부 데이터가 섞이지 않는 정제된 내부 지식만 반환하는 역할만
수행하면 충분하다 (thesis.md §3 유닛 B 설명).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KBEntry:
    keywords: tuple[str, ...]
    content: str


DEFAULT_KB: tuple[KBEntry, ...] = (
    KBEntry(
        keywords=("냉장고", "냉장고 모델", "용량"),
        content="A사 냉장고 주력 모델은 875L 대용량으로, 스마트 절전 모드를 지원합니다.",
    ),
    KBEntry(
        keywords=("세탁기", "건조기"),
        content="A사 세탁기는 21kg 대용량 드럼 세탁기이며, 건조기와 통합 설치가 가능합니다.",
    ),
    KBEntry(
        keywords=("배송", "설치", "배송일정"),
        content="A사 제품은 결제 후 평균 3~5영업일 내 배송 및 설치가 진행됩니다.",
    ),
    KBEntry(
        keywords=("as", "고장", "수리", "보증"),
        content="A사 제품은 구매일로부터 2년 무상 보증을 제공하며, AS 접수는 고객센터를 통해 안내됩니다.",
    ),
    KBEntry(
        keywords=("환불", "교환", "반품"),
        content="A사는 제품 수령 후 7일 이내 단순 변심 반품·교환을 지원합니다 (제품 상태에 따라 상이).",
    ),
)


def retrieve(user_input: str, kb: tuple[KBEntry, ...] = DEFAULT_KB) -> str:
    """user_input과 키워드가 겹치는 항목만 반환한다 (정제된 컨텍스트만 전달)."""
    matched = [entry.content for entry in kb if any(k in user_input for k in entry.keywords)]
    if not matched:
        return "(관련 내부 지식 없음 - 일반 안내로 응대할 것)"
    return "\n".join(f"- {m}" for m in matched)
