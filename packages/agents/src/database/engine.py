"""비동기 데이터베이스 엔진 팩토리 및 세션 관리."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.database.models import Base

logger = logging.getLogger(__name__)

_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_engine_from_url(database_url: str) -> async_sessionmaker[AsyncSession]:
    """database_url로부터 비동기 엔진과 세션 팩토리를 생성합니다.

    Args:
        database_url: SQLAlchemy 비동기 URL
            - 개발: "sqlite+aiosqlite:///./data/agency.db"
            - 프로덕션: "postgresql+asyncpg://user:pass@host/db"

    Returns:
        async_sessionmaker 인스턴스
    """
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        connect_args=connect_args,
    )

    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db(database_url: str) -> async_sessionmaker[AsyncSession]:
    """데이터베이스를 초기화합니다.

    SQLite 사용 시 data 디렉토리를 자동 생성합니다.
    테이블이 없으면 자동으로 생성합니다.

    Args:
        database_url: SQLAlchemy 비동기 URL

    Returns:
        async_sessionmaker 인스턴스
    """
    global _async_session_factory

    if database_url.startswith("sqlite"):
        db_path = database_url.split("///")[-1]
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    session_factory = create_engine_from_url(database_url)
    engine = session_factory.kw["bind"]

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    _async_session_factory = session_factory
    logger.info("데이터베이스 초기화 완료: %s", database_url.split("@")[-1])
    return session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 의존성 주입용 DB 세션 제너레이터."""
    if _async_session_factory is None:
        raise RuntimeError("데이터베이스가 초기화되지 않았습니다. init_db()를 먼저 호출하세요.")

    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_session_factory() -> async_sessionmaker[AsyncSession] | None:
    """현재 세션 팩토리를 반환합니다 (테스트용)."""
    return _async_session_factory


def set_session_factory(factory: async_sessionmaker[AsyncSession] | None) -> None:
    """세션 팩토리를 설정합니다 (테스트용)."""
    global _async_session_factory
    _async_session_factory = factory
