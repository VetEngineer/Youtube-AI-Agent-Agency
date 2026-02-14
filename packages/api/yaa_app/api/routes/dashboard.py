"""대시보드 API 엔드포인트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from yaa_core.database.engine import get_db_session
from yaa_core.database.repositories import RunRepository, UsageRepository

from yaa_app.api.auth import AuthContext, get_auth_context
from yaa_app.api.schemas import DashboardSummary, PipelineRunSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    limit: int = 5,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> DashboardSummary:
    """대시보드 요약 통계를 반환합니다.

    인증된 사용자의 workspace 범위로 필터링합니다.
    """
    repo = RunRepository(session)
    usage_repo = UsageRepository(session)
    ws_id = auth.workspace_id

    stats = await repo.get_stats(workspace_id=ws_id)
    avg_duration = await repo.get_avg_duration(workspace_id=ws_id)
    total_cost = await usage_repo.get_total_cost(workspace_id=ws_id)
    recent = await repo.list_recent(limit=limit, workspace_id=ws_id)

    recent_runs = [
        PipelineRunSummary(
            run_id=run.id,
            channel_id=run.channel_id,
            topic=run.topic,
            status=run.status,
            dry_run=run.dry_run,
            created_at=run.created_at.isoformat() if run.created_at else None,
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
        )
        for run in recent
    ]

    return DashboardSummary(
        total_runs=stats["total"],
        active_runs=stats["pending"] + stats["running"],
        success_runs=stats["completed"],
        failed_runs=stats["failed"],
        avg_duration_sec=avg_duration,
        estimated_cost_usd=total_cost if total_cost > 0 else None,
        recent_runs=recent_runs,
    )
