"""데이터베이스 모듈 테스트."""

from __future__ import annotations

import pytest

from src.database.engine import init_db, set_session_factory
from src.database.models import ApiKeyModel, PipelineRunModel
from src.database.repositories import ApiKeyRepository, AuditLogRepository, RunRepository

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture()
async def session_factory():
    """테스트용 인메모리 DB 세션 팩토리."""
    factory = await init_db(TEST_DB_URL)
    yield factory
    set_session_factory(None)


@pytest.fixture()
async def session(session_factory):
    """테스트용 DB 세션."""
    async with session_factory() as s:
        yield s


# ============================================
# PipelineRunModel 테스트
# ============================================


class TestPipelineRunModel:
    """파이프라인 실행 모델 테스트."""

    def test_result_프로퍼티_직렬화(self):
        run = PipelineRunModel(
            id="test-id",
            channel_id="ch-1",
            topic="테스트",
            status="pending",
        )
        assert run.result is None

        run.result = {"status": "ok", "count": 3}
        assert run.result == {"status": "ok", "count": 3}

    def test_errors_프로퍼티_직렬화(self):
        run = PipelineRunModel(
            id="test-id",
            channel_id="ch-1",
            topic="테스트",
            status="pending",
        )
        assert run.errors == []

        run.errors = ["에러1", "에러2"]
        assert run.errors == ["에러1", "에러2"]

    def test_to_dict(self):
        run = PipelineRunModel(
            id="test-id",
            channel_id="ch-1",
            topic="테스트",
            status="pending",
        )
        d = run.to_dict()
        assert d["run_id"] == "test-id"
        assert d["channel_id"] == "ch-1"
        assert d["status"] == "pending"


# ============================================
# ApiKeyModel 테스트
# ============================================


class TestApiKeyModel:
    """API 키 모델 테스트."""

    def test_scopes_프로퍼티(self):
        key = ApiKeyModel(
            id="key-1",
            key_hash="hash123",
            name="테스트 키",
            scopes_json='["read","write"]',
            is_active=True,
        )
        assert key.scopes == ["read", "write"]

        key.scopes = ["admin"]
        assert key.scopes == ["admin"]

    def test_to_dict(self):
        key = ApiKeyModel(
            id="key-1",
            key_hash="hash123",
            name="테스트 키",
            scopes_json='["read","write"]',
            is_active=True,
        )
        d = key.to_dict()
        assert d["id"] == "key-1"
        assert d["name"] == "테스트 키"
        assert d["is_active"] is True


# ============================================
# RunRepository 테스트
# ============================================


class TestRunRepository:
    """파이프라인 실행 저장소 테스트."""

    async def test_create_및_get(self, session):
        repo = RunRepository(session)
        run = await repo.create(
            run_id="run-1",
            channel_id="ch-1",
            topic="테스트 주제",
            brand_name="브랜드",
            dry_run=True,
        )
        assert run.id == "run-1"
        assert run.status == "pending"

        found = await repo.get("run-1")
        assert found is not None
        assert found.channel_id == "ch-1"
        assert found.topic == "테스트 주제"

    async def test_get_존재하지_않는_ID(self, session):
        repo = RunRepository(session)
        result = await repo.get("nonexistent")
        assert result is None

    async def test_update_status(self, session):
        repo = RunRepository(session)
        await repo.create(run_id="run-2", channel_id="ch-1", topic="테스트")

        await repo.update_status(
            "run-2",
            status="completed",
            result={"ok": True},
            errors=[],
        )
        await session.flush()

        run = await repo.get("run-2")
        assert run is not None
        assert run.status == "completed"
        assert run.result == {"ok": True}
        assert run.completed_at is not None

    async def test_update_status_failed(self, session):
        repo = RunRepository(session)
        await repo.create(run_id="run-3", channel_id="ch-1", topic="테스트")

        await repo.update_status("run-3", status="failed", errors=["에러 발생"])
        await session.flush()

        run = await repo.get("run-3")
        assert run is not None
        assert run.status == "failed"
        assert run.errors == ["에러 발생"]
        assert run.completed_at is not None

    async def test_list_by_channel(self, session):
        repo = RunRepository(session)
        await repo.create(run_id="r-a", channel_id="ch-1", topic="주제A")
        await repo.create(run_id="r-b", channel_id="ch-1", topic="주제B")
        await repo.create(run_id="r-c", channel_id="ch-2", topic="주제C")
        await session.flush()

        results = await repo.list_by_channel("ch-1")
        assert len(results) == 2

    async def test_list_recent(self, session):
        repo = RunRepository(session)
        await repo.create(run_id="r-1", channel_id="ch-1", topic="주제1")
        await repo.create(run_id="r-2", channel_id="ch-2", topic="주제2")
        await session.flush()

        results = await repo.list_recent(limit=10)
        assert len(results) == 2


# ============================================
# ApiKeyRepository 테스트
# ============================================


