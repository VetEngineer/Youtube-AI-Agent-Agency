"""비동기 작업 큐 워커 테스트."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ============================================
# Worker Config 테스트
# ============================================


class TestWorkerConfig:
    """워커 설정 테스트."""

    def test_기본_설정_값(self):
        from src.worker.config import WorkerSettings

        settings = WorkerSettings()
        assert settings.redis_host == "localhost"
        assert settings.redis_port == 6379
        assert settings.redis_db == 0
        assert settings.worker_max_jobs == 5
        assert settings.worker_job_timeout == 1800
        assert settings.worker_queue_name == "yaa:pipeline"

    def test_환경변수_오버라이드(self, monkeypatch):
        from src.worker.config import WorkerSettings

        monkeypatch.setenv("REDIS_HOST", "redis.example.com")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("REDIS_DB", "2")
        monkeypatch.setenv("WORKER_MAX_JOBS", "10")

        settings = WorkerSettings()
        assert settings.redis_host == "redis.example.com"
        assert settings.redis_port == 6380
        assert settings.redis_db == 2
        assert settings.worker_max_jobs == 10

    def test_redis_settings_프로퍼티(self):
        from src.worker.config import WorkerSettings

        settings = WorkerSettings()
        redis_settings = settings.redis_settings
        assert redis_settings.host == "localhost"
        assert redis_settings.port == 6379

    def test_get_worker_settings(self):
        from src.worker.config import get_worker_settings

        settings = get_worker_settings()
        assert settings.redis_host == "localhost"


# ============================================
# Enqueue 테스트
# ============================================


class TestEnqueue:
    """큐 등록 헬퍼 테스트."""

    @pytest.fixture(autouse=True)
    def _reset_pool(self):
        """각 테스트 전에 글로벌 풀을 리셋합니다."""
        import src.worker.enqueue as mod

        mod._arq_pool = None
        yield
        mod._arq_pool = None

    async def test_redis_미연결시_false_반환(self):
        from src.worker.enqueue import enqueue_pipeline

        result = await enqueue_pipeline(
            run_id="test-run",
            channel_id="test-ch",
            topic="topic",
            brand_name="brand",
            dry_run=True,
        )
        assert result is False

    async def test_redis_연결_성공시_true_반환(self):
        import src.worker.enqueue as mod

        mock_pool = AsyncMock()
        mock_pool.enqueue_job = AsyncMock()
        mod._arq_pool = mock_pool

        from src.worker.enqueue import enqueue_pipeline

        result = await enqueue_pipeline(
            run_id="test-run",
            channel_id="test-ch",
            topic="topic",
            brand_name="brand",
            dry_run=True,
        )
        assert result is True
        mock_pool.enqueue_job.assert_called_once()

    async def test_enqueue_실패시_false_반환(self):
        import src.worker.enqueue as mod

        mock_pool = AsyncMock()
        mock_pool.enqueue_job = AsyncMock(side_effect=ConnectionError("Redis 연결 끊김"))
        mod._arq_pool = mock_pool

        from src.worker.enqueue import enqueue_pipeline

        result = await enqueue_pipeline(
            run_id="test-run",
            channel_id="test-ch",
            topic="topic",
            brand_name="brand",
            dry_run=True,
        )
        assert result is False

    async def test_close_arq_pool(self):
        import src.worker.enqueue as mod

        mock_pool = MagicMock()
        mock_pool.close = MagicMock()
        mock_pool.wait_closed = AsyncMock()
        mod._arq_pool = mock_pool

        from src.worker.enqueue import close_arq_pool

        await close_arq_pool()
        mock_pool.close.assert_called_once()
        mock_pool.wait_closed.assert_called_once()
        assert mod._arq_pool is None

    async def test_close_arq_pool_none이면_무시(self):
        from src.worker.enqueue import close_arq_pool

        # None일 때 에러 없이 통과해야 함
        await close_arq_pool()


# ============================================
# Pipeline API 큐 통합 테스트
# ============================================


class TestPipelineQueueIntegration:
    """파이프라인 API에서 큐 enqueue를 사용하는 통합 테스트."""

    @pytest.fixture()
    async def _db_session_factory(self):
        from src.database.engine import init_db, set_session_factory

        factory = await init_db("sqlite+aiosqlite:///:memory:")
        yield factory
        set_session_factory(None)

    @pytest.fixture()
    def _channels_dir(self, tmp_path):
        ch_dir = tmp_path / "channels"
        ch_dir.mkdir()
        ch = ch_dir / "test-channel"
        ch.mkdir()
        (ch / "config.yaml").write_text(
            "channel:\n  name: '테스트 채널'\n  category: 'test'\n",
            encoding="utf-8",
        )
        return ch_dir

    @pytest.fixture()
    def client(self, _channels_dir, _db_session_factory):
        from fastapi.testclient import TestClient

        from src.api.dependencies import get_channel_registry, get_settings
        from src.api.main import create_app
        from src.database.engine import get_db_session
        from src.shared.config import AppSettings, ChannelRegistry

        app = create_app()
        registry = ChannelRegistry(str(_channels_dir))
        test_settings = AppSettings(
            disable_auth=True,
            database_url="sqlite+aiosqlite:///:memory:",
            channels_dir=str(_channels_dir),
        )
        app.dependency_overrides[get_channel_registry] = lambda: registry
        app.dependency_overrides[get_settings] = lambda: test_settings

        async def _override_db_session():
            async with _db_session_factory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        app.dependency_overrides[get_db_session] = _override_db_session

        with TestClient(app) as c:
            yield c

    def test_redis_없을때_BackgroundTasks_폴백(self, client):
        """Redis가 없으면 BackgroundTasks로 폴백하여 정상 응답."""
        response = client.post(
            "/api/v1/pipeline/run",
            json={
                "channel_id": "test-channel",
                "topic": "큐 테스트",
                "dry_run": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "run_id" in data

    @patch("src.worker.enqueue.enqueue_pipeline", new_callable=AsyncMock)
    def test_redis_있을때_큐로_전달(self, mock_enqueue, client):
        """Redis가 가용하면 큐에 enqueue됨."""
        mock_enqueue.return_value = True

        response = client.post(
            "/api/v1/pipeline/run",
            json={
                "channel_id": "test-channel",
                "topic": "큐 enqueue 테스트",
                "dry_run": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        mock_enqueue.assert_called_once()

    @patch("src.worker.enqueue.enqueue_pipeline", new_callable=AsyncMock)
    def test_enqueue_실패시_폴백(self, mock_enqueue, client):
        """enqueue 실패 시 BackgroundTasks로 폴백."""
        mock_enqueue.return_value = False

        response = client.post(
            "/api/v1/pipeline/run",
            json={
                "channel_id": "test-channel",
                "topic": "폴백 테스트",
                "dry_run": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"


# ============================================
# Worker Task 테스트
# ============================================


class TestExecutePipelineTask:
    """execute_pipeline_task 유닛 테스트."""

    async def test_세션_팩토리_없으면_에러_반환(self):
        from src.database.engine import set_session_factory
        from src.worker.tasks import execute_pipeline_task

        set_session_factory(None)

        result = await execute_pipeline_task(
            ctx={},
            run_id="test-run",
            channel_id="test-ch",
            topic="topic",
            brand_name="brand",
            dry_run=True,
        )
        assert result["status"] == "error"
