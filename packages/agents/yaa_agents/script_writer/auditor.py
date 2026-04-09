"""Auditor Agent.

작성된 원고가 가이드라인을 준수하는지 PASS/FAIL로 검수합니다.
FAIL 시 구체적인 수정 지시를 반환합니다.
"""

from __future__ import annotations

import json
import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from yaa_core.shared.llm_utils import extract_json_from_response
from yaa_core.shared.models import AuditResult

from yaa_agents.script_writer.prompts import (
    build_auditor_system_prompt,
    build_auditor_user_prompt,
)

logger = logging.getLogger(__name__)


class AuditorAgent:
    """원고 품질을 검수하는 에이전트."""

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm

    async def audit(self, draft_script: str, guidelines: str = "") -> AuditResult:
        """원고를 검수하고 PASS/FAIL 결과를 반환합니다.

        Args:
            draft_script: 검수할 원고 (full_text 또는 JSON 문자열)
            guidelines: 파일 기반 가이드라인 텍스트 (선택)

        Returns:
            AuditResult 모델
        """
        system_msg = build_auditor_system_prompt()
        user_prompt = build_auditor_user_prompt(draft_script, guidelines)

        messages = [system_msg, HumanMessage(content=user_prompt)]

        try:
            response = await self._llm.ainvoke(messages)
            return self._parse_response(response.content)
        except Exception as error:
            logger.error("AuditorAgent LLM 호출 실패: %s", error)
            # 호출 실패 시 FAIL로 처리하여 파이프라인이 계속 진행하도록 함
            return AuditResult(
                passed=False,
                feedback=f"검수 중 오류 발생: {error}",
                revision_instructions=["LLM 호출 오류로 자동 PASS 처리 불가. 수동 검토 필요."],
            )

    def _parse_response(self, raw: str) -> AuditResult:
        json_str = extract_json_from_response(raw)
        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("Auditor JSON 파싱 실패, PASS로 fallback: %s", e)
            # JSON 파싱 실패 시 원문에서 PASS 여부를 판단
            passed = "passed" in raw.lower() and "false" not in raw.lower()
            return AuditResult(passed=passed, feedback=raw[:500])

        return AuditResult(
            passed=bool(data.get("passed", False)),
            structure_ok=bool(data.get("structure_ok", False)),
            style_ok=bool(data.get("style_ok", False)),
            forbidden_words_ok=bool(data.get("forbidden_words_ok", True)),
            retention_hooks_ok=bool(data.get("retention_hooks_ok", False)),
            feedback=data.get("feedback", ""),
            revision_instructions=data.get("revision_instructions", []),
        )
