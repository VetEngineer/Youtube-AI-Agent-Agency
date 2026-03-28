"""워크스페이스 통합 설정 API."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from yaa_core.database.engine import get_db_session
from yaa_core.database.repositories import WorkspaceRepository

from yaa_app.api.auth import require_api_key

router = APIRouter()
logger = logging.getLogger(__name__)


class IntegrationsResponse(BaseModel):
    """통합 설정 조회 응답."""

    youtube_api_key_set: bool
    youtube_api_key_masked: str | None  # "AIza...XXXX" 형식으로 마스킹


class UpdateIntegrationsRequest(BaseModel):
    """통합 설정 업데이트 요청."""

    youtube_api_key: str | None = None  # None이면 기존 값 유지, "" 빈문자열이면 삭제


def _mask_key(key: str) -> str:
    """API 키를 마스킹합니다 (앞 8자 + ... + 끝 4자)."""
    if len(key) <= 12:
        return key[:4] + "..." + key[-2:]
    return key[:8] + "..." + key[-4:]


@router.get("/integrations", response_model=IntegrationsResponse)
async def get_integrations(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    _api_key_id: str | None = Depends(require_api_key),
) -> IntegrationsResponse:
    """워크스페이스의 통합 설정을 조회합니다."""
    auth_ctx = getattr(request.state, "auth_context", None)
    if auth_ctx is None or auth_ctx.workspace_id is None:
        raise HTTPException(status_code=403, detail="워크스페이스 인증이 필요합니다.")

    ws_repo = WorkspaceRepository(session)
    workspace = await ws_repo.get(auth_ctx.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="워크스페이스를 찾을 수 없습니다.")

    key = workspace.youtube_api_key
    return IntegrationsResponse(
        youtube_api_key_set=bool(key),
        youtube_api_key_masked=_mask_key(key) if key else None,
    )


@router.patch("/integrations", response_model=IntegrationsResponse)
async def update_integrations(
    body: UpdateIntegrationsRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    _api_key_id: str | None = Depends(require_api_key),
) -> IntegrationsResponse:
    """워크스페이스의 통합 설정을 업데이트합니다."""
    auth_ctx = getattr(request.state, "auth_context", None)
    if auth_ctx is None or auth_ctx.workspace_id is None:
        raise HTTPException(status_code=403, detail="워크스페이스 인증이 필요합니다.")

    ws_repo = WorkspaceRepository(session)
    workspace = await ws_repo.get(auth_ctx.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="워크스페이스를 찾을 수 없습니다.")

    if body.youtube_api_key is not None:
        # 빈 문자열이면 삭제, 값이 있으면 저장
        new_key = body.youtube_api_key.strip() or None
        await ws_repo.update(auth_ctx.workspace_id, youtube_api_key=new_key)
        await session.commit()
        await session.refresh(workspace)

    key = workspace.youtube_api_key
    return IntegrationsResponse(
        youtube_api_key_set=bool(key),
        youtube_api_key_masked=_mask_key(key) if key else None,
    )
