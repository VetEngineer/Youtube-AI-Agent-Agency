"""상태 조회 API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.routes.pipeline import get_run_storage
from src.api.schemas import PipelineStatusResponse

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """헬스체크 엔드포인트."""
    return {"status": "healthy"}


@router.get("/status/{run_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(run_id: str) -> PipelineStatusResponse:
    """파이프라인 실행 상태를 조회합니다."""
    storage = get_run_storage()

    if run_id not in storage:
        raise HTTPException(status_code=404, detail=f"실행을 찾을 수 없습니다: {run_id}")

    run_data = storage[run_id]
    return PipelineStatusResponse(
        run_id=run_id,
        status=run_data["status"],
        current_agent=run_data.get("current_agent"),
        errors=run_data.get("errors", []),
        result=run_data.get("result"),
    )
