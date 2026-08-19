"""모든 실제 LLM API 호출의 원문/토큰 사용량/모델 버전을 근거 데이터로 남긴다
(thesis.md §3.5.2, §3.6.2, §6, 부록). 크래시가 나도 이미 기록된 호출은 남도록
매 호출마다 즉시 JSONL 한 줄씩 append한다 - 실행이 끝날 때 한꺼번에 쓰지 않는다.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

# 참고용 개략 단가($/1M 토큰). 가격은 자주 바뀌므로 실제 논문에 인용하기 전
# 해당 콘솔의 최신 단가로 재확인할 것 - 여기서는 총 비용 "규모감"만 준다.
PRICING_TABLE: dict[str, tuple[float, float]] = {
    "claude-sonnet-5": (3.0, 15.0),
    "gpt-5.4": (2.5, 15.0),
    "gemini-3.6-flash": (1.5, 7.5),
}


@dataclass
class CallRecord:
    timestamp: str
    provider: str
    role: str  # "unit_c" | "judge" | "meta_rule_gen" | "redteam_gen"
    model: str  # 설정된 모델명 (요청 시 지정한 값)
    model_version: str | None  # API 응답이 실제로 echo한 모델 식별자 (있는 경우)
    system_prompt: str
    user_prompt: str
    raw_response: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: float | None
    error: str | None = None
    # 프롬프트 캐싱 적중 여부(2026-08-19, thesis.md 결정로그 44). Anthropic은
    # cache_creation(신규 캐시 기록)/cache_read(캐시 적중) 토큰을 input_tokens와
    # 별도로 반환한다. OpenAI/Gemini는 자동 캐싱이라 "적중된 토큰 수"만
    # 있고 신규 기록이라는 개념이 없어 cache_read_input_tokens만 채워진다.
    cache_creation_input_tokens: int | None = None
    cache_read_input_tokens: int | None = None


class CallLogger:
    """원문 요청/응답을 JSONL로 스트리밍 기록하고, 종료 시 사용량을 집계한다."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", encoding="utf-8")
        self._records: list[CallRecord] = []

    def log(self, record: CallRecord) -> None:
        self._records.append(record)
        self._fh.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()

    def usage_summary(self) -> dict:
        """provider/role별 토큰 합계와 개략 비용을 집계한다 (§6 비용 논의 근거)."""
        by_provider_role: dict[str, dict] = {}
        total_input = 0
        total_output = 0
        total_cost = 0.0
        error_count = 0

        total_cache_creation = 0
        total_cache_read = 0

        for r in self._records:
            key = f"{r.provider}:{r.role}"
            bucket = by_provider_role.setdefault(
                key, {
                    "calls": 0, "input_tokens": 0, "output_tokens": 0, "errors": 0,
                    "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
                }
            )
            bucket["calls"] += 1
            if r.error:
                bucket["errors"] += 1
                error_count += 1
                continue
            in_tok = r.input_tokens or 0
            out_tok = r.output_tokens or 0
            cache_creation = r.cache_creation_input_tokens or 0
            cache_read = r.cache_read_input_tokens or 0
            bucket["input_tokens"] += in_tok
            bucket["output_tokens"] += out_tok
            bucket["cache_creation_input_tokens"] += cache_creation
            bucket["cache_read_input_tokens"] += cache_read
            total_input += in_tok
            total_output += out_tok
            total_cache_creation += cache_creation
            total_cache_read += cache_read

            price = PRICING_TABLE.get(r.model)
            if price:
                in_price, out_price = price
                # Anthropic 프롬프트 캐싱 단가(2026 기준 ephemeral/5분 TTL): 캐시
                # 신규 기록은 기본 입력가의 1.25배, 캐시 적중분은 0.1배. 캐싱을
                # 쓰지 않는 프로바이더/호출은 cache_* 값이 0이라 기존 계산과 동일하다.
                total_cost += (
                    in_tok / 1_000_000 * in_price
                    + out_tok / 1_000_000 * out_price
                    + cache_creation / 1_000_000 * in_price * 1.25
                    + cache_read / 1_000_000 * in_price * 0.1
                )

        return {
            "total_calls": len(self._records),
            "total_errors": error_count,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cache_creation_input_tokens": total_cache_creation,
            "total_cache_read_input_tokens": total_cache_read,
            "estimated_cost_usd": round(total_cost, 4),
            "cost_note": (
                "PRICING_TABLE의 개략 단가로 계산한 참고치입니다. 실제 청구액은 "
                "각 콘솔의 결제 내역을 확인하십시오. 캐시 단가(쓰기 1.25배/읽기 "
                "0.1배)도 근사치입니다."
            ),
            "by_provider_role": by_provider_role,
        }
