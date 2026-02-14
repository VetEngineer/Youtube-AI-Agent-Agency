"""요금제 및 사용량 API."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from yaa_core.database.engine import get_db_session
from yaa_core.database.repositories import RunRepository, WorkspaceRepository
from yaa_core.shared.config import PLAN_QUOTAS

from yaa_app.api.auth import AuthContext, get_auth_context

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# 스키마
# ============================================


class PlanQuota(BaseModel):
    """요금제 한도 정보."""

    monthly_pipelines: int = Field(..., description="월간 파이프라인 한도 (-1: 무제한)")
    max_channels: int = Field(..., description="최대 채널 수 (-1: 무제한)")
    media_generation: bool = Field(..., description="미디어 생성 가능 여부")
    youtube_upload: bool = Field(..., description="YouTube 업로드 가능 여부")
    priority_queue: bool = Field(..., description="우선순위 큐 사용 가능 여부")
    api_access: bool = Field(..., description="API 접근 가능 여부")


class PlanInfo(BaseModel):
    """요금제 정보."""

    name: str = Field(..., description="요금제 이름")
    quotas: PlanQuota


class PlanListResponse(BaseModel):
    """요금제 목록 응답."""

    plans: list[PlanInfo]


class PlanUsageResponse(BaseModel):
    """현재 워크스페이스의 사용량 통계."""

    plan: str = Field(..., description="현재 요금제")
    pipelines_used: int = Field(..., description="이번 달 파이프라인 사용 수")
    pipelines_limit: int = Field(..., description="월간 파이프라인 한도 (-1: 무제한)")
    channels_used: int = Field(..., description="현재 채널 수")
    channels_limit: int = Field(..., description="최대 채널 한도 (-1: 무제한)")
    features: dict[str, bool] = Field(
        default_factory=dict, description="기능별 사용 가능 여부"
    )


# ============================================
# 엔드포인트
# ============================================


@router.get("", response_model=PlanListResponse)
async def list_plans() -> PlanListResponse:
    """모든 요금제 목록과 한도를 반환합니다."""
    plans = [
        PlanInfo(
            name=name,
            quotas=PlanQuota(**quotas),
        )
        for name, quotas in PLAN_QUOTAS.items()
    ]
    return PlanListResponse(plans=plans)


@router.get("/usage", response_model=PlanUsageResponse)
async def get_plan_usage(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> PlanUsageResponse:
    """현재 워크스페이스의 요금제 사용량을 반환합니다."""
    if auth.workspace_id is None:
        raise HTTPException(status_code=404, detail="워크스페이스가 없습니다.")

    ws_repo = WorkspaceRepository(session)
    workspace = await ws_repo.get(auth.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="워크스페이스를 찾을 수 없습니다.")

    plan = PLAN_QUOTAS.get(workspace.plan, PLAN_QUOTAS["free"])

    # 이번 달 파이프라인 사용량
    run_repo = RunRepository(session)
    pipelines_used = await run_repo.count_monthly(workspace.id)

    # 채널 수는 ChannelRegistry에서 가져오는 대신
    # 워크스페이스의 채널 한도 정보를 요금제에서 가져옴
    # (실제 채널 수는 파일시스템 기반이므로 0으로 대체, 프론트엔드에서 채널 API 호출로 보완)
    channels_used = 0
    try:
        from yaa_app.api.dependencies import get_channel_registry

        registry = get_channel_registry()
        channels_used = len(registry.list_channels())
    except Exception:
        logger.debug("채널 수 조회 실패, 0으로 설정")

    features: dict[str, bool] = {
        "media_generation": plan["media_generation"],
        "youtube_upload": plan["youtube_upload"],
        "priority_queue": plan["priority_queue"],
        "api_access": plan["api_access"],
    }

    return PlanUsageResponse(
        plan=workspace.plan,
        pipelines_used=pipelines_used,
        pipelines_limit=plan["monthly_pipelines"],
        channels_used=channels_used,
        channels_limit=plan["max_channels"],
        features=features,
    )
