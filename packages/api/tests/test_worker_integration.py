"""워커 통합 테스트 - execute_pipeline_task → DB 상태 검증."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.integration
class TestWorkerPipelineIntegration:
    """execute_pipeline_task 직접 실행 → DB status 검증."""

    @pytest.fixture()
    async def session_factory(self):
        from yaa_core.database.engine import init_db, set_session_factory

        factory = await init_db("sqlite+aiosqlite:///:memory:")
        yield factory
        await factory.kw["bind"].dispose()
        set_session_factory(None)

    @pytest.fixture()
    async def run_id(self, session_factory):
        """테스트용 파이프라인 실행 레코드를 생성합니다."""
        from yaa_core.database.repositories import RunRepository

        async with session_factory() as session:
            repo = RunRepository(session)
            run = await repo.create(
                run_id="integration-run-001",
                channel_id="test-ch",
                topic="통합 테스트 주제",
                brand_name="테스트 브랜드",
                dry_run=True,
            )
            await session.commit()
            return run.id

    async def test_execute_pipeline_task_completes(self, session_factory, run_id):
        """execute_pipeline_task 실행 후 DB 상태가 completed로 변경됩니다."""
        from yaa_app.worker.tasks import execute_pipeline_task
        from yaa_core.database.engine import set_session_factory
        from yaa_core.database.repositories import RunRepository
        from yaa_core.shared.models import ContentStatus

        set_session_factory(session_factory)

        mock_final_state = {
            "status": ContentStatus.APPROVED,
            "errors": [],
        }
        mock_pipeline = AsyncMock()
        mock_pipeline.ainvoke = AsyncMock(return_value=mock_final_state)

        mock_registry = MagicMock()

        with (
            patch("yaa_app.worker.tasks._build_agent_registry", return_value=mock_registry),
            patch("yaa_app.worker.tasks.compile_pipeline", return_value=mock_pipeline),
        ):
            result = await execute_pipeline_task(
                ctx={},
                run_id=run_id,
                channel_id="test-ch",
                topic="통합 테스트 주제",
                brand_name="테스트 브랜드",
                dry_run=True,
            )

        assert result["status"] == "completed"
        assert result["run_id"] == run_id

        async with session_factory() as session:
            repo = RunRepository(session)
            run = await repo.get(run_id)
            assert run is not None
            assert run.status == "completed"

    async def test_execute_pipeline_task_failed(self, session_factory, run_id):
        """파이프라인 예외 발생 시 DB 상태가 failed로 변경됩니다."""
        from yaa_app.worker.tasks import execute_pipeline_task
        from yaa_core.database.engine import set_session_factory
        from yaa_core.database.repositories import RunRepository

        set_session_factory(session_factory)

        mock_pipeline = AsyncMock()
        mock_pipeline.ainvoke = AsyncMock(side_effect=RuntimeError("테스트 실패"))

        mock_registry = MagicMock()

        with (
            patch("yaa_app.worker.tasks._build_agent_registry", return_value=mock_registry),
            patch("yaa_app.worker.tasks.compile_pipeline", return_value=mock_pipeline),
        ):
            result = await execute_pipeline_task(
                ctx={},
                run_id=run_id,
                channel_id="test-ch",
                topic="통합 테스트 주제",
                brand_name="테스트 브랜드",
                dry_run=True,
            )

        assert result["status"] == "failed"
        assert result["run_id"] == run_id

        async with session_factory() as session:
            repo = RunRepository(session)
            run = await repo.get(run_id)
            assert run is not None
            assert run.status == "failed"
