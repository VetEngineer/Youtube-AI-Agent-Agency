"""LLM 응답 파싱 유틸리티.

LLM 응답에서 JSON 블록을 추출하는 공통 함수를 제공합니다.
"""

from __future__ import annotations

import json
import re
from typing import Any


def extract_json_from_response(content: str) -> str:
    """LLM 응답에서 JSON 블록을 추출합니다.

    코드블록(```json ... ```) 내부의 JSON을 우선 추출하고,
    없으면 원본 텍스트를 그대로 반환합니다.
    """
    pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return content.strip()


def parse_json_from_response(content: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
    """LLM 응답에서 JSON을 파싱합니다. 실패 시 기본값을 반환합니다."""
    text = extract_json_from_response(content)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, IndexError):
        return default if default is not None else {}
