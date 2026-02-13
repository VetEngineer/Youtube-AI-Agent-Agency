"""LLM 사용량 추적 시스템 테스트."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from src.cli import _log_usage_summary
from src.database.engine import init_db, set_session_factory
from src.database.models import UsageEventModel
from src.database.repositories import UsageRepository
from src.shared.llm_clients import (
    UsageCollector,
    UsageTrackingCallback,
    calculate_cost,
)

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
# UsageEventModel 테스트
# ============================================


class TestUsageEventModel:
    """사용량 이벤트 모델 테스트."""

    def test_to_dict(self):
        event = UsageEventModel(
            id="evt-1",
            run_id="run-1",
            agent="script_writer",
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            cost_usd=0.0105,
        )
        d = event.to_dict()
        assert d["id"] == "evt-1"
        assert d["run_id"] == "run-1"
        assert d["agent"] == "script_writer"
        assert d["provider"] == "anthropic"
        assert d["model"] == "claude-sonnet-4-20250514"
        assert d["prompt_tokens"] == 1000
        assert d["completion_tokens"] == 500
        assert d["total_tokens"] == 1500
        assert d["cost_usd"] == 0.0105


# ============================================
# calculate_cost 테스트
# ============================================


class TestCalculateCost:
    """비용 계산 테스트."""

    def test_openai_gpt4o(self):
        cost = calculate_cost("openai", "gpt-4o", prompt_tokens=1000, completion_tokens=500)
        expected = (1000 * 2.50 / 1_000_000) + (500 * 10.00 / 1_000_000)
        assert abs(cost - expected) < 1e-10

    def test_openai_gpt4o_mini(self):
        cost = calculate_cost("openai", "gpt-4o-mini", prompt_tokens=2000, completion_tokens=1000)
        expected = (2000 * 0.15 / 1_000_000) + (1000 * 0.60 / 1_000_000)
        assert abs(cost - expected) < 1e-10

    def test_anthropic_claude(self):
        cost = calculate_cost(
            "anthropic", "claude-sonnet-4-20250514", prompt_tokens=1000, completion_tokens=500
        )
        expected = (1000 * 3.00 / 1_000_000) + (500 * 15.00 / 1_000_000)
        assert abs(cost - expected) < 1e-10

    def test_알_수_없는_모델은_0(self):
        cost = calculate_cost("openai", "unknown-model", prompt_tokens=1000, completion_tokens=500)
        assert cost == 0.0

    def test_알_수_없는_프로바이더는_0(self):
        cost = calculate_cost("unknown", "gpt-4o", prompt_tokens=1000, completion_tokens=500)
        assert cost == 0.0

    def test_토큰_0이면_비용_0(self):
        cost = calculate_cost("openai", "gpt-4o", prompt_tokens=0, completion_tokens=0)
        assert cost == 0.0


# ============================================
# UsageCollector 테스트
# ============================================


class TestUsageCollector:
    """사용량 수집기 테스트."""

    def test_초기_상태(self):
        collector = UsageCollector()
        assert collector.events == []

    def test_초기_failed_count(self):
        collector = UsageCollector()
        assert collector.failed_count == 0

    def test_create_callback(self):
        collector = UsageCollector()
        cb = collector.create_callback("script_writer", "anthropic")
        assert isinstance(cb, UsageTrackingCallback)
        assert cb.agent == "script_writer"
        assert cb.provider == "anthropic"
        assert cb.collector is collector

    def test_다수_콜백에서_이벤트_누적(self):
        collector = UsageCollector()
        cb1 = collector.create_callback("brand_researcher", "openai")
        cb2 = collector.create_callback("script_writer", "anthropic")

        response1 = MagicMock()
        response1.llm_output = {
            "token_usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
            "model_name": "gpt-4o",
        }

        response2 = MagicMock()
        response2.llm_output = {
            "token_usage": {
                "prompt_tokens": 200,
                "completion_tokens": 100,
                "total_tokens": 300,
            },
            "model_name": "claude-sonnet-4-20250514",
        }

        cb1.on_llm_end(response1)
        cb2.on_llm_end(response2)

        assert len(collector.events) == 2
        assert collector.events[0]["agent"] == "brand_researcher"
        assert collector.events[0]["provider"] == "openai"
        assert collector.events[1]["agent"] == "script_writer"
        assert collector.events[1]["provider"] == "anthropic"


# ============================================
# UsageTrackingCallback 테스트
# ============================================


class TestUsageTrackingCallback:
    """사용량 추적 콜백 테스트."""

    def test_on_llm_end_openai_형식(self):
        collector = UsageCollector()
        cb = collector.create_callback("seo_optimizer", "openai")

        response = MagicMock()
        response.llm_output = {
            "token_usage": {
                "prompt_tokens": 500,
                "completion_tokens": 200,
                "total_tokens": 700,
            },
            "model_name": "gpt-4o",
        }

        cb.on_llm_end(response)

        assert len(collector.events) == 1
        event = collector.events[0]
        assert event["agent"] == "seo_optimizer"
        assert event["provider"] == "openai"
        assert event["model"] == "gpt-4o"
        assert event["prompt_tokens"] == 500
        assert event["completion_tokens"] == 200
        assert event["total_tokens"] == 700
        assert event["cost_usd"] > 0

    def test_on_llm_end_anthropic_형식(self):
        collector = UsageCollector()
        cb = collector.create_callback("script_writer", "anthropic")

        response = MagicMock()
        response.llm_output = {
            "usage": {
                "prompt_tokens": 1000,
                "completion_tokens": 500,
                "total_tokens": 1500,
            },
            "model": "claude-sonnet-4-20250514",
        }

        cb.on_llm_end(response)

        assert len(collector.events) == 1
        event = collector.events[0]
        assert event["model"] == "claude-sonnet-4-20250514"
        assert event["prompt_tokens"] == 1000
        assert event["completion_tokens"] == 500

    def test_on_llm_end_llm_output이_None이면_에러_안남(self):
        collector = UsageCollector()
        cb = collector.create_callback("test", "openai")

        response = MagicMock()
        response.llm_output = None

        cb.on_llm_end(response)

        assert len(collector.events) == 1
        event = collector.events[0]
        assert event["prompt_tokens"] == 0
        assert event["completion_tokens"] == 0

    def test_on_llm_end_예외_시_failed_count_증가(self):
        collector = UsageCollector()
        cb = collector.create_callback("test", "openai")

        response = MagicMock()
        # llm_output.get()이 예외를 발생시키도록 설정
        response.llm_output = MagicMock()
        response.llm_output.get = MagicMock(side_effect=RuntimeError("test error"))

        cb.on_llm_end(response)

        assert len(collector.events) == 0
        assert collector.failed_count == 1

    def test_on_llm_end_total_tokens_자동_계산(self):
        collector = UsageCollector()
        cb = collector.create_callback("test", "openai")

        response = MagicMock()
        response.llm_output = {
            "token_usage": {
                "prompt_tokens": 300,
                "completion_tokens": 100,
            },
            "model_name": "gpt-4o",
        }

        cb.on_llm_end(response)

        event = collector.events[0]
        assert event["total_tokens"] == 400


# ============================================
# _log_usage_summary 테스트
# ============================================


class TestLogUsageSummary:
    """CLI 사용량 로그 출력 테스트."""

    def test_이벤트_없으면_로그_안남(self, caplog):
        collector = UsageCollector()
        with caplog.at_level(logging.INFO, logger="src.cli"):
            _log_usage_summary(collector)
        assert "LLM 사용량" not in caplog.text

    def test_실패_있으면_경고_로그(self, caplog):
        collector = UsageCollector()
        collector.failed_count = 3
        collector.events.append(
            {
                "agent": "test",
                "provider": "openai",
                "model": "gpt-4o",
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
                "cost_usd": 0.001,
            }
        )
        with caplog.at_level(logging.WARNING, logger="src.cli"):
            _log_usage_summary(collector)
        assert "사용량 추적 실패" in caplog.text
        assert "3건" in caplog.text

    def test_이벤트_있으면_요약_로그(self, caplog):
        collector = UsageCollector()
        collector.events.append(
            {
                "agent": "brand_researcher",
                "provider": "openai",
                "model": "gpt-4o",
                "prompt_tokens": 500,
                "completion_tokens": 200,
                "total_tokens": 700,
                "cost_usd": 0.0033,
            }
        )
        collector.events.append(
            {
                "agent": "script_writer",
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "prompt_tokens": 1000,
                "completion_tokens": 500,
                "total_tokens": 1500,
                "cost_usd": 0.0105,
            }
        )
        with caplog.at_level(logging.INFO, logger="src.cli"):
            _log_usage_summary(collector)
        assert "LLM 사용량" in caplog.text
        assert "calls=2" in caplog.text
        assert "tokens=2200" in caplog.text


# ============================================
# UsageRepository 테스트
# ============================================


class TestUsageRepository:
    """사용량 저장소 테스트."""

    async def test_create(self, session):
        repo = UsageRepository(session)
        event = await repo.create(
            event_id="evt-1",
            run_id="run-1",
            agent="script_writer",
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            cost_usd=0.0105,
        )
        assert event.id == "evt-1"
        assert event.run_id == "run-1"

    async def test_list_by_run(self, session):
        repo = UsageRepository(session)
        await repo.create(
            event_id="e-1",
            run_id="run-a",
            agent="brand_researcher",
            provider="openai",
            model="gpt-4o",
            cost_usd=0.001,
        )
        await repo.create(
            event_id="e-2",
            run_id="run-a",
            agent="script_writer",
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            cost_usd=0.002,
        )
        await repo.create(
            event_id="e-3",
            run_id="run-b",
            agent="seo_optimizer",
            provider="openai",
            model="gpt-4o",
            cost_usd=0.003,
        )
        await session.flush()

        results = await repo.list_by_run("run-a")
        assert len(results) == 2
        assert all(r.run_id == "run-a" for r in results)

    async def test_list_with_filters(self, session):
        repo = UsageRepository(session)
        await repo.create(
            event_id="f-1",
            run_id="run-1",
            agent="brand_researcher",
            provider="openai",
            model="gpt-4o",
        )
        await repo.create(
            event_id="f-2",
            run_id="run-1",
            agent="script_writer",
            provider="anthropic",
            model="claude-sonnet-4-20250514",
        )
        await repo.create(
            event_id="f-3",
            run_id="run-2",
            agent="seo_optimizer",
            provider="openai",
            model="gpt-4o",
        )
        await session.flush()

        # agent 필터
        results = await repo.list_with_filters(agent="brand_researcher")
        assert len(results) == 1

        # provider 필터
        results = await repo.list_with_filters(provider="openai")
        assert len(results) == 2

        # run_id 필터
        results = await repo.list_with_filters(run_id="run-1")
        assert len(results) == 2

    async def test_count_with_filters(self, session):
        repo = UsageRepository(session)
        await repo.create(
            event_id="c-1",
            run_id="run-x",
            agent="brand_researcher",
            provider="openai",
            model="gpt-4o",
        )
        await repo.create(
            event_id="c-2",
            run_id="run-x",
            agent="script_writer",
            provider="anthropic",
            model="claude-sonnet-4-20250514",
        )
        await session.flush()

        count = await repo.count_with_filters(run_id="run-x")
        assert count == 2

        count = await repo.count_with_filters(provider="openai")
        assert count == 1

    async def test_get_summary(self, session):
        repo = UsageRepository(session)
        await repo.create(
            event_id="s-1",
            run_id="run-s",
            agent="brand_researcher",
            provider="openai",
            model="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            cost_usd=0.0075,
        )
        await repo.create(
            event_id="s-2",
            run_id="run-s",
            agent="script_writer",
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            prompt_tokens=2000,
            completion_tokens=1000,
            total_tokens=3000,
            cost_usd=0.021,
        )
        await session.flush()

        summary = await repo.get_summary()
        assert abs(summary["total_cost_usd"] - 0.0285) < 1e-6
        assert summary["total_tokens"] == 4500
        assert "brand_researcher" in summary["by_agent"]
        assert "script_writer" in summary["by_agent"]
        assert "openai" in summary["by_provider"]
        assert "anthropic" in summary["by_provider"]
        assert "gpt-4o" in summary["by_model"]
        assert "claude-sonnet-4-20250514" in summary["by_model"]

    async def test_get_summary_run_id_필터(self, session):
        repo = UsageRepository(session)
        await repo.create(
            event_id="sf-1",
            run_id="run-1",
            agent="brand_researcher",
            provider="openai",
            model="gpt-4o",
            cost_usd=0.01,
            total_tokens=100,
        )
        await repo.create(
            event_id="sf-2",
            run_id="run-2",
            agent="script_writer",
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            cost_usd=0.02,
            total_tokens=200,
        )
        await session.flush()

        summary = await repo.get_summary(run_id="run-1")
        assert abs(summary["total_cost_usd"] - 0.01) < 1e-6
        assert summary["total_tokens"] == 100

    async def test_get_total_cost(self, session):
        repo = UsageRepository(session)
        await repo.create(
            event_id="tc-1",
            run_id="run-tc",
            agent="brand_researcher",
            provider="openai",
            model="gpt-4o",
            cost_usd=0.005,
        )
        await repo.create(
            event_id="tc-2",
            run_id="run-tc",
            agent="script_writer",
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            cost_usd=0.015,
        )
        await session.flush()

        total = await repo.get_total_cost()
        assert abs(total - 0.02) < 1e-6

    async def test_get_total_cost_이벤트_없으면_0(self, session):
        repo = UsageRepository(session)
        total = await repo.get_total_cost()
        assert total == 0.0

    async def test_list_with_filters_페이지네이션(self, session):
        repo = UsageRepository(session)
        for i in range(5):
            await repo.create(
                event_id=f"pg-{i}",
                run_id="run-pg",
                agent="test_agent",
                provider="openai",
                model="gpt-4o",
            )
        await session.flush()

        page1 = await repo.list_with_filters(limit=2, offset=0)
        page2 = await repo.list_with_filters(limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id
