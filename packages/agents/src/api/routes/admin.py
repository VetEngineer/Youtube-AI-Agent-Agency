"""관리자 API 엔드포인트 - API 키 관리 및 감사 로그 조회."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import create_api_key, require_admin_scope
from src.api.schemas import (
    ApiKeyInfo,
    ApiKeyListResponse,
    AuditLogEntry,
    AuditLogListResponse,
    CreateApiKeyRequest,
    CreateApiKeyResponse,
)
from src.database.engine import get_db_session
from src.database.repositories import ApiKeyRepository, AuditLogRepository

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# API 키 관리
# ============================================


@router.post("/api-keys", response_model=CreateApiKeyResponse, status_code=201)
async def create_key(
    request_body: CreateApiKeyRequest,
    session: AsyncSession = Depends(get_db_session),
    _admin_key_id: str | None = Depends(require_admin_scope),
) -> CreateApiKeyResponse:
    """새 API 키를 생성합니다.

    생성된 평문 키는 이 응답에서만 확인 가능합니다.
    """
    plaintext_key, key_id = await create_api_key(
        session=session,
        name=request_body.name,
        scopes=request_body.scopes,
    )

    repo = ApiKeyRepository(session)
    api_key = await repo.get_by_id(key_id)

    expires_at = None
    if request_body.expires_days is not None and api_key is not None:
        expires_at_dt = datetime.now(UTC) + timedelta(days=request_body.expires_days)
        from sqlalchemy import update as sa_update

        from src.database.models import ApiKeyModel

        await session.execute(
            sa_update(ApiKeyModel).where(ApiKeyModel.id == key_id).values(expires_at=expires_at_dt)
        )
        await session.commit()
        expires_at = expires_at_dt.isoformat()

    return CreateApiKeyResponse(
        api_key=plaintext_key,
        key_id=key_id,
        name=request_body.name,
        scopes=request_body.scopes,
        created_at=api_key.created_at.isoformat() if api_key and api_key.created_at else None,
        expires_at=expires_at,
    )


@router.get("/api-keys", response_model=ApiKeyListResponse)
async def list_keys(
    include_inactive: bool = Query(False, description="비활성 키 포함 여부"),
    session: AsyncSession = Depends(get_db_session),
    _admin_key_id: str | None = Depends(require_admin_scope),
) -> ApiKeyListResponse:
    """등록된 API 키 목록을 조회합니다."""
    repo = ApiKeyRepository(session)
    keys = await repo.get_all(include_inactive=include_inactive)

    return ApiKeyListResponse(
        keys=[
            ApiKeyInfo(
                key_id=k.id,
                name=k.name,
                scopes=k.scopes,
                is_active=k.is_active,
                created_at=k.created_at.isoformat() if k.created_at else None,
                expires_at=k.expires_at.isoformat() if k.expires_at else None,
                last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            )
            for k in keys
        ],
        total=len(keys),
    )


@router.delete("/api-keys/{key_id}")
async def deactivate_key(
    key_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    admin_key_id: str | None = Depends(require_admin_scope),
) -> dict[str, str]:
    """API 키를 비활성화합니다."""
    repo = ApiKeyRepository(session)
    target_key = await repo.get_by_id(key_id)

    if target_key is None:
        raise HTTPException(status_code=404, detail=f"API 키를 찾을 수 없습니다: {key_id}")

    if not target_key.is_active:
        raise HTTPException(status_code=400, detail="이미 비활성화된 API 키입니다.")

    if admin_key_id is not None and admin_key_id == key_id:
        raise HTTPException(status_code=400, detail="자기 자신의 API 키는 비활성화할 수 없습니다.")

    await repo.deactivate(key_id)

    return {"message": "API 키가 비활성화되었습니다.", "key_id": key_id}


# ============================================
# 감사 로그
# ============================================


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    api_key_id: str | None = Query(None, description="특정 API 키 필터링"),
    method: str | None = Query(None, description="HTTP 메서드 필터링"),
    limit: int = Query(100, ge=1, le=1000, description="페이지 크기"),
    offset: int = Query(0, ge=0, description="오프셋"),
    session: AsyncSession = Depends(get_db_session),
    _admin_key_id: str | None = Depends(require_admin_scope),
) -> AuditLogListResponse:
    """감사 로그를 조회합니다."""
    repo = AuditLogRepository(session)

    logs = await repo.list_with_filters(
        api_key_id=api_key_id,
        method=method,
        limit=limit,
        offset=offset,
    )
    total = await repo.count_with_filters(
        api_key_id=api_key_id,
        method=method,
    )

    return AuditLogListResponse(
        logs=[
            AuditLogEntry(
                id=log.id,
                timestamp=log.timestamp.isoformat() if log.timestamp else None,
                method=log.method,
                path=log.path,
                status_code=log.status_code,
                api_key_id=log.api_key_id,
                ip_address=log.ip_address,
                duration_ms=log.duration_ms,
            )
            for log in logs
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
