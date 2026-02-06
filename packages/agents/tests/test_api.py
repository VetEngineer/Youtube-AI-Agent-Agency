"""FastAPI API 서버 테스트."""

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
    """테스트용 채널 디렉토리를 생성합니다."""
    ch_dir = tmp_path / "channels"
    ch_dir.mkdir()

    # 템플릿 채널 생성
    template = ch_dir / "_template"
    template.mkdir()
    (template / "config.yaml").write_text(
        "channel:\n  name: template\n  category: general\n  language: ko\n",
        encoding="utf-8",
    )

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
async def _db_session_factory():
    """테스트용 인메모리 DB를 초기화합니다."""
    factory = await init_db(TEST_DB_URL)
    yield factory
    set_session_factory(None)


@pytest.fixture()
def client(_registry: ChannelRegistry, _db_session_factory) -> TestClient:
    """FastAPI TestClient를 생성합니다."""
    from src.api.dependencies import get_channel_registry, get_settings
    from src.shared.config import AppSettings

    app = create_app()

    # 의존성 오버라이드
    app.dependency_overrides[get_channel_registry] = lambda: _registry

    # 인증 비활성화 (테스트용)
    test_settings = AppSettings(
        disable_auth=True,
        database_url=TEST_DB_URL,
        channels_dir=str(_registry.channels_dir),
    )
    app.dependency_overrides[get_settings] = lambda: test_settings

    # DB 세션 오버라이드 (실제 get_db_session과 동일한 commit/rollback 패턴)
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


# ============================================
# Pipeline Runs List API
# ============================================


class TestPipelineRunsList:
    """파이프라인 실행 이력 조회 테스트."""

    def test_실행_목록_빈_결과(self, client: TestClient):
        response = client.get("/api/v1/pipeline/runs")
        assert response.status_code == 200
        data = response.json()
        assert data["runs"] == [] or isinstance(data["runs"], list)
        assert data["total"] >= 0

    def test_실행_목록_생성_후_조회(self, client: TestClient):
        client.post(
            "/api/v1/pipeline/run",
            json={"channel_id": "test-channel", "topic": "주제1", "dry_run": True},
        )
        client.post(
            "/api/v1/pipeline/run",
            json={"channel_id": "test-channel", "topic": "주제2", "dry_run": True},
        )

        response = client.get("/api/v1/pipeline/runs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2

    def test_실행_목록_채널_필터(self, client: TestClient):
        client.post(
            "/api/v1/pipeline/run",
            json={"channel_id": "test-channel", "topic": "필터 테스트", "dry_run": True},
        )

        response = client.get("/api/v1/pipeline/runs?channel_id=test-channel")
        assert response.status_code == 200
        data = response.json()
        for run in data["runs"]:
            assert run["channel_id"] == "test-channel"

    def test_실행_목록_페이지네이션(self, client: TestClient):
        response = client.get("/api/v1/pipeline/runs?limit=1&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 1
        assert data["offset"] == 0


# ============================================
# Channels CRUD API
# ============================================


class TestChannelsCRUD:
    """채널 CRUD 테스트."""

    def test_채널_생성_성공(self, client: TestClient):
        response = client.post(
            "/api/v1/channels/",
            json={
                "channel_id": "new-channel",
                "name": "새 채널",
                "category": "tech",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["channel_id"] == "new-channel"
        assert data["name"] == "새 채널"
        assert data["category"] == "tech"

    def test_채널_생성_중복_409(self, client: TestClient):
        client.post(
            "/api/v1/channels/",
            json={"channel_id": "dup-channel", "name": "중복", "category": "test"},
        )
        response = client.post(
            "/api/v1/channels/",
            json={"channel_id": "dup-channel", "name": "중복2", "category": "test"},
        )
        assert response.status_code == 409

    def test_채널_생성_잘못된_ID_422(self, client: TestClient):
        response = client.post(
            "/api/v1/channels/",
            json={"channel_id": "invalid id!", "name": "잘못된 ID", "category": "test"},
        )
        assert response.status_code == 422

    def test_채널_수정_성공(self, client: TestClient):
        response = client.patch(
            "/api/v1/channels/test-channel",
            json={"name": "수정된 채널"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "수정된 채널"

    def test_채널_수정_존재하지_않는_채널_404(self, client: TestClient):
        response = client.patch(
            "/api/v1/channels/nonexistent",
            json={"name": "업데이트"},
        )
        assert response.status_code == 404

    def test_채널_수정_빈_요청_400(self, client: TestClient):
        response = client.patch(
            "/api/v1/channels/test-channel",
            json={},
        )
        assert response.status_code == 400

    def test_채널_삭제_성공(self, client: TestClient):
        # 삭제용 채널 생성
        client.post(
            "/api/v1/channels/",
            json={"channel_id": "to-delete", "name": "삭제할 채널", "category": "test"},
        )

        response = client.delete("/api/v1/channels/to-delete")
        assert response.status_code == 200
        assert response.json()["channel_id"] == "to-delete"

        # 삭제 후 조회 시 404
        response = client.get("/api/v1/channels/to-delete")
        assert response.status_code == 404

    def test_채널_삭제_존재하지_않는_채널_404(self, client: TestClient):
        response = client.delete("/api/v1/channels/nonexistent")
        assert response.status_code == 404


# ============================================
# Dashboard API
# ============================================


class TestDashboardAPI:
    """대시보드 API 테스트."""

    def test_대시보드_요약_조회(self, client: TestClient):
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200

        data = response.json()
        assert "total_runs" in data
        assert "active_runs" in data
        assert "success_runs" in data
        assert "failed_runs" in data
        assert "recent_runs" in data
        assert isinstance(data["recent_runs"], list)

    def test_대시보드_요약_데이터_생성_후_조회(self, client: TestClient):
        # 파이프라인 실행 생성
        client.post(
            "/api/v1/pipeline/run",
            json={"channel_id": "test-channel", "topic": "대시보드 테스트", "dry_run": True},
        )

        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200

        data = response.json()
        assert data["total_runs"] >= 1
        assert len(data["recent_runs"]) >= 1

    def test_대시보드_요약_limit_파라미터(self, client: TestClient):
        response = client.get("/api/v1/dashboard/summary?limit=3")
        assert response.status_code == 200

        data = response.json()
        assert len(data["recent_runs"]) <= 3


# ============================================
# Pipeline Run Detail API
# ============================================


class TestPipelineRunDetail:
    """파이프라인 실행 상세 조회 테스트."""

    def test_실행_상세_조회(self, client: TestClient):
        # 실행 생성
        run_response = client.post(
            "/api/v1/pipeline/run",
            json={"channel_id": "test-channel", "topic": "상세 조회 테스트", "dry_run": True},
        )
        run_id = run_response.json()["run_id"]

        # 상세 조회
        response = client.get(f"/api/v1/pipeline/runs/{run_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["run_id"] == run_id
        assert data["channel_id"] == "test-channel"
        assert data["topic"] == "상세 조회 테스트"
        assert data["dry_run"] is True
        assert "status" in data
        assert "created_at" in data

    def test_존재하지_않는_실행_상세_404(self, client: TestClient):
        response = client.get("/api/v1/pipeline/runs/nonexistent-run-id")
        assert response.status_code == 404
