"""환경 설정 로딩. 논문 §3.5.2(사용 모델 및 버전)에 대응."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    provider: str
    openai_api_key: str | None
    openai_model: str
    gemini_api_key: str | None
    gemini_model: str
    llm_temperature: float
    judge_temperature: float


def load_config() -> Config:
    return Config(
        provider=os.getenv("LLM_PROVIDER", "mock").lower(),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        judge_temperature=float(os.getenv("JUDGE_TEMPERATURE", "0")),
    )
