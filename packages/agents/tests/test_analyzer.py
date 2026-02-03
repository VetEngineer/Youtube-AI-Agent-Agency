"""Analyzer 모듈 단위 테스트.

YouTubeAnalytics, ReportGenerator, AnalyzerAgent를
Mock을 사용하여 외부 의존성 없이 테스트합니다.
"""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage

from src.analyzer.agent import AnalyzerAgent
from src.analyzer.analytics import (
    YouTubeAnalytics,
    _parse_video_analytics,
)
from src.analyzer.report_gen import (
    ReportGenerator,
    _build_analytics_prompt,
    _parse_llm_response,
)
from src.shared.models import (
    AnalysisReport,
    ChannelAnalytics,
    VideoAnalytics,
)

# ============================================
# Fixtures
# ============================================


def _make_video_analytics(
    video_id: str = "test_video_1",
    views: int = 1000,
    likes: int = 50,
    comments: int = 10,
) -> VideoAnalytics:
    """테스트용 VideoAnalytics 인스턴스를 생성합니다."""
    return VideoAnalytics(
        video_id=video_id,
        views=views,
        likes=likes,
        comments=comments,
        watch_time_hours=5.0,
        average_view_duration_seconds=120.0,
        click_through_rate=0.05,
        collected_at=datetime(2025, 1, 1),
    )


def _make_channel_analytics(
    channel_id: str = "test_channel",
    video_count: int = 2,
) -> ChannelAnalytics:
    """테스트용 ChannelAnalytics 인스턴스를 생성합니다."""
    videos = [_make_video_analytics(f"video_{i}", views=1000 * (i + 1)) for i in range(video_count)]
    return ChannelAnalytics(
        channel_id=channel_id,
        subscriber_count=500,
        total_views=sum(v.views for v in videos),
        video_count=len(videos),
        recent_videos=videos,
    )


def _make_llm_response_json() -> str:
    """테스트용 LLM JSON 응답을 생성합니다."""
    return json.dumps(
        {
            "summary": "채널이 꾸준히 성장하고 있습니다.",
            "insights": [
                "조회수가 증가 추세입니다.",
                "평균 시청 시간이 업계 평균보다 높습니다.",
                "댓글 참여율이 우수합니다.",
            ],
            "recommended_topics": [
                "AI 트렌드 정리",
                "초보자를 위한 가이드",
                "업계 뉴스 분석",
            ],
        },
        ensure_ascii=False,
    )


@pytest.fixture()
def channel_analytics() -> ChannelAnalytics:
    return _make_channel_analytics()


@pytest.fixture()
def mock_llm() -> MagicMock:
    llm = MagicMock()
    llm.ainvoke = AsyncMock(
        return_value=AIMessage(content=_make_llm_response_json()),
    )
    return llm


# ============================================
# VideoAnalytics 모델 검증
# ============================================


class TestVideoAnalyticsModel:
    """VideoAnalytics 데이터 모델 테스트."""

    def test_기본값으로_생성된다(self) -> None:
        video = VideoAnalytics(video_id="v1")
        assert video.video_id == "v1"
        assert video.views == 0
        assert video.likes == 0
        assert video.comments == 0
        assert video.watch_time_hours == 0.0

    def test_모든_필드를_설정할_수_있다(self) -> None:
        video = _make_video_analytics(views=5000, likes=200, comments=30)
        assert video.views == 5000
        assert video.likes == 200
        assert video.comments == 30
        assert video.watch_time_hours == 5.0
        assert video.average_view_duration_seconds == 120.0


class TestChannelAnalyticsModel:
    """ChannelAnalytics 데이터 모델 테스트."""

    def test_기본값으로_생성된다(self) -> None:
        channel = ChannelAnalytics(channel_id="ch1")
        assert channel.channel_id == "ch1"
        assert channel.subscriber_count == 0
        assert channel.total_views == 0
        assert channel.recent_videos == []

    def test_recent_videos를_포함한다(self) -> None:
        analytics = _make_channel_analytics(video_count=3)
        assert len(analytics.recent_videos) == 3
        assert analytics.total_views == 1000 + 2000 + 3000


