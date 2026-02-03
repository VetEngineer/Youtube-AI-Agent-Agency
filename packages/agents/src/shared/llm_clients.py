"""LLM 클라이언트 팩토리.

각 에이전트가 사용할 LLM 인스턴스를 생성합니다.
환경변수에서 API 키를 로드하며, 키가 없으면 명확한 에러를 발생시킵니다.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from .config import AppSettings


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """AppSettings 싱글턴을 반환합니다."""
    return AppSettings()


def create_openai_client(
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: int = 4096,
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
    )


def create_anthropic_client(
    model: str = "claude-sonnet-4-20250514",
    temperature: float = 0.7,
    max_tokens: int = 4096,
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
    )
