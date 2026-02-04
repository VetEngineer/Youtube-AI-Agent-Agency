"""Alembic 마이그레이션 환경 설정."""

from __future__ import annotations

import re
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from src.database.models import Base
from src.shared.config import AppSettings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_sync_url() -> str:
    """AppSettings에서 DB URL을 읽고 동기 드라이버로 변환합니다."""
    settings = AppSettings()
    url = settings.database_url

    # 비동기 드라이버를 동기 드라이버로 변환
    url = re.sub(r"\+aiosqlite", "", url)
    url = re.sub(r"\+asyncpg", "+psycopg2", url)

    return url


def run_migrations_offline() -> None:
    """오프라인 모드로 마이그레이션을 실행합니다."""
    url = _get_sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """온라인 모드로 마이그레이션을 실행합니다."""
    ini_section = config.get_section(config.config_ini_section, {})
    ini_section["sqlalchemy.url"] = _get_sync_url()

    connectable = engine_from_config(
        ini_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
