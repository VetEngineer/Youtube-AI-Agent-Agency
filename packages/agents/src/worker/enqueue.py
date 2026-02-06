"""큐 작업 enqueue 헬퍼."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_arq_pool = None


async def get_arq_pool():
    """Arq Redis 커넥션 풀을 반환합니다 (lazy singleton)."""
    global _arq_pool
    if _arq_pool is not None:
        return _arq_pool

    try:
        from arq import create_pool

        from src.worker.config import get_worker_settings

        settings = get_worker_settings()
        _arq_pool = await create_pool(settings.redis_settings)
        logger.info("Arq Redis 풀 생성 완료")
        return _arq_pool
    except Exception:
        logger.debug("Redis 연결 실패 — BackgroundTasks 폴백 사용")
        return None


async def close_arq_pool() -> None:
    """Arq Redis 풀을 종료합니다."""
    global _arq_pool
    if _arq_pool is not None:
        _arq_pool.close()
        await _arq_pool.wait_closed()
        _arq_pool = None
        logger.info("Arq Redis 풀 종료")


async def enqueue_pipeline(
    run_id: str,
    channel_id: str,
    topic: str,
    brand_name: str,
    dry_run: bool,
) -> bool:
    """파이프라인 실행을 큐에 등록합니다.

    Returns:
        True: 큐에 성공적으로 등록됨
        False: Redis 미사용 또는 연결 실패 (폴백 필요)
    """
    pool = await get_arq_pool()
    if pool is None:
        return False

    try:
        from src.worker.config import get_worker_settings

        settings = get_worker_settings()
        await pool.enqueue_job(
            "execute_pipeline_task",
            run_id=run_id,
            channel_id=channel_id,
            topic=topic,
            brand_name=brand_name,
            dry_run=dry_run,
            _queue_name=settings.worker_queue_name,
        )
        logger.info("파이프라인 큐 등록: run_id=%s", run_id)
        return True
    except Exception:
        logger.warning("큐 등록 실패, 폴백 필요: run_id=%s", run_id, exc_info=True)
        return False
