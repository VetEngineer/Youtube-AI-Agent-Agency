"""파이프라인 실행 API."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from yaa_core.database.engine import get_db_session, get_session_factory
from yaa_core.database.repositories import RunRepository, UsageRepository, WorkspaceRepository
from yaa_core.shared.config import AppSettings, ChannelRegistry
from yaa_core.shared.llm_clients import UsageCollector

from yaa_app.api.auth import AuthContext, get_auth_context
from yaa_app.api.dependencies import get_channel_registry, get_settings
from yaa_app.api.quota import check_pipeline_quota
from yaa_app.api.schemas import (
    PipelineRunDetail,
    PipelineRunListResponse,
    PipelineRunRequest,
    PipelineRunResponse,
    PipelineRunSummary,
)

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
    workspace_id: str | None = None,
) -> None:
    """백그라운드에서 파이프라인을 실행합니다 (Redis 미사용 시 폴백)."""
    from yaa_agents.orchestrator import compile_pipeline, create_initial_state

    from yaa_app.cli import _build_agent_registry

    logger.info("파이프라인 시작 (BackgroundTask 폴백): run_id=%s, channel=%s", run_id, channel_id)

    session_factory = get_session_factory()
    if session_factory is None:
        logger.error("DB 세션 팩토리가 없습니다: run_id=%s", run_id)
        return

    # 워크스페이스별 채널 격리 + ElevenLabs 키 로드
    workspace_elevenlabs_key: str | None = None
    if workspace_id:
        channel_registry = channel_registry.for_workspace(workspace_id)
        async with session_factory() as session:
            ws_repo = WorkspaceRepository(session)
            workspace = await ws_repo.get(workspace_id)
            if workspace and workspace.elevenlabs_api_key:
                workspace_elevenlabs_key = workspace.elevenlabs_api_key

    async with session_factory() as session:
        repo = RunRepository(session)
        await repo.update_status(run_id, status="running")
        await session.commit()

    collector = UsageCollector()

    try:
        agent_registry = _build_agent_registry(
            settings, collector=collector, elevenlabs_api_key=workspace_elevenlabs_key,
        )
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

    # 수집된 사용량 이벤트를 DB에 저장 (성공/실패 무관)
    if collector.events:
        try:
            async with session_factory() as session:
                usage_repo = UsageRepository(session)
                for event in collector.events:
                    await usage_repo.create(
                        event_id=str(uuid.uuid4()),
                        run_id=run_id,
                        **event,
                    )
                await session.commit()
            logger.info("사용량 이벤트 저장: run_id=%s, count=%d", run_id, len(collector.events))
        except Exception:
            logger.exception("사용량 이벤트 저장 실패: run_id=%s", run_id)


@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    settings: AppSettings = Depends(get_settings),
    channel_registry: ChannelRegistry = Depends(get_channel_registry),
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> PipelineRunResponse:
    """파이프라인을 실행합니다.

    Redis가 사용 가능하면 Arq 큐를 통해 워커에서 실행하고,
    Redis가 없으면 FastAPI BackgroundTasks로 폴백합니다.
    """
    # 요금제 파이프라인 한도 검사 (인증 활성 시 workspace 필수)
    if auth.workspace_id:
        ws_repo = WorkspaceRepository(session)
        workspace = await ws_repo.get(auth.workspace_id)
        if workspace:
            await check_pipeline_quota(workspace, session)
    elif auth.auth_method != "none":
        raise HTTPException(
            status_code=400, detail="파이프라인 실행에는 워크스페이스가 필요합니다."
        )

    run_id = str(uuid.uuid4())

    repo = RunRepository(session)
    await repo.create(
        run_id=run_id,
        channel_id=request.channel_id,
        topic=request.topic,
        brand_name=request.brand_name,
        dry_run=request.dry_run,
        workspace_id=auth.workspace_id,
    )

    # Redis 큐로 enqueue 시도
    enqueued = False
    try:
        from yaa_app.worker.enqueue import enqueue_pipeline

        enqueued = await enqueue_pipeline(
            run_id=run_id,
            channel_id=request.channel_id,
            topic=request.topic,
            brand_name=request.brand_name,
            dry_run=request.dry_run,
            workspace_id=auth.workspace_id,
        )
    except ImportError:
        logger.debug("arq 패키지 미설치 — BackgroundTasks 폴백")

    # 큐 등록 실패 시 BackgroundTasks 폴백
    if not enqueued:
        background_tasks.add_task(
            _execute_pipeline,
            run_id=run_id,
            channel_id=request.channel_id,
            topic=request.topic,
            brand_name=request.brand_name,
            dry_run=request.dry_run,
            settings=settings,
            channel_registry=channel_registry,
            workspace_id=auth.workspace_id,
        )

    return PipelineRunResponse(
        run_id=run_id,
        status="pending",
        channel_id=request.channel_id,
        topic=request.topic,
    )


@router.get("/runs", response_model=PipelineRunListResponse)
async def list_pipeline_runs(
    channel_id: str | None = Query(None, description="채널 ID 필터"),
    status: str | None = Query(None, description="상태 필터 (pending, running, completed, failed)"),
    limit: int = Query(20, ge=1, le=100, description="페이지 크기"),
    offset: int = Query(0, ge=0, description="오프셋"),
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> PipelineRunListResponse:
    """파이프라인 실행 이력을 조회합니다."""
    repo = RunRepository(session)

    runs = await repo.list_with_filters(
        channel_id=channel_id,
        status=status,
        limit=limit,
        offset=offset,
        workspace_id=auth.workspace_id,
    )
    total = await repo.count_with_filters(
        channel_id=channel_id,
        status=status,
        workspace_id=auth.workspace_id,
    )

    return PipelineRunListResponse(
        runs=[
            PipelineRunSummary(
                run_id=r.id,
                channel_id=r.channel_id,
                topic=r.topic,
                status=r.status,
                dry_run=r.dry_run,
                created_at=r.created_at.isoformat() if r.created_at else None,
                completed_at=r.completed_at.isoformat() if r.completed_at else None,
            )
            for r in runs
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/runs/{run_id}", response_model=PipelineRunDetail)
async def get_pipeline_run(
    run_id: str,
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> PipelineRunDetail:
    """특정 파이프라인 실행의 상세 정보를 조회합니다."""
    repo = RunRepository(session)
    run = await repo.get(run_id)

    if run is None:
        raise HTTPException(status_code=404, detail="파이프라인 실행을 찾을 수 없습니다")

    # workspace 격리: 자기 workspace의 run만 접근 가능
    if run.workspace_id != auth.workspace_id:
        raise HTTPException(status_code=404, detail="파이프라인 실행을 찾을 수 없습니다")

    usage_repo = UsageRepository(session)
    cost_usd = await usage_repo.get_run_cost(run_id)

    return PipelineRunDetail(
        run_id=run.id,
        channel_id=run.channel_id,
        topic=run.topic,
        brand_name=run.brand_name,
        status=run.status,
        current_agent=run.current_agent,
        dry_run=run.dry_run,
        created_at=run.created_at.isoformat() if run.created_at else None,
        updated_at=run.updated_at.isoformat() if run.updated_at else None,
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
        result=run.result,
        errors=run.errors or [],
        cost_usd=cost_usd if cost_usd > 0 else None,
    )


@router.post("/runs/{run_id}/cancel")
async def cancel_pipeline_run(
    run_id: str,
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, str]:
    """파이프라인 실행을 취소합니다."""
    repo = RunRepository(session)
    run = await repo.get(run_id)

    if run is None:
        raise HTTPException(status_code=404, detail="파이프라인 실행을 찾을 수 없습니다")

    if run.workspace_id != auth.workspace_id:
        raise HTTPException(status_code=404, detail="파이프라인 실행을 찾을 수 없습니다")

    if run.status not in {"pending", "running"}:
        raise HTTPException(status_code=400, detail=f"취소할 수 없는 상태입니다: {run.status}")

    await repo.update_status(run_id, status="cancelled")

    return {"run_id": run_id, "status": "cancelled"}


@router.get("/runs/{run_id}/stream")
async def stream_pipeline_run(
    run_id: str,
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> StreamingResponse:
    """파이프라인 실행 상태를 SSE로 스트리밍합니다."""
    repo = RunRepository(session)
    run = await repo.get(run_id)

    if run is None:
        raise HTTPException(status_code=404, detail="파이프라인 실행을 찾을 수 없습니다")

    if run.workspace_id != auth.workspace_id:
        raise HTTPException(status_code=404, detail="파이프라인 실행을 찾을 수 없습니다")

    async def event_generator() -> AsyncGenerator[str, None]:
        session_factory = get_session_factory()
        if session_factory is None:
            return

        terminal_statuses = {"completed", "failed", "cancelled"}
        max_duration_seconds = 35 * 60  # 35분
        elapsed = 0

        while elapsed < max_duration_seconds:
            async with session_factory() as poll_session:
                poll_repo = RunRepository(poll_session)
                current_run = await poll_repo.get(run_id)

            if current_run is None:
                break

            data = {
                "run_id": current_run.id,
                "status": current_run.status,
                "current_agent": current_run.current_agent,
                "errors": current_run.errors,
            }
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            if current_run.status in terminal_statuses:
                break

            await asyncio.sleep(2)
            elapsed += 2

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/runs/{run_id}/retry", response_model=PipelineRunResponse)
async def retry_pipeline_run(
    run_id: str,
    background_tasks: BackgroundTasks,
    settings: AppSettings = Depends(get_settings),
    channel_registry: ChannelRegistry = Depends(get_channel_registry),
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> PipelineRunResponse:
    """실패하거나 취소된 파이프라인 실행을 동일한 파라미터로 재실행합니다."""
    repo = RunRepository(session)
    original_run = await repo.get(run_id)

    if original_run is None:
        raise HTTPException(status_code=404, detail="파이프라인 실행을 찾을 수 없습니다")

    if original_run.workspace_id and original_run.workspace_id != auth.workspace_id:
        raise HTTPException(status_code=404, detail="파이프라인 실행을 찾을 수 없습니다")

    if original_run.status not in {"failed", "cancelled"}:
        raise HTTPException(
            status_code=400, detail=f"재실행할 수 없는 상태입니다: {original_run.status}"
        )

    # 요금제 파이프라인 한도 검사 (재실행도 새 실행으로 카운트)
    if auth.workspace_id:
        ws_repo = WorkspaceRepository(session)
        workspace = await ws_repo.get(auth.workspace_id)
        if workspace:
            await check_pipeline_quota(workspace, session)
    elif auth.auth_method != "none":
        raise HTTPException(
            status_code=400, detail="파이프라인 실행에는 워크스페이스가 필요합니다."
        )

    new_run_id = str(uuid.uuid4())
    await repo.create(
        run_id=new_run_id,
        channel_id=original_run.channel_id,
        topic=original_run.topic,
        brand_name=original_run.brand_name,
        dry_run=original_run.dry_run,
        workspace_id=original_run.workspace_id,
    )

    enqueued = False
    try:
        from yaa_app.worker.enqueue import enqueue_pipeline

        enqueued = await enqueue_pipeline(
            run_id=new_run_id,
            channel_id=original_run.channel_id,
            topic=original_run.topic,
            brand_name=original_run.brand_name,
            dry_run=original_run.dry_run,
            workspace_id=original_run.workspace_id,
        )
    except ImportError:
        logger.debug("arq 패키지 미설치 — BackgroundTasks 폴백")

    if not enqueued:
        background_tasks.add_task(
            _execute_pipeline,
            run_id=new_run_id,
            channel_id=original_run.channel_id,
            topic=original_run.topic,
            brand_name=original_run.brand_name,
            dry_run=original_run.dry_run,
            settings=settings,
            channel_registry=channel_registry,
            workspace_id=original_run.workspace_id,
        )

    return PipelineRunResponse(
        run_id=new_run_id,
        status="pending",
        channel_id=original_run.channel_id,
        topic=original_run.topic,
    )
