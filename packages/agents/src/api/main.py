"""FastAPI 애플리케이션 메인 진입점."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import channels, pipeline, status

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 인스턴스를 생성합니다."""
    application = FastAPI(
        title="YouTube AI Agent Agency API",
        description="LangGraph 기반 YouTube 콘텐츠 자동화 파이프라인",
        version="0.1.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["pipeline"])
    application.include_router(channels.router, prefix="/api/v1/channels", tags=["channels"])
    application.include_router(status.router, prefix="/api/v1", tags=["status"])

    return application


app = create_app()