class TestAnalysisReportModel:
    """AnalysisReport 데이터 모델 테스트."""

    def test_기본값으로_생성된다(self) -> None:
        report = AnalysisReport(channel_id="ch1")
        assert report.channel_id == "ch1"
        assert report.summary == ""
        assert report.insights == []
        assert report.recommended_topics == []

    def test_모든_필드를_설정할_수_있다(self) -> None:
        report = AnalysisReport(
            channel_id="ch1",
            period="최근 30일",
            summary="성장 중",
            insights=["인사이트 1"],
            recommended_topics=["주제 1"],
        )
        assert report.period == "최근 30일"
        assert report.summary == "성장 중"
        assert len(report.insights) == 1
        assert len(report.recommended_topics) == 1


# ============================================
# _parse_video_analytics 헬퍼 함수 테스트
# ============================================


class TestParseVideoAnalytics:
    """_parse_video_analytics 유틸 함수 테스트."""

    def test_정상_데이터를_파싱한다(self) -> None:
        raw = {
            "views": 1500,
            "likes": 80,
            "comments": 15,
            "estimatedMinutesWatched": 300,
            "averageViewDuration": 180,
            "cardClickRate": 0.03,
        }
        result = _parse_video_analytics(raw, "v_test")
        assert result.video_id == "v_test"
        assert result.views == 1500
        assert result.likes == 80
        assert result.comments == 15
        assert result.watch_time_hours == 5.0
        assert result.average_view_duration_seconds == 180.0
        assert result.click_through_rate == pytest.approx(0.03)

    def test_빈_데이터에서_기본값을_반환한다(self) -> None:
        result = _parse_video_analytics({}, "v_empty")
        assert result.video_id == "v_empty"
        assert result.views == 0
        assert result.likes == 0
        assert result.watch_time_hours == 0.0


# ============================================
# YouTubeAnalytics 클래스 테스트
# ============================================


class TestYouTubeAnalytics:
    """YouTubeAnalytics 클래스 테스트."""

    def test_빈_client_id면_에러를_발생시킨다(self) -> None:
        with pytest.raises(ValueError, match="client_id"):
            YouTubeAnalytics(client_id="", client_secret="secret")

    def test_빈_client_secret이면_에러를_발생시킨다(self) -> None:
        with pytest.raises(ValueError, match="client_secret"):
            YouTubeAnalytics(client_id="id", client_secret="")

    def test_정상적으로_인스턴스를_생성한다(self) -> None:
        client = YouTubeAnalytics(client_id="test_id", client_secret="test_secret")
        assert client._client_id == "test_id"
        assert client._client_secret == "test_secret"

    async def test_빈_video_id면_에러를_발생시킨다(self) -> None:
        client = YouTubeAnalytics(client_id="id", client_secret="secret")
        with pytest.raises(ValueError, match="video_id"):
            await client.get_video_analytics("")

    async def test_빈_channel_id면_에러를_발생시킨다(self) -> None:
        client = YouTubeAnalytics(client_id="id", client_secret="secret")
        with pytest.raises(ValueError, match="channel_id"):
            await client.get_channel_analytics("")

    async def test_잘못된_days면_에러를_발생시킨다(self) -> None:
        client = YouTubeAnalytics(client_id="id", client_secret="secret")
        with pytest.raises(ValueError, match="days"):
            await client.get_channel_analytics("ch1", days=0)


# ============================================
# _parse_llm_response 테스트
# ============================================


class TestParseLLMResponse:
    """_parse_llm_response 유틸 함수 테스트."""

    def test_정상_JSON을_파싱한다(self) -> None:
        raw = _make_llm_response_json()
        result = _parse_llm_response(raw)
        assert result["summary"] == "채널이 꾸준히 성장하고 있습니다."
        assert len(result["insights"]) == 3
        assert len(result["recommended_topics"]) == 3

    def test_코드블록_감싼_JSON을_파싱한다(self) -> None:
        raw = f"```json\n{_make_llm_response_json()}\n```"
        result = _parse_llm_response(raw)
        assert "summary" in result
        assert len(result["insights"]) == 3

    def test_잘못된_JSON이면_기본값을_반환한다(self) -> None:
        result = _parse_llm_response("이건 JSON이 아닙니다")
        assert "summary" in result
        assert "insights" in result
        assert "recommended_topics" in result

    def test_빈_문자열이면_기본값을_반환한다(self) -> None:
        result = _parse_llm_response("")
        assert "summary" in result


# ============================================
# _build_analytics_prompt 테스트
# ============================================


