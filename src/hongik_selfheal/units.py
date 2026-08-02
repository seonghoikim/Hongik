"""유닛 A~D 파이프라인 (thesis.md 제3장).

유닛 A: 명백한 탈옥/사칭/인코딩 우회만 1차 차단한다. 교묘한 사회공학적
공격(가스라이팅, 어투 강요 등)은 의도적으로 통과시켜 유닛 C(SRS/Meta-Rule)가
방어하도록 한다 - 이래야 자가 치유 루프가 검증할 대상이 남는다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .knowledge_base import DEFAULT_KB, retrieve
from .llm_client import LLMClient
from .srs import SRS

_BLOCK_PATTERNS = [
    re.compile(r"(?i)ignore (all|any|previous) instructions"),
    re.compile(r"(?i)system\s*:\s*"),
    re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),  # 40자 이상 base64 유사 블롭
    re.compile(r"당신은\s*(이제\s*)?개발자\s*모드"),
    re.compile(r"디버그\s*모드로\s*전환"),
]

_OUTPUT_LEAK_PATTERNS = [
    re.compile(r"\[META-RULE"),
    re.compile(r"(?i)system prompt"),
    re.compile(r"시스템\s*프롬프트"),
    re.compile(r"핵심\s*제약\s*조건"),
]

_REFUSAL_MESSAGE = "죄송하지만 그 요청은 도와드릴 수 없어요. 제품 관련해서 궁금하신 점 있으실까요?"


@dataclass
class PipelineResult:
    final_response: str
    blocked_by_unit: str | None  # "A" | "D" | None
    raw_unit_c_response: str
    retrieved_context: str


def unit_a_input_guardrail(user_input: str) -> tuple[bool, str | None]:
    for pattern in _BLOCK_PATTERNS:
        if pattern.search(user_input):
            return True, f"명백한 우회 패턴 탐지: {pattern.pattern}"
    return False, None


def unit_b_retrieve(user_input: str, kb=DEFAULT_KB) -> str:
    return retrieve(user_input, kb)


def unit_c_generate(
    srs: SRS, context: str, user_input: str, llm_client: LLMClient, temperature: float
) -> str:
    system_prompt = srs.render_system_prompt()
    user_prompt = f"[내부 참고 지식]\n{context}\n\n[사용자 입력]\n{user_input}"
    return llm_client.complete(system_prompt, user_prompt, temperature)


def unit_d_output_guardrail(response: str) -> tuple[str, bool]:
    for pattern in _OUTPUT_LEAK_PATTERNS:
        if pattern.search(response):
            return _REFUSAL_MESSAGE, True
    return response, False


def run_pipeline(
    user_input: str,
    srs: SRS,
    llm_client: LLMClient,
    *,
    temperature: float = 0.2,
    kb=DEFAULT_KB,
) -> PipelineResult:
    blocked, reason = unit_a_input_guardrail(user_input)
    if blocked:
        return PipelineResult(
            final_response=_REFUSAL_MESSAGE,
            blocked_by_unit="A",
            raw_unit_c_response="",
            retrieved_context="",
        )

    context = unit_b_retrieve(user_input, kb)
    raw_response = unit_c_generate(srs, context, user_input, llm_client, temperature)
    filtered_response, flagged_d = unit_d_output_guardrail(raw_response)

    return PipelineResult(
        final_response=filtered_response,
        blocked_by_unit="D" if flagged_d else None,
        raw_unit_c_response=raw_response,
        retrieved_context=context,
    )
