"""Brand Researcher 모듈 단위 테스트.

LLM 호출은 Mock으로 대체하여 외부 API 의존성 없이 테스트합니다.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml

from src.brand_researcher.agent import BrandResearcherAgent
from src.brand_researcher.analyzer import BrandAnalysisResult, BrandAnalyzer
from src.brand_researcher.collector import BrandCollector, CollectedSource, CollectionResult
from src.brand_researcher.voice_designer import VoiceDesigner
from src.shared.config import ChannelRegistry
from src.shared.models import BrandGuide, BrandInfo

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
def sample_collection() -> CollectionResult:
    """테스트용 수집 결과."""
    return CollectionResult(
        sources=[
            CollectedSource(
                title="브랜드 소개",
                content="딥퓨어캐터리는 프리미엄 고양이 브리더입니다.",
                source_type="document",
            ),
            CollectedSource(
                title="고객 후기",
                content="건강한 고양이를 분양받았습니다. 사후 관리도 훌륭합니다.",
                url="https://example.com/review",
                source_type="web",
            ),
        ],
    )


@pytest.fixture
def sample_analysis_json() -> str:
    """Mock LLM이 반환할 분석 JSON."""
    return json.dumps(
        {
            "brand": {
                "name": "딥퓨어캐터리",
                "tagline": "건강한 혈통, 따뜻한 가족",
                "positioning": "프리미엄 고양이 브리더",
                "values": ["전문성", "신뢰", "애정"],
            },
            "target_audience": {
                "primary": "고양이 분양을 고려하는 30-40대",
                "pain_points": ["건강한 묘종 선택 어려움"],
                "content_needs": ["묘종 정보", "건강 관리 팁"],
            },
            "competitors": [
                {
                    "channel": "경쟁사A",
                    "strengths": ["큰 규모"],
                    "differentiation": "개인 맞춤 케어",
                },
            ],
        },
        ensure_ascii=False,
    )


@pytest.fixture
def sample_voice_design_json() -> str:
    """Mock LLM이 반환할 보이스 설계 JSON."""
    return json.dumps(
        {
            "tone_and_manner": {
                "personality": "따뜻하지만 전문적인 수의사 친구",
                "formality": "semi-formal",
                "emotion": "warm",
                "humor_level": "light",
                "writing_style": {
                    "sentence_length": "medium",
                    "vocabulary": "전문용어를 쉽게 풀어서 설명",
                    "call_to_action": "부드러운 권유형",
                },
                "do": ["전문 지식을 쉽게 풀어 설명"],
                "dont": ["과도한 판매 압박"],
            },
            "voice_design": {
                "narration_style": "차분하고 신뢰감 있는 여성 목소리",
                "speech_rate": "moderate",
                "pitch": "medium",
                "language": "ko",
            },
            "visual_identity": {
                "color_palette": ["#2D5016", "#F5E6D3", "#FFFFFF"],
                "thumbnail_style": "따뜻한 톤, 고양이 클로즈업 중심",
                "font_preference": "둥근 산세리프",
            },
        },
        ensure_ascii=False,
    )


@pytest.fixture
def registry_with_channel(tmp_path: Path) -> ChannelRegistry:
    """테스트용 ChannelRegistry."""
    channels_dir = tmp_path / "channels"
    channels_dir.mkdir()

    # 템플릿
    template_dir = channels_dir / "_template"
    template_dir.mkdir()
    (template_dir / "config.yaml").write_text(
        yaml.dump({"channel": {"name": "", "youtube_channel_id": "", "category": ""}}),
        encoding="utf-8",
    )

    # 딥퓨어캐터리
    cattery_dir = channels_dir / "deepure-cattery"
    cattery_dir.mkdir()
    (cattery_dir / "sources").mkdir()
    (cattery_dir / "config.yaml").write_text(
        yaml.dump(
            {
                "channel": {"name": "딥퓨어캐터리", "youtube_channel_id": "", "category": "pets"},
            }
        ),
        encoding="utf-8",
    )
    (cattery_dir / "sources" / "intro.txt").write_text(
        "딥퓨어캐터리는 건강한 고양이를 분양하는 프리미엄 브리더입니다.",
        encoding="utf-8",
    )

    return ChannelRegistry(channels_dir)


# ============================================
# Collector 테스트
# ============================================


class TestBrandCollector:
    def test_load_local_documents(self, tmp_path: Path):
        sources_dir = tmp_path / "sources"
        sources_dir.mkdir()
        (sources_dir / "intro.txt").write_text("브랜드 소개 문서", encoding="utf-8")
        (sources_dir / "data.yaml").write_text("key: value", encoding="utf-8")

        collector = BrandCollector()
        docs = collector.load_local_documents(sources_dir)
        assert len(docs) == 2
        assert docs[0].source_type == "yaml"
        assert docs[1].source_type == "document"

    def test_load_local_documents_empty_dir(self, tmp_path: Path):
        sources_dir = tmp_path / "sources"
        sources_dir.mkdir()
        collector = BrandCollector()
        docs = collector.load_local_documents(sources_dir)
        assert docs == []

    def test_load_local_documents_nonexistent(self, tmp_path: Path):
        collector = BrandCollector()
        docs = collector.load_local_documents(tmp_path / "nonexistent")
        assert docs == []

    def test_load_link_list(self, tmp_path: Path):
        sources_dir = tmp_path / "sources"
        sources_dir.mkdir()
        (sources_dir / "links.txt").write_text(
            "# 참고 링크\nhttps://example.com\nhttps://test.com\n\n",
            encoding="utf-8",
        )
        collector = BrandCollector()
        links = collector.load_link_list(sources_dir)
        assert links == ["https://example.com", "https://test.com"]

    def test_load_link_list_missing(self, tmp_path: Path):
        collector = BrandCollector()
        links = collector.load_link_list(tmp_path)
        assert links == []


class TestCollectionResult:
    def test_combined_text(self):
        result = CollectionResult(
            sources=[
                CollectedSource(title="A", content="내용A", source_type="web"),
                CollectedSource(title="B", content="내용B", source_type="document"),
            ],
        )
        text = result.combined_text
        assert "[web] A" in text
        assert "[document] B" in text


# ============================================
# Analyzer 테스트
# ============================================


class TestBrandAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_valid_response(
        self,
        mock_llm: MagicMock,
        sample_collection: CollectionResult,
        sample_analysis_json: str,
    ):
        mock_response = MagicMock()
        mock_response.content = sample_analysis_json
        mock_llm.ainvoke.return_value = mock_response

        analyzer = BrandAnalyzer(mock_llm)
        result = await analyzer.analyze("딥퓨어캐터리", sample_collection)

        assert result.brand.name == "딥퓨어캐터리"
        assert result.brand.positioning == "프리미엄 고양이 브리더"
        assert len(result.brand.values) == 3
        assert result.target_audience.primary == "고양이 분양을 고려하는 30-40대"
        assert len(result.competitors) == 1

    @pytest.mark.asyncio
    async def test_analyze_json_in_code_block(
        self,
        mock_llm: MagicMock,
        sample_collection: CollectionResult,
        sample_analysis_json: str,
    ):
        mock_response = MagicMock()
        mock_response.content = f"```json\n{sample_analysis_json}\n```"
        mock_llm.ainvoke.return_value = mock_response

        analyzer = BrandAnalyzer(mock_llm)
        result = await analyzer.analyze("딥퓨어캐터리", sample_collection)
        assert result.brand.name == "딥퓨어캐터리"

    @pytest.mark.asyncio
    async def test_analyze_invalid_response(
        self,
        mock_llm: MagicMock,
        sample_collection: CollectionResult,
    ):
        mock_response = MagicMock()
        mock_response.content = "이것은 유효하지 않은 JSON입니다."
        mock_llm.ainvoke.return_value = mock_response

        analyzer = BrandAnalyzer(mock_llm)
        result = await analyzer.analyze("딥퓨어캐터리", sample_collection)

        # 파싱 실패 시 기본값
        assert result.brand.name == "딥퓨어캐터리"
        assert result.raw_response == "이것은 유효하지 않은 JSON입니다."


# ============================================
# Voice Designer 테스트
# ============================================


class TestVoiceDesigner:
    @pytest.mark.asyncio
    async def test_design_valid_response(self, mock_llm: MagicMock, sample_voice_design_json: str):
        mock_response = MagicMock()
        mock_response.content = sample_voice_design_json
        mock_llm.ainvoke.return_value = mock_response

        analysis = BrandAnalysisResult(
            brand=BrandInfo(name="딥퓨어캐터리", positioning="프리미엄 브리더", values=["전문성"]),
            target_audience=MagicMock(
                primary="30-40대",
                pain_points=["선택 어려움"],
                content_needs=["묘종 정보"],
            ),
            competitors=[],
        )

        designer = VoiceDesigner(mock_llm)
        result = await designer.design(analysis)

        assert result.tone_and_manner.personality == "따뜻하지만 전문적인 수의사 친구"
        assert result.tone_and_manner.formality == "semi-formal"
        assert result.voice_design.narration_style == "차분하고 신뢰감 있는 여성 목소리"
        assert len(result.visual_identity.color_palette) == 3

    @pytest.mark.asyncio
    async def test_design_invalid_response(self, mock_llm: MagicMock):
        mock_response = MagicMock()
        mock_response.content = "유효하지 않은 응답"
        mock_llm.ainvoke.return_value = mock_response

        analysis = BrandAnalysisResult(
            brand=BrandInfo(name="테스트"),
            target_audience=MagicMock(primary="", pain_points=[], content_needs=[]),
            competitors=[],
        )

        designer = VoiceDesigner(mock_llm)
        result = await designer.design(analysis)

        assert result.tone_and_manner.formality == "semi-formal"
        assert result.raw_response == "유효하지 않은 응답"


# ============================================
# Agent 통합 테스트 (Mock LLM)
# ============================================


class TestBrandResearcherAgent:
    @pytest.mark.asyncio
    async def test_research_from_collection(
        self,
        mock_llm: MagicMock,
        sample_collection: CollectionResult,
        sample_analysis_json: str,
        sample_voice_design_json: str,
    ):
        # 첫 번째 호출: 분석, 두 번째 호출: 보이스 설계
        analysis_response = MagicMock()
        analysis_response.content = sample_analysis_json
        voice_response = MagicMock()
        voice_response.content = sample_voice_design_json
        mock_llm.ainvoke = AsyncMock(side_effect=[analysis_response, voice_response])

        registry = MagicMock(spec=ChannelRegistry)
        agent = BrandResearcherAgent(llm=mock_llm, registry=registry)

        guide = await agent.research_from_collection("딥퓨어캐터리", sample_collection)

        assert isinstance(guide, BrandGuide)
        assert guide.brand.name == "딥퓨어캐터리"
        assert guide.tone_and_manner.personality == "따뜻하지만 전문적인 수의사 친구"
        assert guide.voice_design.narration_style == "차분하고 신뢰감 있는 여성 목소리"

    @pytest.mark.asyncio
    async def test_research_and_save(
        self,
        mock_llm: MagicMock,
        sample_analysis_json: str,
        sample_voice_design_json: str,
        registry_with_channel: ChannelRegistry,
    ):
        analysis_response = MagicMock()
        analysis_response.content = sample_analysis_json
        voice_response = MagicMock()
        voice_response.content = sample_voice_design_json
        mock_llm.ainvoke = AsyncMock(side_effect=[analysis_response, voice_response])

        # Collector도 Mock (웹 검색 건너뛰기)
        mock_collector = MagicMock(spec=BrandCollector)
        mock_collector.collect_all = AsyncMock(
            return_value=CollectionResult(
                sources=[
                    CollectedSource(title="문서", content="브랜드 소개", source_type="document")
                ],
            )
        )

        agent = BrandResearcherAgent(
            llm=mock_llm,
            registry=registry_with_channel,
            collector=mock_collector,
        )

        guide, saved_path = await agent.research_and_save("deepure-cattery", "딥퓨어캐터리")

        assert saved_path.exists()
        assert guide.brand.name == "딥퓨어캐터리"

        # 저장된 YAML 확인
        saved_data = yaml.safe_load(saved_path.read_text(encoding="utf-8"))
        assert saved_data["brand"]["name"] == "딥퓨어캐터리"
