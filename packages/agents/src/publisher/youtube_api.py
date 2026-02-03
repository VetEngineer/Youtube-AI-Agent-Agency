"""YouTube Data API v3 연동 모듈.

YouTubeUploader 클래스를 통해 영상 업로드 및 메타데이터 관리를 수행합니다.
google-api-python-client는 optional dependency이므로, 미설치 시 명확한 에러를 출력합니다.
"""

from __future__ import annotations

import logging
import os
import stat
from pathlib import Path
from typing import Any

from src.shared.models import (
    ContentStatus,
    PublishRequest,
    PublishResult,
    VideoMetadata,
)

logger = logging.getLogger(__name__)

# Google API 클라이언트 optional import
_GOOGLE_API_AVAILABLE = False
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    _GOOGLE_API_AVAILABLE = True
except ImportError:
    pass

_YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload"]
_YOUTUBE_API_SERVICE = "youtube"
_YOUTUBE_API_VERSION = "v3"

_DEFAULT_CHUNK_SIZE_MB = 10
_BYTES_PER_MB = 1024 * 1024

_TOKEN_FILE = "youtube_token.json"


class YouTubeAPIError(Exception):
    """YouTube API 호출 중 발생하는 에러."""


class QuotaExceededError(YouTubeAPIError):
    """YouTube API 할당량 초과 에러."""


class AuthenticationError(YouTubeAPIError):
    """OAuth2 인증 실패 에러."""


def _require_google_api() -> None:
    """Google API 클라이언트가 설치되어 있는지 확인합니다."""
    if not _GOOGLE_API_AVAILABLE:
        raise ImportError(
            "google-api-python-client 패키지가 필요합니다. "
            "설치하려면: pip install 'youtube-ai-agents[publisher]' "
            "또는: pip install google-api-python-client google-auth-oauthlib"
        )


