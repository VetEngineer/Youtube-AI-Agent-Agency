"""Prometheus 메트릭 미들웨어.

prometheus_client가 설치되지 않은 경우 no-op으로 동작합니다.
"""

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

# 메트릭에서 제외할 경로
_METRICS_EXCLUDED_PATHS = {"/metrics", "/docs", "/openapi.json", "/redoc"}

# ──────────────────────────────────────────
# prometheus_client가 없으면 no-op 스텁 사용
# ──────────────────────────────────────────

_HAS_PROMETHEUS = False

try:
    from prometheus_client import (
        REGISTRY,
        Counter,
        Histogram,
        generate_latest,
    )

    _HAS_PROMETHEUS = True
except ImportError:
    pass


class _NoOpMetric:
    """prometheus_client 미설치 시 사용할 no-op 메트릭 스텁."""

    def labels(self, **_kwargs: object) -> _NoOpMetric:
        return self

    def inc(self, _amount: float = 1) -> None:  # noqa: N802
        pass

    def observe(self, _amount: float) -> None:
        pass


def _build_counter(name: str, doc: str, labelnames: list[str]) -> object:
    """Counter를 생성합니다. prometheus_client가 없으면 no-op을 반환합니다."""
    if _HAS_PROMETHEUS:
        return Counter(name, doc, labelnames)
    return _NoOpMetric()


def _build_histogram(name: str, doc: str, labelnames: list[str]) -> object:
    """Histogram을 생성합니다. prometheus_client가 없으면 no-op을 반환합니다."""
    if _HAS_PROMETHEUS:
        return Histogram(name, doc, labelnames)
    return _NoOpMetric()


# ──────────────────────────────────────────
# 메트릭 정의
# ──────────────────────────────────────────

http_requests_total = _build_counter(
    "yaa_http_requests_total",
    "HTTP 요청 총 수",
    ["method", "path", "status"],
)

http_request_duration_seconds = _build_histogram(
    "yaa_http_request_duration_seconds",
    "HTTP 요청 처리 시간(초)",
    ["method", "path"],
)

pipeline_runs_total = _build_counter(
    "yaa_pipeline_runs_total",
    "파이프라인 실행 총 수",
    ["status"],
)

pipeline_duration_seconds = _build_histogram(
    "yaa_pipeline_duration_seconds",
    "파이프라인 실행 시간(초)",
    ["channel_id"],
)


def _normalize_path(path: str) -> str:
    """경로에서 동적 파라미터를 제거하여 카디널리티를 낮춥니다.

    예: /api/v1/channels/my-ch → /api/v1/channels/{id}
    """
    parts = path.strip("/").split("/")
    normalized: list[str] = []
    # api/v1 이후의 3번째 이상 세그먼트를 {id}로 대체
    for i, part in enumerate(parts):
        if i >= 3 and not part.startswith("{"):
            normalized.append("{id}")
        else:
            normalized.append(part)
    return "/" + "/".join(normalized) if normalized else path


class PrometheusMiddleware(BaseHTTPMiddleware):
    """HTTP 요청 메트릭을 수집하는 미들웨어."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in _METRICS_EXCLUDED_PATHS:
            return await call_next(request)

        method = request.method
        path = _normalize_path(request.url.path)

        start = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start

        http_requests_total.labels(method=method, path=path, status=str(response.status_code)).inc()
        http_request_duration_seconds.labels(method=method, path=path).observe(duration)

        return response


def setup_metrics(app: FastAPI) -> None:
    """Prometheus 메트릭 미들웨어와 /metrics 엔드포인트를 설정합니다.

    prometheus_client가 설치되지 않은 경우 미들웨어만 추가합니다
    (no-op 메트릭이 사용되므로 오버헤드 최소).
    """
    app.add_middleware(PrometheusMiddleware)

    if _HAS_PROMETHEUS:
        from starlette.responses import Response as StarletteResponse

        @app.get("/metrics", include_in_schema=False)
        async def metrics_endpoint() -> StarletteResponse:
            """Prometheus 메트릭을 반환합니다."""
            body = generate_latest(REGISTRY)
            return StarletteResponse(
                content=body,
                media_type="text/plain; version=0.0.4; charset=utf-8",
            )

        logger.info("Prometheus 메트릭 엔드포인트 활성화: /metrics")
    else:
        logger.info("prometheus_client 미설치 - 메트릭 수집 비활성화")
