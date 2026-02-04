"""API 키 인증 모듈."""

from __future__ import annotations

import hashlib
import logging
import secrets
import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_settings
from src.database.engine import get_db_session
from src.database.repositories import ApiKeyRepository
from src.shared.config import AppSettings

logger = logging.getLogger(__name__)

API_KEY_PREFIX = "yaa_"
API_KEY_LENGTH = 32


def generate_api_key() -> str:
    """새 API 키를 생성합니다.

    Returns:
        "yaa_" 접두사가 붙은 API 키 (평문, 한 번만 표시됨)
    """
    return f"{API_KEY_PREFIX}{secrets.token_urlsafe(API_KEY_LENGTH)}"


def hash_api_key(key: str) -> str:
    """API 키를 SHA-256으로 해싱합니다.

    bcrypt 대신 SHA-256을 사용하여 빠른 검색을 지원합니다.
    API 키 자체가 충분히 높은 엔트로피를 가지므로 안전합니다.
    """
    return hashlib.sha256(key.encode()).hexdigest()


def generate_key_id() -> str:
    """API 키 ID를 생성합니다."""
    return str(uuid.uuid4())


async def create_api_key(
    session: AsyncSession,
    name: str,
    scopes: list[str] | None = None,
) -> tuple[str, str]:
    """새 API 키를 생성하고 DB에 저장합니다.

    Args:
        session: DB 세션
        name: API 키 설명 이름
        scopes: 권한 스코프 (기본: ["read", "write"])

    Returns:
        (plaintext_key, key_id) 튜플. plaintext_key는 이 호출에서만 확인 가능.
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
    )
    await session.commit()

    return plaintext_key, key_id


async def _resolve_api_key(
    request: Request, session: AsyncSession, settings: AppSettings
) -> str | None:
    """요청에서 API 키를 추출하고 검증합니다.

    Returns:
        API 키 ID (유효한 경우) 또는 None
    """
    header_value = request.headers.get(settings.api_key_header)
    if not header_value:
        return None

    key_hash = hash_api_key(header_value)
    repo = ApiKeyRepository(session)
    api_key = await repo.get_by_hash(key_hash)

    if api_key is None:
        return None

    await repo.update_last_used(api_key.id)
    return api_key.id


async def require_api_key(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> str | None:
    """API 키 인증을 요구하는 FastAPI 의존성.

    DISABLE_AUTH=true인 경우 인증을 건너뜁니다.

    Returns:
        API 키 ID
    Raises:
        HTTPException 401: API 키가 없거나 유효하지 않은 경우
    """
    if settings.disable_auth:
        return None

    api_key_id = await _resolve_api_key(request, session, settings)
    if api_key_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 API 키입니다.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key_id


async def optional_api_key(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> str | None:
    """인증이 선택적인 엔드포인트용 FastAPI 의존성.

    API 키가 없어도 요청을 허용하되, 있으면 검증합니다.
    """
    if settings.disable_auth:
        return None

    return await _resolve_api_key(request, session, settings)


async def require_admin_scope(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> str | None:
    """관리자 스코프를 요구하는 FastAPI 의존성.

    DISABLE_AUTH=true인 경우 인증을 건너뜁니다.
    API 키의 scopes에 "admin"이 포함되어 있어야 합니다.

    Returns:
        API 키 ID
    Raises:
        HTTPException 401: API 키가 없거나 유효하지 않은 경우
        HTTPException 403: admin 스코프가 없는 경우
    """
    if settings.disable_auth:
        return None

    api_key_id = await _resolve_api_key(request, session, settings)
    if api_key_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 API 키입니다.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    repo = ApiKeyRepository(session)
    api_key = await repo.get_by_id(api_key_id)
    if api_key is None or "admin" not in api_key.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다.",
        )

    return api_key_id
