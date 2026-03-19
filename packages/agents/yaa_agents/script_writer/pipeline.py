"""Script Pipeline.

4단계 원고 생성 파이프라인을 오케스트레이션합니다:
  1. Strategist: 아웃라인 기획
  2. Writer:     초안 작성
  3. Auditor:    PASS/FAIL 검수 (최대 max_revisions회 수정 루프)
  4. Editor:     최종 다듬기
"""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from yaa_core.shared.models import (
    AuditResult,
    BrandGuide,
    ContentPlan,
    Script,
    ScriptOutline,
)

from yaa_agents.script_writer.agent import ScriptWriterAgent
from yaa_agents.script_writer.auditor import AuditorAgent
from yaa_agents.script_writer.editor import EditorAgent
from yaa_agents.script_writer.guidelines import format_references, load_guidelines, load_references
from yaa_agents.script_writer.strategist import StrategistAgent

logger = logging.getLogger(__name__)


class ScriptPipeline:
    """4단계 원고 생성 파이프라인.

    Supervisor에서 ScriptWriterAgent 대신 사용합니다.
    외부 인터페이스(execute)는 Script를 반환합니다.
    """

    def __init__(
        self,
        strategist_llm: BaseChatModel,
        writer_llm: BaseChatModel,
        auditor_llm: BaseChatModel,
        editor_llm: BaseChatModel,
    ) -> None:
        self._strategist = StrategistAgent(strategist_llm)
        self._writer = ScriptWriterAgent(writer_llm)
        self._auditor = AuditorAgent(auditor_llm)
        self._editor = EditorAgent(editor_llm)

    async def execute(
        self,
        plan: ContentPlan,
        brand_guide: BrandGuide,
        max_revisions: int = 3,
        skip_audit: bool = False,
    ) -> Script:
        """4단계 파이프라인을 실행하여 최종 원고를 반환합니다.

        Args:
            plan: 콘텐츠 기획안
            brand_guide: 브랜드 가이드
            max_revisions: 검수 실패 시 최대 수정 횟수
            skip_audit: True이면 검수/편집 단계를 건너뜁니다 (비용 절감 모드)

        Returns:
            최종 원고 Script
        """
        # 채널별 가이드라인/레퍼런스 로드 (channels/{channel_id}/ 기준)
        channel_dir = _resolve_channel_dir(plan.channel_id)
        guidelines = load_guidelines(channel_dir)
        references = load_references(channel_dir)
        references_text = format_references(references)

        # 1단계: Strategist - 아웃라인 기획
        logger.info("[pipeline] 1/4 Strategist 실행: topic=%s", plan.topic)
        outline = await self._strategist.plan_outline(
            plan=plan,
            tone=brand_guide.tone_and_manner,
            guidelines=guidelines,
        )
        outline_text = _format_outline(outline)
        logger.debug("[pipeline] 아웃라인 생성 완료: points=%d", len(outline.main_points))

        # 2단계: Writer - 초안 작성
        logger.info("[pipeline] 2/4 Writer 실행")
        script = await self._writer.generate(
            plan=plan,
            brand_guide=brand_guide,
            outline=outline_text,
            guidelines=guidelines,
            references=references_text,
        )

        if skip_audit:
            logger.info("[pipeline] skip_audit=True, 검수/편집 건너뜀")
            return script

        # 3단계: Auditor - 검수 루프
        audit_result: AuditResult | None = None
        revision_count = 0

        for attempt in range(max_revisions + 1):
            logger.info("[pipeline] 3/4 Auditor 검수 (시도 %d/%d)", attempt + 1, max_revisions + 1)
            audit_result = await self._auditor.audit(script.full_text, guidelines)

            if audit_result.passed:
                logger.info("[pipeline] 검수 PASS")
                break

            if attempt >= max_revisions:
                logger.warning(
                    "[pipeline] max_revisions(%d) 초과, 강제 진행: feedback=%s",
                    max_revisions,
                    audit_result.feedback[:100],
                )
                break

            # FAIL → Writer 수정
            revision_count += 1
            logger.info(
                "[pipeline] 검수 FAIL (revision %d/%d), Writer 수정 요청",
                revision_count,
                max_revisions,
            )
            audit_feedback = _format_audit_feedback(audit_result)
            script = await self._writer.generate(
                plan=plan,
                brand_guide=brand_guide,
                outline=outline_text,
                guidelines=guidelines,
                references=references_text,
                audit_feedback=audit_feedback,
            )

        # 4단계: Editor - 최종 다듬기
        logger.info("[pipeline] 4/4 Editor 실행")
        final_script = await self._editor.polish(script, guidelines)
        logger.info("[pipeline] 파이프라인 완료: title=%s", final_script.title)
        return final_script


def _resolve_channel_dir(channel_id: str) -> Path:
    """채널 ID로 채널 디렉토리 경로를 반환합니다."""
    # 프로젝트 루트의 channels/ 디렉토리 기준
    # 런타임에는 yaa_app 패키지가 실행되므로 상대 경로가 작동
    return Path("channels") / channel_id


def _format_outline(outline: ScriptOutline) -> str:
    """ScriptOutline을 프롬프트용 텍스트로 변환합니다."""
    lines = [
        f"[오프닝 훅] {outline.opening_hook}",
        f"[핵심 약속] {outline.opening_promise}",
        "",
        "[본론]",
    ]
    for i, point in enumerate(outline.main_points, 1):
        lines.append(f"{i}. {point.title}")
        if point.key_message:
            lines.append(f"   - 핵심: {point.key_message}")
        if point.example:
            lines.append(f"   - 예시: {point.example}")
    lines += [
        "",
        f"[클로징 요약] {outline.closing_summary}",
        f"[액션 아이템] {outline.closing_action}",
    ]
    return "\n".join(lines)


def _format_audit_feedback(audit: AuditResult) -> str:
    """AuditResult를 Writer에게 전달할 피드백 텍스트로 변환합니다."""
    parts = [f"[전체 평가] {audit.feedback}"]
    checks = {
        "구조": audit.structure_ok,
        "문체": audit.style_ok,
        "금지어": audit.forbidden_words_ok,
        "리텐션 장치": audit.retention_hooks_ok,
    }
    for name, ok in checks.items():
        parts.append(f"- {name}: {'✅' if ok else '❌'}")
    if audit.revision_instructions:
        parts.append("\n[수정 지시]")
        for instruction in audit.revision_instructions:
            parts.append(f"  - {instruction}")
    return "\n".join(parts)
