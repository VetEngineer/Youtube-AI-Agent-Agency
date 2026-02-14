"""요금제 기반 사용량 제한 검사."""

from __future__ import annotations

import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from yaa_core.database.models import WorkspaceModel
from yaa_core.database.repositories import RunRepository
from yaa_core.shared.config import PLAN_QUOTAS

logger = logging.getLogger(__name__)


async def check_pipeline_quota(workspace: WorkspaceModel, session: AsyncSession) -> None:
    """월간 파이프라인 실행 한도를 검사합니다.

    한도 초과 시 HTTP 402 (Payment Required) 예외를 발생시킵니다.
    unlimited(-1)인 경우 검사를 건너뜁니다.
    """
    plan = PLAN_QUOTAS.get(workspace.plan, PLAN_QUOTAS["free"])
    monthly_limit = plan["monthly_pipelines"]

    # unlimited
    if monthly_limit == -1:
        return

    repo = RunRepository(session)
    used = await repo.count_monthly(workspace.id)

    if used >= monthly_limit:
        logger.warning(
            "파이프라인 한도 초과: workspace_id=%s, plan=%s, used=%d, limit=%d",
            workspace.id,
            workspace.plan,
            used,
            monthly_limit,
        )
        raise HTTPException(
            status_code=402,
            detail=(
                f"월간 파이프라인 한도를 초과했습니다 ({used}/{monthly_limit}). "
                f"요금제를 업그레이드해 주세요."
            ),
        )


def check_feature_access(workspace: WorkspaceModel, feature: str) -> None:
    """요금제에서 특정 기능의 사용 가능 여부를 검사합니다.

    허용되지 않은 기능 접근 시 HTTP 403 (Forbidden) 예외를 발생시킵니다.

    Args:
        workspace: 워크스페이스 모델
        feature: 기능 키 (media_generation, youtube_upload, priority_queue, api_access)
    """
    plan = PLAN_QUOTAS.get(workspace.plan, PLAN_QUOTAS["free"])

    if feature not in plan:
        raise HTTPException(
            status_code=400,
            detail=f"알 수 없는 기능입니다: {feature}",
        )

    if not plan[feature]:
        logger.warning(
            "기능 접근 거부: workspace_id=%s, plan=%s, feature=%s",
            workspace.id,
            workspace.plan,
            feature,
        )
        raise HTTPException(
            status_code=403,
            detail=(
                f"현재 요금제({workspace.plan})에서는 {feature} 기능을 사용할 수 없습니다. "
                f"요금제를 업그레이드해 주세요."
            ),
        )
