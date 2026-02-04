"""Admin API 엔드포인트 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.database.engine import get_db_session, init_db, set_session_factory
from src.shared.config import ChannelRegistry

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture()
def _channels_dir(tmp_path: Path) -> Path:
    channels = tmp_path / "channels"
    channels.mkdir()
    template = channels / "_template"
    template.mkdir()
    (template / "config.yaml").write_text(
        "channel:\n  name: template\n  category: general\n  language: ko\n",
        encoding="utf-8",
    )
    ch = channels / "test-channel"
    ch.mkdir()
    (ch / "config.yaml").write_text(
        "channel:\n  name: 테스트\n  category: pets\n  language: ko\n",
        encoding="utf-8",
    )
    return channels


@pytest.fixture()
def _registry(_channels_dir: Path) -> ChannelRegistry:
    return ChannelRegistry(channels_dir=_channels_dir)


@pytest.fixture()
async def _db_session_factory():
    factory = await init_db(TEST_DB_URL)
    yield factory
    set_session_factory(None)


@pytest.fixture()
def client(_registry: ChannelRegistry, _db_session_factory) -> TestClient:
    from src.api.dependencies import get_channel_registry, get_settings
    from src.shared.config import AppSettings

    app = create_app()

    test_settings = AppSettings(
        disable_auth=True,
        database_url=TEST_DB_URL,
        channels_dir=str(_registry.channels_dir),
    )
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_channel_registry] = lambda: _registry

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


# ============================================
# API 키 관리 테스트
# ============================================


class TestApiKeyManagement:
    """API 키 CRUD 테스트."""

    def test_키_생성_성공(self, client: TestClient):
        resp = client.post(
            "/api/v1/admin/api-keys",
            json={"name": "테스트 키", "scopes": ["read", "write"]},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["api_key"].startswith("yaa_")
        assert data["name"] == "테스트 키"
        assert data["scopes"] == ["read", "write"]
        assert data["key_id"]

    def test_키_생성_만료일_설정(self, client: TestClient):
        resp = client.post(
            "/api/v1/admin/api-keys",
            json={"name": "만료 키", "expires_days": 30},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["expires_at"] is not None

    def test_키_목록_조회(self, client: TestClient):
        client.post("/api/v1/admin/api-keys", json={"name": "키1"})
        client.post("/api/v1/admin/api-keys", json={"name": "키2"})

        resp = client.get("/api/v1/admin/api-keys")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        assert all("api_key" not in k for k in data["keys"])

    def test_키_비활성화_성공(self, client: TestClient):
        create_resp = client.post("/api/v1/admin/api-keys", json={"name": "삭제할 키"})
        key_id = create_resp.json()["key_id"]

        resp = client.delete(f"/api/v1/admin/api-keys/{key_id}")
        assert resp.status_code == 200
        assert resp.json()["key_id"] == key_id

    def test_존재하지_않는_키_비활성화_404(self, client: TestClient):
        resp = client.delete("/api/v1/admin/api-keys/nonexistent-id")
        assert resp.status_code == 404

    def test_이미_비활성화된_키_재비활성화_400(self, client: TestClient):
        create_resp = client.post("/api/v1/admin/api-keys", json={"name": "중복 비활성화"})
        key_id = create_resp.json()["key_id"]

        client.delete(f"/api/v1/admin/api-keys/{key_id}")
        resp = client.delete(f"/api/v1/admin/api-keys/{key_id}")
        assert resp.status_code == 400

    def test_비활성_키_포함_목록_조회(self, client: TestClient):
        create_resp = client.post("/api/v1/admin/api-keys", json={"name": "비활성화할 키"})
        key_id = create_resp.json()["key_id"]
        client.delete(f"/api/v1/admin/api-keys/{key_id}")

        resp_active = client.get("/api/v1/admin/api-keys")
        resp_all = client.get("/api/v1/admin/api-keys?include_inactive=true")

        assert resp_all.json()["total"] >= resp_active.json()["total"]


# ============================================
# 감사 로그 조회 테스트
# ============================================


class TestAuditLogsApi:
    """감사 로그 API 테스트."""

    def test_감사_로그_조회(self, client: TestClient, _db_session_factory):
        resp = client.get("/api/v1/admin/audit-logs")
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data
        assert "total" in data
        assert data["limit"] == 100
        assert data["offset"] == 0

    def test_감사_로그_페이지네이션(self, client: TestClient):
        resp = client.get("/api/v1/admin/audit-logs?limit=5&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit"] == 5

    def test_감사_로그_메서드_필터(self, client: TestClient):
        resp = client.get("/api/v1/admin/audit-logs?method=GET")
        assert resp.status_code == 200
