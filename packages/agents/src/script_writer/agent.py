"""Script Writer Agent.

ContentPlan + BrandGuide를 입력받아 구조화된 Script를 생성합니다.
Claude (Anthropic)를 사용하여 브랜드 톤앤매너를 유지한 원고를 작성합니다.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.script_writer.prompts import build_system_prompt, build_user_prompt
from src.shared.llm_utils import extract_json_from_response
from src.shared.models import (
    BrandGuide,
    ContentPlan,
    Script,
    ScriptSection,
)

logger = logging.getLogger(__name__)


class ScriptWriterAgent:
    """YouTube 영상 원고를 생성하는 에이전트.

    Attributes:
        llm: LangChain BaseChatModel 인스턴스 (Anthropic Claude 권장).
    """

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm

    async def generate(
        self,
        plan: ContentPlan,
        brand_guide: BrandGuide,
    ) -> Script:
        """콘텐츠 기획안과 브랜드 가이드를 기반으로 원고를 생성합니다.

        Args:
            plan: 콘텐츠 기획안 (주제, 키워드, 메모 등).
            brand_guide: 브랜드 가이드 (톤앤매너 포함).

        Returns:
            구조화된 Script 모델.

        Raises:
            ValueError: plan 또는 brand_guide가 유효하지 않은 경우.
        """
        self._validate_inputs(plan, brand_guide)

        system_prompt = build_system_prompt(brand_guide.tone_and_manner)
        user_prompt = build_user_prompt(
            topic=plan.topic,
            content_type=plan.content_type,
            keywords=plan.target_keywords,
            notes=plan.notes,
        )

        raw_response = await self._invoke_llm(system_prompt, user_prompt)
        return self._parse_response(raw_response)

    async def _invoke_llm(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """LLM을 호출하여 원시 응답 텍스트를 반환합니다."""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = await self._llm.ainvoke(messages)
            return response.content
        except Exception as error:
            logger.error("LLM 호출 실패: %s", error)
            raise RuntimeError(f"원고 생성 중 LLM 호출에 실패했습니다: {error}") from error

    def _parse_response(self, raw: str) -> Script:
        """LLM 응답 텍스트를 Script 모델로 파싱합니다.

        JSON 파싱 실패 시 기본 Script를 반환합니다.
        """
        json_str = _extract_json(raw)

        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as error:
            logger.warning("JSON 파싱 실패, 기본값 반환: %s", error)
            return _build_fallback_script(raw)

        return _build_script_from_dict(data)

    @staticmethod
    def _validate_inputs(
        plan: ContentPlan,
        brand_guide: BrandGuide,
    ) -> None:
        """입력값의 필수 필드를 검증합니다."""
        if not plan.topic.strip():
            raise ValueError("ContentPlan의 topic은 빈 문자열일 수 없습니다.")
        if not brand_guide.brand.name.strip():
            raise ValueError("BrandGuide의 brand.name은 빈 문자열일 수 없습니다.")


def _extract_json(text: str) -> str:
    """응답 텍스트에서 JSON 블록을 추출합니다.

    shared.llm_utils.extract_json_from_response의 얇은 래퍼입니다.
    """
    return extract_json_from_response(text)


def _build_script_from_dict(data: dict) -> Script:
    """딕셔너리에서 Script 모델을 생성합니다."""
    sections = [
        ScriptSection(
            heading=section.get("heading", ""),
            body=section.get("body", ""),
            visual_notes=section.get("visual_notes", ""),
            duration_seconds=section.get("duration_seconds", 0),
        )
        for section in data.get("sections", [])
    ]

    full_text = "\n\n".join(section.body for section in sections if section.body)

    return Script(
        title=data.get("title", "제목 없음"),
        sections=sections,
        full_text=full_text,
        estimated_duration_seconds=data.get("estimated_duration_seconds", 0),
        created_at=datetime.now(),
    )


def _build_fallback_script(raw_response: str) -> Script:
    """파싱 실패 시 원시 응답을 본론에 담은 기본 Script를 반환합니다."""
    fallback_section = ScriptSection(
        heading="원고 (파싱 실패)",
        body=raw_response,
        visual_notes="",
        duration_seconds=0,
    )

    return Script(
        title="제목 없음 (파싱 실패)",
        sections=[fallback_section],
        full_text=raw_response,
        estimated_duration_seconds=0,
        created_at=datetime.now(),
    )
