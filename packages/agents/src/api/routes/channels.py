"""채널 관리 API."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_channel_registry
from src.api.schemas import ChannelInfo, ChannelListResponse
from src.shared.config import ChannelRegistry

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=ChannelListResponse)
async def list_channels(
    registry: ChannelRegistry = Depends(get_channel_registry),
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
