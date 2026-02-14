"""Arq 작업 정의 및 워커 진입점."""

from __future__ import annotations

import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


async def _save_usage_events(
    session_factory: Any,
    collector: Any,
    run_id: str,
) -> None:
    """수집된 LLM 사용량 이벤트를 DB에 저장합니다."""
    if not collector.events:
        return

    try:
        from yaa_core.database.repositories import UsageRepository

        async with session_factory() as session:
            usage_repo = UsageRepository(session)
            for event in collector.events:
                await usage_repo.create(
                    event_id=str(uuid.uuid4()),
                    run_id=run_id,
                    **event,
                )
            await session.commit()
        logger.info(
            "사용량 이벤트 저장: run_id=%s, count=%d", run_id, len(collector.events)
        )
    except Exception:
        logger.exception("사용량 이벤트 저장 실패: run_id=%s", run_id)


async def execute_pipeline_task(
    ctx: dict[str, Any],
    run_id: str,
    channel_id: str,
    topic: str,
    brand_name: str,
    dry_run: bool,
) -> dict[str, Any]:
    """큐에서 파이프라인을 실행하는 Arq 작업.

    Args:
        ctx: Arq 컨텍스트 (startup에서 주입한 의존성 포함)
        run_id: 파이프라인 실행 ID
        channel_id: 채널 ID
        topic: 콘텐츠 주제
        brand_name: 브랜드명
        dry_run: 실제 업로드 건너뜀 여부

    Returns:
        실행 결과 딕셔너리
    """
    from yaa_agents.orchestrator import compile_pipeline, create_initial_state
    from yaa_core.database.engine import get_session_factory
    from yaa_core.database.repositories import RunRepository
    from yaa_core.shared.config import AppSettings
    from yaa_core.shared.llm_clients import UsageCollector

    from yaa_app.cli import _build_agent_registry

    logger.info("파이프라인 작업 시작: run_id=%s, channel=%s", run_id, channel_id)

    session_factory = get_session_factory()
    if session_factory is None:
        logger.error("DB 세션 팩토리가 없습니다: run_id=%s", run_id)
        return {"status": "error", "message": "DB 세션 팩토리 없음"}

    # running 상태로 업데이트
    async with session_factory() as session:
        repo = RunRepository(session)
        await repo.update_status(run_id, status="running")
        await session.commit()

    collector = UsageCollector()

    try:
        settings = AppSettings()
        channel_registry = ctx.get("channel_registry")
        if channel_registry is None:
            from yaa_core.shared.config import ChannelRegistry

            channel_registry = ChannelRegistry(settings.channels_dir)

        agent_registry = _build_agent_registry(settings, collector=collector)
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
            await repo.update_status(run_id, status="completed", result=result)
            await session.commit()

        logger.info("파이프라인 완료: run_id=%s", run_id)
        return {"status": "completed", "run_id": run_id}

    except Exception as exc:
        logger.exception("파이프라인 실패: run_id=%s", run_id)
        async with session_factory() as session:
            repo = RunRepository(session)
            await repo.update_status(run_id, status="failed", errors=[str(exc)])
            await session.commit()
        return {"status": "failed", "run_id": run_id, "error": str(exc)}

    finally:
        await _save_usage_events(session_factory, collector, run_id)


async def startup(ctx: dict[str, Any]) -> None:
    """워커 시작 시 리소스를 초기화합니다."""
    from yaa_core.database.engine import init_db
    from yaa_core.shared.config import AppSettings, ChannelRegistry

    settings = AppSettings()
    await init_db(settings.database_url)

    ctx["channel_registry"] = ChannelRegistry(settings.channels_dir)
    logger.info("워커 초기화 완료")


async def shutdown(ctx: dict[str, Any]) -> None:
    """워커 종료 시 리소스를 정리합니다."""
    logger.info("워커 종료")


class WorkerConfig:
    """Arq 워커 설정 클래스.

    arq CLI에서 `arq src.worker.tasks.WorkerConfig` 으로 실행합니다.
    """

    from yaa_app.worker.config import get_worker_settings

    _settings = get_worker_settings()

    functions = [execute_pipeline_task]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = _settings.redis_settings
    max_jobs = _settings.worker_max_jobs
    job_timeout = _settings.worker_job_timeout
    queue_name = _settings.worker_queue_name
