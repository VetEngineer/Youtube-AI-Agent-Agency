"""YouTube Analytics API 연동 모듈.

YouTube Analytics API를 통해 채널/영상 성과 데이터를 수집합니다.
google-api-python-client는 optional dependency이므로,
import 실패 시 명확한 에러 메시지를 제공합니다.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from src.shared.models import ChannelAnalytics, VideoAnalytics

_MISSING_DEPENDENCY_MSG = (
    "YouTube Analytics API를 사용하려면 google-api-python-client가 필요합니다. "
    "다음 명령어로 설치하세요: pip install 'youtube-ai-agents[publisher]'"
)


def _ensure_google_api_available() -> None:
    """google-api-python-client가 설치되어 있는지 확인합니다."""
    try:
        import googleapiclient  # noqa: F401
    except ImportError as exc:
        raise ImportError(_MISSING_DEPENDENCY_MSG) from exc


def _parse_video_analytics(raw: dict[str, Any], video_id: str) -> VideoAnalytics:
    """API 응답 딕셔너리를 VideoAnalytics 모델로 변환합니다."""
    return VideoAnalytics(
        video_id=video_id,
        views=int(raw.get("views", 0)),
        likes=int(raw.get("likes", 0)),
        comments=int(raw.get("comments", 0)),
        watch_time_hours=float(raw.get("estimatedMinutesWatched", 0)) / 60.0,
        average_view_duration_seconds=float(raw.get("averageViewDuration", 0)),
        click_through_rate=float(raw.get("cardClickRate", 0)),
        collected_at=datetime.now(),
    )


class YouTubeAnalytics:
    """YouTube Analytics API 클라이언트.

    google-api-python-client를 통해 YouTube Analytics Data API에
    접근하여 채널 및 영상 성과 데이터를 수집합니다.

    NOTE: 실제 API 호출에는 OAuth2 인증이 필요합니다.
    이 클래스는 인터페이스 수준의 구현만 제공하며,
    실제 인증 플로우는 별도로 구현해야 합니다.
    """

    def __init__(self, client_id: str, client_secret: str) -> None:
        if not client_id:
            raise ValueError("client_id가 비어 있습니다.")
        if not client_secret:
            raise ValueError("client_secret이 비어 있습니다.")

        self._client_id = client_id
        self._client_secret = client_secret
        self._service: Any = None

    def _get_service(self) -> Any:
        """YouTube Analytics API 서비스 인스턴스를 반환합니다."""
        if self._service is not None:
            return self._service

        _ensure_google_api_available()

        from googleapiclient.discovery import build  # type: ignore[import-untyped]

        self._service = build("youtubeAnalytics", "v2")
        return self._service

    async def get_video_analytics(self, video_id: str) -> VideoAnalytics:
        """개별 영상의 성과 데이터를 조회합니다.

        Args:
            video_id: YouTube 영상 ID

        Returns:
            VideoAnalytics 데이터 모델

        Raises:
            ValueError: video_id가 비어 있는 경우
            ImportError: google-api-python-client가 설치되지 않은 경우
        """
        if not video_id:
            raise ValueError("video_id가 비어 있습니다.")

        _ensure_google_api_available()
        service = self._get_service()

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        try:
            response = (
                service.reports()
                .query(
                    ids="channel==MINE",
                    startDate=start_date,
                    endDate=end_date,
                    metrics="views,likes,comments,estimatedMinutesWatched,averageViewDuration",
                    filters=f"video=={video_id}",
                )
                .execute()
            )
        except Exception as err:
            raise RuntimeError(f"영상 분석 데이터 조회 실패 (video_id={video_id}): {err}") from err

        rows = response.get("rows", [])
        if not rows:
            return VideoAnalytics(video_id=video_id, collected_at=datetime.now())

        headers = [col["name"] for col in response.get("columnHeaders", [])]
        raw = dict(zip(headers, rows[0]))
        return _parse_video_analytics(raw, video_id)

    async def get_channel_analytics(
        self,
        channel_id: str,
        days: int = 30,
    ) -> ChannelAnalytics:
        """채널 전체의 성과 데이터를 조회합니다.

        Args:
            channel_id: YouTube 채널 ID
            days: 조회 기간 (일 단위, 기본 30일)

        Returns:
            ChannelAnalytics 데이터 모델

        Raises:
            ValueError: channel_id가 비어 있거나 days가 0 이하인 경우
            ImportError: google-api-python-client가 설치되지 않은 경우
        """
        if not channel_id:
            raise ValueError("channel_id가 비어 있습니다.")
        if days <= 0:
            raise ValueError("days는 1 이상이어야 합니다.")

        _ensure_google_api_available()
        service = self._get_service()

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        try:
            response = (
                service.reports()
                .query(
                    ids=f"channel=={channel_id}",
                    startDate=start_date,
                    endDate=end_date,
                    metrics="views,likes,comments,estimatedMinutesWatched,averageViewDuration",
                    dimensions="video",
                    sort="-views",
                    maxResults=10,
                )
                .execute()
            )
        except Exception as err:
            raise RuntimeError(
                f"채널 분석 데이터 조회 실패 (channel_id={channel_id}): {err}"
            ) from err

        headers = [col["name"] for col in response.get("columnHeaders", [])]
        rows = response.get("rows", [])

        recent_videos = [
            _parse_video_analytics(
                dict(zip(headers[1:], row[1:])),
                video_id=str(row[0]),
            )
            for row in rows
        ]

        total_views = sum(v.views for v in recent_videos)

        return ChannelAnalytics(
            channel_id=channel_id,
            total_views=total_views,
            video_count=len(recent_videos),
            recent_videos=recent_videos,
        )
