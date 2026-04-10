"""사용자 인증 API 엔드포인트."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from yaa_core.database.engine import get_db_session
from yaa_core.database.repositories import UserRepository, WorkspaceRepository
from yaa_core.shared.config import AppSettings

from yaa_app.api.auth import AuthContext, get_auth_context
from yaa_app.api.dependencies import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)


class OAuthLoginRequest(BaseModel):
    """OAuth 로그인/회원가입 요청."""

    email: str = Field(..., description="사용자 이메일")
    name: str | None = Field(None, description="사용자 이름")
    image: str | None = Field(None, description="프로필 이미지 URL")
    provider: str = Field(..., description="OAuth 프로바이더 (google, github)")
    provider_account_id: str | None = Field(None, description="프로바이더 계정 ID")


class UserResponse(BaseModel):
    """사용자 정보 응답."""

    id: str
    email: str
    name: str | None = None
    image: str | None = None
    provider: str
    plan: str
    is_active: bool
    is_admin: bool = False
    workspace_id: str | None = None


class WorkspaceResponse(BaseModel):
    """워크스페이스 정보 응답."""

    id: str
    name: str
    owner_id: str
    plan: str
    pipeline_quota: int
    channel_quota: int


def _verify_internal_secret(
    settings: AppSettings,
    x_internal_secret: str | None,
) -> None:
    """내부 API 시크릿을 검증합니다."""
    if settings.disable_auth:
        return
    if not settings.internal_api_secret:
        raise HTTPException(
            status_code=500,
            detail="INTERNAL_API_SECRET이 설정되지 않았습니다.",
        )
    if not x_internal_secret or x_internal_secret != settings.internal_api_secret:
        raise HTTPException(status_code=403, detail="내부 API 접근 권한이 없습니다.")


@router.post("/oauth/callback", response_model=UserResponse)
async def oauth_callback(
    request: OAuthLoginRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
    x_internal_secret: str | None = Header(None),
) -> UserResponse:
    """OAuth 로그인 콜백 - 사용자 생성 또는 조회.

    NextAuth.js에서 JWT 발급 전 사용자 DB 동기화에 사용합니다.
    INTERNAL_API_SECRET 헤더가 필요합니다.
    """
    _verify_internal_secret(settings, x_internal_secret)

    user_repo = UserRepository(session)
    ws_repo = WorkspaceRepository(session)

    # 관리자 이메일 목록 파싱
    admin_emails: set[str] = set()
    if settings.admin_emails:
        admin_emails = {e.strip().lower() for e in settings.admin_emails.split(",") if e.strip()}

    user, created = await user_repo.get_or_create_by_oauth(
        email=request.email,
        name=request.name,
        image=request.image,
        provider=request.provider,
        provider_account_id=request.provider_account_id,
    )

    # 관리자 이메일이면 is_admin=True 동기화
    should_be_admin = request.email.lower() in admin_emails
    if user.is_admin != should_be_admin:
        await user_repo.update(user.id, is_admin=should_be_admin)
        user.is_admin = should_be_admin
        logger.info("관리자 권한 업데이트: email=%s, is_admin=%s", user.email, should_be_admin)

    workspace_id: str | None = None
    if created:
        ws_id = str(uuid.uuid4())
        await ws_repo.create(
            workspace_id=ws_id,
            name=f"{user.name or user.email}의 워크스페이스",
            owner_id=user.id,
        )
        workspace_id = ws_id
        await session.commit()
        logger.info("새 사용자 생성: email=%s, workspace_id=%s", user.email, ws_id)
    else:
        workspaces = await ws_repo.list_by_owner(user.id)
        workspace_id = workspaces[0].id if workspaces else None

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        image=user.image,
        provider=user.provider,
        plan=user.plan,
        is_active=user.is_active,
        is_admin=user.is_admin,
        workspace_id=workspace_id,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """현재 인증된 사용자 정보를 반환합니다."""
    if auth.user_id is None:
        raise HTTPException(status_code=401, detail="사용자 인증이 필요합니다.")

    user_repo = UserRepository(session)
    user = await user_repo.get(auth.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        image=user.image,
        provider=user.provider,
        plan=user.plan,
        is_active=user.is_active,
        is_admin=user.is_admin,
        workspace_id=auth.workspace_id,
    )


@router.get("/me/workspace", response_model=WorkspaceResponse)
async def get_current_workspace(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> WorkspaceResponse:
    """현재 인증된 사용자의 워크스페이스 정보를 반환합니다."""
    if auth.workspace_id is None:
        raise HTTPException(status_code=404, detail="워크스페이스가 없습니다.")

    ws_repo = WorkspaceRepository(session)
    workspace = await ws_repo.get(auth.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="워크스페이스를 찾을 수 없습니다.")

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        owner_id=workspace.owner_id,
        plan=workspace.plan,
        pipeline_quota=workspace.pipeline_quota,
        channel_quota=workspace.channel_quota,
    )
