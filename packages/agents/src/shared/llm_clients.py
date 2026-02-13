"""LLM 클라이언트 팩토리.

각 에이전트가 사용할 LLM 인스턴스를 생성합니다.
환경변수에서 API 키를 로드하며, 키가 없으면 명확한 에러를 발생시킵니다.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_openai import ChatOpenAI

from .config import AppSettings

logger = logging.getLogger(__name__)

# ============================================
# LLM 가격표 (USD per token)
# ============================================

LLM_PRICING: dict[str, dict[str, dict[str, float]]] = {
    "openai": {
        "gpt-4o": {"prompt": 2.50 / 1_000_000, "completion": 10.00 / 1_000_000},
        "gpt-4o-mini": {"prompt": 0.15 / 1_000_000, "completion": 0.60 / 1_000_000},
    },
    "anthropic": {
        "claude-sonnet-4-20250514": {
            "prompt": 3.00 / 1_000_000,
            "completion": 15.00 / 1_000_000,
        },
    },
}


def calculate_cost(
    provider: str, model: str, prompt_tokens: int, completion_tokens: int
) -> float:
    """LLM 사용 비용을 계산합니다."""
    provider_pricing = LLM_PRICING.get(provider, {})
    model_pricing = provider_pricing.get(model)
    if model_pricing is None:
        logger.warning(
            "알 수 없는 모델 비용 0 처리: provider=%s, model=%s", provider, model
        )
        return 0.0
    return (prompt_tokens * model_pricing["prompt"]) + (
        completion_tokens * model_pricing["completion"]
    )


# ============================================
# 사용량 수집기 + 콜백
# ============================================


class UsageCollector:
    """파이프라인 실행 중 LLM 사용량을 메모리에 수집합니다."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.failed_count: int = 0

    def create_callback(self, agent: str, provider: str) -> UsageTrackingCallback:
        """에이전트별 콜백을 생성합니다."""
        return UsageTrackingCallback(agent=agent, provider=provider, collector=self)


class UsageTrackingCallback(BaseCallbackHandler):
    """LangChain 콜백으로 토큰/비용을 자동 캡처합니다."""

    def __init__(self, agent: str, provider: str, collector: UsageCollector) -> None:
        super().__init__()
        self.agent = agent
        self.provider = provider
        self.collector = collector

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """LLM 응답에서 토큰 사용량을 추출합니다."""
        try:
            llm_output = response.llm_output or {}
            token_usage = llm_output.get("token_usage") or llm_output.get("usage", {})

            prompt_tokens = token_usage.get("prompt_tokens", 0) or 0
            completion_tokens = token_usage.get("completion_tokens", 0) or 0
            total_tokens = token_usage.get("total_tokens", 0) or (
                prompt_tokens + completion_tokens
            )
            model = llm_output.get("model_name") or llm_output.get("model", "unknown")

            cost = calculate_cost(self.provider, model, prompt_tokens, completion_tokens)

            self.collector.events.append(
                {
                    "agent": self.agent,
                    "provider": self.provider,
                    "model": model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "cost_usd": cost,
                }
            )
        except Exception:
            self.collector.failed_count += 1
            logger.exception(
                "토큰 사용량 추출 실패: agent=%s, provider=%s",
                self.agent,
                self.provider,
            )


# ============================================
# LLM 클라이언트 팩토리
# ============================================


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """AppSettings 싱글턴을 반환합니다."""
    return AppSettings()


def create_openai_client(
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    callbacks: list[BaseCallbackHandler] | None = None,
) -> ChatOpenAI:
    """OpenAI ChatModel 인스턴스를 생성합니다.

    용도: Supervisor, SEO Optimizer, Brand Researcher
    """
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.openai_api_key,
        callbacks=callbacks,
    )


def create_anthropic_client(
    model: str = "claude-sonnet-4-20250514",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    callbacks: list[BaseCallbackHandler] | None = None,
) -> ChatAnthropic:
    """Anthropic ChatModel 인스턴스를 생성합니다.

    용도: Script Writer (원고 생성)
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

    return ChatAnthropic(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.anthropic_api_key,
        callbacks=callbacks,
    )
