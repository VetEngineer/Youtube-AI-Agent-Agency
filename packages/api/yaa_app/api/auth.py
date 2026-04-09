"""API 키 + JWT 인증 모듈."""

from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from yaa_core.database.engine import get_db_session
from yaa_core.database.models import UserModel, WorkspaceModel
from yaa_core.database.repositories import (
    ApiKeyRepository,
    UserRepository,
    WorkspaceRepository,
)
from yaa_core.shared.config import AppSettings

from yaa_app.api.dependencies import get_settings

logger = logging.getLogger(__name__)

API_KEY_PREFIX = "yaa_"
API_KEY_LENGTH = 32


@dataclass(frozen=True)
class AuthContext:
    """인증 컨텍스트 - 현재 요청의 인증 정보."""

    user_id: str | None = None
    workspace_id: str | None = None
    api_key_id: str | None = None
    scopes: tuple[str, ...] = ("read", "write")  # JWT는 기본 전체 권한
    auth_method: str = "none"  # "api_key", "jwt", "none"


def generate_api_key() -> str:
    """새 API 키를 생성합니다."""
    return f"{API_KEY_PREFIX}{secrets.token_urlsafe(API_KEY_LENGTH)}"


def hash_api_key(key: str) -> str:
    """API 키를 SHA-256으로 해싱합니다."""
    return hashlib.sha256(key.encode()).hexdigest()


def generate_key_id() -> str:
    """API 키 ID를 생성합니다."""
    return str(uuid.uuid4())


async def create_api_key(
    session: AsyncSession,
    name: str,
    scopes: list[str] | None = None,
    workspace_id: str | None = None,
) -> tuple[str, str]:
    """새 API 키를 생성하고 DB에 저장합니다.

    Returns:
        (plaintext_key, key_id) 튜플
    """
    plaintext_key = generate_api_key()
    key_id = generate_key_id()
    key_hash = hash_api_key(plaintext_key)

    repo = ApiKeyRepository(session)
    await repo.create(
        key_id=key_id,
        key_hash=key_hash,
        name=name,
        scopes=scopes,
        workspace_id=workspace_id,
    )
    await session.commit()

    return plaintext_key, key_id


def _decode_jwt(token: str, settings: AppSettings) -> dict | None:
    """JWT 토큰을 디코딩합니다."""
    if not settings.jwt_secret:
        logger.error("JWT_SECRET이 구성되지 않았지만 JWT 토큰이 제공됨")
        return None
    try:
        import jwt

        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except Exception:
        return None


async def _resolve_api_key(
    request: Request, session: AsyncSession, settings: AppSettings
) -> AuthContext:
    """요청에서 API 키를 추출하고 검증합니다."""
    header_value = request.headers.get(settings.api_key_header)
    if not header_value:
        return AuthContext()

    key_hash = hash_api_key(header_value)
    repo = ApiKeyRepository(session)
    api_key = await repo.get_by_hash(key_hash)

    if api_key is None:
        return AuthContext()

    # 만료된 키 거부 (#4)
    if api_key.expires_at is not None:
        from datetime import UTC, datetime

        if api_key.expires_at <= datetime.now(UTC):
            logger.warning("만료된 API 키 사용 시도: key_id=%s", api_key.id)
            return AuthContext()

    await repo.update_last_used(api_key.id)
    return AuthContext(
        api_key_id=api_key.id,
        workspace_id=api_key.workspace_id,
        scopes=tuple(api_key.scopes),
        auth_method="api_key",
    )


