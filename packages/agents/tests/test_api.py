"""FastAPI API 서버 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.routes.pipeline import _run_storage
from src.shared.config import ChannelRegistry


@pytest.fixture()
def _channels_dir(tmp_path: Path) -> Path:
    """테스트용 채널 디렉토리를 생성합니다."""
    ch_dir = tmp_path / "channels"
    ch_dir.mkdir()

    # 테스트 채널 생성
    ch = ch_dir / "test-channel"
    ch.mkdir()
    (ch / "config.yaml").write_text(
        "channel:\n  name: '테스트 채널'\n  category: 'test'\n",
        encoding="utf-8",
    )

    return ch_dir


@pytest.fixture()
def _registry(_channels_dir: Path) -> ChannelRegistry:
    return ChannelRegistry(str(_channels_dir))


@pytest.fixture()
def client(_registry: ChannelRegistry) -> TestClient:
    """FastAPI TestClient를 생성합니다."""
    from src.api.dependencies import get_channel_registry

    app = create_app()
    app.dependency_overrides[get_channel_registry] = lambda: _registry

    with TestClient(app) as c:
        yield c

    # 실행 스토리지 초기화
    _run_storage.clear()


# ============================================
# Health Check
# ============================================


class TestHealthCheck:
    """헬스체크 엔드포인트 테스트."""

    def test_헬스체크_정상(self, client: TestClient):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


# ============================================
# Channels API
# ============================================


class TestChannelsAPI:
    """채널 관리 API 테스트."""

    def test_채널_목록_조회(self, client: TestClient):
        response = client.get("/api/v1/channels/")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        assert data["channels"][0]["channel_id"] == "test-channel"
        assert data["channels"][0]["name"] == "테스트 채널"

    def test_특정_채널_조회(self, client: TestClient):
        response = client.get("/api/v1/channels/test-channel")
        assert response.status_code == 200

        data = response.json()
        assert data["channel_id"] == "test-channel"
        assert data["name"] == "테스트 채널"
        assert data["has_brand_guide"] is False

    def test_존재하지_않는_채널_404(self, client: TestClient):
        response = client.get("/api/v1/channels/nonexistent")
        assert response.status_code == 404


# ============================================
# Pipeline API
# ============================================


class TestPipelineAPI:
    """파이프라인 실행 API 테스트."""

    def test_파이프라인_실행_요청(self, client: TestClient):
        response = client.post(
            "/api/v1/pipeline/run",
            json={
                "channel_id": "test-channel",
                "topic": "테스트 주제",
                "dry_run": True,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "pending"
        assert data["channel_id"] == "test-channel"
        assert data["topic"] == "테스트 주제"
        assert "run_id" in data

    def test_파이프라인_실행_필수_필드_누락(self, client: TestClient):
        response = client.post(
            "/api/v1/pipeline/run",
            json={"channel_id": "test-channel"},
        )
        assert response.status_code == 422


# ============================================
# Status API
# ============================================


class TestStatusAPI:
    """상태 조회 API 테스트."""

    def test_존재하지_않는_실행_404(self, client: TestClient):
        response = client.get("/api/v1/status/nonexistent-id")
        assert response.status_code == 404

    def test_실행_상태_조회(self, client: TestClient):
        # 실행 요청 먼저 생성
        run_response = client.post(
            "/api/v1/pipeline/run",
            json={
                "channel_id": "test-channel",
                "topic": "테스트",
                "dry_run": True,
            },
        )
        run_id = run_response.json()["run_id"]

        # 상태 조회
        response = client.get(f"/api/v1/status/{run_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["run_id"] == run_id
        assert data["status"] in ("pending", "running", "completed", "failed")
