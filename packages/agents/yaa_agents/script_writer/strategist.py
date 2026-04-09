"""Strategist Agent.

ContentPlan을 받아 구조화된 ScriptOutline을 생성합니다.
Writer가 원고를 작성하기 전 아웃라인을 먼저 기획합니다.
"""

from __future__ import annotations

import json
import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from yaa_core.shared.llm_utils import extract_json_from_response
from yaa_core.shared.models import (
    ContentPlan,
    MainPoint,
    ScriptOutline,
    ToneAndManner,
)

from yaa_agents.script_writer.prompts import (
    build_strategist_system_prompt,
    build_strategist_user_prompt,
)

logger = logging.getLogger(__name__)


class StrategistAgent:
    """YouTube 영상 아웃라인을 기획하는 에이전트."""

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm

    async def plan_outline(
        self,
        plan: ContentPlan,
        tone: ToneAndManner,
        guidelines: str = "",
    ) -> ScriptOutline:
        """콘텐츠 기획안을 바탕으로 아웃라인을 생성합니다.

        Args:
            plan: 콘텐츠 기획안
            tone: 브랜드 톤앤매너
            guidelines: 파일 기반 가이드라인 텍스트 (선택)

        Returns:
            ScriptOutline 모델
        """
        system_msg = build_strategist_system_prompt(tone)
        user_prompt = build_strategist_user_prompt(
            topic=plan.topic,
            content_type=plan.content_type,
            keywords=plan.target_keywords,
            notes=plan.notes,
            guidelines=guidelines,
        )

        messages = [system_msg, HumanMessage(content=user_prompt)]

        try:
            response = await self._llm.ainvoke(messages)
            content = response.content
            if isinstance(content, list):
                content = "".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                )
            return self._parse_response(content)
        except Exception as error:
            logger.error("StrategistAgent LLM 호출 실패: %s", error)
            raise RuntimeError(f"아웃라인 생성 중 LLM 호출에 실패했습니다: {error}") from error

    def _parse_response(self, raw: str) -> ScriptOutline:
        json_str = extract_json_from_response(raw)
        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("Strategist JSON 파싱 실패, fallback 반환: %s", e)
            return ScriptOutline(opening_hook=raw[:500])

        main_points = [
            MainPoint(
                title=p.get("title", ""),
                key_message=p.get("key_message", ""),
                example=p.get("example", ""),
            )
            for p in data.get("main_points", [])
        ]
        return ScriptOutline(
            opening_hook=data.get("opening_hook", ""),
            opening_promise=data.get("opening_promise", ""),
            main_points=main_points,
            closing_summary=data.get("closing_summary", ""),
            closing_action=data.get("closing_action", ""),
        )
