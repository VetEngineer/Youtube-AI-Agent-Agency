"""LLM 사용량 API 엔드포인트."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from yaa_core.database.engine import get_db_session
from yaa_core.database.repositories import UsageRepository

from yaa_app.api.auth import require_api_key
from yaa_app.api.schemas import UsageEventResponse, UsageListResponse, UsageSummaryResponse

router = APIRouter()


@router.get("/events", response_model=UsageListResponse)
async def list_usage_events(
    run_id: str | None = Query(None, description="파이프라인 실행 ID 필터"),
    agent: str | None = Query(None, description="에이전트명 필터"),
    provider: str | None = Query(None, description="프로바이더 필터 (openai, anthropic)"),
    date_from: datetime | None = Query(None, description="시작 일시 (ISO 8601)"),
    date_to: datetime | None = Query(None, description="종료 일시 (ISO 8601)"),
    limit: int = Query(20, ge=1, le=100, description="페이지 크기"),
    offset: int = Query(0, ge=0, description="오프셋"),
    session: AsyncSession = Depends(get_db_session),
    _api_key_id: str | None = Depends(require_api_key),
) -> UsageListResponse:
    """사용량 이벤트 목록을 조회합니다."""
    repo = UsageRepository(session)

    events = await repo.list_with_filters(
        run_id=run_id,
        agent=agent,
        provider=provider,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    total = await repo.count_with_filters(
        run_id=run_id,
        agent=agent,
        provider=provider,
        date_from=date_from,
        date_to=date_to,
    )

    return UsageListResponse(
        events=[
            UsageEventResponse(
                id=e.id,
                run_id=e.run_id,
                agent=e.agent,
                provider=e.provider,
                model=e.model,
                prompt_tokens=e.prompt_tokens,
                completion_tokens=e.completion_tokens,
                total_tokens=e.total_tokens,
                cost_usd=e.cost_usd,
                created_at=e.created_at.isoformat() if e.created_at else None,
            )
            for e in events
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    run_id: str | None = Query(None, description="파이프라인 실행 ID 필터"),
    date_from: datetime | None = Query(None, description="시작 일시 (ISO 8601)"),
    date_to: datetime | None = Query(None, description="종료 일시 (ISO 8601)"),
    session: AsyncSession = Depends(get_db_session),
    _api_key_id: str | None = Depends(require_api_key),
) -> UsageSummaryResponse:
    """사용량 집계 통계를 반환합니다."""
    repo = UsageRepository(session)
    summary = await repo.get_summary(
        run_id=run_id,
        date_from=date_from,
        date_to=date_to,
    )

    return UsageSummaryResponse(
        total_cost_usd=summary["total_cost_usd"],
        total_tokens=summary["total_tokens"],
        by_agent=summary["by_agent"],
        by_provider=summary["by_provider"],
        by_model=summary["by_model"],
    )
