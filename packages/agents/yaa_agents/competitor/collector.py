"""경쟁 채널 데이터 수집 모듈.

YouTube Data API v3 (API Key 방식)을 사용하여 공개 채널 정보와
영상 데이터를 수집합니다. OAuth 불필요 - 공개 데이터만 수집.

Quota 최적화:
- channels.list + contentDetails → 업로드 플레이리스트 ID 획득 (1 unit)
- playlistItems.list → 최근 영상 ID 목록 (1 unit)
- videos.list → 영상 상세 정보 (1 unit)
- 채널당 총 ~3 units (search.list 방식의 1/33)
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

_MISSING_DEPENDENCY_MSG = (
    "YouTube Data API를 사용하려면 google-api-python-client가 필요합니다. "
    "다음 명령어로 설치하세요: pip install 'yaa-agents[publisher]'"
)


def _ensure_google_api_available() -> None:
    """google-api-python-client가 설치되어 있는지 확인합니다."""
    try:
        import googleapiclient  # noqa: F401
    except ImportError as exc:
        raise ImportError(_MISSING_DEPENDENCY_MSG) from exc


def _parse_iso8601_duration(duration: str) -> int:
    """ISO 8601 duration 문자열을 초로 변환합니다. (예: PT1H2M3S → 3723)"""
    if not duration:
        return 0
    pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.match(pattern, duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def _parse_published_at(published_at: str) -> datetime:
    """YouTube API의 publishedAt 문자열을 datetime으로 변환합니다."""
    # "2024-01-15T10:30:00Z" 형식
    return datetime.fromisoformat(published_at.replace("Z", "+00:00"))


class CompetitorCollector:
    """YouTube Data API v3를 통해 경쟁 채널 데이터를 수집합니다.

    API Key 방식으로 공개 채널/영상 데이터를 수집합니다.
    """

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("YouTube API Key가 비어 있습니다.")
        self._api_key = api_key
        self._service: Any = None

    def _get_service(self) -> Any:
        """YouTube Data API v3 서비스 인스턴스를 반환합니다."""
        if self._service is not None:
            return self._service

        _ensure_google_api_available()

        from googleapiclient.discovery import build  # type: ignore[import-untyped]

        self._service = build("youtube", "v3", developerKey=self._api_key)
        return self._service

    async def fetch_channel_info(self, youtube_channel_id: str) -> dict[str, Any]:
        """채널 기본 정보와 통계를 수집합니다.

        Args:
            youtube_channel_id: YouTube 채널 ID (UC로 시작)

        Returns:
            채널 정보 딕셔너리:
            {name, description, subscriber_count, video_count,
             thumbnail_url, uploads_playlist_id}

        Raises:
            ValueError: 채널 ID가 비어 있거나 채널을 찾을 수 없는 경우
            ImportError: google-api-python-client가 없는 경우
            RuntimeError: API 호출 실패 시
        """
        if not youtube_channel_id:
            raise ValueError("youtube_channel_id가 비어 있습니다.")

        _ensure_google_api_available()
        service = self._get_service()

        try:
            response = (
                service.channels()
                .list(
                    part="snippet,statistics,contentDetails",
                    id=youtube_channel_id,
                )
                .execute()
            )
        except Exception as err:
            raise RuntimeError(
                f"채널 정보 조회 실패 (channel_id={youtube_channel_id}): {err}"
            ) from err

        items = response.get("items", [])
        if not items:
            raise ValueError(f"채널을 찾을 수 없습니다: {youtube_channel_id}")

        item = items[0]
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})

        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
        )

        uploads_playlist_id = content_details.get("relatedPlaylists", {}).get("uploads", "")

        return {
            "name": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "subscriber_count": int(statistics.get("subscriberCount", 0)),
            "video_count": int(statistics.get("videoCount", 0)),
            "thumbnail_url": thumbnail_url,
            "uploads_playlist_id": uploads_playlist_id,
        }

    async def fetch_recent_videos(
        self,
        youtube_channel_id: str,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        """최근 업로드된 영상 목록을 수집합니다.

        Quota 최적화: playlistItems.list + videos.list 방식 사용
        (search.list 대비 1/100 quota 절약)

        Args:
            youtube_channel_id: YouTube 채널 ID
            max_results: 수집할 최대 영상 수 (기본 20)

        Returns:
            영상 정보 딕셔너리 목록:
            [{video_id, title, description, view_count, like_count,
              comment_count, published_at, tags, duration_seconds, thumbnail_url}]
        """
        if not youtube_channel_id:
            raise ValueError("youtube_channel_id가 비어 있습니다.")

        _ensure_google_api_available()
        service = self._get_service()

        # Step 1: 채널의 uploads 플레이리스트 ID 조회
        channel_info = await self.fetch_channel_info(youtube_channel_id)
        uploads_playlist_id = channel_info.get("uploads_playlist_id", "")

        if not uploads_playlist_id:
            return []

        # Step 2: 플레이리스트에서 최근 영상 ID 수집
        try:
            playlist_response = (
                service.playlistItems()
                .list(
                    part="contentDetails",
                    playlistId=uploads_playlist_id,
                    maxResults=min(max_results, 50),
                )
                .execute()
            )
        except Exception as err:
            raise RuntimeError(
                f"플레이리스트 조회 실패 (channel_id={youtube_channel_id}): {err}"
            ) from err

        video_ids = [
            item["contentDetails"]["videoId"]
            for item in playlist_response.get("items", [])
            if item.get("contentDetails", {}).get("videoId")
        ]

        if not video_ids:
            return []

        # Step 3: videos.list로 영상 상세 정보 수집
        try:
            videos_response = (
                service.videos()
                .list(
                    part="snippet,statistics,contentDetails",
                    id=",".join(video_ids),
                )
                .execute()
            )
        except Exception as err:
            raise RuntimeError(
                f"영상 상세 정보 조회 실패 (channel_id={youtube_channel_id}): {err}"
            ) from err

        results = []
        for item in videos_response.get("items", []):
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})

            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = (
                thumbnails.get("maxres", {}).get("url")
                or thumbnails.get("high", {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url")
            )

            published_at_str = snippet.get("publishedAt", "")
            published_at = (
                _parse_published_at(published_at_str) if published_at_str else datetime.utcnow()
            )

            duration_str = content_details.get("duration", "")
            duration_seconds = _parse_iso8601_duration(duration_str)

            results.append(
                {
                    "video_id": item.get("id", ""),
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "view_count": int(statistics.get("viewCount", 0)),
                    "like_count": int(statistics.get("likeCount", 0)),
                    "comment_count": int(statistics.get("commentCount", 0)),
                    "published_at": published_at,
                    "tags": snippet.get("tags", []),
                    "duration_seconds": duration_seconds,
                    "thumbnail_url": thumbnail_url,
                }
            )

        return results
