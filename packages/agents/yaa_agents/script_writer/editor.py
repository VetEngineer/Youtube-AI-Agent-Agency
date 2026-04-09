"""Editor Agent.

검수를 통과한 원고를 최종적으로 말맛 있게 다듬습니다.
내용 변경 없이 표현과 리듬감만 개선합니다.
"""

from __future__ import annotations

import json
import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from yaa_core.shared.llm_utils import extract_json_from_response
from yaa_core.shared.models import Script, ScriptSection

from yaa_agents.script_writer.prompts import (
    build_editor_system_prompt,
    build_editor_user_prompt,
)

logger = logging.getLogger(__name__)


class EditorAgent:
    """원고를 최종 다듬는 에이전트."""

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm

    async def polish(self, script: Script, guidelines: str = "") -> Script:
        """원고를 다듬어 최종 버전을 반환합니다.

        Args:
            script: 다듬을 Script 모델
            guidelines: 파일 기반 가이드라인 텍스트 (선택)

        Returns:
            다듬어진 Script 모델 (원본 Script 기반, full_text/sections 업데이트)
        """
        system_msg = build_editor_system_prompt()
        user_prompt = build_editor_user_prompt(script.full_text, guidelines)

        messages = [system_msg, HumanMessage(content=user_prompt)]

        try:
            response = await self._llm.ainvoke(messages)
            return self._apply_polish(script, response.content)
        except Exception as error:
            logger.error("EditorAgent LLM 호출 실패: %s", error)
            # 편집 실패 시 원본 반환 (편집은 필수가 아님)
            logger.warning("편집 실패로 원본 원고를 반환합니다.")
            return script

    def _apply_polish(self, original: Script, raw: str) -> Script:
        """LLM 응답을 파싱하여 원본 Script에 적용합니다."""
        json_str = extract_json_from_response(raw)
        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("Editor JSON 파싱 실패, 원본 반환: %s", e)
            return original

        sections = [
            ScriptSection(
                heading=s.get("heading", ""),
                body=s.get("body", ""),
                visual_notes=s.get("visual_notes", ""),
                duration_seconds=s.get("duration_seconds", 0),
            )
            for s in data.get("sections", [])
        ]
        full_text = "\n\n".join(s.body for s in sections if s.body)

        return Script(
            title=data.get("title", original.title),
            sections=sections if sections else original.sections,
            full_text=full_text if full_text else original.full_text,
            estimated_duration_seconds=data.get(
                "estimated_duration_seconds", original.estimated_duration_seconds
            ),
            created_at=original.created_at,
        )
