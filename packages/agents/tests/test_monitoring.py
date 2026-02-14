"""모니터링 + 로깅 시스템 테스트."""

from __future__ import annotations

import json
import logging
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.database.engine import get_db_session, init_db, set_session_factory
from src.shared.logging_config import JSONFormatter, setup_logging

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


# ============================================
# JSONFormatter 테스트
# ============================================


class TestJSONFormatter:
    """JSONFormatter 출력 형식 테스트."""

    def test_기본_필드_포함(self):
        """JSON 로그에 timestamp, level, logger, message가 포함되어야 합니다."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="테스트 메시지",
            args=None,
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "timestamp" in data
        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "테스트 메시지"

    def test_모듈_함수_위치_포함(self):
        """JSON 로그에 module, function, line 정보가 포함되어야 합니다."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="/path/to/module.py",
            lineno=42,
            msg="경고",
            args=None,
            exc_info=None,
        )
        record.funcName = "my_function"

        output = formatter.format(record)
        data = json.loads(output)

        assert data["module"] == "module"
        assert data["function"] == "my_function"
        assert data["line"] == 42

    def test_extra_필드_병합(self):
        """extra 딕셔너리 필드가 JSON 로그에 포함되어야 합니다."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="요청 처리",
            args=None,
            exc_info=None,
        )
        record.channel_id = "my-channel"
        record.duration_ms = 123.45

        output = formatter.format(record)
        data = json.loads(output)

        assert data["channel_id"] == "my-channel"
        assert data["duration_ms"] == 123.45

    def test_예외_정보_포함(self):
        """예외 발생 시 exception 필드가 포함되어야 합니다."""
        formatter = JSONFormatter()

        try:
            raise ValueError("테스트 에러")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="에러 발생",
            args=None,
            exc_info=exc_info,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "exception" in data
        assert "ValueError" in data["exception"]
        assert "테스트 에러" in data["exception"]

    def test_한글_메시지_처리(self):
        """한글 메시지가 escape 없이 출력되어야 합니다."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="한글 메시지 테스트",
            args=None,
            exc_info=None,
        )

        output = formatter.format(record)
        assert "한글 메시지 테스트" in output

    def test_유효한_JSON_출력(self):
        """출력이 항상 유효한 JSON이어야 합니다."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=1,
            msg="msg with 'quotes' and \"double\"",
            args=None,
            exc_info=None,
        )

        output = formatter.format(record)
        # json.loads가 에러 없이 성공해야 합니다
        data = json.loads(output)
        assert isinstance(data, dict)


# ============================================
# setup_logging 테스트
# ============================================


class TestSetupLogging:
    """setup_logging 설정 테스트."""

    def test_text_포맷_설정(self):
        """LOG_FORMAT=text 시 텍스트 포맷터가 적용되어야 합니다."""
        setup_logging(log_format="text", log_level="INFO")
        root = logging.getLogger()

        assert len(root.handlers) > 0
        handler = root.handlers[0]
        assert not isinstance(handler.formatter, JSONFormatter)

    def test_json_포맷_설정(self):
        """LOG_FORMAT=json 시 JSONFormatter가 적용되어야 합니다."""
        setup_logging(log_format="json", log_level="INFO")
        root = logging.getLogger()

        assert len(root.handlers) > 0
        handler = root.handlers[0]
        assert isinstance(handler.formatter, JSONFormatter)

    def test_로그_레벨_설정(self):
        """log_level 파라미터에 따라 루트 로거 레벨이 변경되어야 합니다."""
        setup_logging(log_format="text", log_level="WARNING")
        root = logging.getLogger()
        assert root.level == logging.WARNING

        setup_logging(log_format="text", log_level="DEBUG")
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_중복_핸들러_방지(self):
        """setup_logging을 여러 번 호출해도 핸들러가 중복되지 않아야 합니다."""
        setup_logging(log_format="text")
        setup_logging(log_format="text")
        setup_logging(log_format="json")
        root = logging.getLogger()

        assert len(root.handlers) == 1


# ============================================
# AppSettings log_format 테스트
# ============================================


class TestAppSettingsLogFormat:
    """AppSettings log_format 필드 테스트."""

    def test_기본값_text(self):
        """log_format 기본값은 'text'이어야 합니다."""
        from src.shared.config import AppSettings

        settings = AppSettings()
        assert settings.log_format == "text"

    def test_환경변수_json(self):
        """LOG_FORMAT=json 환경변수가 적용되어야 합니다."""
        from src.shared.config import AppSettings

        with patch.dict("os.environ", {"LOG_FORMAT": "json"}):
            settings = AppSettings()
            assert settings.log_format == "json"


# ============================================
# 메트릭 모듈 import 테스트
# ============================================


class TestMetricsModule:
    """메트릭 모듈 import 및 graceful fallback 테스트."""

    def test_모듈_import_성공(self):
        """metrics 모듈이 정상적으로 import 되어야 합니다."""
        from src.api.metrics import (
            PrometheusMiddleware,
            http_request_duration_seconds,
            http_requests_total,
            pipeline_duration_seconds,
            pipeline_runs_total,
            setup_metrics,
        )

        assert http_requests_total is not None
        assert http_request_duration_seconds is not None
        assert pipeline_runs_total is not None
        assert pipeline_duration_seconds is not None
        assert PrometheusMiddleware is not None
        assert setup_metrics is not None

    def test_no_op_메트릭_labels_동작(self):
        """prometheus_client 미설치 시 no-op 메트릭이 에러 없이 동작해야 합니다."""
        from src.api.metrics import _NoOpMetric

        noop = _NoOpMetric()
        # labels → inc/observe 체인이 에러 없이 동작
        noop.labels(method="GET", path="/test").inc()
        noop.labels(method="GET", path="/test").observe(0.5)
        noop.inc(2)
        noop.observe(1.0)

    def test_경로_정규화(self):
        """_normalize_path가 동적 파라미터를 {id}로 대체해야 합니다."""
        from src.api.metrics import _normalize_path

        # 3번째 세그먼트 이상은 {id}로 대체
        result = _normalize_path("/api/v1/channels/my-channel")
        assert result == "/api/v1/channels/{id}"

        # 짧은 경로는 그대로 유지
        result = _normalize_path("/api/v1/health")
        assert result == "/api/v1/health"

    def test_prometheus_가용성_플래그(self):
        """_HAS_PROMETHEUS 플래그가 prometheus_client 설치 여부를 반영해야 합니다."""
        from src.api.metrics import _HAS_PROMETHEUS

        # 테스트 환경에서는 prometheus_client가 설치되지 않았을 수 있음
        assert isinstance(_HAS_PROMETHEUS, bool)

    def test_prometheus_미설치_graceful_fallback(self):
        """prometheus_client가 없을 때 no-op 스텁이 사용되어야 합니다."""
        from src.api.metrics import _build_counter, _build_histogram, _NoOpMetric

        # _HAS_PROMETHEUS를 False로 패치하여 no-op 동작 확인
        with patch("src.api.metrics._HAS_PROMETHEUS", False):
            counter = _build_counter("test_counter", "doc", ["label"])
            histogram = _build_histogram("test_hist", "doc", ["label"])

            assert isinstance(counter, _NoOpMetric)
            assert isinstance(histogram, _NoOpMetric)


# ============================================
# /metrics 엔드포인트 테스트
# ============================================


@pytest.fixture()
async def _db_factory():
    """테스트용 인메모리 DB 세션 팩토리."""
    factory = await init_db(TEST_DB_URL)
    yield factory
    set_session_factory(None)


@pytest.fixture()
def monitoring_client(_db_factory) -> TestClient:
    """메트릭 테스트용 FastAPI TestClient."""
    from src.api.dependencies import get_settings
    from src.shared.config import AppSettings

    app = create_app()

    test_settings = AppSettings(
        disable_auth=True,
        database_url=TEST_DB_URL,
    )
    app.dependency_overrides[get_settings] = lambda: test_settings

    async def _override_db_session():
        async with _db_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override_db_session

    with TestClient(app) as c:
        yield c


class TestMetricsEndpoint:
    """Prometheus /metrics 엔드포인트 테스트."""

    def test_prometheus_설치시_metrics_200(self, monitoring_client: TestClient):
        """prometheus_client 설치 시 /metrics가 200을 반환해야 합니다."""
        from src.api.metrics import _HAS_PROMETHEUS

        response = monitoring_client.get("/metrics")

        if _HAS_PROMETHEUS:
            assert response.status_code == 200
            assert "text/plain" in response.headers.get("content-type", "")
        else:
            # prometheus_client 미설치 시 /metrics 엔드포인트 미등록
            assert response.status_code == 404

    def test_http_요청시_메트릭_수집(self, monitoring_client: TestClient):
        """HTTP 요청 시 메트릭 카운터가 증가해야 합니다."""
        from src.api.metrics import _HAS_PROMETHEUS

        if not _HAS_PROMETHEUS:
            pytest.skip("prometheus_client 미설치")

        # 요청 발생
        monitoring_client.get("/api/v1/health")

        # /metrics 확인
        response = monitoring_client.get("/metrics")
        assert response.status_code == 200
        body = response.text
        assert "yaa_http_requests_total" in body
