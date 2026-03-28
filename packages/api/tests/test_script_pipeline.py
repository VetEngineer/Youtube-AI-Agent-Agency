"""Script Pipeline 통합 테스트.

ScriptPipeline의 4단계 흐름과 피드백 루프를 검증합니다.
모든 LLM은 Mock으로 대체합니다.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from yaa_agents.script_writer.auditor import AuditorAgent
from yaa_agents.script_writer.editor import EditorAgent
from yaa_agents.script_writer.pipeline import (
    ScriptPipeline,
    _format_audit_feedback,
    _format_outline,
)
from yaa_agents.script_writer.strategist import StrategistAgent
from yaa_core.shared.models import (
    AuditResult,
    BrandGuide,
    BrandInfo,
    ContentPlan,
    Emotion,
    Formality,
    HumorLevel,
    MainPoint,
    Script,
    ScriptOutline,
    ScriptSection,
    ToneAndManner,
    WritingStyle,
)

# ============================================
# Fixtures
# ============================================


@pytest.fixture
def mock_llm() -> MagicMock:
    llm = MagicMock()
    llm.ainvoke = AsyncMock()
    return llm


@pytest.fixture
def sample_plan() -> ContentPlan:
    return ContentPlan(
        channel_id="test-channel",
        topic="고양이 건강 관리",
        content_type="long_form",
        target_keywords=["고양이"],
        notes="",
    )


@pytest.fixture
def sample_brand_guide() -> BrandGuide:
    return BrandGuide(
        brand=BrandInfo(name="테스트채널"),
        tone_and_manner=ToneAndManner(
            formality=Formality.SEMI_FORMAL,
            emotion=Emotion.WARM,
            humor_level=HumorLevel.NONE,
            writing_style=WritingStyle(),
        ),
    )


@pytest.fixture
def sample_outline() -> ScriptOutline:
    return ScriptOutline(
        opening_hook="고양이가 아프면 어떻게 하시나요?",
        opening_promise="오늘 3가지 건강 관리 팁을 드릴게요",
        main_points=[
            MainPoint(title="정기 검진", key_message="1년에 1회", example="동물병원 방문"),
            MainPoint(title="영양 관리", key_message="균형잡힌 사료", example="나이별 맞춤 사료"),
        ],
        closing_summary="정기검진, 영양, 운동이 핵심입니다",
        closing_action="오늘 동물병원에 전화해보세요",
    )


@pytest.fixture
def sample_script() -> Script:
    section = ScriptSection(heading="인트로", body="안녕하세요 여러분", duration_seconds=30)
    return Script(
        title="고양이 건강 관리 가이드",
        sections=[section],
        full_text="안녕하세요 여러분",
        estimated_duration_seconds=600,
    )


def _make_outline_response(outline: ScriptOutline) -> str:
    data = {
        "opening_hook": outline.opening_hook,
        "opening_promise": outline.opening_promise,
        "main_points": [
            {"title": p.title, "key_message": p.key_message, "example": p.example}
            for p in outline.main_points
        ],
        "closing_summary": outline.closing_summary,
        "closing_action": outline.closing_action,
    }
    return f"```json\n{json.dumps(data, ensure_ascii=False)}\n```"


def _make_script_response(script: Script) -> str:
    data = {
        "title": script.title,
        "sections": [
            {
                "heading": s.heading,
                "body": s.body,
                "visual_notes": s.visual_notes,
                "duration_seconds": s.duration_seconds,
            }
            for s in script.sections
        ],
        "estimated_duration_seconds": script.estimated_duration_seconds,
    }
    return f"```json\n{json.dumps(data, ensure_ascii=False)}\n```"


def _make_audit_pass_response() -> str:
    data = {
        "passed": True,
        "structure_ok": True,
        "style_ok": True,
        "forbidden_words_ok": True,
        "retention_hooks_ok": True,
        "feedback": "모든 항목 통과",
        "revision_instructions": [],
    }
    return f"```json\n{json.dumps(data, ensure_ascii=False)}\n```"


def _make_audit_fail_response() -> str:
    data = {
        "passed": False,
        "structure_ok": False,
        "style_ok": True,
        "forbidden_words_ok": True,
        "retention_hooks_ok": False,
        "feedback": "구조가 불명확합니다",
        "revision_instructions": ["오프닝을 더 명확히 해주세요", "리텐션 장치를 추가하세요"],
    }
    return f"```json\n{json.dumps(data, ensure_ascii=False)}\n```"


# ============================================
# StrategistAgent 단위 테스트
# ============================================


@pytest.mark.asyncio
async def test_strategist_returns_outline(
    mock_llm, sample_plan, sample_outline, sample_brand_guide
):
    """StrategistAgent가 ScriptOutline을 반환한다."""
    mock_llm.ainvoke.return_value = MagicMock(content=_make_outline_response(sample_outline))
    agent = StrategistAgent(mock_llm)

    result = await agent.plan_outline(sample_plan, sample_brand_guide.tone_and_manner)

    assert isinstance(result, ScriptOutline)
    assert result.opening_hook == sample_outline.opening_hook
    assert len(result.main_points) == 2


@pytest.mark.asyncio
async def test_strategist_fallback_on_parse_error(mock_llm, sample_plan, sample_brand_guide):
    """JSON 파싱 실패 시 fallback ScriptOutline을 반환한다."""
    mock_llm.ainvoke.return_value = MagicMock(content="파싱 불가 응답입니다")
    agent = StrategistAgent(mock_llm)

    result = await agent.plan_outline(sample_plan, sample_brand_guide.tone_and_manner)

    assert isinstance(result, ScriptOutline)
    assert result.opening_hook != ""  # raw 응답 일부가 들어 있음


# ============================================
# AuditorAgent 단위 테스트
# ============================================


@pytest.mark.asyncio
async def test_auditor_pass(mock_llm):
    """PASS 응답을 받으면 AuditResult.passed=True를 반환한다."""
    mock_llm.ainvoke.return_value = MagicMock(content=_make_audit_pass_response())
    agent = AuditorAgent(mock_llm)

    result = await agent.audit("원고 내용")

    assert isinstance(result, AuditResult)
    assert result.passed is True
    assert result.structure_ok is True


@pytest.mark.asyncio
async def test_auditor_fail(mock_llm):
    """FAIL 응답을 받으면 AuditResult.passed=False와 수정 지시를 반환한다."""
    mock_llm.ainvoke.return_value = MagicMock(content=_make_audit_fail_response())
    agent = AuditorAgent(mock_llm)

    result = await agent.audit("원고 내용")

    assert result.passed is False
    assert len(result.revision_instructions) == 2


@pytest.mark.asyncio
async def test_auditor_fallback_on_parse_error(mock_llm):
    """JSON 파싱 실패 시 AuditResult를 반환한다."""
    mock_llm.ainvoke.return_value = MagicMock(content="PASS 형식이 아닌 응답")
    agent = AuditorAgent(mock_llm)

    result = await agent.audit("원고 내용")

    assert isinstance(result, AuditResult)


# ============================================
# EditorAgent 단위 테스트
# ============================================


@pytest.mark.asyncio
async def test_editor_returns_polished_script(mock_llm, sample_script):
    """EditorAgent가 다듬어진 Script를 반환한다."""
    polished = Script(
        title="다듬어진 제목",
        sections=[ScriptSection(heading="인트로", body="자연스러운 문장이에요")],
        full_text="자연스러운 문장이에요",
        estimated_duration_seconds=600,
    )
    mock_llm.ainvoke.return_value = MagicMock(content=_make_script_response(polished))
    agent = EditorAgent(mock_llm)

    result = await agent.polish(sample_script)

    assert result.title == "다듬어진 제목"
    assert result.full_text == "자연스러운 문장이에요"


@pytest.mark.asyncio
async def test_editor_fallback_returns_original(mock_llm, sample_script):
    """파싱 실패 시 원본 Script를 반환한다."""
    mock_llm.ainvoke.return_value = MagicMock(content="JSON이 아닌 응답")
    agent = EditorAgent(mock_llm)

    result = await agent.polish(sample_script)

    assert result.title == sample_script.title


# ============================================
# ScriptPipeline 통합 테스트
# ============================================

_PATCH_GUIDELINES = "yaa_agents.script_writer.pipeline.load_guidelines"
_PATCH_REFERENCES = "yaa_agents.script_writer.pipeline.load_references"


@pytest.mark.asyncio
async def test_pipeline_single_pass(
    mock_llm, sample_plan, sample_brand_guide, sample_outline, sample_script
):
    """1회에 PASS하는 정상 케이스."""
    pipeline = ScriptPipeline(mock_llm, mock_llm, mock_llm, mock_llm)
    mock_strategist = AsyncMock(return_value=sample_outline)
    mock_writer = AsyncMock(return_value=sample_script)
    mock_auditor = AsyncMock(return_value=AuditResult(passed=True))
    mock_editor = AsyncMock(return_value=sample_script)

    with (
        patch.object(pipeline._strategist, "plan_outline", mock_strategist),
        patch.object(pipeline._writer, "generate", mock_writer),
        patch.object(pipeline._auditor, "audit", mock_auditor),
        patch.object(pipeline._editor, "polish", mock_editor),
        patch(_PATCH_GUIDELINES, return_value=""),
        patch(_PATCH_REFERENCES, return_value=[]),
    ):
        result = await pipeline.execute(sample_plan, sample_brand_guide)

    assert isinstance(result, Script)
    mock_writer.assert_called_once()
    mock_auditor.assert_called_once()
    mock_editor.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_fail_then_pass(
    mock_llm, sample_plan, sample_brand_guide, sample_outline, sample_script
):
    """1회 FAIL 후 2회에 PASS. Writer가 2회 호출된다."""
    fail_result = AuditResult(
        passed=False, feedback="수정 필요", revision_instructions=["수정하세요"]
    )
    pass_result = AuditResult(passed=True)

    pipeline = ScriptPipeline(mock_llm, mock_llm, mock_llm, mock_llm)
    mock_writer = AsyncMock(return_value=sample_script)
    mock_auditor = AsyncMock(side_effect=[fail_result, pass_result])
    mock_editor = AsyncMock(return_value=sample_script)

    with (
        patch.object(pipeline._strategist, "plan_outline", AsyncMock(return_value=sample_outline)),
        patch.object(pipeline._writer, "generate", mock_writer),
        patch.object(pipeline._auditor, "audit", mock_auditor),
        patch.object(pipeline._editor, "polish", mock_editor),
        patch(_PATCH_GUIDELINES, return_value=""),
        patch(_PATCH_REFERENCES, return_value=[]),
    ):
        result = await pipeline.execute(sample_plan, sample_brand_guide, max_revisions=3)

    assert isinstance(result, Script)
    assert mock_writer.call_count == 2
    assert mock_auditor.call_count == 2


@pytest.mark.asyncio
async def test_pipeline_max_revisions_exceeded(
    mock_llm, sample_plan, sample_brand_guide, sample_outline, sample_script
):
    """max_revisions 초과 시 강제로 Editor로 진행한다."""
    fail_result = AuditResult(passed=False, feedback="계속 실패")

    pipeline = ScriptPipeline(mock_llm, mock_llm, mock_llm, mock_llm)
    mock_writer = AsyncMock(return_value=sample_script)
    mock_auditor = AsyncMock(return_value=fail_result)
    mock_editor = AsyncMock(return_value=sample_script)

    with (
        patch.object(pipeline._strategist, "plan_outline", AsyncMock(return_value=sample_outline)),
        patch.object(pipeline._writer, "generate", mock_writer),
        patch.object(pipeline._auditor, "audit", mock_auditor),
        patch.object(pipeline._editor, "polish", mock_editor),
        patch(_PATCH_GUIDELINES, return_value=""),
        patch(_PATCH_REFERENCES, return_value=[]),
    ):
        await pipeline.execute(sample_plan, sample_brand_guide, max_revisions=2)

    # max_revisions=2 → 최초 + 2회 수정 = Writer 3회, Auditor 3회
    assert mock_writer.call_count == 3
    assert mock_auditor.call_count == 3
    mock_editor.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_skip_audit(
    mock_llm, sample_plan, sample_brand_guide, sample_outline, sample_script
):
    """skip_audit=True이면 검수/편집 단계를 건너뛴다."""
    pipeline = ScriptPipeline(mock_llm, mock_llm, mock_llm, mock_llm)
    mock_auditor = AsyncMock()

    with (
        patch.object(pipeline._strategist, "plan_outline", AsyncMock(return_value=sample_outline)),
        patch.object(pipeline._writer, "generate", AsyncMock(return_value=sample_script)),
        patch.object(pipeline._auditor, "audit", mock_auditor),
        patch(_PATCH_GUIDELINES, return_value=""),
        patch(_PATCH_REFERENCES, return_value=[]),
    ):
        result = await pipeline.execute(sample_plan, sample_brand_guide, skip_audit=True)

    assert isinstance(result, Script)
    mock_auditor.assert_not_called()


# ============================================
# 헬퍼 함수 테스트
# ============================================


def test_format_outline(sample_outline):
    """_format_outline이 텍스트를 올바르게 포맷한다."""
    text = _format_outline(sample_outline)
    assert "[오프닝 훅]" in text
    assert "정기 검진" in text
    assert "[클로징 요약]" in text


def test_format_audit_feedback():
    """_format_audit_feedback이 텍스트를 올바르게 포맷한다."""
    audit = AuditResult(
        passed=False,
        structure_ok=False,
        style_ok=True,
        feedback="수정 필요",
        revision_instructions=["오프닝 개선", "리텐션 장치 추가"],
    )
    text = _format_audit_feedback(audit)
    assert "수정 필요" in text
    assert "오프닝 개선" in text
