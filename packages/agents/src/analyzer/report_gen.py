"""리포트 생성 모듈.

LLM을 활용하여 채널 분석 데이터를 기반으로
성과 요약, 인사이트, 추천 주제를 포함한 리포트를 생성합니다.
"""

from __future__ import annotations

import logging
from datetime import datetime

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.shared.llm_utils import parse_json_from_response
from src.shared.models import AnalysisReport, ChannelAnalytics, VideoAnalytics

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
당신은 YouTube 채널 분석 전문가입니다.
채널의 성과 데이터를 분석하여 인사이트를 도출하고, 다음 콘텐츠 주제를 추천합니다.

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.

{
  "summary": "채널 성과 요약 (2-3문장)",
  "insights": ["인사이트 1", "인사이트 2", "인사이트 3"],
  "recommended_topics": ["추천 주제 1", "추천 주제 2", "추천 주제 3"]
}
"""

_DEFAULT_SUMMARY = "분석 데이터가 부족하여 요약을 생성할 수 없습니다."
_DEFAULT_INSIGHTS = ["충분한 데이터가 수집되면 인사이트를 제공합니다."]
_DEFAULT_TOPICS = ["채널 소개 영상 제작을 권장합니다."]


def _format_video_stats(video: VideoAnalytics) -> str:
    """영상 통계를 읽기 쉬운 텍스트로 변환합니다."""
    return (
        f"- 영상 ID: {video.video_id} | "
        f"조회수: {video.views:,} | "
        f"좋아요: {video.likes:,} | "
        f"댓글: {video.comments:,} | "
        f"시청 시간: {video.watch_time_hours:.1f}시간 | "
        f"평균 시청 시간: {video.average_view_duration_seconds:.0f}초 | "
        f"CTR: {video.click_through_rate:.2%}"
    )


def _build_analytics_prompt(
    analytics: ChannelAnalytics,
    brand_name: str,
) -> str:
    """분석 데이터를 LLM 프롬프트로 변환합니다."""
    video_stats = "\n".join(_format_video_stats(v) for v in analytics.recent_videos)

    return (
        f"브랜드명: {brand_name}\n"
        f"채널 ID: {analytics.channel_id}\n"
        f"구독자 수: {analytics.subscriber_count:,}\n"
        f"총 조회수: {analytics.total_views:,}\n"
        f"영상 수: {analytics.video_count}\n\n"
        f"최근 영상 성과:\n{video_stats if video_stats else '(데이터 없음)'}\n\n"
        f"위 데이터를 기반으로 채널 성과를 분석하고, "
        f"인사이트와 다음 콘텐츠 주제를 추천해주세요."
    )


def _parse_llm_response(raw_text: str) -> dict:
    """LLM 응답에서 JSON을 파싱합니다. 실패 시 기본값을 반환합니다."""
    data = parse_json_from_response(raw_text)
    if not data:
        logger.warning("LLM 응답 JSON 파싱 실패, 기본값을 사용합니다: %s", raw_text[:200])
        return {
            "summary": _DEFAULT_SUMMARY,
            "insights": list(_DEFAULT_INSIGHTS),
            "recommended_topics": list(_DEFAULT_TOPICS),
        }
    return data


class ReportGenerator:
    """LLM 기반 분석 리포트 생성기.

    채널 분석 데이터를 LLM에 전달하여 성과 요약, 인사이트,
    추천 주제를 포함한 AnalysisReport를 생성합니다.
    """

    def __init__(self, llm: BaseChatModel) -> None:
        if llm is None:
            raise ValueError("llm 인스턴스가 필요합니다.")
        self._llm = llm

    async def generate_report(
        self,
        analytics: ChannelAnalytics,
        brand_name: str,
    ) -> AnalysisReport:
        """채널 분석 데이터를 기반으로 리포트를 생성합니다.

        Args:
            analytics: 채널 분석 데이터
            brand_name: 브랜드명

        Returns:
            AnalysisReport 데이터 모델

        Raises:
            ValueError: analytics 또는 brand_name이 유효하지 않은 경우
        """
        if not brand_name:
            raise ValueError("brand_name이 비어 있습니다.")

        user_prompt = _build_analytics_prompt(analytics, brand_name)

        try:
            response = await self._llm.ainvoke(
                [
                    SystemMessage(content=_SYSTEM_PROMPT),
                    HumanMessage(content=user_prompt),
                ]
            )
        except Exception as err:
            logger.error("LLM 호출 실패: %s", err)
            return self._build_fallback_report(analytics)

        parsed = _parse_llm_response(response.content)

        return AnalysisReport(
            channel_id=analytics.channel_id,
            period=f"최근 {len(analytics.recent_videos)}개 영상 기준",
            summary=str(parsed.get("summary", _DEFAULT_SUMMARY)),
            insights=list(parsed.get("insights", _DEFAULT_INSIGHTS)),
            recommended_topics=list(parsed.get("recommended_topics", _DEFAULT_TOPICS)),
            created_at=datetime.now(),
        )

    @staticmethod
    def _build_fallback_report(analytics: ChannelAnalytics) -> AnalysisReport:
        """LLM 호출 실패 시 기본 리포트를 생성합니다."""
        return AnalysisReport(
            channel_id=analytics.channel_id,
            period="분석 실패",
            summary=_DEFAULT_SUMMARY,
            insights=list(_DEFAULT_INSIGHTS),
            recommended_topics=list(_DEFAULT_TOPICS),
            created_at=datetime.now(),
        )
