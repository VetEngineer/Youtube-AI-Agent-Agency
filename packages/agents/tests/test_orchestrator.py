"""Orchestrator 모듈 테스트.

LangGraph 파이프라인의 상태 관리, 라우팅, 에이전트 노드 실행을 검증합니다.
모든 에이전트는 Mock으로 대체하여 단위 테스트합니다.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.orchestrator.state import (
    PipelineState,
    append_error,
    create_initial_state,
)
from src.orchestrator.supervisor import (
    AgentRegistry,
    _make_brand_research_node,
    _make_media_editing_node,
    _make_media_generation_node,
    _make_publishing_node,
    _make_script_writing_node,
    _make_seo_optimization_node,
    _route_after_brand_research,
    _route_after_media_editing,
    _route_after_media_generation,
    _route_after_script_writing,
    _route_after_seo,
    build_pipeline_graph,
    compile_pipeline,
)
from src.shared.models import (
    AgentRole,
    BrandGuide,
    BrandInfo,
    ContentStatus,
    EditResult,
    PublishResult,
    Script,
    ScriptSection,
    SEOAnalysis,
    ToneAndManner,
    VideoMetadata,
    VoiceDesign,
    VoiceGenerationResult,
)

# ============================================
# Fixtures
# ============================================


@pytest.fixture
def sample_brand_guide() -> BrandGuide:
    return BrandGuide(
        brand=BrandInfo(
            name="테스트브랜드",
            positioning="테스트 포지셔닝",
            values=["가치1", "가치2"],
        ),
        tone_and_manner=ToneAndManner(personality="전문적인"),
        voice_design=VoiceDesign(
            elevenlabs_voice_id="test-voice-id",
            speech_rate="moderate",
        ),
    )


@pytest.fixture
def sample_script() -> Script:
    return Script(
        title="테스트 원고 제목",
        sections=[
            ScriptSection(heading="인트로", body="안녕하세요"),
            ScriptSection(heading="본론", body="오늘의 주제는..."),
        ],
        full_text="안녕하세요\n\n오늘의 주제는...",
        estimated_duration_seconds=120,
    )


@pytest.fixture
def sample_voice_result() -> VoiceGenerationResult:
    return VoiceGenerationResult(
        audio_path="/tmp/test_voice.mp3",
        duration_seconds=10.0,
        sample_rate=44100,
    )


@pytest.fixture
def sample_metadata() -> VideoMetadata:
    return VideoMetadata(
        title="SEO 최적화된 제목",
        description="최적화된 설명",
        tags=["태그1", "태그2"],
    )


@pytest.fixture
def sample_seo_analysis() -> SEOAnalysis:
    return SEOAnalysis(
        primary_keywords=["키워드1", "키워드2"],
        secondary_keywords=["보조키워드1"],
    )


@pytest.fixture
def base_state() -> PipelineState:
    return create_initial_state(
        channel_id="test-channel",
        topic="테스트 주제",
        brand_name="테스트브랜드",
    )


@pytest.fixture
def mock_channel_registry() -> MagicMock:
    registry = MagicMock()
    registry.has_brand_guide.return_value = False
    return registry


def _make_full_registry(
    brand_guide: BrandGuide,
    script: Script,
    voice_result: VoiceGenerationResult,
    seo_analysis: SEOAnalysis,
    metadata: VideoMetadata,
    mock_channel_registry: MagicMock,
) -> AgentRegistry:
    """모든 에이전트가 Mock으로 설정된 AgentRegistry를 생성합니다."""
    mock_brand_researcher = MagicMock()
    mock_brand_researcher.research = AsyncMock(return_value=brand_guide)

    mock_script_writer = MagicMock()
    mock_script_writer.generate = AsyncMock(return_value=script)

    mock_media_generator = MagicMock()
    mock_media_generator.generate_voice = AsyncMock(return_value=voice_result)

    mock_media_editor = MagicMock()
    mock_media_editor.edit = AsyncMock(return_value=EditResult(output_path="/output/final.mp4"))

    mock_seo_optimizer = MagicMock()
    mock_seo_optimizer.optimize = AsyncMock(return_value=(seo_analysis, metadata))

    mock_publisher = MagicMock()
    mock_publisher.publish = AsyncMock(
        return_value=PublishResult(
            video_id="vid123",
            video_url="https://youtube.com/watch?v=vid123",
            status=ContentStatus.PUBLISHED,
        )
    )

    return AgentRegistry(
        brand_researcher=mock_brand_researcher,
        script_writer=mock_script_writer,
        media_generator=mock_media_generator,
        media_editor=mock_media_editor,
        seo_optimizer=mock_seo_optimizer,
        publisher=mock_publisher,
        channel_registry=mock_channel_registry,
    )


# ============================================
# state.py 테스트
# ============================================


class TestCreateInitialState:
    def test_필수_필드가_설정된다(self) -> None:
        state = create_initial_state(
            channel_id="ch1",
            topic="고양이 건강",
            brand_name="딥퓨어",
        )
        assert state["channel_id"] == "ch1"
        assert state["topic"] == "고양이 건강"
        assert state["brand_name"] == "딥퓨어"
        assert state["status"] == ContentStatus.DRAFT
        assert state["errors"] == []

    def test_dry_run_기본값은_False이다(self) -> None:
        state = create_initial_state(channel_id="ch1", topic="test")
        assert state["dry_run"] is False

    def test_dry_run_True로_설정된다(self) -> None:
        state = create_initial_state(channel_id="ch1", topic="test", dry_run=True)
        assert state["dry_run"] is True

    def test_빈_brand_name은_허용된다(self) -> None:
        state = create_initial_state(channel_id="ch1", topic="test")
        assert state["brand_name"] == ""


class TestAppendError:
    def test_에러를_추가한다(self, base_state: PipelineState) -> None:
        update = append_error(base_state, "테스트 에러")
        assert "테스트 에러" in update["errors"]
        assert update["status"] == ContentStatus.FAILED

    def test_기존_에러에_추가한다(self) -> None:
        state = create_initial_state(channel_id="ch1", topic="test")
        state["errors"] = ["기존 에러"]
        update = append_error(state, "새 에러")
        assert len(update["errors"]) == 2
        assert "기존 에러" in update["errors"]
        assert "새 에러" in update["errors"]


# ============================================
# AgentRegistry 테스트
# ============================================


class TestAgentRegistry:
    def test_기본값은_None이다(self) -> None:
        registry = AgentRegistry()
        assert registry.brand_researcher is None
        assert registry.script_writer is None
        assert registry.media_generator is None

    def test_에이전트를_주입할_수_있다(self) -> None:
        mock_writer = MagicMock()
        registry = AgentRegistry(script_writer=mock_writer)
        assert registry.script_writer is mock_writer

    def test_channel_registry_기본값(self) -> None:
        registry = AgentRegistry()
        assert registry.channel_registry is not None


# ============================================
# 라우팅 함수 테스트
# ============================================


class TestRoutingFunctions:
    def test_brand_research_성공시_script_writing(self, base_state: PipelineState) -> None:
        assert _route_after_brand_research(base_state) == "script_writing"

    def test_brand_research_실패시_END(self, base_state: PipelineState) -> None:
        base_state["status"] = ContentStatus.FAILED
        assert _route_after_brand_research(base_state) == "__end__"

    def test_script_writing_성공시_seo(self, base_state: PipelineState) -> None:
        assert _route_after_script_writing(base_state) == "seo_optimization"

    def test_script_writing_실패시_END(self, base_state: PipelineState) -> None:
        base_state["status"] = ContentStatus.FAILED
        assert _route_after_script_writing(base_state) == "__end__"

    def test_seo_성공시_media_generation(self, base_state: PipelineState) -> None:
        assert _route_after_seo(base_state) == "media_generation"

    def test_media_generation_성공시_media_editing(self, base_state: PipelineState) -> None:
        assert _route_after_media_generation(base_state) == "media_editing"

    def test_media_generation_skip_media_edit시_publishing(self, base_state: PipelineState) -> None:
        base_state["skip_media_edit"] = True
        assert _route_after_media_generation(base_state) == "publishing"

    def test_media_editing_성공시_publishing(self, base_state: PipelineState) -> None:
        assert _route_after_media_editing(base_state) == "publishing"


# ============================================
# 노드 함수 테스트
# ============================================


class TestBrandResearchNode:
    @pytest.mark.asyncio
    async def test_새_리서치를_실행한다(
        self,
        base_state: PipelineState,
        sample_brand_guide: BrandGuide,
        mock_channel_registry: MagicMock,
    ) -> None:
        mock_researcher = MagicMock()
        mock_researcher.research = AsyncMock(return_value=sample_brand_guide)

        registry = AgentRegistry(
            brand_researcher=mock_researcher,
            channel_registry=mock_channel_registry,
        )
        node_fn = _make_brand_research_node(registry)
        result = await node_fn(base_state)

        assert result["brand_guide"] == sample_brand_guide
        mock_researcher.research.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_기존_brand_guide가_있으면_건너뛴다(
        self,
        base_state: PipelineState,
        sample_brand_guide: BrandGuide,
        mock_channel_registry: MagicMock,
    ) -> None:
        base_state["brand_guide"] = sample_brand_guide

        registry = AgentRegistry(channel_registry=mock_channel_registry)
        node_fn = _make_brand_research_node(registry)
        result = await node_fn(base_state)

        assert "brand_guide" not in result

    @pytest.mark.asyncio
    async def test_채널에서_기존_guide를_로드한다(
        self,
        base_state: PipelineState,
        sample_brand_guide: BrandGuide,
    ) -> None:
        mock_registry = MagicMock()
        mock_registry.has_brand_guide.return_value = True
        mock_registry.load_brand_guide.return_value = sample_brand_guide

        registry = AgentRegistry(channel_registry=mock_registry)
        node_fn = _make_brand_research_node(registry)
        result = await node_fn(base_state)

        assert result["brand_guide"] == sample_brand_guide
        mock_registry.load_brand_guide.assert_called_once()

    @pytest.mark.asyncio
    async def test_에이전트_미등록시_에러(
        self,
        base_state: PipelineState,
        mock_channel_registry: MagicMock,
    ) -> None:
        registry = AgentRegistry(channel_registry=mock_channel_registry)
        node_fn = _make_brand_research_node(registry)
        result = await node_fn(base_state)

        assert result["status"] == ContentStatus.FAILED
        assert any("등록되지 않았습니다" in e for e in result["errors"])


class TestScriptWritingNode:
    @pytest.mark.asyncio
    async def test_원고를_생성한다(
        self,
        base_state: PipelineState,
        sample_brand_guide: BrandGuide,
        sample_script: Script,
    ) -> None:
        base_state["brand_guide"] = sample_brand_guide

        mock_writer = MagicMock()
        mock_writer.generate = AsyncMock(return_value=sample_script)

        registry = AgentRegistry(script_writer=mock_writer)
        node_fn = _make_script_writing_node(registry)
        result = await node_fn(base_state)

        assert result["script"] == sample_script
        assert result["human_review_requested"] is True

    @pytest.mark.asyncio
    async def test_brand_guide_없으면_에러(self, base_state: PipelineState) -> None:
        registry = AgentRegistry(script_writer=MagicMock())
        node_fn = _make_script_writing_node(registry)
        result = await node_fn(base_state)

        assert result["status"] == ContentStatus.FAILED

    @pytest.mark.asyncio
    async def test_ContentPlan이_자동생성된다(
        self,
        base_state: PipelineState,
        sample_brand_guide: BrandGuide,
        sample_script: Script,
    ) -> None:
        base_state["brand_guide"] = sample_brand_guide

        mock_writer = MagicMock()
        mock_writer.generate = AsyncMock(return_value=sample_script)

        registry = AgentRegistry(script_writer=mock_writer)
        node_fn = _make_script_writing_node(registry)
        result = await node_fn(base_state)

        assert result["content_plan"].topic == "테스트 주제"


class TestSEOOptimizationNode:
    @pytest.mark.asyncio
    async def test_SEO_최적화를_수행한다(
        self,
        base_state: PipelineState,
        sample_brand_guide: BrandGuide,
        sample_script: Script,
        sample_seo_analysis: SEOAnalysis,
        sample_metadata: VideoMetadata,
    ) -> None:
        base_state["brand_guide"] = sample_brand_guide
        base_state["script"] = sample_script

        mock_optimizer = MagicMock()
        mock_optimizer.optimize = AsyncMock(return_value=(sample_seo_analysis, sample_metadata))

        registry = AgentRegistry(seo_optimizer=mock_optimizer)
        node_fn = _make_seo_optimization_node(registry)
        result = await node_fn(base_state)

        assert result["seo_analysis"] == sample_seo_analysis
        assert result["metadata"] == sample_metadata

    @pytest.mark.asyncio
    async def test_script_없으면_에러(
        self,
        base_state: PipelineState,
        sample_brand_guide: BrandGuide,
    ) -> None:
        base_state["brand_guide"] = sample_brand_guide

        registry = AgentRegistry(seo_optimizer=MagicMock())
        node_fn = _make_seo_optimization_node(registry)
        result = await node_fn(base_state)

        assert result["status"] == ContentStatus.FAILED


class TestMediaGenerationNode:
    @pytest.mark.asyncio
    async def test_음성을_생성한다(
        self,
        base_state: PipelineState,
        sample_brand_guide: BrandGuide,
        sample_script: Script,
        sample_voice_result: VoiceGenerationResult,
    ) -> None:
        base_state["brand_guide"] = sample_brand_guide
        base_state["script"] = sample_script

        mock_generator = MagicMock()
        mock_generator.generate_voice = AsyncMock(return_value=sample_voice_result)

        registry = AgentRegistry(media_generator=mock_generator)
        node_fn = _make_media_generation_node(registry)
        result = await node_fn(base_state)

        assert result["voice_result"] == sample_voice_result

    @pytest.mark.asyncio
    async def test_에이전트_예외시_에러(
        self,
        base_state: PipelineState,
        sample_brand_guide: BrandGuide,
        sample_script: Script,
    ) -> None:
        base_state["brand_guide"] = sample_brand_guide
        base_state["script"] = sample_script

        mock_generator = MagicMock()
        mock_generator.generate_voice = AsyncMock(side_effect=RuntimeError("API 실패"))

        registry = AgentRegistry(media_generator=mock_generator)
        node_fn = _make_media_generation_node(registry)
        result = await node_fn(base_state)

        assert result["status"] == ContentStatus.FAILED


class TestMediaEditingNode:
    @pytest.mark.asyncio
    async def test_편집을_수행한다(
        self,
        base_state: PipelineState,
        sample_voice_result: VoiceGenerationResult,
    ) -> None:
        base_state["voice_result"] = sample_voice_result

        mock_editor = MagicMock()
        mock_editor.edit = AsyncMock(return_value=EditResult(output_path="/output/final.mp4"))

        registry = AgentRegistry(media_editor=mock_editor)
        node_fn = _make_media_editing_node(registry)
        result = await node_fn(base_state)

        assert result["edit_result"].output_path == "/output/final.mp4"

    @pytest.mark.asyncio
    async def test_skip_media_edit시_건너뛴다(self, base_state: PipelineState) -> None:
        base_state["skip_media_edit"] = True

        registry = AgentRegistry()
        node_fn = _make_media_editing_node(registry)
        result = await node_fn(base_state)

        assert result["current_agent"] == AgentRole.MEDIA_EDITOR
        assert "edit_result" not in result


class TestPublishingNode:
    @pytest.mark.asyncio
    async def test_업로드를_수행한다(
        self,
        base_state: PipelineState,
        sample_metadata: VideoMetadata,
    ) -> None:
        base_state["metadata"] = sample_metadata
        base_state["edit_result"] = EditResult(output_path="/output/final.mp4")

        mock_publisher = MagicMock()
        mock_publisher.publish = AsyncMock(
            return_value=PublishResult(
                video_id="vid123",
                video_url="https://youtube.com/watch?v=vid123",
                status=ContentStatus.PUBLISHED,
            )
        )

        registry = AgentRegistry(publisher=mock_publisher)
        node_fn = _make_publishing_node(registry)
        result = await node_fn(base_state)

        assert result["publish_result"].video_id == "vid123"
        assert result["status"] == ContentStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_dry_run시_건너뛴다(self, base_state: PipelineState) -> None:
        base_state["dry_run"] = True

        registry = AgentRegistry()
        node_fn = _make_publishing_node(registry)
        result = await node_fn(base_state)

        assert result["status"] == ContentStatus.APPROVED
        assert result["current_agent"] == AgentRole.PUBLISHER

    @pytest.mark.asyncio
    async def test_metadata_없으면_에러(self, base_state: PipelineState) -> None:
        mock_publisher = MagicMock()
        registry = AgentRegistry(publisher=mock_publisher)
        node_fn = _make_publishing_node(registry)
        result = await node_fn(base_state)

        assert result["status"] == ContentStatus.FAILED


# ============================================
# 그래프 빌드 테스트
# ============================================


class TestBuildPipelineGraph:
    def test_그래프를_빌드할_수_있다(self) -> None:
        registry = AgentRegistry()
        graph = build_pipeline_graph(registry)
        assert graph is not None

    def test_컴파일할_수_있다(self) -> None:
        registry = AgentRegistry()
        compiled = compile_pipeline(registry)
        assert compiled is not None


# ============================================
# E2E 파이프라인 테스트
# ============================================


class TestE2EPipeline:
    @pytest.mark.asyncio
    async def test_전체_파이프라인_dry_run(
        self,
        sample_brand_guide: BrandGuide,
        sample_script: Script,
        sample_voice_result: VoiceGenerationResult,
        sample_seo_analysis: SEOAnalysis,
        sample_metadata: VideoMetadata,
        mock_channel_registry: MagicMock,
    ) -> None:
        """dry_run=True로 전체 파이프라인을 실행합니다."""
        registry = _make_full_registry(
            brand_guide=sample_brand_guide,
            script=sample_script,
            voice_result=sample_voice_result,
            seo_analysis=sample_seo_analysis,
            metadata=sample_metadata,
            mock_channel_registry=mock_channel_registry,
        )

        compiled = compile_pipeline(registry)

        initial_state = create_initial_state(
            channel_id="test-channel",
            topic="고양이 건강 관리",
            brand_name="테스트브랜드",
            dry_run=True,
        )

        final_state = await compiled.ainvoke(initial_state)

        assert final_state["brand_guide"] is not None
        assert final_state["script"] is not None
        assert final_state["seo_analysis"] is not None
        assert final_state["metadata"] is not None
        assert final_state["voice_result"] is not None
        assert final_state["status"] == ContentStatus.APPROVED

    @pytest.mark.asyncio
    async def test_전체_파이프라인_publish(
        self,
        sample_brand_guide: BrandGuide,
        sample_script: Script,
        sample_voice_result: VoiceGenerationResult,
        sample_seo_analysis: SEOAnalysis,
        sample_metadata: VideoMetadata,
        mock_channel_registry: MagicMock,
    ) -> None:
        """dry_run=False로 전체 파이프라인 (업로드 포함) 을 실행합니다."""
        registry = _make_full_registry(
            brand_guide=sample_brand_guide,
            script=sample_script,
            voice_result=sample_voice_result,
            seo_analysis=sample_seo_analysis,
            metadata=sample_metadata,
            mock_channel_registry=mock_channel_registry,
        )

        compiled = compile_pipeline(registry)

        initial_state = create_initial_state(
            channel_id="test-channel",
            topic="고양이 건강 관리",
            brand_name="테스트브랜드",
            dry_run=False,
        )

        final_state = await compiled.ainvoke(initial_state)

        assert final_state["publish_result"] is not None
        assert final_state["publish_result"].video_id == "vid123"
        assert final_state["status"] == ContentStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_brand_research_실패시_중단(
        self,
        mock_channel_registry: MagicMock,
    ) -> None:
        """브랜드 리서치에서 실패하면 파이프라인이 중단됩니다."""
        mock_researcher = MagicMock()
        mock_researcher.research = AsyncMock(side_effect=RuntimeError("리서치 API 실패"))

        registry = AgentRegistry(
            brand_researcher=mock_researcher,
            channel_registry=mock_channel_registry,
        )

        compiled = compile_pipeline(registry)

        initial_state = create_initial_state(
            channel_id="test-channel",
            topic="테스트",
            brand_name="테스트",
        )

        final_state = await compiled.ainvoke(initial_state)

        assert final_state["status"] == ContentStatus.FAILED
        assert any("리서치" in e for e in final_state["errors"])
        assert final_state.get("script") is None

    @pytest.mark.asyncio
    async def test_skip_media_edit_파이프라인(
        self,
        sample_brand_guide: BrandGuide,
        sample_script: Script,
        sample_voice_result: VoiceGenerationResult,
        sample_seo_analysis: SEOAnalysis,
        sample_metadata: VideoMetadata,
        mock_channel_registry: MagicMock,
    ) -> None:
        """skip_media_edit=True 시 편집을 건너뛰고 업로드합니다."""
        registry = _make_full_registry(
            brand_guide=sample_brand_guide,
            script=sample_script,
            voice_result=sample_voice_result,
            seo_analysis=sample_seo_analysis,
            metadata=sample_metadata,
            mock_channel_registry=mock_channel_registry,
        )

        compiled = compile_pipeline(registry)

        initial_state = create_initial_state(
            channel_id="test-channel",
            topic="테스트",
            brand_name="테스트",
            dry_run=True,
        )
        initial_state["skip_media_edit"] = True

        final_state = await compiled.ainvoke(initial_state)

        assert final_state["status"] == ContentStatus.APPROVED
