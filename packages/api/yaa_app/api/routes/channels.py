"""채널 관리 API."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from yaa_core.database.engine import get_db_session
from yaa_core.database.repositories import WorkspaceRepository
from yaa_core.shared.config import ChannelRegistry

from yaa_app.api.auth import require_admin_scope, require_api_key
from yaa_app.api.dependencies import get_channel_registry
from yaa_app.api.schemas import (
    ChannelInfo,
    ChannelListResponse,
    CreateChannelRequest,
    UpdateChannelRequest,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=ChannelListResponse)
async def list_channels(
    registry: ChannelRegistry = Depends(get_channel_registry),
    _api_key_id: str | None = Depends(require_api_key),
) -> ChannelListResponse:
    """등록된 채널 목록을 조회합니다."""
    channel_ids = registry.list_channels()

    channels: list[ChannelInfo] = []
    for channel_id in channel_ids:
        try:
            settings = registry.load_settings(channel_id)
            has_guide = registry.has_brand_guide(channel_id)
            channels.append(
                ChannelInfo(
                    channel_id=channel_id,
                    name=settings.channel.name,
                    category=settings.channel.category,
                    has_brand_guide=has_guide,
                )
            )
        except Exception:
            logger.warning("채널 설정 로드 실패: %s", channel_id, exc_info=True)

    return ChannelListResponse(channels=channels, total=len(channels))


@router.get("/{channel_id}", response_model=ChannelInfo)
async def get_channel(
    channel_id: str,
    registry: ChannelRegistry = Depends(get_channel_registry),
    _api_key_id: str | None = Depends(require_api_key),
) -> ChannelInfo:
    """특정 채널 정보를 조회합니다."""
    try:
        settings = registry.load_settings(channel_id)
        has_guide = registry.has_brand_guide(channel_id)
        return ChannelInfo(
            channel_id=channel_id,
            name=settings.channel.name,
            category=settings.channel.category,
            has_brand_guide=has_guide,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"채널을 찾을 수 없습니다: {channel_id}")


@router.post("/", response_model=ChannelInfo, status_code=201)
async def create_channel(
    request: CreateChannelRequest,
    http_request: Request,
    registry: ChannelRegistry = Depends(get_channel_registry),
    _admin_key_id: str | None = Depends(require_admin_scope),
    session: AsyncSession = Depends(get_db_session),
) -> ChannelInfo:
    """새 채널을 생성합니다."""
    auth_ctx = getattr(http_request.state, "auth_context", None)
    if auth_ctx is not None and auth_ctx.workspace_id is not None:
        ws_repo = WorkspaceRepository(session)
        workspace = await ws_repo.get(auth_ctx.workspace_id)
        if workspace is not None and workspace.channel_quota != -1:
            channel_count = len(registry.list_channels())
            if channel_count >= workspace.channel_quota:
                raise HTTPException(
                    status_code=409,
                    detail="채널 한도 초과. 플랜을 업그레이드하세요.",
                )

    try:
        registry.create_channel_from_template(request.channel_id)
    except FileExistsError:
        raise HTTPException(status_code=409, detail=f"채널이 이미 존재합니다: {request.channel_id}")

    registry.update_channel_config(
        request.channel_id,
        {
            "name": request.name,
            "category": request.category,
            "description": request.description,
        },
    )

    return ChannelInfo(
        channel_id=request.channel_id,
        name=request.name,
        category=request.category,
        has_brand_guide=False,
    )


@router.patch("/{channel_id}", response_model=ChannelInfo)
async def update_channel(
    channel_id: str,
    request: UpdateChannelRequest,
    registry: ChannelRegistry = Depends(get_channel_registry),
    _admin_key_id: str | None = Depends(require_admin_scope),
) -> ChannelInfo:
    """채널 설정을 수정합니다."""
    try:
        registry.get_channel_path(channel_id)
    except (FileNotFoundError, ValueError):
        raise HTTPException(status_code=404, detail=f"채널을 찾을 수 없습니다: {channel_id}")

    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="수정할 필드가 없습니다.")

    registry.update_channel_config(channel_id, updates)
    settings = registry.load_settings(channel_id)
    has_guide = registry.has_brand_guide(channel_id)

    return ChannelInfo(
        channel_id=channel_id,
        name=settings.channel.name,
        category=settings.channel.category,
        has_brand_guide=has_guide,
    )


@router.post("/{channel_id}/rag/index")
async def rag_index_channel(
    channel_id: str,
    registry: ChannelRegistry = Depends(get_channel_registry),
    _api_key_id: str | None = Depends(require_api_key),
) -> dict:
    """채널 브랜드 자료를 RAG 벡터 스토리지에 인덱싱합니다."""
    try:
        channel_path = registry.get_channel_path(channel_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"채널을 찾을 수 없습니다: {channel_id}")

    try:
        from yaa_agents.brand_researcher.rag import BrandIndexer, RAGConfig
    except ImportError:
        raise HTTPException(status_code=503, detail="chromadb가 설치되지 않아 RAG를 사용할 수 없습니다")

    indexer = BrandIndexer(RAGConfig())
    n = indexer.index_channel(channel_id, channel_path)
    logger.info("[RAG] 인덱싱 완료: channel=%s, chunks=%d", channel_id, n)

    return {"channel_id": channel_id, "indexed_chunks": n}


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: str,
    registry: ChannelRegistry = Depends(get_channel_registry),
    _admin_key_id: str | None = Depends(require_admin_scope),
) -> dict[str, str]:
    """채널을 삭제합니다."""
    try:
        registry.delete_channel(channel_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"채널을 찾을 수 없습니다: {channel_id}")

    return {"message": "채널이 삭제되었습니다.", "channel_id": channel_id}
