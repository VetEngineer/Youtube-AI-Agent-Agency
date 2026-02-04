"""API 요청/응답 스키마."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PipelineRunRequest(BaseModel):
    """파이프라인 실행 요청."""

    channel_id: str = Field(..., description="채널 ID")
    topic: str = Field(..., description="콘텐츠 주제")
    brand_name: str = Field("", description="브랜드명 (선택)")
    dry_run: bool = Field(False, description="실제 업로드 건너뜀")


class PipelineRunResponse(BaseModel):
    """파이프라인 실행 응답."""

    run_id: str
    status: str
    channel_id: str
    topic: str


class ChannelInfo(BaseModel):
    """채널 정보."""

    channel_id: str
    name: str
    category: str
    has_brand_guide: bool


class ChannelListResponse(BaseModel):
    """채널 목록 응답."""

    channels: list[ChannelInfo]
    total: int


class PipelineStatusResponse(BaseModel):
    """파이프라인 상태 조회 응답."""

    run_id: str
    status: str
    current_agent: str | None = None
    errors: list[str] = Field(default_factory=list)
    result: dict[str, Any] | None = None
