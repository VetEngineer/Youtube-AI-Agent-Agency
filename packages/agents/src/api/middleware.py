"""API 미들웨어 - 감사 로그, Rate Limiting."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)

# 감사 로그에서 제외할 경로
_EXCLUDED_PATHS = {"/api/v1/health", "/docs", "/openapi.json", "/redoc"}


class AuditLogMiddleware(BaseHTTPMiddleware):
    """모든 API 요청을 감사 로그에 기록하는 미들웨어."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        start_time = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start_time) * 1000

        # 비동기로 감사 로그 저장 (fire-and-forget)
        try:
            await self._save_audit_log(request, response, duration_ms)
        except Exception:
            logger.warning("감사 로그 저장 실패", exc_info=True)

        return response

    async def _save_audit_log(
        self, request: Request, response: Response, duration_ms: float
    ) -> None:
        """감사 로그를 DB에 저장합니다."""
        from src.database.engine import get_session_factory
        from src.database.repositories import AuditLogRepository

        session_factory = get_session_factory()
        if session_factory is None:
            return

        async with session_factory() as session:
            repo = AuditLogRepository(session)
            await repo.create(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                api_key_id=getattr(request.state, "api_key_id", None),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent", "")[:500],
                duration_ms=round(duration_ms, 2),
            )
            await session.commit()


def setup_rate_limiting(app: FastAPI) -> None:
    """Rate Limiting을 설정합니다.

    slowapi 라이브러리를 사용하여 API 요청 속도를 제한합니다.
    slowapi가 설치되지 않은 경우 건너뜁니다.
    """
    try:
        from slowapi import Limiter
        from slowapi.errors import RateLimitExceeded
        from slowapi.middleware import SlowAPIMiddleware
        from slowapi.util import get_remote_address
    except ImportError:
        logger.info("slowapi가 설치되지 않아 Rate Limiting을 건너뜁니다")
        return

    from src.api.dependencies import get_settings

    settings = get_settings()
    default_limit = f"{settings.rate_limit_per_minute}/minute"

    limiter = Limiter(key_func=get_remote_address, default_limits=[default_limit])
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
        from starlette.responses import JSONResponse

        return JSONResponse(
            status_code=429,
            content={"detail": "요청 속도 제한을 초과했습니다. 잠시 후 다시 시도하세요."},
            headers={"Retry-After": str(exc.detail)},
        )

    logger.info("Rate Limiting 설정 완료: %s", default_limit)