class TestBuildAnalyticsPrompt:
    """_build_analytics_prompt 유틸 함수 테스트."""

    def test_브랜드명이_포함된다(self, channel_analytics: ChannelAnalytics) -> None:
        prompt = _build_analytics_prompt(channel_analytics, "테스트브랜드")
        assert "테스트브랜드" in prompt

    def test_채널_정보가_포함된다(self, channel_analytics: ChannelAnalytics) -> None:
        prompt = _build_analytics_prompt(channel_analytics, "브랜드")
        assert "test_channel" in prompt
        assert "500" in prompt  # subscriber_count

    def test_영상_데이터가_없으면_데이터_없음을_표시한다(self) -> None:
        empty_analytics = ChannelAnalytics(channel_id="empty_ch")
        prompt = _build_analytics_prompt(empty_analytics, "브랜드")
        assert "(데이터 없음)" in prompt


# ============================================
# ReportGenerator 클래스 테스트
# ============================================


class TestReportGenerator:
    """ReportGenerator 클래스 테스트."""

    def test_None_llm이면_에러를_발생시킨다(self) -> None:
        with pytest.raises(ValueError, match="llm"):
            ReportGenerator(llm=None)

    async def test_정상_리포트를_생성한다(
        self,
        mock_llm: MagicMock,
        channel_analytics: ChannelAnalytics,
    ) -> None:
        generator = ReportGenerator(llm=mock_llm)
        report = await generator.generate_report(channel_analytics, "테스트브랜드")

        assert isinstance(report, AnalysisReport)
        assert report.channel_id == "test_channel"
        assert report.summary == "채널이 꾸준히 성장하고 있습니다."
        assert len(report.insights) == 3
        assert len(report.recommended_topics) == 3
        mock_llm.ainvoke.assert_awaited_once()

    async def test_빈_brand_name이면_에러를_발생시킨다(
        self,
        mock_llm: MagicMock,
        channel_analytics: ChannelAnalytics,
    ) -> None:
        generator = ReportGenerator(llm=mock_llm)
        with pytest.raises(ValueError, match="brand_name"):
            await generator.generate_report(channel_analytics, "")

    async def test_LLM_실패시_기본_리포트를_반환한다(
        self,
        channel_analytics: ChannelAnalytics,
    ) -> None:
        failing_llm = MagicMock()
        failing_llm.ainvoke = AsyncMock(side_effect=RuntimeError("LLM 오류"))

        generator = ReportGenerator(llm=failing_llm)
        report = await generator.generate_report(channel_analytics, "브랜드")

        assert isinstance(report, AnalysisReport)
        assert report.channel_id == "test_channel"
        assert report.period == "분석 실패"

    async def test_잘못된_JSON_응답시_기본값_리포트를_반환한다(
        self,
        channel_analytics: ChannelAnalytics,
    ) -> None:
        bad_llm = MagicMock()
        bad_llm.ainvoke = AsyncMock(
            return_value=AIMessage(content="이건 JSON이 아닙니다"),
        )

        generator = ReportGenerator(llm=bad_llm)
        report = await generator.generate_report(channel_analytics, "브랜드")

        assert isinstance(report, AnalysisReport)
        assert report.channel_id == "test_channel"
        assert len(report.insights) >= 1


# ============================================
# AnalyzerAgent 클래스 테스트
# ============================================