class YouTubeUploader:
    """YouTube Data API v3를 통한 영상 업로드 클라이언트.

    OAuth2 인증 흐름을 사용하며, 대용량 영상은 청크 업로드를 지원합니다.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_path: str = _TOKEN_FILE,
        chunk_size_mb: int = _DEFAULT_CHUNK_SIZE_MB,
    ) -> None:
        if not client_id:
            raise ValueError("client_id는 필수입니다")
        if not client_secret:
            raise ValueError("client_secret는 필수입니다")

        self._client_id = client_id
        self._client_secret = client_secret
        self._token_path = Path(token_path)
        self._chunk_size = chunk_size_mb * _BYTES_PER_MB

    async def upload(self, request: PublishRequest) -> PublishResult:
        """영상을 YouTube에 업로드합니다.

        Args:
            request: 업로드 요청 (영상 경로, 메타데이터, 공개 설정 등)

        Returns:
            업로드 결과 (video_id, URL, 상태)

        Raises:
            FileNotFoundError: 영상 파일이 존재하지 않을 때
            ImportError: google-api-python-client 미설치
            QuotaExceededError: API 할당량 초과
            AuthenticationError: 인증 실패
        """
        _require_google_api()
        self._validate_video_file(request.video_path)

        try:
            service = self._build_service()
            body = self._build_upload_body(request)
            media = self._create_media_upload(request.video_path)

            insert_request = service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )

            response = self._execute_upload(insert_request)
            video_id = response.get("id", "")

            logger.info("영상 업로드 완료: video_id=%s", video_id)

            return PublishResult(
                video_id=video_id,
                video_url=f"https://www.youtube.com/watch?v={video_id}",
                status=ContentStatus.PUBLISHED,
            )

        except ImportError:
            raise
        except Exception as error:
            return self._handle_upload_error(error)

    async def update_metadata(
        self,
        video_id: str,
        metadata: VideoMetadata,
    ) -> PublishResult:
        """업로드된 영상의 메타데이터를 업데이트합니다.

        Args:
            video_id: YouTube 영상 ID
            metadata: 업데이트할 메타데이터

        Returns:
            업데이트 결과

        Raises:
            ImportError: google-api-python-client 미설치
        """
        _require_google_api()

        if not video_id:
            raise ValueError("video_id는 필수입니다")

        try:
            service = self._build_service()
            body = self._build_metadata_body(video_id, metadata)

            service.videos().update(
                part="snippet",
                body=body,
            ).execute()

            logger.info("메타데이터 업데이트 완료: video_id=%s", video_id)

            return PublishResult(
                video_id=video_id,
                video_url=f"https://www.youtube.com/watch?v={video_id}",
                status=ContentStatus.PUBLISHED,
            )

        except Exception as error:
            return self._handle_upload_error(error)

    def _validate_video_file(self, video_path: str) -> None:
        """영상 파일의 존재 여부를 확인합니다."""
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"영상 파일을 찾을 수 없습니다: {video_path}")
        if not path.is_file():
            raise FileNotFoundError(f"유효한 파일이 아닙니다: {video_path}")

    def _build_service(self) -> Any:
        """YouTube API 서비스 클라이언트를 생성합니다."""
        _require_google_api()
        credentials = self._get_credentials()
        return build(
            _YOUTUBE_API_SERVICE,
            _YOUTUBE_API_VERSION,
            credentials=credentials,
        )

    def _get_credentials(self) -> Any:
        """OAuth2 자격증명을 가져옵니다 (토큰 파일 기반)."""
        _require_google_api()

        if self._token_path.exists():
            credentials = Credentials.from_authorized_user_file(
                str(self._token_path),
                _YOUTUBE_UPLOAD_SCOPE,
            )
            if credentials and credentials.valid:
                return credentials

            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    from google.auth.transport.requests import Request

                    credentials.refresh(Request())
                    self._save_token(credentials)
                    return credentials
                except Exception as error:
                    logger.warning("토큰 갱신 실패, 재인증 필요: %s", error)

        return self._run_auth_flow()

    def _run_auth_flow(self) -> Any:
        """OAuth2 인증 흐름을 실행합니다."""
        _require_google_api()

        client_config = {
            "installed": {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

        try:
            flow = InstalledAppFlow.from_client_config(
                client_config,
                scopes=_YOUTUBE_UPLOAD_SCOPE,
            )
            credentials = flow.run_local_server(port=0)
            self._save_token(credentials)
            return credentials
        except Exception as error:
            raise AuthenticationError(f"OAuth2 인증에 실패했습니다: {error}") from error

    def _save_token(self, credentials: Any) -> None:
        """자격증명을 토큰 파일에 저장합니다 (권한 600)."""
        self._token_path.write_text(credentials.to_json(), encoding="utf-8")
        os.chmod(self._token_path, stat.S_IRUSR | stat.S_IWUSR)
        logger.info("토큰 저장 완료 (권한 600): %s", self._token_path)

    def _create_media_upload(self, video_path: str) -> Any:
        """청크 업로드용 MediaFileUpload 객체를 생성합니다."""
        _require_google_api()
        return MediaFileUpload(
            video_path,
            chunksize=self._chunk_size,
            resumable=True,
        )

    def _build_upload_body(self, request: PublishRequest) -> dict[str, Any]:
        """업로드 API 요청 body를 생성합니다."""
        status: dict[str, Any] = {
            "privacyStatus": request.privacy_status,
        }
        if request.scheduled_at is not None:
            status["privacyStatus"] = "private"
            status["publishAt"] = request.scheduled_at.isoformat()

        return {
            "snippet": {
                "title": request.metadata.title,
                "description": request.metadata.description,
                "tags": list(request.metadata.tags),
                "categoryId": request.metadata.category_id,
                "defaultLanguage": request.metadata.language,
            },
            "status": status,
        }

    def _build_metadata_body(
        self,
        video_id: str,
        metadata: VideoMetadata,
    ) -> dict[str, Any]:
        """메타데이터 업데이트 API 요청 body를 생성합니다."""
        return {
            "id": video_id,
            "snippet": {
                "title": metadata.title,
                "description": metadata.description,
                "tags": list(metadata.tags),
                "categoryId": metadata.category_id,
                "defaultLanguage": metadata.language,
            },
        }

    def _execute_upload(self, request: Any) -> dict[str, Any]:
        """청크 업로드를 실행합니다."""
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                logger.info("업로드 진행률: %d%%", progress)
        return response

    def _handle_upload_error(self, error: Exception) -> PublishResult:
        """업로드 에러를 처리하고 실패 결과를 반환합니다."""
        error_message = str(error)

        if "quotaExceeded" in error_message or "quota" in error_message.lower():
            logger.error("YouTube API 할당량 초과: %s", error_message)
            raise QuotaExceededError(
                f"YouTube API 할당량이 초과되었습니다: {error_message}"
            ) from error

        if "unauthorized" in error_message.lower() or "401" in error_message:
            logger.error("인증 실패: %s", error_message)
            raise AuthenticationError(
                f"YouTube API 인증에 실패했습니다: {error_message}"
            ) from error

        logger.error("업로드 실패: %s", error_message)
        return PublishResult(
            status=ContentStatus.FAILED,
            error=f"업로드 실패: {error_message}",
        )
