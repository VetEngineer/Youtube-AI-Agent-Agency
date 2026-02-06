"""대시보드 API 엔드포인트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import require_api_key
from src.api.schemas import DashboardSummary, PipelineRunSummary
from src.database.engine import get_db_session
from src.database.repositories import RunRepository

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    limit: int = 5,
    _api_key_id: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_db_session),
) -> DashboardSummary:
    """대시보드 요약 통계를 반환합니다.

    - total_runs: 전체 파이프라인 실행 수
    - active_runs: 활성 실행 수 (pending + running)
    - success_runs: 성공한 실행 수 (completed)
    - failed_runs: 실패한 실행 수 (failed)
    - avg_duration_sec: 완료된 실행의 평균 소요시간 (초)
    - estimated_cost_usd: 예상 비용 (P8-3 전까지 null)
    - recent_runs: 최근 실행 목록 (기본 5개)
    """
    repo = RunRepository(session)

    # 통계 조회
    stats = await repo.get_stats()

    # 평균 소요시간
    avg_duration = await repo.get_avg_duration()

    # 최근 실행 목록
    recent = await repo.list_recent(limit=limit)
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
        estimated_cost_usd=None,  # P8-3에서 구현
        recent_runs=recent_runs,
    )
