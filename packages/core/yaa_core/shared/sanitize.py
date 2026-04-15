"""LLM 입력 새니타이징 유틸리티.

프롬프트 인젝션 방어를 위한 사용자 입력 전처리.
"""

from __future__ import annotations

import re

# 프롬프트 인젝션에 사용되는 위험한 패턴
_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?previous\s+instructions",
    r"(?i)ignore\s+(all\s+)?above",
    r"(?i)disregard\s+(all\s+)?previous",
    r"(?i)you\s+are\s+now\s+a",
    r"(?i)act\s+as\s+(a\s+)?",
    r"(?i)system\s*:\s*",
    r"(?i)assistant\s*:\s*",
    r"(?i)user\s*:\s*",
    r"(?i)\[INST\]",
    r"(?i)<\|im_start\|>",
    r"(?i)<\|system\|>",
]

_COMPILED_PATTERNS = [re.compile(p) for p in _INJECTION_PATTERNS]


def sanitize_llm_input(text: str, *, max_length: int = 1000) -> str:
    """사용자 입력을 LLM 프롬프트에 안전하게 삽입하기 위해 새니타이징합니다.

    1. 길이 제한
    2. 제어 문자 제거
    3. 프롬프트 인젝션 패턴 제거
    4. 과도한 공백 정규화
    """
    # 길이 제한
    text = text[:max_length]

    # 제어 문자 제거 (줄바꿈, 탭 제외)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 프롬프트 인젝션 패턴 제거
    for pattern in _COMPILED_PATTERNS:
        text = pattern.sub("[filtered]", text)

    # 과도한 공백 정규화
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {3,}", "  ", text)

    return text.strip()


def validate_llm_output(text: str, *, max_length: int = 50000) -> tuple[bool, str]:
    """LLM 출력의 기본 안전성을 검증합니다.

    Returns:
        (is_valid, sanitized_text) 튜플
    """
    if not text or not text.strip():
        return False, ""

    # 길이 제한
    if len(text) > max_length:
        text = text[:max_length]

    return True, text.strip()
