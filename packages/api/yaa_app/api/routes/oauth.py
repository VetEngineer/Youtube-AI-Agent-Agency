"""OAuth 토큰 관리 API 엔드포인트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from yaa_core.database.engine import get_db_session
from yaa_core.database.repositories import OAuthTokenRepository

from yaa_app.api.auth import AuthContext, get_auth_context

router = APIRouter()


@router.get("/youtube")
async def get_youtube_token_status(
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict:
    """YouTube OAuth 연결 상태를 조회합니다."""
    if not auth.workspace_id:
        return {"connected": False, "updated_at": None}

    repo = OAuthTokenRepository(session)
    token = await repo.get_by_workspace(auth.workspace_id, provider="youtube")

    if token is None:
        return {"connected": False, "updated_at": None}

    return {
        "connected": True,
        "updated_at": token.updated_at.isoformat() if token.updated_at else None,
    }


@router.delete("/youtube", status_code=204)
async def delete_youtube_token(
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> None:
    """YouTube OAuth 토큰을 삭제합니다."""
    if not auth.workspace_id:
        return

    repo = OAuthTokenRepository(session)
    await repo.delete_by_workspace(auth.workspace_id, provider="youtube")
