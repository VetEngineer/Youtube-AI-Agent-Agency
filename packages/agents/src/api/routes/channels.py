"""채널 관리 API."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import require_admin_scope, require_api_key
from src.api.dependencies import get_channel_registry
from src.api.schemas import (
    ChannelInfo,
    ChannelListResponse,
    CreateChannelRequest,
    UpdateChannelRequest,
)
from src.shared.config import ChannelRegistry

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
    registry: ChannelRegistry = Depends(get_channel_registry),
    _admin_key_id: str | None = Depends(require_admin_scope),
) -> ChannelInfo:
    """새 채널을 생성합니다."""
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
