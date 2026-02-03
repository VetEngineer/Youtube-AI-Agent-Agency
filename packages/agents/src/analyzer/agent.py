"""Analyzer Agent.

YouTube 채널/영상 성과를 분석하고 LLM 기반 인사이트 리포트를 생성합니다.

입력: 채널 ID + 브랜드명
출력: AnalysisReport (성과 요약, 인사이트, 추천 주제)
"""

from __future__ import annotations

import logging

from src.shared.models import AnalysisReport

from .analytics import YouTubeAnalytics
from .report_gen import ReportGenerator

logger = logging.getLogger(__name__)


class AnalyzerAgent:
    """채널 분석 에이전트.

    YouTube Analytics API로 성과 데이터를 수집한 뒤,
    LLM을 활용하여 인사이트 분석 리포트를 생성합니다.
    """

    def __init__(
        self,
        analytics: YouTubeAnalytics,
        report_generator: ReportGenerator,
    ) -> None:
        if analytics is None:
            raise ValueError("analytics 인스턴스가 필요합니다.")
        if report_generator is None:
            raise ValueError("report_generator 인스턴스가 필요합니다.")

        self._analytics = analytics
        self._report_generator = report_generator

    async def analyze(
        self,
        channel_id: str,
        brand_name: str,
        days: int = 30,
    ) -> AnalysisReport:
        """채널 성과를 분석하고 리포트를 생성합니다.

        Args:
            channel_id: YouTube 채널 ID
            brand_name: 브랜드명
            days: 분석 기간 (일 단위, 기본 30일)

        Returns:
            AnalysisReport 데이터 모델

        Raises:
            ValueError: channel_id 또는 brand_name이 비어 있는 경우
            RuntimeError: 데이터 수집 또는 리포트 생성 중 오류 발생 시
        """
        if not channel_id:
            raise ValueError("channel_id가 비어 있습니다.")
        if not brand_name:
            raise ValueError("brand_name이 비어 있습니다.")
        if days <= 0:
            raise ValueError("days는 1 이상이어야 합니다.")

        try:
            channel_analytics = await self._analytics.get_channel_analytics(
                channel_id=channel_id,
                days=days,
            )
        except Exception as err:
            logger.error("채널 데이터 수집 실패 (channel_id=%s): %s", channel_id, err)
            raise RuntimeError(
                f"채널 데이터 수집에 실패했습니다 (channel_id={channel_id}): {err}"
            ) from err

        try:
            report = await self._report_generator.generate_report(
                analytics=channel_analytics,
                brand_name=brand_name,
            )
        except Exception as err:
            logger.error("리포트 생성 실패: %s", err)
            raise RuntimeError(f"리포트 생성에 실패했습니다: {err}") from err

        return report