class TestAnalyzerAgent:
    """AnalyzerAgent 클래스 테스트."""

    def test_None_analytics면_에러를_발생시킨다(self) -> None:
        mock_report_gen = MagicMock(spec=ReportGenerator)
        with pytest.raises(ValueError, match="analytics"):
            AnalyzerAgent(analytics=None, report_generator=mock_report_gen)

    def test_None_report_generator면_에러를_발생시킨다(self) -> None:
        mock_analytics = MagicMock(spec=YouTubeAnalytics)
        with pytest.raises(ValueError, match="report_generator"):
            AnalyzerAgent(analytics=mock_analytics, report_generator=None)

    async def test_정상_분석_파이프라인을_실행한다(self) -> None:
        channel_analytics = _make_channel_analytics()
        expected_report = AnalysisReport(
            channel_id="test_channel",
            period="최근 2개 영상 기준",
            summary="채널이 성장 중입니다.",
            insights=["인사이트 A", "인사이트 B"],
            recommended_topics=["주제 X", "주제 Y"],
        )

        mock_analytics = MagicMock(spec=YouTubeAnalytics)
        mock_analytics.get_channel_analytics = AsyncMock(
            return_value=channel_analytics,
        )

        mock_report_gen = MagicMock(spec=ReportGenerator)
        mock_report_gen.generate_report = AsyncMock(
            return_value=expected_report,
        )

        agent = AnalyzerAgent(
            analytics=mock_analytics,
            report_generator=mock_report_gen,
        )
        report = await agent.analyze("test_channel", "테스트브랜드")

        assert isinstance(report, AnalysisReport)
        assert report.channel_id == "test_channel"
        assert report.summary == "채널이 성장 중입니다."
        assert len(report.insights) == 2
        assert len(report.recommended_topics) == 2

        mock_analytics.get_channel_analytics.assert_awaited_once_with(
            channel_id="test_channel",
            days=30,
        )
        mock_report_gen.generate_report.assert_awaited_once_with(
            analytics=channel_analytics,
            brand_name="테스트브랜드",
        )

    async def test_빈_channel_id면_에러를_발생시킨다(self) -> None:
        mock_analytics = MagicMock(spec=YouTubeAnalytics)
        mock_report_gen = MagicMock(spec=ReportGenerator)

        agent = AnalyzerAgent(
            analytics=mock_analytics,
            report_generator=mock_report_gen,
        )
        with pytest.raises(ValueError, match="channel_id"):
            await agent.analyze("", "브랜드")

    async def test_빈_brand_name이면_에러를_발생시킨다(self) -> None:
        mock_analytics = MagicMock(spec=YouTubeAnalytics)
        mock_report_gen = MagicMock(spec=ReportGenerator)

        agent = AnalyzerAgent(
            analytics=mock_analytics,
            report_generator=mock_report_gen,
        )
        with pytest.raises(ValueError, match="brand_name"):
            await agent.analyze("channel_1", "")

    async def test_잘못된_days면_에러를_발생시킨다(self) -> None:
        mock_analytics = MagicMock(spec=YouTubeAnalytics)
        mock_report_gen = MagicMock(spec=ReportGenerator)

        agent = AnalyzerAgent(
            analytics=mock_analytics,
            report_generator=mock_report_gen,
        )
        with pytest.raises(ValueError, match="days"):
            await agent.analyze("ch1", "브랜드", days=-1)

    async def test_데이터_수집_실패시_RuntimeError를_발생시킨다(self) -> None:
        mock_analytics = MagicMock(spec=YouTubeAnalytics)
        mock_analytics.get_channel_analytics = AsyncMock(
            side_effect=RuntimeError("API 연결 실패"),
        )

        mock_report_gen = MagicMock(spec=ReportGenerator)
        agent = AnalyzerAgent(
            analytics=mock_analytics,
            report_generator=mock_report_gen,
        )

        with pytest.raises(RuntimeError, match="채널 데이터 수집에 실패"):
            await agent.analyze("ch1", "브랜드")

    async def test_리포트_생성_실패시_RuntimeError를_발생시킨다(self) -> None:
        mock_analytics = MagicMock(spec=YouTubeAnalytics)
        mock_analytics.get_channel_analytics = AsyncMock(
            return_value=_make_channel_analytics(),
        )

        mock_report_gen = MagicMock(spec=ReportGenerator)
        mock_report_gen.generate_report = AsyncMock(
            side_effect=RuntimeError("생성 실패"),
        )

        agent = AnalyzerAgent(
            analytics=mock_analytics,
            report_generator=mock_report_gen,
        )

        with pytest.raises(RuntimeError, match="리포트 생성에 실패"):
            await agent.analyze("ch1", "브랜드")

    async def test_custom_days로_분석한다(self) -> None:
        mock_analytics = MagicMock(spec=YouTubeAnalytics)
        mock_analytics.get_channel_analytics = AsyncMock(
            return_value=_make_channel_analytics(),
        )

        mock_report_gen = MagicMock(spec=ReportGenerator)
        mock_report_gen.generate_report = AsyncMock(
            return_value=AnalysisReport(channel_id="ch1"),
        )

        agent = AnalyzerAgent(
            analytics=mock_analytics,
            report_generator=mock_report_gen,
        )
        await agent.analyze("ch1", "브랜드", days=90)

        mock_analytics.get_channel_analytics.assert_awaited_once_with(
            channel_id="ch1",
            days=90,
        )
