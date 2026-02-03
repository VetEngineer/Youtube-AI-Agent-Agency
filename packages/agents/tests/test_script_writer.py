"""Script Writer 모듈 단위 테스트.

LLM 호출은 Mock으로 대체하여 외부 API 의존성 없이 테스트합니다.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.script_writer.agent import (
    ScriptWriterAgent,
    _build_fallback_script,
    _build_script_from_dict,
    _extract_json,
)
from src.script_writer.prompts import (
    build_system_prompt,
    build_tone_guide,
    build_user_prompt,
)
from src.shared.models import (
    BrandGuide,
    BrandInfo,
    ContentPlan,
    Emotion,
    Formality,
    HumorLevel,
    Script,
    ToneAndManner,
    WritingStyle,
)

# ============================================
# Fixtures
# ============================================


@pytest.fixture
def mock_llm() -> MagicMock:
    """Mock LLM 인스턴스."""
    llm = MagicMock()
    llm.ainvoke = AsyncMock()
    return llm


@pytest.fixture
def sample_plan() -> ContentPlan:
    """테스트용 콘텐츠 기획안."""
    return ContentPlan(
        channel_id="test-channel",
        topic="고양이 건강 관리 필수 가이드",
        content_type="long_form",
        target_keywords=["고양이 건강", "고양이 관리", "반려묘"],
        notes="초보 집사 대상, 실용적인 팁 중심",
    )


@pytest.fixture
def sample_brand_guide() -> BrandGuide:
    """테스트용 브랜드 가이드."""
    return BrandGuide(
        brand=BrandInfo(
            name="딥퓨어캐터리",
            tagline="건강한 혈통, 따뜻한 가족",
            positioning="프리미엄 고양이 브리더",
            values=["전문성", "신뢰", "애정"],
        ),
        tone_and_manner=ToneAndManner(
            personality="따뜻하지만 전문적인 수의사 친구",
            formality=Formality.SEMI_FORMAL,
            emotion=Emotion.WARM,
            humor_level=HumorLevel.LIGHT,
            writing_style=WritingStyle(
                sentence_length="medium",
                vocabulary="전문용어를 쉽게 풀어서 설명",
                call_to_action="부드러운 권유형",
            ),
            do=["전문 지식을 쉽게 풀어 설명", "공감 표현 사용"],
            dont=["과도한 판매 압박", "전문용어 남발"],
        ),
    )


@pytest.fixture
def sample_script_json() -> str:
    """Mock LLM이 반환할 스크립트 JSON."""
    return json.dumps(
        {
            "title": "고양이 건강 관리, 이것만은 꼭 알아두세요!",
            "sections": [
                {
                    "heading": "인트로",
                    "body": "혹시 우리 고양이가 아픈 건 아닌지 걱정되신 적 있으시죠?",
                    "visual_notes": "걱정스러운 표정의 집사와 고양이 클로즈업",
                    "duration_seconds": 25,
                },
                {
                    "heading": "본론 1: 건강 체크 포인트",
                    "body": "고양이 건강을 확인하는 가장 기본적인 방법은 매일의 관찰입니다.",
                    "visual_notes": "건강 체크리스트 인포그래픽",
                    "duration_seconds": 120,
                },
                {
                    "heading": "본론 2: 예방접종 스케줄",
                    "body": "예방접종은 고양이 건강의 기본 중의 기본이에요.",
                    "visual_notes": "예방접종 일정표 그래픽",
                    "duration_seconds": 90,
                },
                {
                    "heading": "아웃트로",
                    "body": "오늘 알려드린 팁, 꼭 기억해주세요. 구독과 좋아요 부탁드려요!",
                    "visual_notes": "구독 버튼 애니메이션",
                    "duration_seconds": 20,
                },
            ],
            "estimated_duration_seconds": 255,
        },
        ensure_ascii=False,
    )


@pytest.fixture
def sample_tone() -> ToneAndManner:
    """테스트용 톤앤매너."""
    return ToneAndManner(
        personality="따뜻하지만 전문적인 수의사 친구",
        formality=Formality.SEMI_FORMAL,
        emotion=Emotion.WARM,
        humor_level=HumorLevel.LIGHT,
        writing_style=WritingStyle(
            sentence_length="medium",
            vocabulary="전문용어를 쉽게 풀어서 설명",
            call_to_action="부드러운 권유형",
        ),
        do=["전문 지식을 쉽게 풀어 설명"],
        dont=["과도한 판매 압박"],
    )


# ============================================
# 프롬프트 빌더 테스트
# ============================================


class TestBuildToneGuide:
    def test_includes_personality(self, sample_tone: ToneAndManner):
        guide = build_tone_guide(sample_tone)
        assert "따뜻하지만 전문적인 수의사 친구" in guide

    def test_includes_formality(self, sample_tone: ToneAndManner):
        guide = build_tone_guide(sample_tone)
        assert "semi-formal" in guide

    def test_includes_emotion(self, sample_tone: ToneAndManner):
        guide = build_tone_guide(sample_tone)
        assert "warm" in guide

    def test_includes_do_rules(self, sample_tone: ToneAndManner):
        guide = build_tone_guide(sample_tone)
        assert "전문 지식을 쉽게 풀어 설명" in guide
        assert "반드시 지켜야 할 것" in guide

    def test_includes_dont_rules(self, sample_tone: ToneAndManner):
        guide = build_tone_guide(sample_tone)
        assert "과도한 판매 압박" in guide
        assert "하지 말아야 할 것" in guide

    def test_includes_writing_style(self, sample_tone: ToneAndManner):
        guide = build_tone_guide(sample_tone)
        assert "전문용어를 쉽게 풀어서 설명" in guide
        assert "부드러운 권유형" in guide

    def test_empty_personality_omitted(self):
        tone = ToneAndManner()
        guide = build_tone_guide(tone)
        assert "퍼스널리티" not in guide

    def test_empty_do_dont_omitted(self):
        tone = ToneAndManner()
        guide = build_tone_guide(tone)
        assert "반드시 지켜야 할 것" not in guide
        assert "하지 말아야 할 것" not in guide


class TestBuildSystemPrompt:
    def test_contains_tone_guide(self, sample_tone: ToneAndManner):
        prompt = build_system_prompt(sample_tone)
        assert "따뜻하지만 전문적인 수의사 친구" in prompt
        assert "스크립트 라이터" in prompt

    def test_contains_json_format(self, sample_tone: ToneAndManner):
        prompt = build_system_prompt(sample_tone)
        assert '"title"' in prompt
        assert '"sections"' in prompt


class TestBuildUserPrompt:
    def test_includes_topic(self):
        prompt = build_user_prompt(
            topic="고양이 건강",
            content_type="long_form",
            keywords=["건강", "관리"],
            notes="초보 집사 대상",
        )
        assert "고양이 건강" in prompt

    def test_includes_keywords(self):
        prompt = build_user_prompt(
            topic="테스트",
            content_type="short_form",
            keywords=["키워드A", "키워드B"],
            notes="",
        )
        assert "키워드A" in prompt
        assert "키워드B" in prompt

    def test_empty_keywords_shows_none(self):
        prompt = build_user_prompt(
            topic="테스트",
            content_type="short_form",
            keywords=[],
            notes="",
        )
        assert "없음" in prompt

    def test_empty_notes_shows_none(self):
        prompt = build_user_prompt(
            topic="테스트",
            content_type="short_form",
            keywords=["키워드"],
            notes="",
        )
        assert "없음" in prompt


# ============================================
# JSON 추출/파싱 유틸리티 테스트
# ============================================


class TestExtractJson:
    def test_plain_json(self):
        raw = '{"title": "테스트"}'
        assert _extract_json(raw) == '{"title": "테스트"}'

    def test_json_in_code_block(self):
        raw = '```json\n{"title": "테스트"}\n```'
        result = _extract_json(raw)
        assert result == '{"title": "테스트"}'

    def test_json_in_code_block_without_lang(self):
        raw = '```\n{"title": "테스트"}\n```'
        result = _extract_json(raw)
        assert result == '{"title": "테스트"}'

    def test_text_with_surrounding_content(self):
        raw = '여기 결과입니다:\n```json\n{"title": "테스트"}\n```\n감사합니다.'
        result = _extract_json(raw)
        assert result == '{"title": "테스트"}'

    def test_no_code_block_returns_stripped(self):
        raw = '  {"title": "테스트"}  '
        assert _extract_json(raw) == '{"title": "테스트"}'


class TestBuildScriptFromDict:
    def test_valid_dict(self):
        data = {
            "title": "테스트 제목",
            "sections": [
                {
                    "heading": "인트로",
                    "body": "본문 내용",
                    "visual_notes": "영상 메모",
                    "duration_seconds": 30,
                },
            ],
            "estimated_duration_seconds": 30,
        }
        script = _build_script_from_dict(data)
        assert script.title == "테스트 제목"
        assert len(script.sections) == 1
        assert script.sections[0].heading == "인트로"
        assert script.full_text == "본문 내용"
        assert script.estimated_duration_seconds == 30

    def test_empty_sections(self):
        data = {"title": "빈 원고"}
        script = _build_script_from_dict(data)
        assert script.title == "빈 원고"
        assert script.sections == []
        assert script.full_text == ""

    def test_missing_title_defaults(self):
        data = {"sections": []}
        script = _build_script_from_dict(data)
        assert script.title == "제목 없음"

    def test_multiple_sections_full_text(self):
        data = {
            "title": "멀티 섹션",
            "sections": [
                {"heading": "A", "body": "첫 번째"},
                {"heading": "B", "body": "두 번째"},
            ],
        }
        script = _build_script_from_dict(data)
        assert "첫 번째" in script.full_text
        assert "두 번째" in script.full_text


class TestBuildFallbackScript:
    def test_fallback_contains_raw_response(self):
        raw = "LLM이 반환한 비정형 텍스트입니다."
        script = _build_fallback_script(raw)
        assert script.title == "제목 없음 (파싱 실패)"
        assert len(script.sections) == 1
        assert script.sections[0].body == raw
        assert script.full_text == raw


# ============================================
# ScriptWriterAgent 테스트
# ============================================


class TestScriptWriterAgentValidation:
    @pytest.mark.asyncio
    async def test_empty_topic_raises(self, mock_llm: MagicMock):
        agent = ScriptWriterAgent(mock_llm)
        plan = ContentPlan(channel_id="ch", topic="  ")
        guide = BrandGuide(brand=BrandInfo(name="테스트"))
        with pytest.raises(ValueError, match="topic"):
            await agent.generate(plan, guide)

    @pytest.mark.asyncio
    async def test_empty_brand_name_raises(self, mock_llm: MagicMock):
        agent = ScriptWriterAgent(mock_llm)
        plan = ContentPlan(channel_id="ch", topic="유효한 주제")
        guide = BrandGuide(brand=BrandInfo(name="  "))
        with pytest.raises(ValueError, match="brand.name"):
            await agent.generate(plan, guide)


class TestScriptWriterAgentGenerate:
    @pytest.mark.asyncio
    async def test_generate_valid_response(
        self,
        mock_llm: MagicMock,
        sample_plan: ContentPlan,
        sample_brand_guide: BrandGuide,
        sample_script_json: str,
    ):
        mock_response = MagicMock()
        mock_response.content = sample_script_json
        mock_llm.ainvoke.return_value = mock_response

        agent = ScriptWriterAgent(mock_llm)
        script = await agent.generate(sample_plan, sample_brand_guide)

        assert isinstance(script, Script)
        assert script.title == "고양이 건강 관리, 이것만은 꼭 알아두세요!"
        assert len(script.sections) == 4
        assert script.sections[0].heading == "인트로"
        assert script.sections[-1].heading == "아웃트로"
        assert script.estimated_duration_seconds == 255
        assert "관찰" in script.full_text

    @pytest.mark.asyncio
    async def test_generate_json_in_code_block(
        self,
        mock_llm: MagicMock,
        sample_plan: ContentPlan,
        sample_brand_guide: BrandGuide,
        sample_script_json: str,
    ):
        mock_response = MagicMock()
        mock_response.content = f"```json\n{sample_script_json}\n```"
        mock_llm.ainvoke.return_value = mock_response

        agent = ScriptWriterAgent(mock_llm)
        script = await agent.generate(sample_plan, sample_brand_guide)

        assert script.title == "고양이 건강 관리, 이것만은 꼭 알아두세요!"
        assert len(script.sections) == 4

    @pytest.mark.asyncio
    async def test_generate_invalid_json_returns_fallback(
        self,
        mock_llm: MagicMock,
        sample_plan: ContentPlan,
        sample_brand_guide: BrandGuide,
    ):
        mock_response = MagicMock()
        mock_response.content = "이것은 유효하지 않은 JSON입니다."
        mock_llm.ainvoke.return_value = mock_response

        agent = ScriptWriterAgent(mock_llm)
        script = await agent.generate(sample_plan, sample_brand_guide)

        assert script.title == "제목 없음 (파싱 실패)"
        assert len(script.sections) == 1
        assert "유효하지 않은 JSON" in script.full_text

    @pytest.mark.asyncio
    async def test_generate_llm_error_raises_runtime(
        self,
        mock_llm: MagicMock,
        sample_plan: ContentPlan,
        sample_brand_guide: BrandGuide,
    ):
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("API 연결 실패"))

        agent = ScriptWriterAgent(mock_llm)
        with pytest.raises(RuntimeError, match="LLM 호출에 실패"):
            await agent.generate(sample_plan, sample_brand_guide)

    @pytest.mark.asyncio
    async def test_generate_passes_correct_messages(
        self,
        mock_llm: MagicMock,
        sample_plan: ContentPlan,
        sample_brand_guide: BrandGuide,
        sample_script_json: str,
    ):
        mock_response = MagicMock()
        mock_response.content = sample_script_json
        mock_llm.ainvoke.return_value = mock_response

        agent = ScriptWriterAgent(mock_llm)
        await agent.generate(sample_plan, sample_brand_guide)

        # LLM이 호출되었는지 확인
        mock_llm.ainvoke.assert_called_once()
        messages = mock_llm.ainvoke.call_args[0][0]
        assert len(messages) == 2

        # 시스템 프롬프트에 톤앤매너 포함 확인
        system_msg = messages[0]
        assert "따뜻하지만 전문적인 수의사 친구" in system_msg.content

        # 유저 프롬프트에 주제 포함 확인
        user_msg = messages[1]
        assert "고양이 건강 관리 필수 가이드" in user_msg.content
        assert "고양이 건강" in user_msg.content

    @pytest.mark.asyncio
    async def test_generate_full_text_joins_sections(
        self,
        mock_llm: MagicMock,
        sample_plan: ContentPlan,
        sample_brand_guide: BrandGuide,
    ):
        script_data = json.dumps(
            {
                "title": "테스트",
                "sections": [
                    {"heading": "A", "body": "섹션A 내용"},
                    {"heading": "B", "body": "섹션B 내용"},
                    {"heading": "C", "body": ""},
                ],
                "estimated_duration_seconds": 100,
            },
            ensure_ascii=False,
        )

        mock_response = MagicMock()
        mock_response.content = script_data
        mock_llm.ainvoke.return_value = mock_response

        agent = ScriptWriterAgent(mock_llm)
        script = await agent.generate(sample_plan, sample_brand_guide)

        # 빈 body는 full_text에서 제외
        assert "섹션A 내용" in script.full_text
        assert "섹션B 내용" in script.full_text
        assert script.full_text == "섹션A 내용\n\n섹션B 내용"
