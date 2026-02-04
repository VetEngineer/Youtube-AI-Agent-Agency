"""상태 조회 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import require_api_key
from src.api.schemas import PipelineStatusResponse
from src.database.engine import get_db_session
from src.database.repositories import RunRepository

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """헬스체크 엔드포인트."""
    return {"status": "healthy"}


@router.get("/status/{run_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    run_id: str,
    session: AsyncSession = Depends(get_db_session),
    _api_key_id: str | None = Depends(require_api_key),
) -> PipelineStatusResponse:
    """파이프라인 실행 상태를 조회합니다."""
    repo = RunRepository(session)
    run = await repo.get(run_id)

    if run is None:
        raise HTTPException(status_code=404, detail=f"실행을 찾을 수 없습니다: {run_id}")

    return PipelineStatusResponse(
        run_id=run_id,
        status=run.status,
        current_agent=run.current_agent,
        errors=run.errors,
        result=run.result,
    )
