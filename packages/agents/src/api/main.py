"""FastAPI 애플리케이션 메인 진입점."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.dependencies import get_settings
from src.api.middleware import AuditLogMiddleware, setup_rate_limiting
from src.api.routes import admin, channels, dashboard, pipeline, status

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """애플리케이션 시작/종료 시 리소스를 관리합니다."""
    from src.database.engine import init_db

    settings = get_settings()

    await init_db(settings.database_url)
    logger.info("데이터베이스 초기화 완료")

    yield

    # Arq Redis 풀 정리
    try:
        from src.worker.enqueue import close_arq_pool

        await close_arq_pool()
    except ImportError:
        pass

    logger.info("애플리케이션 종료")


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 인스턴스를 생성합니다."""
    settings = get_settings()

    application = FastAPI(
        title="YouTube AI Agent Agency API",
        description="LangGraph 기반 YouTube 콘텐츠 자동화 파이프라인",
        version="0.2.0",
        lifespan=lifespan,
    )

    # CORS 설정 (환경변수에서 읽기)
    cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 감사 로그 미들웨어
    application.add_middleware(AuditLogMiddleware)

    # Rate Limiting
    setup_rate_limiting(application)

    # 라우터 등록
    application.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
    application.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["pipeline"])
    application.include_router(channels.router, prefix="/api/v1/channels", tags=["channels"])
    application.include_router(status.router, prefix="/api/v1", tags=["status"])
    application.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

    return application


app = create_app()
