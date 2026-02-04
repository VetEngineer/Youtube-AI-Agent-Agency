"""파이프라인 실행 API."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import require_api_key
from src.api.dependencies import get_channel_registry, get_settings
from src.api.schemas import PipelineRunRequest, PipelineRunResponse
from src.database.engine import get_db_session, get_session_factory
from src.database.repositories import RunRepository
from src.shared.config import AppSettings, ChannelRegistry

router = APIRouter()
logger = logging.getLogger(__name__)


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

    session_factory = get_session_factory()
    if session_factory is None:
        logger.error("DB 세션 팩토리가 없습니다: run_id=%s", run_id)
        return

    async with session_factory() as session:
        repo = RunRepository(session)
        await repo.update_status(run_id, status="running")
        await session.commit()

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

        result: dict[str, Any] = {
            "content_status": str(final_state.get("status", "")),
            "errors": final_state.get("errors", []),
        }

        async with session_factory() as session:
            repo = RunRepository(session)
            await repo.update_status(
                run_id,
                status="completed",
                result=result,
            )
            await session.commit()

        logger.info("파이프라인 완료: run_id=%s", run_id)

    except Exception as exc:
        logger.exception("파이프라인 실패: run_id=%s", run_id)
        async with session_factory() as session:
            repo = RunRepository(session)
            await repo.update_status(
                run_id,
                status="failed",
                errors=[str(exc)],
            )
            await session.commit()


@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    settings: AppSettings = Depends(get_settings),
    channel_registry: ChannelRegistry = Depends(get_channel_registry),
    session: AsyncSession = Depends(get_db_session),
    _api_key_id: str | None = Depends(require_api_key),
) -> PipelineRunResponse:
    """파이프라인을 백그라운드에서 실행합니다."""
    run_id = str(uuid.uuid4())

    repo = RunRepository(session)
    await repo.create(
        run_id=run_id,
        channel_id=request.channel_id,
        topic=request.topic,
        brand_name=request.brand_name,
        dry_run=request.dry_run,
    )

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
