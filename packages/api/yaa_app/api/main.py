"""FastAPI 애플리케이션 메인 진입점."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from yaa_core.shared.logging_config import setup_logging

from yaa_app.api.dependencies import get_settings
from yaa_app.api.metrics import setup_metrics
from yaa_app.api.middleware import AuditLogMiddleware, setup_rate_limiting
from yaa_app.api.routes import (
    admin,
    auth,
    billing,
    channels,
    competitors,
    dashboard,
    oauth,
    pipeline,
    plans,
    status,
    usage,
    users,
)
from yaa_app.api.routes import (
    settings as settings_routes,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """애플리케이션 시작/종료 시 리소스를 관리합니다."""
    from yaa_core.database.engine import init_db

    settings = get_settings()

    try:
        await asyncio.wait_for(init_db(settings.database_url), timeout=30)
        logger.info("데이터베이스 초기화 완료")
    except TimeoutError:
        logger.error("데이터베이스 초기화 타임아웃 (30초) — 서버를 종료합니다")
        raise RuntimeError("DB 초기화 타임아웃") from None

    yield

    # Arq Redis 풀 정리
    try:
        from yaa_app.worker.enqueue import close_arq_pool

        await close_arq_pool()
    except ImportError:
        pass

    logger.info("애플리케이션 종료")


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 인스턴스를 생성합니다."""
    settings = get_settings()

    # 구조화 로깅 초기화
    setup_logging(log_format=settings.log_format, log_level=settings.log_level)

    # 프로덕션에서는 OpenAPI 문서 비활성화 (#68)
    docs_url = "/docs" if settings.disable_auth else None
    redoc_url = "/redoc" if settings.disable_auth else None
    openapi_url = "/openapi.json" if settings.disable_auth else None

    application = FastAPI(
        title="YouTube AI Agent Agency API",
        description="LangGraph 기반 YouTube 콘텐츠 자동화 파이프라인",
        version="0.2.0",
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    # CORS 설정 (환경변수에서 읽기)
    cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
    )

    # 감사 로그 미들웨어
    application.add_middleware(AuditLogMiddleware)

    # Prometheus 메트릭 미들웨어 + /metrics 엔드포인트
    setup_metrics(application)

    # Rate Limiting
    setup_rate_limiting(application)

    # 전역 예외 핸들러 (프로덕션 에러 새니타이징)
    application.add_exception_handler(Exception, _global_exception_handler)

    # 라우터 등록
    application.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    application.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
    application.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["pipeline"])
    application.include_router(channels.router, prefix="/api/v1/channels", tags=["channels"])
    application.include_router(
        competitors.router, prefix="/api/v1/competitors", tags=["competitors"]
    )
    application.include_router(status.router, prefix="/api/v1", tags=["status"])
    application.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
    application.include_router(usage.router, prefix="/api/v1/usage", tags=["usage"])
    application.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    application.include_router(plans.router, prefix="/api/v1/plans", tags=["plans"])
    application.include_router(billing.router, prefix="/api/v1/billing", tags=["billing"])
    application.include_router(settings_routes.router, prefix="/api/v1/settings", tags=["settings"])
    application.include_router(oauth.router, prefix="/api/v1/oauth", tags=["oauth"])

    return application


async def _global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """프로덕션 환경에서 내부 에러 상세를 숨기는 전역 예외 핸들러."""
    logger.error("Unhandled exception: %s %s - %s", request.method, request.url.path, exc)
    settings = get_settings()
    if settings.disable_auth:
        # 개발 환경: 상세 에러 노출
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )
    # 프로덕션: 일반 메시지만 노출
    return JSONResponse(
        status_code=500,
        content={"detail": "내부 서버 오류가 발생했습니다."},
    )


app = create_app()
