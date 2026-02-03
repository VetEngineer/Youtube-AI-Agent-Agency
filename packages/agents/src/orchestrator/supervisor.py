"""LangGraph Supervisor - 콘텐츠 생성 파이프라인 오케스트레이터.

각 에이전트를 LangGraph 노드로 등록하고, 조건부 엣지로 실행 순서를 제어합니다.
Human-in-the-loop 검토 포인트를 제공합니다.

파이프라인 흐름:
  brand_research → script_writing → [seo_optimization, media_generation]
    → media_editing → review → publishing
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from src.shared.config import ChannelRegistry
from src.shared.models import (
    AgentRole,
    ContentPlan,
    ContentStatus,
    EditProject,
    PublishRequest,
)

from .state import PipelineState, append_error

logger = logging.getLogger(__name__)


# ============================================
# 노드 함수 (각 에이전트 래퍼)
# ============================================


class AgentRegistry:
    """에이전트 인스턴스를 보관하는 레지스트리.

    Supervisor 빌드 시 주입받아 각 노드 함수에서 사용합니다.
    """

    def __init__(
        self,
        brand_researcher: Any = None,
        script_writer: Any = None,
        media_generator: Any = None,
        media_editor: Any = None,
        seo_optimizer: Any = None,
        publisher: Any = None,
        channel_registry: ChannelRegistry | None = None,
    ) -> None:
        self.brand_researcher = brand_researcher
        self.script_writer = script_writer
        self.media_generator = media_generator
        self.media_editor = media_editor
        self.seo_optimizer = seo_optimizer
        self.publisher = publisher
        self.channel_registry = channel_registry or ChannelRegistry()


def _make_brand_research_node(registry: AgentRegistry):
    """Brand Researcher 노드 함수를 생성합니다."""

    async def brand_research_node(state: PipelineState) -> dict[str, Any]:
        logger.info("[brand_research] 시작: channel=%s", state["channel_id"])

        try:
            channel_id = state["channel_id"]
            brand_name = state.get("brand_name", "")

            # 이미 brand_guide가 있으면 건너뜀
            if state.get("brand_guide") is not None:
                logger.info("[brand_research] 기존 brand_guide 사용")
                return {"current_agent": AgentRole.BRAND_RESEARCHER}

            # ChannelRegistry에서 기존 brand_guide 로드 시도
            if registry.channel_registry.has_brand_guide(channel_id):
                guide = registry.channel_registry.load_brand_guide(channel_id)
                logger.info("[brand_research] 채널에서 기존 brand_guide 로드")
                return {
                    "brand_guide": guide,
                    "current_agent": AgentRole.BRAND_RESEARCHER,
                }

            # 에이전트가 등록되지 않았으면 에러
            if registry.brand_researcher is None:
                return append_error(state, "BrandResearcherAgent가 등록되지 않았습니다")

            # 새로 리서치 실행
            guide = await registry.brand_researcher.research(
                channel_id=channel_id,
                brand_name=brand_name,
            )

            logger.info("[brand_research] 완료: brand=%s", guide.brand.name)
            return {
                "brand_guide": guide,
                "current_agent": AgentRole.BRAND_RESEARCHER,
            }

        except Exception as exc:
            logger.error("[brand_research] 실패: %s", exc)
            return append_error(state, f"브랜드 리서치 실패: {exc}")

    return brand_research_node


def _make_script_writing_node(registry: AgentRegistry):
    """Script Writer 노드 함수를 생성합니다."""

    async def script_writing_node(state: PipelineState) -> dict[str, Any]:
        logger.info("[script_writing] 시작: topic=%s", state.get("topic", ""))

        if registry.script_writer is None:
            return append_error(state, "ScriptWriterAgent가 등록되지 않았습니다")

        try:
            brand_guide = state.get("brand_guide")
            if brand_guide is None:
                return append_error(
                    state,
                    "brand_guide가 없습니다. 브랜드 리서치를 먼저 실행하세요.",
                )

            plan = state.get("content_plan") or ContentPlan(
                channel_id=state["channel_id"],
                topic=state.get("topic", ""),
            )

            script = await registry.script_writer.generate(plan, brand_guide)

            logger.info("[script_writing] 완료: title=%s", script.title)
            return {
                "script": script,
                "content_plan": plan,
                "current_agent": AgentRole.SCRIPT_WRITER,
                "human_review_requested": True,
            }

        except Exception as exc:
            logger.error("[script_writing] 실패: %s", exc)
            return append_error(state, f"원고 생성 실패: {exc}")

    return script_writing_node


def _make_seo_optimization_node(registry: AgentRegistry):
    """SEO Optimizer 노드 함수를 생성합니다."""

    async def seo_optimization_node(state: PipelineState) -> dict[str, Any]:
        logger.info("[seo_optimization] 시작")

        if registry.seo_optimizer is None:
            return append_error(state, "SEOOptimizerAgent가 등록되지 않았습니다")

        try:
            script = state.get("script")
            brand_guide = state.get("brand_guide")

            if script is None or brand_guide is None:
                return append_error(state, "script 또는 brand_guide가 없습니다")

            seo_analysis, metadata = await registry.seo_optimizer.optimize(
                topic=state.get("topic", ""),
                script_title=script.title,
                script_text=script.full_text,
                brand_guide=brand_guide,
            )

            logger.info(
                "[seo_optimization] 완료: keywords=%d, title=%s",
                len(seo_analysis.primary_keywords),
                metadata.title,
            )
            return {
                "seo_analysis": seo_analysis,
                "metadata": metadata,
                "current_agent": AgentRole.SEO_OPTIMIZER,
            }

        except Exception as exc:
            logger.error("[seo_optimization] 실패: %s", exc)
            return append_error(state, f"SEO 최적화 실패: {exc}")

    return seo_optimization_node


def _make_media_generation_node(registry: AgentRegistry):
    """Media Generator 노드 함수를 생성합니다."""

    async def media_generation_node(state: PipelineState) -> dict[str, Any]:
        logger.info("[media_generation] 시작")

        if registry.media_generator is None:
            return append_error(state, "MediaGeneratorAgent가 등록되지 않았습니다")

        try:
            script = state.get("script")
            brand_guide = state.get("brand_guide")

            if script is None or brand_guide is None:
                return append_error(state, "script 또는 brand_guide가 없습니다")

            # 음성 생성
            voice_result = await registry.media_generator.generate_voice(
                text=script.full_text,
                voice_design=brand_guide.voice_design,
            )

            logger.info(
                "[media_generation] 음성 완료: %.1f초",
                voice_result.duration_seconds,
            )
            return {
                "voice_result": voice_result,
                "current_agent": AgentRole.MEDIA_GENERATOR,
            }

        except Exception as exc:
            logger.error("[media_generation] 실패: %s", exc)
            return append_error(state, f"미디어 생성 실패: {exc}")

    return media_generation_node


def _make_media_editing_node(registry: AgentRegistry):
    """Media Editor 노드 함수를 생성합니다."""

    async def media_editing_node(state: PipelineState) -> dict[str, Any]:
        logger.info("[media_editing] 시작")

        if state.get("skip_media_edit"):
            logger.info("[media_editing] 건너뜀 (skip_media_edit=True)")
            return {"current_agent": AgentRole.MEDIA_EDITOR}

        if registry.media_editor is None:
            return append_error(state, "MediaEditorAgent가 등록되지 않았습니다")

        try:
            voice_result = state.get("voice_result")

            audio_tracks: list[str] = []
            if voice_result and voice_result.audio_path:
                audio_tracks.append(voice_result.audio_path)

            project = EditProject(
                source_videos=[],
                audio_tracks=audio_tracks,
                output_path=(
                    f"{state.get('output_dir', './output')}/{state['channel_id']}/final.mp4"
                ),
            )

            edit_result = await registry.media_editor.edit(project)

            logger.info("[media_editing] 완료: %s", edit_result.output_path)
            return {
                "edit_result": edit_result,
                "current_agent": AgentRole.MEDIA_EDITOR,
            }

        except Exception as exc:
            logger.error("[media_editing] 실패: %s", exc)
            return append_error(state, f"영상 편집 실패: {exc}")

    return media_editing_node


def _make_publishing_node(registry: AgentRegistry):
    """Publisher 노드 함수를 생성합니다."""

    async def publishing_node(state: PipelineState) -> dict[str, Any]:
        logger.info("[publishing] 시작")

        if state.get("dry_run"):
            logger.info("[publishing] 건너뜀 (dry_run=True)")
            return {
                "status": ContentStatus.APPROVED,
                "current_agent": AgentRole.PUBLISHER,
            }

        if registry.publisher is None:
            return append_error(state, "PublisherAgent가 등록되지 않았습니다")

        try:
            metadata = state.get("metadata")
            edit_result = state.get("edit_result")

            if metadata is None:
                return append_error(state, "metadata가 없습니다")

            video_path = edit_result.output_path if edit_result else ""

            request = PublishRequest(
                video_path=video_path,
                metadata=metadata,
                channel_id=state["channel_id"],
                privacy_status="private",
            )

            result = await registry.publisher.publish(request)

            if result.status == ContentStatus.PUBLISHED:
                logger.info(
                    "[publishing] 성공: video_id=%s",
                    result.video_id,
                )
            else:
                logger.warning("[publishing] 실패: %s", result.error)

            return {
                "publish_result": result,
                "status": result.status,
                "current_agent": AgentRole.PUBLISHER,
            }

        except Exception as exc:
            logger.error("[publishing] 실패: %s", exc)
            return append_error(state, f"업로드 실패: {exc}")

    return publishing_node


# ============================================
# 라우팅 함수
# ============================================


def _route_after_brand_research(state: PipelineState) -> str:
    """브랜드 리서치 이후 라우팅."""
    if state.get("status") == ContentStatus.FAILED:
        return END
    return "script_writing"


def _route_after_script_writing(state: PipelineState) -> str:
    """원고 생성 이후 라우팅.

    Human-in-the-loop: 원고 검토가 필요하면 review 노드로 이동.
    """
    if state.get("status") == ContentStatus.FAILED:
        return END
    return "seo_optimization"


def _route_after_seo(state: PipelineState) -> str:
    """SEO 최적화 이후 라우팅."""
    if state.get("status") == ContentStatus.FAILED:
        return END
    return "media_generation"


def _route_after_media_generation(state: PipelineState) -> str:
    """미디어 생성 이후 라우팅."""
    if state.get("status") == ContentStatus.FAILED:
        return END
    if state.get("skip_media_edit"):
        return "publishing"
    return "media_editing"


def _route_after_media_editing(state: PipelineState) -> str:
    """영상 편집 이후 라우팅."""
    if state.get("status") == ContentStatus.FAILED:
        return END
    return "publishing"


# ============================================
# 그래프 빌더
# ============================================


def build_pipeline_graph(
    agent_registry: AgentRegistry,
) -> StateGraph:
    """콘텐츠 생성 파이프라인 StateGraph를 빌드합니다.

    Args:
        agent_registry: 에이전트 인스턴스가 등록된 레지스트리

    Returns:
        컴파일 가능한 StateGraph
    """
    graph = StateGraph(PipelineState)

    # 노드 등록
    graph.add_node("brand_research", _make_brand_research_node(agent_registry))
    graph.add_node("script_writing", _make_script_writing_node(agent_registry))
    graph.add_node("seo_optimization", _make_seo_optimization_node(agent_registry))
    graph.add_node("media_generation", _make_media_generation_node(agent_registry))
    graph.add_node("media_editing", _make_media_editing_node(agent_registry))
    graph.add_node("publishing", _make_publishing_node(agent_registry))

    # 진입점
    graph.set_entry_point("brand_research")

    # 조건부 엣지
    graph.add_conditional_edges("brand_research", _route_after_brand_research)
    graph.add_conditional_edges("script_writing", _route_after_script_writing)
    graph.add_conditional_edges("seo_optimization", _route_after_seo)
    graph.add_conditional_edges("media_generation", _route_after_media_generation)
    graph.add_conditional_edges("media_editing", _route_after_media_editing)
    graph.add_edge("publishing", END)

    return graph


def compile_pipeline(
    agent_registry: AgentRegistry,
) -> Any:
    """파이프라인 그래프를 컴파일하여 실행 가능한 Runnable을 반환합니다.

    Args:
        agent_registry: 에이전트 인스턴스가 등록된 레지스트리

    Returns:
        CompiledGraph (ainvoke 가능)
    """
    graph = build_pipeline_graph(agent_registry)
    return graph.compile()