class TestApiKeyRepository:
    """API 키 저장소 테스트."""

    async def test_create_및_get_by_hash(self, session):
        repo = ApiKeyRepository(session)
        key = await repo.create(
            key_id="key-1",
            key_hash="hash_abc123",
            name="테스트 키",
            scopes=["read"],
        )
        assert key.name == "테스트 키"

        found = await repo.get_by_hash("hash_abc123")
        assert found is not None
        assert found.id == "key-1"

    async def test_get_by_hash_비활성_키(self, session):
        repo = ApiKeyRepository(session)
        await repo.create(
            key_id="key-2",
            key_hash="hash_inactive",
            name="비활성 키",
        )
        await repo.deactivate("key-2")
        await session.flush()

        found = await repo.get_by_hash("hash_inactive")
        assert found is None

    async def test_get_all_active(self, session):
        repo = ApiKeyRepository(session)
        await repo.create(key_id="k-1", key_hash="h1", name="키1")
        await repo.create(key_id="k-2", key_hash="h2", name="키2")
        await repo.create(key_id="k-3", key_hash="h3", name="키3")
        await repo.deactivate("k-2")
        await session.flush()

        active_keys = await repo.get_all_active()
        assert len(active_keys) == 2

    async def test_update_last_used(self, session):
        repo = ApiKeyRepository(session)
        await repo.create(key_id="k-use", key_hash="h-use", name="사용 키")
        await repo.update_last_used("k-use")
        await session.flush()


# ============================================
# AuditLogRepository 테스트
# ============================================


class TestAuditLogRepository:
    """감사 로그 저장소 테스트."""

    async def test_create(self, session):
        repo = AuditLogRepository(session)
        log = await repo.create(
            method="GET",
            path="/api/v1/channels/",
            status_code=200,
            ip_address="127.0.0.1",
            duration_ms=15.3,
        )
        assert log.method == "GET"
        assert log.path == "/api/v1/channels/"

    async def test_list_recent(self, session):
        repo = AuditLogRepository(session)
        await repo.create(method="GET", path="/a", status_code=200)
        await repo.create(method="POST", path="/b", status_code=201)
        await session.flush()

        logs = await repo.list_recent(limit=10)
        assert len(logs) == 2


# ============================================
# RunRepository 필터링 테스트
# ============================================


class TestRunRepositoryFilters:
    """RunRepository 필터링/페이지네이션 테스트."""

    async def test_list_with_filters_채널_필터(self, session):
        repo = RunRepository(session)
        await repo.create(run_id="f-1", channel_id="ch-a", topic="A")
        await repo.create(run_id="f-2", channel_id="ch-a", topic="B")
        await repo.create(run_id="f-3", channel_id="ch-b", topic="C")
        await session.flush()

        results = await repo.list_with_filters(channel_id="ch-a")
        assert len(results) == 2

    async def test_list_with_filters_상태_필터(self, session):
        repo = RunRepository(session)
        await repo.create(run_id="s-1", channel_id="ch-1", topic="A")
        await repo.create(run_id="s-2", channel_id="ch-1", topic="B")
        await repo.update_status("s-2", status="completed")
        await session.flush()

        results = await repo.list_with_filters(status="pending")
        assert all(r.status == "pending" for r in results)

    async def test_list_with_filters_페이지네이션(self, session):
        repo = RunRepository(session)
        for i in range(5):
            await repo.create(run_id=f"p-{i}", channel_id="ch-1", topic=f"T{i}")
        await session.flush()

        page1 = await repo.list_with_filters(limit=2, offset=0)
        page2 = await repo.list_with_filters(limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    async def test_count_with_filters(self, session):
        repo = RunRepository(session)
        await repo.create(run_id="c-1", channel_id="ch-x", topic="A")
        await repo.create(run_id="c-2", channel_id="ch-x", topic="B")
        await repo.create(run_id="c-3", channel_id="ch-y", topic="C")
        await session.flush()

        total = await repo.count_with_filters(channel_id="ch-x")
        assert total == 2

        total_all = await repo.count_with_filters()
        assert total_all >= 3


# ============================================
# ApiKeyRepository 확장 테스트
# ============================================


class TestApiKeyRepositoryExtended:
    """ApiKeyRepository 확장 메서드 테스트."""

    async def test_get_by_id(self, session):
        repo = ApiKeyRepository(session)
        await repo.create(key_id="ext-1", key_hash="h-ext-1", name="확장 키")
        await session.flush()

        found = await repo.get_by_id("ext-1")
        assert found is not None
        assert found.name == "확장 키"

    async def test_get_by_id_없는_키(self, session):
        repo = ApiKeyRepository(session)
        found = await repo.get_by_id("nonexistent")
        assert found is None

    async def test_get_all_비활성_포함(self, session):
        repo = ApiKeyRepository(session)
        await repo.create(key_id="ga-1", key_hash="ga-h1", name="활성")
        await repo.create(key_id="ga-2", key_hash="ga-h2", name="비활성")
        await repo.deactivate("ga-2")
        await session.flush()

        active_only = await repo.get_all(include_inactive=False)
        all_keys = await repo.get_all(include_inactive=True)
        assert len(all_keys) >= len(active_only)


# ============================================
# AuditLogRepository 필터링 테스트
# ============================================


class TestAuditLogRepositoryFilters:
    """AuditLogRepository 필터링 테스트."""

    async def test_list_with_filters_메서드_필터(self, session):
        repo = AuditLogRepository(session)
        await repo.create(method="GET", path="/a", status_code=200)
        await repo.create(method="POST", path="/b", status_code=201)
        await repo.create(method="GET", path="/c", status_code=200)
        await session.flush()

        results = await repo.list_with_filters(method="GET")
        assert all(r.method == "GET" for r in results)

    async def test_count_with_filters(self, session):
        repo = AuditLogRepository(session)
        await repo.create(method="GET", path="/x", status_code=200)
        await repo.create(method="POST", path="/y", status_code=201)
        await session.flush()

        total = await repo.count_with_filters(method="GET")
        assert total >= 1
