"""이메일/패스워드 JWT 인증 API 라우터."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from yaa_core.database.engine import get_db_session
from yaa_core.database.repositories import UserRepository, WorkspaceRepository
from yaa_core.shared.config import AppSettings

from yaa_app.api.auth import AuthContext, get_auth_context
from yaa_app.api.dependencies import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)

_ACCESS_TOKEN_EXPIRE_HOURS = 24
_REFRESH_TOKEN_EXPIRE_DAYS = 7


# ============================================
# Pydantic 스키마
# ============================================


class RegisterRequest(BaseModel):
    """회원가입 요청."""

    email: str = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=8, description="최소 8자 이상")
    name: str | None = Field(None, max_length=200)


class LoginRequest(BaseModel):
    """로그인 요청."""

    email: str = Field(..., description="이메일 주소")
    password: str


class TokenResponse(BaseModel):
    """JWT 토큰 응답."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = _ACCESS_TOKEN_EXPIRE_HOURS * 3600


class RefreshRequest(BaseModel):
    """토큰 갱신 요청."""

    refresh_token: str


class MeResponse(BaseModel):
    """현재 사용자 정보 응답."""

    id: str
    email: str
    name: str | None = None
    plan: str
    workspace_id: str | None = None


# ============================================
# 헬퍼 함수
# ============================================


def _hash_password(password: str) -> str:
    """패스워드를 bcrypt로 해싱합니다."""
    import bcrypt

    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, password_hash: str) -> bool:
    """패스워드를 검증합니다 (bcrypt + SHA-256 레거시 호환)."""
    import bcrypt

    # bcrypt 해시 ($2b$ 접두사)
    if password_hash.startswith("$2"):
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    # 레거시 SHA-256 해시 (마이그레이션 기간)
    import hashlib

    if hashlib.sha256(password.encode()).hexdigest() == password_hash:
        return True

    return False


def _create_jwt(payload: dict, secret: str, algorithm: str, expires_delta: timedelta) -> str:
    """JWT 토큰을 생성합니다."""
    try:
        import jwt
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PyJWT 패키지가 설치되지 않았습니다.",
        ) from exc

    expire = datetime.now(UTC) + expires_delta
    data = {**payload, "exp": expire, "iat": datetime.now(UTC)}
    return jwt.encode(data, secret, algorithm=algorithm)


def _decode_jwt(token: str, secret: str, algorithm: str) -> dict:
    """JWT 토큰을 디코딩합니다."""
    try:
        import jwt
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PyJWT 패키지가 설치되지 않았습니다.",
        ) from exc

    try:
        return jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었습니다.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )


def _require_jwt_config(settings: AppSettings) -> None:
    """JWT 설정이 유효한지 확인합니다."""
    if not settings.jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="JWT_SECRET이 설정되지 않았습니다.",
        )


# ============================================
# 엔드포인트
# ============================================


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> TokenResponse:
    """이메일/패스워드로 회원가입하고 JWT를 발급합니다."""
    _require_jwt_config(settings)

    user_repo = UserRepository(session)
    ws_repo = WorkspaceRepository(session)

    existing = await user_repo.get_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 이메일입니다.",
        )

    user_id = str(uuid.uuid4())
    password_hash = _hash_password(body.password)

    user = await user_repo.create(
        user_id=user_id,
        email=body.email,
        name=body.name,
        provider="email",
    )
    user.password_hash = password_hash

    ws_id = str(uuid.uuid4())
    await ws_repo.create(
        workspace_id=ws_id,
        name=f"{body.name or body.email}의 워크스페이스",
        owner_id=user_id,
    )

    await session.commit()
    logger.info("새 사용자 등록: email=%s workspace_id=%s", body.email, ws_id)

    access_token = _create_jwt(
        {"sub": user_id, "email": body.email, "workspace_id": ws_id},
        settings.jwt_secret,
        settings.jwt_algorithm,
        timedelta(hours=_ACCESS_TOKEN_EXPIRE_HOURS),
    )
    refresh_token = _create_jwt(
        {"sub": user_id, "type": "refresh"},
        settings.jwt_secret,
        settings.jwt_algorithm,
        timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> TokenResponse:
    """이메일/패스워드로 로그인하고 JWT를 발급합니다."""
    _require_jwt_config(settings)

    user_repo = UserRepository(session)
    ws_repo = WorkspaceRepository(session)

    user = await user_repo.get_by_email(body.email)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 패스워드가 올바르지 않습니다.",
        )

    if user.provider != "email" or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이 계정은 소셜 로그인만 지원합니다.",
        )

    if not _verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 패스워드가 올바르지 않습니다.",
        )

    workspaces = await ws_repo.list_by_owner(user.id)
    workspace_id = workspaces[0].id if workspaces else None

    logger.info("로그인 성공: email=%s", body.email)

    access_token = _create_jwt(
        {"sub": user.id, "email": user.email, "workspace_id": workspace_id},
        settings.jwt_secret,
        settings.jwt_algorithm,
        timedelta(hours=_ACCESS_TOKEN_EXPIRE_HOURS),
    )
    refresh_token = _create_jwt(
        {"sub": user.id, "type": "refresh"},
        settings.jwt_secret,
        settings.jwt_algorithm,
        timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> TokenResponse:
    """refresh_token으로 새 access_token을 발급합니다."""
    _require_jwt_config(settings)

    payload = _decode_jwt(body.refresh_token, settings.jwt_secret, settings.jwt_algorithm)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 refresh 토큰입니다.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )

    user_repo = UserRepository(session)
    ws_repo = WorkspaceRepository(session)

    user = await user_repo.get(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
        )

    workspaces = await ws_repo.list_by_owner(user.id)
    workspace_id = workspaces[0].id if workspaces else None

    access_token = _create_jwt(
        {"sub": user.id, "email": user.email, "workspace_id": workspace_id},
        settings.jwt_secret,
        settings.jwt_algorithm,
        timedelta(hours=_ACCESS_TOKEN_EXPIRE_HOURS),
    )
    new_refresh_token = _create_jwt(
        {"sub": user.id, "type": "refresh"},
        settings.jwt_secret,
        settings.jwt_algorithm,
        timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=MeResponse)
async def get_me(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> MeResponse:
    """현재 인증된 사용자 정보를 반환합니다."""
    if auth.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자 인증이 필요합니다.",
        )

    user_repo = UserRepository(session)
    user = await user_repo.get(auth.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    return MeResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        plan=user.plan,
        workspace_id=auth.workspace_id,
    )
