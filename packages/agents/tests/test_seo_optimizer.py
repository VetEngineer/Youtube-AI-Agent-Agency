"""SEO Optimizer 모듈 단위 테스트.

LLM 호출은 Mock으로 대체하여 외부 API 의존성 없이 테스트합니다.
키워드 리서치, 메타데이터 생성, 에이전트 통합 테스트를 포함합니다.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.seo_optimizer.agent import SEOOptimizerAgent
from src.seo_optimizer.keyword_research import KeywordResearcher
from src.seo_optimizer.metadata_gen import MetadataGenerator
from src.shared.models import (
    BrandGuide,
    BrandInfo,
    SEOAnalysis,
    TargetAudience,
    ToneAndManner,
    VideoMetadata,
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
def sample_brand_guide() -> BrandGuide:
    """테스트용 브랜드 가이드."""
    return BrandGuide(
        brand=BrandInfo(
            name="딥퓨어캐터리",
            tagline="건강한 혈통, 따뜻한 가족",
            positioning="프리미엄 고양이 브리더",
            values=["전문성", "신뢰", "애정"],
        ),
        target_audience=TargetAudience(
            primary="고양이 분양을 고려하는 30-40대",
            pain_points=["건강한 묘종 선택 어려움", "사기 분양 걱정"],
            content_needs=["묘종 정보", "건강 관리 팁", "분양 가이드"],
        ),
        tone_and_manner=ToneAndManner(
            personality="따뜻하지만 전문적인 수의사 친구",
            writing_style=WritingStyle(
                call_to_action="부드러운 권유형",
            ),
        ),
    )


@pytest.fixture
def sample_keyword_json() -> str:
    """Mock LLM이 반환할 키워드 리서치 JSON."""
    return json.dumps(
        {
            "primary_keywords": ["고양이 분양", "브리티시숏헤어", "고양이 건강"],
            "secondary_keywords": [
                "고양이 분양 가격",
                "브리티시숏헤어 성격",
                "고양이 예방접종",
                "고양이 사료 추천",
                "묘종 선택 가이드",
            ],
            "search_volume": {
                "고양이 분양": 12000,
                "브리티시숏헤어": 8000,
                "고양이 건강": 6000,
                "고양이 분양 가격": 4000,
                "브리티시숏헤어 성격": 3000,
            },
            "competition_level": {
                "고양이 분양": "high",
                "브리티시숏헤어": "medium",
                "고양이 건강": "medium",
                "고양이 분양 가격": "low",
                "브리티시숏헤어 성격": "low",
            },
        },
        ensure_ascii=False,
    )


@pytest.fixture
def sample_metadata_json() -> str:
    """Mock LLM이 반환할 메타데이터 JSON."""
    return json.dumps(
        {
            "title": "브리티시숏헤어 분양 전 반드시 알아야 할 5가지",
            "description": (
                "브리티시숏헤어 분양을 고려하고 계신가요? "
                "건강한 고양이를 만나기 위해 반드시 확인해야 할 체크리스트를 정리했습니다.\n\n"
                "00:00 인트로\n"
                "01:30 건강 체크 포인트\n"
                "05:00 성격과 특징\n"
                "08:00 분양처 선택 가이드\n"
                "11:00 마무리\n\n"
                "#고양이분양 #브리티시숏헤어 #고양이건강"
            ),
            "tags": [
                "고양이 분양",
                "브리티시숏헤어",
                "고양이 건강",
                "분양 가이드",
                "브리티시숏헤어 성격",
                "고양이 예방접종",
                "고양이 사료",
                "묘종 추천",
                "반려동물",
                "고양이 키우기",
            ],
        },
        ensure_ascii=False,
    )


@pytest.fixture
def sample_seo_analysis() -> SEOAnalysis:
    """테스트용 SEO 분석 결과."""
    return SEOAnalysis(
        primary_keywords=["고양이 분양", "브리티시숏헤어", "고양이 건강"],
        secondary_keywords=[
            "고양이 분양 가격",
            "브리티시숏헤어 성격",
            "고양이 예방접종",
        ],
        search_volume={"고양이 분양": 12000, "브리티시숏헤어": 8000},
        competition_level={"고양이 분양": "high", "브리티시숏헤어": "medium"},
    )


# ============================================
# KeywordResearcher 테스트
# ============================================


class TestKeywordResearcher:
    @pytest.mark.asyncio
    async def test_research_valid_response(
        self,
        mock_llm: MagicMock,
        sample_brand_guide: BrandGuide,
        sample_keyword_json: str,
    ):
        """정상 JSON 응답 시 SEOAnalysis가 올바르게 파싱된다."""
        mock_response = MagicMock()
        mock_response.content = sample_keyword_json
        mock_llm.ainvoke.return_value = mock_response

        researcher = KeywordResearcher(mock_llm)
        result = await researcher.research(
            topic="브리티시숏헤어 분양 가이드",
            brand_guide=sample_brand_guide,
        )

        assert isinstance(result, SEOAnalysis)
        assert len(result.primary_keywords) == 3
        assert "고양이 분양" in result.primary_keywords
        assert len(result.secondary_keywords) == 5
        assert result.search_volume["고양이 분양"] == 12000
        assert result.competition_level["고양이 분양"] == "high"

    @pytest.mark.asyncio
    async def test_research_with_code_block(
        self,
        mock_llm: MagicMock,
        sample_brand_guide: BrandGuide,
        sample_keyword_json: str,
    ):
        """JSON이 코드 블록으로 감싸진 경우에도 파싱된다."""
        mock_response = MagicMock()
        mock_response.content = f"```json\n{sample_keyword_json}\n```"
        mock_llm.ainvoke.return_value = mock_response

        researcher = KeywordResearcher(mock_llm)
        result = await researcher.research(
            topic="브리티시숏헤어 분양 가이드",
            brand_guide=sample_brand_guide,
        )

        assert len(result.primary_keywords) == 3
        assert "브리티시숏헤어" in result.primary_keywords

    @pytest.mark.asyncio
    async def test_research_invalid_json_returns_default(
        self,
        mock_llm: MagicMock,
        sample_brand_guide: BrandGuide,
    ):
        """JSON 파싱 실패 시 빈 SEOAnalysis를 반환한다."""
        mock_response = MagicMock()
        mock_response.content = "이것은 유효하지 않은 JSON입니다."
        mock_llm.ainvoke.return_value = mock_response

        researcher = KeywordResearcher(mock_llm)
        result = await researcher.research(
            topic="테스트 토픽",
            brand_guide=sample_brand_guide,
        )

        assert isinstance(result, SEOAnalysis)
        assert result.primary_keywords == []
        assert result.secondary_keywords == []
        assert result.search_volume == {}

    @pytest.mark.asyncio
    async def test_research_with_existing_keywords(
        self,
        mock_llm: MagicMock,
        sample_brand_guide: BrandGuide,
        sample_keyword_json: str,
    ):
        """기존 키워드를 프롬프트에 포함하여 전달한다."""
        mock_response = MagicMock()
        mock_response.content = sample_keyword_json
        mock_llm.ainvoke.return_value = mock_response

        researcher = KeywordResearcher(mock_llm)
        existing = ["고양이", "펫케어"]
        await researcher.research(
            topic="브리티시숏헤어 분양 가이드",
            brand_guide=sample_brand_guide,
            existing_keywords=existing,
        )

        # LLM 호출 시 프롬프트에 기존 키워드가 포함되었는지 확인
        call_args = mock_llm.ainvoke.call_args[0][0]
        user_message = call_args[1].content
        assert "고양이" in user_message
        assert "펫케어" in user_message

    @pytest.mark.asyncio
    async def test_research_llm_error_raises_runtime_error(
        self,
        mock_llm: MagicMock,
        sample_brand_guide: BrandGuide,
    ):
        """LLM 호출 실패 시 RuntimeError를 발생시킨다."""
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("API 연결 실패"))

        researcher = KeywordResearcher(mock_llm)

        with pytest.raises(RuntimeError, match="키워드 리서치 중 오류"):
            await researcher.research(
                topic="테스트",
                brand_guide=sample_brand_guide,
            )

    def test_build_prompt_includes_brand_info(
        self,
        mock_llm: MagicMock,
        sample_brand_guide: BrandGuide,
    ):
        """프롬프트에 브랜드 정보가 포함된다."""
        researcher = KeywordResearcher(mock_llm)
        prompt = researcher._build_prompt(
            topic="고양이 건강 관리",
            brand_guide=sample_brand_guide,
            existing_keywords=[],
        )

        assert "고양이 건강 관리" in prompt
        assert "프리미엄 고양이 브리더" in prompt
        assert "30-40대" in prompt

    def test_build_prompt_includes_pain_points(
        self,
        mock_llm: MagicMock,
        sample_brand_guide: BrandGuide,
    ):
        """프롬프트에 오디언스 페인포인트가 포함된다."""
        researcher = KeywordResearcher(mock_llm)
        prompt = researcher._build_prompt(
            topic="테스트",
            brand_guide=sample_brand_guide,
            existing_keywords=[],
        )

        assert "건강한 묘종 선택 어려움" in prompt


# ============================================
# MetadataGenerator 테스트
# ============================================


class TestMetadataGenerator:
    @pytest.mark.asyncio
    async def test_generate_valid_response(
        self,
        mock_llm: MagicMock,
        sample_seo_analysis: SEOAnalysis,
        sample_brand_guide: BrandGuide,
        sample_metadata_json: str,
    ):
        """정상 JSON 응답 시 VideoMetadata가 올바르게 파싱된다."""
        mock_response = MagicMock()
        mock_response.content = sample_metadata_json
        mock_llm.ainvoke.return_value = mock_response

        generator = MetadataGenerator(mock_llm)
        result = await generator.generate(
            script_title="브리티시숏헤어 분양 가이드",
            script_text="안녕하세요, 오늘은 브리티시숏헤어 분양에 대해 알아보겠습니다...",
            seo_analysis=sample_seo_analysis,
            brand_guide=sample_brand_guide,
        )

        assert isinstance(result, VideoMetadata)
        assert "브리티시숏헤어" in result.title
        assert len(result.tags) == 10
        assert "고양이 분양" in result.tags
        assert "인트로" in result.description

    @pytest.mark.asyncio
    async def test_generate_with_code_block(
        self,
        mock_llm: MagicMock,
        sample_seo_analysis: SEOAnalysis,
        sample_brand_guide: BrandGuide,
        sample_metadata_json: str,
    ):
        """JSON이 코드 블록으로 감싸진 경우에도 파싱된다."""
        mock_response = MagicMock()
        mock_response.content = f"```json\n{sample_metadata_json}\n```"
        mock_llm.ainvoke.return_value = mock_response

        generator = MetadataGenerator(mock_llm)
        result = await generator.generate(
            script_title="테스트",
            script_text="테스트 스크립트",
            seo_analysis=sample_seo_analysis,
            brand_guide=sample_brand_guide,
        )

        assert "브리티시숏헤어" in result.title

    @pytest.mark.asyncio
    async def test_generate_invalid_json_returns_fallback(
        self,
        mock_llm: MagicMock,
        sample_seo_analysis: SEOAnalysis,
        sample_brand_guide: BrandGuide,
    ):
        """JSON 파싱 실패 시 fallback 제목으로 기본 VideoMetadata를 반환한다."""
        mock_response = MagicMock()
        mock_response.content = "유효하지 않은 응답입니다."
        mock_llm.ainvoke.return_value = mock_response

        generator = MetadataGenerator(mock_llm)
        result = await generator.generate(
            script_title="원본 제목",
            script_text="테스트",
            seo_analysis=sample_seo_analysis,
            brand_guide=sample_brand_guide,
        )

        assert isinstance(result, VideoMetadata)
        assert result.title == "원본 제목"
        assert result.description == ""
        assert result.tags == []

    @pytest.mark.asyncio
    async def test_generate_llm_error_raises_runtime_error(
        self,
        mock_llm: MagicMock,
        sample_seo_analysis: SEOAnalysis,
        sample_brand_guide: BrandGuide,
    ):
        """LLM 호출 실패 시 RuntimeError를 발생시킨다."""
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("API 오류"))

        generator = MetadataGenerator(mock_llm)

        with pytest.raises(RuntimeError, match="메타데이터 생성 중 오류"):
            await generator.generate(
                script_title="테스트",
                script_text="테스트",
                seo_analysis=sample_seo_analysis,
                brand_guide=sample_brand_guide,
            )

    def test_truncate_script_short_text(self, mock_llm: MagicMock):
        """짧은 스크립트는 잘리지 않는다."""
        generator = MetadataGenerator(mock_llm)
        text = "짧은 스크립트"
        assert generator._truncate_script(text) == text

    def test_truncate_script_long_text(self, mock_llm: MagicMock):
        """긴 스크립트는 최대 길이로 잘린다."""
        generator = MetadataGenerator(mock_llm)
        text = "가" * 3000
        result = generator._truncate_script(text, max_length=100)
        assert len(result) < 3000
        assert "이하 생략" in result

    def test_build_prompt_includes_keywords(
        self,
        mock_llm: MagicMock,
        sample_seo_analysis: SEOAnalysis,
        sample_brand_guide: BrandGuide,
    ):
        """프롬프트에 SEO 키워드가 포함된다."""
        generator = MetadataGenerator(mock_llm)
        prompt = generator._build_prompt(
            script_title="테스트 제목",
            script_text="테스트 본문",
            seo_analysis=sample_seo_analysis,
            brand_guide=sample_brand_guide,
        )

        assert "고양이 분양" in prompt
        assert "브리티시숏헤어" in prompt
        assert "고양이 분양 가격" in prompt


# ============================================
# SEOOptimizerAgent 통합 테스트
# ============================================


class TestSEOOptimizerAgent:
    @pytest.mark.asyncio
    async def test_optimize_full_pipeline(
        self,
        mock_llm: MagicMock,
        sample_brand_guide: BrandGuide,
        sample_keyword_json: str,
        sample_metadata_json: str,
    ):
        """키워드 리서치 -> 메타데이터 생성 전체 파이프라인이 동작한다."""
        keyword_response = MagicMock()
        keyword_response.content = sample_keyword_json
        metadata_response = MagicMock()
        metadata_response.content = sample_metadata_json

        mock_llm.ainvoke = AsyncMock(
            side_effect=[keyword_response, metadata_response],
        )

        agent = SEOOptimizerAgent(mock_llm)
        seo_analysis, metadata = await agent.optimize(
            topic="브리티시숏헤어 분양 가이드",
            script_title="브리티시숏헤어 분양 가이드",
            script_text="안녕하세요, 오늘은 브리티시숏헤어 분양에 대해...",
            brand_guide=sample_brand_guide,
        )

        assert isinstance(seo_analysis, SEOAnalysis)
        assert isinstance(metadata, VideoMetadata)
        assert len(seo_analysis.primary_keywords) == 3
        assert "브리티시숏헤어" in metadata.title
        assert len(metadata.tags) >= 5

    @pytest.mark.asyncio
    async def test_optimize_with_existing_keywords(
        self,
        mock_llm: MagicMock,
        sample_brand_guide: BrandGuide,
        sample_keyword_json: str,
        sample_metadata_json: str,
    ):
        """기존 키워드를 전달하면 키워드 리서치에 반영된다."""
        keyword_response = MagicMock()
        keyword_response.content = sample_keyword_json
        metadata_response = MagicMock()
        metadata_response.content = sample_metadata_json

        mock_llm.ainvoke = AsyncMock(
            side_effect=[keyword_response, metadata_response],
        )

        agent = SEOOptimizerAgent(mock_llm)
        seo_analysis, metadata = await agent.optimize(
            topic="테스트 토픽",
            script_title="테스트",
            script_text="테스트 본문",
            brand_guide=sample_brand_guide,
            existing_keywords=["기존키워드1", "기존키워드2"],
        )

        # 첫 번째 LLM 호출 (키워드 리서치)의 프롬프트 확인
        first_call_args = mock_llm.ainvoke.call_args_list[0][0][0]
        user_prompt = first_call_args[1].content
        assert "기존키워드1" in user_prompt

        assert isinstance(seo_analysis, SEOAnalysis)
        assert isinstance(metadata, VideoMetadata)

    @pytest.mark.asyncio
    async def test_optimize_keyword_failure_propagates(
        self,
        mock_llm: MagicMock,
        sample_brand_guide: BrandGuide,
    ):
        """키워드 리서치 단계에서 LLM 오류 시 RuntimeError가 전파된다."""
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("키워드 API 실패"))

        agent = SEOOptimizerAgent(mock_llm)

        with pytest.raises(RuntimeError):
            await agent.optimize(
                topic="테스트",
                script_title="테스트",
                script_text="테스트",
                brand_guide=sample_brand_guide,
            )

    @pytest.mark.asyncio
    async def test_optimize_metadata_failure_propagates(
        self,
        mock_llm: MagicMock,
        sample_brand_guide: BrandGuide,
        sample_keyword_json: str,
    ):
        """메타데이터 생성 단계에서 LLM 오류 시 RuntimeError가 전파된다."""
        keyword_response = MagicMock()
        keyword_response.content = sample_keyword_json

        mock_llm.ainvoke = AsyncMock(
            side_effect=[keyword_response, Exception("메타데이터 API 실패")],
        )

        agent = SEOOptimizerAgent(mock_llm)

        with pytest.raises(RuntimeError):
            await agent.optimize(
                topic="테스트",
                script_title="테스트",
                script_text="테스트",
                brand_guide=sample_brand_guide,
            )

    @pytest.mark.asyncio
    async def test_optimize_returns_correct_types(
        self,
        mock_llm: MagicMock,
        sample_brand_guide: BrandGuide,
        sample_keyword_json: str,
        sample_metadata_json: str,
    ):
        """반환값이 정확한 타입 (SEOAnalysis, VideoMetadata) 튜플이다."""
        keyword_response = MagicMock()
        keyword_response.content = sample_keyword_json
        metadata_response = MagicMock()
        metadata_response.content = sample_metadata_json

        mock_llm.ainvoke = AsyncMock(
            side_effect=[keyword_response, metadata_response],
        )

        agent = SEOOptimizerAgent(mock_llm)
        result = await agent.optimize(
            topic="테스트",
            script_title="테스트",
            script_text="테스트 본문",
            brand_guide=sample_brand_guide,
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], SEOAnalysis)
        assert isinstance(result[1], VideoMetadata)

    @pytest.mark.asyncio
    async def test_optimize_json_parse_failure_returns_defaults(
        self,
        mock_llm: MagicMock,
        sample_brand_guide: BrandGuide,
    ):
        """두 단계 모두 JSON 파싱이 실패해도 기본값으로 동작한다."""
        invalid_response = MagicMock()
        invalid_response.content = "유효하지 않은 응답"

        mock_llm.ainvoke = AsyncMock(
            return_value=invalid_response,
        )

        agent = SEOOptimizerAgent(mock_llm)
        seo_analysis, metadata = await agent.optimize(
            topic="테스트",
            script_title="원래 제목",
            script_text="테스트 본문",
            brand_guide=sample_brand_guide,
        )

        # 키워드 리서치 기본값
        assert seo_analysis.primary_keywords == []
        assert seo_analysis.secondary_keywords == []

        # 메타데이터 기본값 (fallback 제목 사용)
        assert metadata.title == "원래 제목"
        assert metadata.tags == []