async def _resolve_jwt(
    request: Request, session: AsyncSession, settings: AppSettings
) -> AuthContext:
    """요청에서 JWT Bearer 토큰을 추출하고 검증합니다."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return AuthContext()

    token = auth_header[7:]
    payload = _decode_jwt(token, settings)
    if payload is None:
        return AuthContext()

    user_email = payload.get("email")
    user_sub = payload.get("sub")
    if not user_email and not user_sub:
        return AuthContext()

    user_repo = UserRepository(session)
    user: UserModel | None = None

    if user_email:
        user = await user_repo.get_by_email(user_email)
    if user is None and user_sub:
        user = await user_repo.get(user_sub)

    if user is None:
        return AuthContext()

    if not user.is_active:
        return AuthContext()

    # JWT에 workspace_id가 있으면 우선 사용 (멀티 워크스페이스 지원)
    jwt_workspace_id = payload.get("workspace_id")
    if jwt_workspace_id:
        workspace_repo = WorkspaceRepository(session)
        ws = await workspace_repo.get(jwt_workspace_id)
        if ws is None or ws.owner_id != user.id:
            logger.warning(
                "JWT workspace_id 소유권 불일치: user=%s ws=%s",
                user.id,
                jwt_workspace_id,
            )
            return AuthContext()
        workspace_id = jwt_workspace_id
    else:
        workspace_repo = WorkspaceRepository(session)
        workspaces = await workspace_repo.list_by_owner(user.id)
        workspace_id = workspaces[0].id if workspaces else None

    return AuthContext(
        user_id=user.id,
        workspace_id=workspace_id,
        auth_method="jwt",
    )


async def _resolve_auth(
    request: Request, session: AsyncSession, settings: AppSettings
) -> AuthContext:
    """API 키 또는 JWT로 인증을 시도합니다."""
    ctx = await _resolve_api_key(request, session, settings)
    if ctx.auth_method != "none":
        return ctx

    return await _resolve_jwt(request, session, settings)


async def require_api_key(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> str | None:
    """API 키 또는 JWT 인증을 요구하는 FastAPI 의존성.

    하위 호환을 위해 API 키 ID를 반환합니다.
    JWT 인증의 경우 None을 반환합니다.
    """
    if settings.disable_auth:
        return None

    ctx = await _resolve_auth(request, session, settings)
    if ctx.auth_method == "none":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.state.auth_context = ctx
    return ctx.api_key_id


async def get_auth_context(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> AuthContext:
    """인증 컨텍스트를 반환하는 FastAPI 의존성.

    인증 필수. workspace_id 포함.
    """
    if settings.disable_auth:
        return AuthContext(auth_method="none", workspace_id="__dev__")

    ctx = await _resolve_auth(request, session, settings)
    if ctx.auth_method == "none":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.state.auth_context = ctx
    return ctx


async def optional_api_key(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> str | None:
    """인증이 선택적인 엔드포인트용 FastAPI 의존성."""
    if settings.disable_auth:
        return None

    ctx = await _resolve_auth(request, session, settings)
    if ctx.auth_method != "none":
        request.state.auth_context = ctx
    return ctx.api_key_id


def require_scope(scope: str):
    """특정 scope를 요구하는 FastAPI 의존성 팩토리."""

    async def _dependency(
        request: Request,
        session: AsyncSession = Depends(get_db_session),
        settings: AppSettings = Depends(get_settings),
    ) -> str | None:
        if settings.disable_auth:
            return None

        ctx = await _resolve_auth(request, session, settings)
        if ctx.auth_method == "none":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 정보입니다.",
            )

        if scope not in ctx.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"'{scope}' 권한이 필요합니다.",
            )

        request.state.auth_context = ctx
        return ctx.api_key_id

    return _dependency


async def require_admin_scope(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> str | None:
    """관리자 스코프를 요구하는 FastAPI 의존성."""
    if settings.disable_auth:
        return None

    ctx = await _resolve_auth(request, session, settings)
    if ctx.auth_method == "none":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # JWT 인증 사용자는 자기 workspace에 대해 admin 권한을 가짐
    if ctx.auth_method == "jwt":
        request.state.auth_context = ctx
        return None

    # API 키 인증일 경우 admin 스코프 확인
    if ctx.api_key_id:
        repo = ApiKeyRepository(session)
        api_key = await repo.get_by_id(ctx.api_key_id)
        if api_key is None or not api_key.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API 키가 비활성화되었습니다.",
            )
        if "admin" not in api_key.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="관리자 권한이 필요합니다.",
            )

    request.state.auth_context = ctx
    return ctx.api_key_id


async def require_user(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> UserModel:
    """JWT 인증된 사용자를 반환하는 FastAPI 의존성."""
    if settings.disable_auth:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="인증이 비활성화된 상태에서는 사용자 정보를 조회할 수 없습니다.",
        )

    ctx = await _resolve_auth(request, session, settings)
    if ctx.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자 인증이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(session)
    user = await user_repo.get(ctx.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
        )

    request.state.auth_context = ctx
    return user


async def require_workspace(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> WorkspaceModel:
    """인증된 사용자의 워크스페이스를 반환하는 FastAPI 의존성."""
    if settings.disable_auth:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="인증이 비활성화된 상태에서는 워크스페이스를 조회할 수 없습니다.",
        )

    ctx = await _resolve_auth(request, session, settings)
    if ctx.workspace_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="워크스페이스 접근 권한이 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    ws_repo = WorkspaceRepository(session)
    workspace = await ws_repo.get(ctx.workspace_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="워크스페이스를 찾을 수 없습니다.",
        )

    request.state.auth_context = ctx
    return workspace
