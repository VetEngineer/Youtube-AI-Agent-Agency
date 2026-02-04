"""파이프라인 실행 API."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends

from src.api.dependencies import get_channel_registry, get_settings
from src.api.schemas import PipelineRunRequest, PipelineRunResponse
from src.shared.config import AppSettings, ChannelRegistry

router = APIRouter()
logger = logging.getLogger(__name__)

# 실행 상태 저장소 (프로덕션에서는 Redis 등으로 교체)
_run_storage: dict[str, dict[str, Any]] = {}


def get_run_storage() -> dict[str, dict[str, Any]]:
    """실행 상태 저장소를 반환합니다."""
    return _run_storage


async def _execute_pipeline(
    run_id: str,
    channel_id: str,
    topic: str,
    brand_name: str,
    dry_run: bool,
    settings: AppSettings,
    channel_registry: ChannelRegistry,
) -> None:
    """백그라운드에서 파이프라인을 실행합니다."""
    from src.cli import _build_agent_registry
    from src.orchestrator import compile_pipeline, create_initial_state

    logger.info("파이프라인 시작: run_id=%s, channel=%s", run_id, channel_id)
    _run_storage[run_id]["status"] = "running"

    try:
        agent_registry = _build_agent_registry(settings)
        pipeline = compile_pipeline(agent_registry)
        initial_state = create_initial_state(
            channel_id=channel_id,
            topic=topic,
            brand_name=brand_name,
            dry_run=dry_run,
        )

        final_state = await pipeline.ainvoke(initial_state)

        _run_storage[run_id].update(
            {
                "status": "completed",
                "result": {
                    "content_status": str(final_state.get("status", "")),
                    "errors": final_state.get("errors", []),
                },
            }
        )
        logger.info("파이프라인 완료: run_id=%s", run_id)

    except Exception as exc:
        logger.exception("파이프라인 실패: run_id=%s", run_id)
        _run_storage[run_id].update(
            {
                "status": "failed",
                "errors": [str(exc)],
            }
        )


@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    settings: AppSettings = Depends(get_settings),
    channel_registry: ChannelRegistry = Depends(get_channel_registry),
) -> PipelineRunResponse:
    """파이프라인을 백그라운드에서 실행합니다."""
    run_id = str(uuid.uuid4())

    _run_storage[run_id] = {
        "run_id": run_id,
        "channel_id": request.channel_id,
        "topic": request.topic,
        "status": "pending",
        "current_agent": None,
        "errors": [],
    }

    background_tasks.add_task(
        _execute_pipeline,
        run_id=run_id,
        channel_id=request.channel_id,
        topic=request.topic,
        brand_name=request.brand_name,
        dry_run=request.dry_run,
        settings=settings,
        channel_registry=channel_registry,
    )

    return PipelineRunResponse(
        run_id=run_id,
        status="pending",
        channel_id=request.channel_id,
        topic=request.topic,
    )
