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


def _scoped_registry(request: Request, registry: ChannelRegistry) -> ChannelRegistry:
    """auth_context의 workspace_id로 스코프된 레지스트리를 반환합니다."""
    auth_ctx = getattr(request.state, "auth_context", None)
    if auth_ctx and auth_ctx.workspace_id:
        return registry.for_workspace(auth_ctx.workspace_id)
    return registry


@router.get("/", response_model=ChannelListResponse)
async def list_channels(
    request: Request,
    registry: ChannelRegistry = Depends(get_channel_registry),
    _api_key_id: str | None = Depends(require_api_key),
) -> ChannelListResponse:
    """등록된 채널 목록을 조회합니다."""
    scoped = _scoped_registry(request, registry)
    channel_ids = scoped.list_channels()

    channels: list[ChannelInfo] = []
    for channel_id in channel_ids:
        try:
            settings = scoped.load_settings(channel_id)
            has_guide = scoped.has_brand_guide(channel_id)
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
    request: Request,
    registry: ChannelRegistry = Depends(get_channel_registry),
    _api_key_id: str | None = Depends(require_api_key),
) -> ChannelInfo:
    """특정 채널 정보를 조회합니다."""
    scoped = _scoped_registry(request, registry)
    try:
        settings = scoped.load_settings(channel_id)
        has_guide = scoped.has_brand_guide(channel_id)
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
    scoped = _scoped_registry(http_request, registry)

    auth_ctx = getattr(http_request.state, "auth_context", None)
    if auth_ctx is not None and auth_ctx.workspace_id is not None:
        ws_repo = WorkspaceRepository(session)
        workspace = await ws_repo.get(auth_ctx.workspace_id)
        if workspace is not None and workspace.channel_quota != -1:
            channel_count = len(scoped.list_channels())
            if channel_count >= workspace.channel_quota:
                raise HTTPException(
                    status_code=409,
                    detail="채널 한도 초과. 플랜을 업그레이드하세요.",
                )

    try:
        scoped.create_channel_from_template(request.channel_id)
    except FileExistsError:
        raise HTTPException(status_code=409, detail=f"채널이 이미 존재합니다: {request.channel_id}")

    scoped.update_channel_config(
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
    http_request: Request,
    registry: ChannelRegistry = Depends(get_channel_registry),
    _admin_key_id: str | None = Depends(require_admin_scope),
) -> ChannelInfo:
    """채널 설정을 수정합니다."""
    scoped = _scoped_registry(http_request, registry)
    try:
        scoped.get_channel_path(channel_id)
    except (FileNotFoundError, ValueError):
        raise HTTPException(status_code=404, detail=f"채널을 찾을 수 없습니다: {channel_id}")

    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="수정할 필드가 없습니다.")

    scoped.update_channel_config(channel_id, updates)
    settings = scoped.load_settings(channel_id)
    has_guide = scoped.has_brand_guide(channel_id)

    return ChannelInfo(
        channel_id=channel_id,
        name=settings.channel.name,
        category=settings.channel.category,
        has_brand_guide=has_guide,
    )


@router.post("/{channel_id}/rag/index")
async def rag_index_channel(
    channel_id: str,
    request: Request,
    registry: ChannelRegistry = Depends(get_channel_registry),
    _api_key_id: str | None = Depends(require_api_key),
) -> dict:
    """채널 브랜드 자료를 RAG 벡터 스토리지에 인덱싱합니다."""
    scoped = _scoped_registry(request, registry)
    try:
        channel_path = scoped.get_channel_path(channel_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"채널을 찾을 수 없습니다: {channel_id}")

    try:
        from yaa_agents.brand_researcher.rag import BrandIndexer, RAGConfig
    except ImportError:
        raise HTTPException(
            status_code=503, detail="chromadb가 설치되지 않아 RAG를 사용할 수 없습니다"
        )

    indexer = BrandIndexer(RAGConfig())
    n = indexer.index_channel(channel_id, channel_path)
    logger.info("[RAG] 인덱싱 완료: channel=%s, chunks=%d", channel_id, n)

    return {"channel_id": channel_id, "indexed_chunks": n}


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: str,
    request: Request,
    registry: ChannelRegistry = Depends(get_channel_registry),
    _admin_key_id: str | None = Depends(require_admin_scope),
) -> dict[str, str]:
    """채널을 삭제합니다."""
    scoped = _scoped_registry(request, registry)
    try:
        scoped.delete_channel(channel_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"채널을 찾을 수 없습니다: {channel_id}")

    return {"message": "채널이 삭제되었습니다.", "channel_id": channel_id}
