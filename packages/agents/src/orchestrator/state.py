"""Orchestrator 상태 정의.

LangGraph StateGraph에서 사용하는 TypedDict 기반 상태 및
상태 업데이트 유틸리티를 제공합니다.
"""

from __future__ import annotations

from typing import Any, TypedDict

from src.shared.models import (
    AgentRole,
    BrandGuide,
    ContentPlan,
    ContentStatus,
    EditResult,
    ImageGenerationResult,
    PublishResult,
    Script,
    SEOAnalysis,
    VideoMetadata,
    VoiceGenerationResult,
)


class PipelineState(TypedDict, total=False):
    """LangGraph 파이프라인의 공유 상태.

    각 노드는 자신의 출력 키만 업데이트합니다.
    TypedDict(total=False)로 선언하여 부분 업데이트가 가능합니다.
    """

    # 입력 (Supervisor가 설정)
    channel_id: str
    brand_name: str
    topic: str
    content_plan: ContentPlan

    # Brand Researcher 출력
    brand_guide: BrandGuide

    # Script Writer 출력
    script: Script

    # Media Generator 출력
    voice_result: VoiceGenerationResult
    image_results: list[ImageGenerationResult]

    # Media Editor 출력
    edit_result: EditResult

    # SEO Optimizer 출력
    seo_analysis: SEOAnalysis
    metadata: VideoMetadata

    # Publisher 출력
    publish_result: PublishResult

    # 실행 제어
    current_agent: AgentRole | None
    status: ContentStatus
    errors: list[str]
    human_review_requested: bool
    skip_media_edit: bool
    dry_run: bool
    output_dir: str


def create_initial_state(
    channel_id: str,
    topic: str,
    brand_name: str = "",
    dry_run: bool = False,
) -> PipelineState:
    """파이프라인 초기 상태를 생성합니다.

    Args:
        channel_id: 채널 디렉토리명 (예: "deepure-cattery")
        topic: 콘텐츠 주제
        brand_name: 브랜드명 (비어 있으면 채널 설정에서 로드)
        dry_run: True이면 실제 업로드를 건너뜀

    Returns:
        초기화된 PipelineState
    """
    return PipelineState(
        channel_id=channel_id,
        brand_name=brand_name,
        topic=topic,
        status=ContentStatus.DRAFT,
        current_agent=None,
        errors=[],
        image_results=[],
        human_review_requested=False,
        skip_media_edit=False,
        dry_run=dry_run,
    )


def append_error(state: PipelineState, error_msg: str) -> dict[str, Any]:
    """에러 메시지를 상태의 errors 리스트에 추가하는 업데이트를 반환합니다."""
    existing = state.get("errors", [])
    return {"errors": [*existing, error_msg], "status": ContentStatus.FAILED}
