"""경쟁 채널 모니터링 API."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from yaa_core.database.engine import get_db_session
from yaa_core.database.repositories import CompetitorRepository

from yaa_app.api.auth import require_admin_scope, require_api_key
from yaa_app.api.dependencies import get_settings
from yaa_app.api.schemas import (
    AddCompetitorRequest,
    CompetitorChannelInfo,
    CompetitorDetailResponse,
    CompetitorListResponse,
    CompetitorVideoInfo,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _to_channel_info(model) -> CompetitorChannelInfo:
    """ORM 모델을 스키마로 변환합니다."""
    return CompetitorChannelInfo(
        id=model.id,
        youtube_channel_id=model.youtube_channel_id,
        name=model.name,
        description=model.description,
        subscriber_count=model.subscriber_count,
        video_count=model.video_count,
        thumbnail_url=model.thumbnail_url,
        last_crawled_at=model.last_crawled_at.isoformat() if model.last_crawled_at else None,
        is_active=model.is_active,
    )


def _to_video_info(model) -> CompetitorVideoInfo:
    """영상 ORM 모델을 스키마로 변환합니다."""
    return CompetitorVideoInfo(
        video_id=model.video_id,
        title=model.title,
        view_count=model.view_count,
        like_count=model.like_count,
        comment_count=model.comment_count,
        published_at=model.published_at.isoformat() if model.published_at else "",
        tags=model.tags,
        duration_seconds=model.duration_seconds,
        thumbnail_url=model.thumbnail_url,
    )


@router.get("/", response_model=CompetitorListResponse)
async def list_competitors(
    workspace_id: str,
    session: AsyncSession = Depends(get_db_session),
    _api_key_id: str | None = Depends(require_api_key),
) -> CompetitorListResponse:
    """등록된 경쟁 채널 목록을 조회합니다."""
    repo = CompetitorRepository(session)
    competitors = await repo.list_by_workspace(workspace_id)
    return CompetitorListResponse(
        competitors=[_to_channel_info(c) for c in competitors],
        total=len(competitors),
    )


@router.post("/", response_model=CompetitorChannelInfo, status_code=201)
async def add_competitor(
    request: AddCompetitorRequest,
    workspace_id: str,
    session: AsyncSession = Depends(get_db_session),
    _admin_key_id: str | None = Depends(require_admin_scope),
    settings=Depends(get_settings),
) -> CompetitorChannelInfo:
    """경쟁 채널을 등록하고 즉시 데이터를 수집합니다."""
    if not settings.youtube_api_key:
        raise HTTPException(
            status_code=503,
            detail="YOUTUBE_API_KEY가 설정되지 않았습니다. 환경변수를 확인하세요.",
        )

    from yaa_agents.competitor.collector import CompetitorCollector

    # YouTube API로 채널 정보 조회
    collector = CompetitorCollector(settings.youtube_api_key)
    try:
        channel_info = await collector.fetch_channel_info(request.youtube_channel_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=f"YouTube API 오류: {exc}")

    # DB 저장
    repo = CompetitorRepository(session)
    competitor_id = str(uuid.uuid4())
    competitor = await repo.create(
        competitor_id=competitor_id,
        workspace_id=workspace_id,
        youtube_channel_id=request.youtube_channel_id,
        name=channel_info["name"],
    )

    # 통계 업데이트
    await repo.update_channel_stats(
        competitor_id=competitor_id,
        name=channel_info["name"],
        description=channel_info.get("description"),
        subscriber_count=channel_info["subscriber_count"],
        video_count=channel_info["video_count"],
        thumbnail_url=channel_info.get("thumbnail_url"),
    )

    await session.commit()
    await session.refresh(competitor)

    return _to_channel_info(competitor)


@router.get("/{competitor_id}", response_model=CompetitorDetailResponse)
async def get_competitor(
    competitor_id: str,
    session: AsyncSession = Depends(get_db_session),
    _api_key_id: str | None = Depends(require_api_key),
) -> CompetitorDetailResponse:
    """경쟁 채널 상세 정보와 최근 영상 목록을 조회합니다."""
    repo = CompetitorRepository(session)
    competitor = await repo.get(competitor_id)
    if competitor is None:
        raise HTTPException(status_code=404, detail="경쟁 채널을 찾을 수 없습니다.")

    videos = await repo.list_videos(competitor_id, limit=20)

    return CompetitorDetailResponse(
        channel=_to_channel_info(competitor),
        recent_videos=[_to_video_info(v) for v in videos],
    )


@router.delete("/{competitor_id}")
async def delete_competitor(
    competitor_id: str,
    session: AsyncSession = Depends(get_db_session),
    _admin_key_id: str | None = Depends(require_admin_scope),
) -> dict[str, str]:
    """경쟁 채널을 제거합니다."""
    repo = CompetitorRepository(session)
    competitor = await repo.get(competitor_id)
    if competitor is None:
        raise HTTPException(status_code=404, detail="경쟁 채널을 찾을 수 없습니다.")

    await repo.delete(competitor_id)
    await session.commit()

    return {"message": "경쟁 채널이 삭제되었습니다.", "competitor_id": competitor_id}


@router.post("/{competitor_id}/refresh", response_model=CompetitorDetailResponse)
async def refresh_competitor(
    competitor_id: str,
    session: AsyncSession = Depends(get_db_session),
    _admin_key_id: str | None = Depends(require_admin_scope),
    settings=Depends(get_settings),
) -> CompetitorDetailResponse:
    """경쟁 채널 데이터를 즉시 수집합니다."""
    if not settings.youtube_api_key:
        raise HTTPException(
            status_code=503,
            detail="YOUTUBE_API_KEY가 설정되지 않았습니다.",
        )

    repo = CompetitorRepository(session)
    competitor = await repo.get(competitor_id)
    if competitor is None:
        raise HTTPException(status_code=404, detail="경쟁 채널을 찾을 수 없습니다.")

    from yaa_agents.competitor.collector import CompetitorCollector

    collector = CompetitorCollector(settings.youtube_api_key)

    # 채널 정보 수집
    try:
        channel_info = await collector.fetch_channel_info(competitor.youtube_channel_id)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=f"YouTube API 오류: {exc}")

    await repo.update_channel_stats(
        competitor_id=competitor_id,
        name=channel_info["name"],
        description=channel_info.get("description"),
        subscriber_count=channel_info["subscriber_count"],
        video_count=channel_info["video_count"],
        thumbnail_url=channel_info.get("thumbnail_url"),
    )

    # 최근 영상 수집
    try:
        videos = await collector.fetch_recent_videos(
            competitor.youtube_channel_id, max_results=20
        )
    except (ValueError, RuntimeError) as exc:
        logger.warning("영상 수집 실패 (competitor_id=%s): %s", competitor_id, exc)
        videos = []

    for video_data in videos:
        await repo.upsert_video(
            video_id_internal=str(uuid.uuid4()),
            competitor_channel_id=competitor_id,
            **video_data,
        )

    await session.commit()
    await session.refresh(competitor)

    video_models = await repo.list_videos(competitor_id, limit=20)

    return CompetitorDetailResponse(
        channel=_to_channel_info(competitor),
        recent_videos=[_to_video_info(v) for v in video_models],
    )
