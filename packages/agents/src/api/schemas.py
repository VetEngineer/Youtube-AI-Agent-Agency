"""API 요청/응답 스키마."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ============================================
# 파이프라인
# ============================================


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


class PipelineStatusResponse(BaseModel):
    """파이프라인 상태 조회 응답."""

    run_id: str
    status: str
    current_agent: str | None = None
    errors: list[str] = Field(default_factory=list)
    result: dict[str, Any] | None = None


class PipelineRunSummary(BaseModel):
    """파이프라인 실행 요약 (목록용)."""

    run_id: str
    channel_id: str
    topic: str
    status: str
    dry_run: bool = False
    created_at: str | None = None
    completed_at: str | None = None


class PipelineRunListResponse(BaseModel):
    """파이프라인 실행 이력 목록 응답."""

    runs: list[PipelineRunSummary]
    total: int
    limit: int
    offset: int


class PipelineRunDetail(BaseModel):
    """파이프라인 실행 상세 정보."""

    run_id: str
    channel_id: str
    topic: str
    brand_name: str = ""
    status: str
    current_agent: str | None = None
    dry_run: bool = False
    created_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None
    result: dict[str, Any] | None = None
    errors: list[str] = Field(default_factory=list)


# ============================================
# 대시보드
# ============================================


class DashboardSummary(BaseModel):
    """대시보드 요약 통계."""

    total_runs: int = Field(..., description="전체 실행 수")
    active_runs: int = Field(..., description="활성 실행 수 (pending + running)")
    success_runs: int = Field(..., description="성공 실행 수")
    failed_runs: int = Field(..., description="실패 실행 수")
    avg_duration_sec: float | None = Field(None, description="평균 소요시간 (초)")
    estimated_cost_usd: float | None = Field(None, description="예상 비용 (USD, P8-3 전까지 null)")
    recent_runs: list[PipelineRunSummary] = Field(
        default_factory=list, description="최근 실행 목록"
    )


# ============================================
# 채널
# ============================================


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


class CreateChannelRequest(BaseModel):
    """채널 생성 요청."""

    channel_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="채널 ID (영문, 숫자, 하이픈, 언더스코어)",
    )
    name: str = Field(..., min_length=1, max_length=200, description="채널 표시명")
    category: str = Field("general", max_length=50, description="카테고리")
    description: str = Field("", max_length=500, description="채널 설명")


class UpdateChannelRequest(BaseModel):
    """채널 수정 요청."""

    name: str | None = Field(None, min_length=1, max_length=200)
    category: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=500)


# ============================================
# API 키 관리
# ============================================


class CreateApiKeyRequest(BaseModel):
    """API 키 생성 요청."""

    name: str = Field(..., min_length=1, max_length=200, description="API 키 설명")
    scopes: list[str] = Field(
        default=["read", "write"],
        description="권한 스코프",
    )
    expires_days: int | None = Field(None, ge=1, le=365, description="만료일 (일, 선택)")


class CreateApiKeyResponse(BaseModel):
    """API 키 생성 응답 (평문 키는 이 응답에서만 확인 가능)."""

    api_key: str
    key_id: str
    name: str
    scopes: list[str]
    created_at: str | None = None
    expires_at: str | None = None


class ApiKeyInfo(BaseModel):
    """API 키 정보 (평문 키 미포함)."""

    key_id: str
    name: str
    scopes: list[str]
    is_active: bool
    created_at: str | None = None
    expires_at: str | None = None
    last_used_at: str | None = None


class ApiKeyListResponse(BaseModel):
    """API 키 목록 응답."""

    keys: list[ApiKeyInfo]
    total: int


# ============================================
# 감사 로그
# ============================================


class AuditLogEntry(BaseModel):
    """감사 로그 항목."""

    id: int
    timestamp: str | None = None
    method: str
    path: str
    status_code: int | None = None
    api_key_id: str | None = None
    ip_address: str | None = None
    duration_ms: float | None = None


class AuditLogListResponse(BaseModel):
    """감사 로그 목록 응답."""

    logs: list[AuditLogEntry]
    total: int
    limit: int
    offset: int
