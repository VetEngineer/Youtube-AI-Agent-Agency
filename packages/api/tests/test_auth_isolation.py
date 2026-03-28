"""멀티테넌트 보안 격리 테스트 (Phase 9-1)."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from yaa_app.api.auth import hash_api_key
from yaa_app.api.main import create_app
from yaa_core.database.engine import get_db_session, init_db, set_session_factory
from yaa_core.database.models import ApiKeyModel, PipelineRunModel, UsageEventModel, WorkspaceModel
from yaa_core.database.repositories import ApiKeyRepository
from yaa_core.shared.config import ChannelRegistry

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
    await factory.kw["bind"].dispose()
    set_session_factory(None)


@pytest.fixture()
def client_factory(_registry: ChannelRegistry, _db_session_factory):
    """API 키 헤더를 지원하는 TestClient 팩토리를 반환합니다."""
    from yaa_app.api.dependencies import get_channel_registry, get_settings
    from yaa_core.shared.config import AppSettings

    app = create_app()

    test_settings = AppSettings(
        disable_auth=False,
        database_url=TEST_DB_URL,
        channels_dir=str(_registry.channels_dir),
        api_key_header="X-API-Key",
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

    return app, _db_session_factory


async def _create_workspace_with_key(session_factory, name: str) -> tuple[str, str, str]:
    """워크스페이스와 API 키를 생성하고 (workspace_id, plaintext_key, key_id)를 반환합니다."""
    workspace_id = str(uuid.uuid4())
    key_id = str(uuid.uuid4())
    plaintext_key = f"yaa_test_{name}_{uuid.uuid4().hex[:8]}"
    key_hash = hash_api_key(plaintext_key)

    async with session_factory() as session:
        ws = WorkspaceModel(
            id=workspace_id,
            name=f"Workspace {name}",
            owner_id=str(uuid.uuid4()),
        )
        session.add(ws)

        api_key = ApiKeyModel(
            id=key_id,
            key_hash=key_hash,
            name=f"Key {name}",
            scopes_json='["read","write","admin"]',
            workspace_id=workspace_id,
        )
        session.add(api_key)
        await session.commit()

    return workspace_id, plaintext_key, key_id


async def _create_run(session_factory, workspace_id: str) -> str:
    """파이프라인 실행 레코드를 생성하고 run_id를 반환합니다."""
    run_id = str(uuid.uuid4())
    async with session_factory() as session:
        run = PipelineRunModel(
            id=run_id,
            channel_id="test-channel",
            topic="테스트 주제",
            workspace_id=workspace_id,
            status="completed",
        )
        session.add(run)
        await session.commit()
    return run_id


async def _create_usage_event(session_factory, run_id: str) -> str:
    """사용량 이벤트를 생성하고 event_id를 반환합니다."""
    event_id = str(uuid.uuid4())
    async with session_factory() as session:
        event = UsageEventModel(
            id=event_id,
            run_id=run_id,
            agent="script_writer",
            provider="anthropic",
            model="claude-3-5-sonnet",
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            cost_usd=0.005,
        )
        session.add(event)
        await session.commit()
    return event_id


class TestStatusEndpointIsolation:
    """GET /status/{run_id} 워크스페이스 격리 테스트."""

    async def test_wsA키로_wsB_run_조회시_404(self, client_factory, _db_session_factory):
        app, session_factory = client_factory

        ws_a_id, key_a, _ = await _create_workspace_with_key(session_factory, "A")
        ws_b_id, _, _ = await _create_workspace_with_key(session_factory, "B")
        run_b_id = await _create_run(session_factory, ws_b_id)

        with TestClient(app) as c:
            resp = c.get(f"/api/v1/status/{run_b_id}", headers={"X-API-Key": key_a})

        assert resp.status_code == 404

    async def test_wsA키로_wsA_run_조회시_200(self, client_factory, _db_session_factory):
        app, session_factory = client_factory

        ws_a_id, key_a, _ = await _create_workspace_with_key(session_factory, "A")
        run_a_id = await _create_run(session_factory, ws_a_id)

        with TestClient(app) as c:
            resp = c.get(f"/api/v1/status/{run_a_id}", headers={"X-API-Key": key_a})

        assert resp.status_code == 200
        assert resp.json()["run_id"] == run_a_id


class TestUsageEndpointIsolation:
    """GET /usage/events 워크스페이스 격리 테스트."""

    async def test_wsB키로_events_B만_반환(self, client_factory, _db_session_factory):
        app, session_factory = client_factory

        ws_a_id, key_a, _ = await _create_workspace_with_key(session_factory, "A")
        ws_b_id, key_b, _ = await _create_workspace_with_key(session_factory, "B")

        run_a_id = await _create_run(session_factory, ws_a_id)
        run_b_id = await _create_run(session_factory, ws_b_id)

        event_a_id = await _create_usage_event(session_factory, run_a_id)
        event_b_id = await _create_usage_event(session_factory, run_b_id)

        with TestClient(app) as c:
            resp = c.get("/api/v1/usage/events", headers={"X-API-Key": key_b})

        assert resp.status_code == 200
        data = resp.json()
        returned_ids = {e["id"] for e in data["events"]}
        assert event_b_id in returned_ids
        assert event_a_id not in returned_ids


class TestAdminKeyWorkspaceIsolation:
    """POST /admin/api-keys workspace_id 격리 테스트."""

    async def test_api_키_생성시_workspace_id_일치(self, client_factory, _db_session_factory):
        app, session_factory = client_factory

        ws_a_id, key_a, _ = await _create_workspace_with_key(session_factory, "A")

        with TestClient(app) as c:
            resp = c.post(
                "/api/v1/admin/api-keys",
                json={"name": "새 키", "scopes": ["read", "write"]},
                headers={"X-API-Key": key_a},
            )

        assert resp.status_code == 201
        created_key_id = resp.json()["key_id"]

        # DB에서 생성된 키의 workspace_id 확인
        async with session_factory() as session:
            repo = ApiKeyRepository(session)
            created = await repo.get_by_id(created_key_id)
        assert created is not None
        assert created.workspace_id == ws_a_id
