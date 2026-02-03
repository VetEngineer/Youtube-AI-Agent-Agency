"""Publisher 모듈 단위 테스트.

YouTube API 호출은 Mock으로 대체하여 외부 의존성 없이 테스트합니다.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.publisher.agent import (
    _SUPPORTED_VIDEO_EXTENSIONS,
    PublisherAgent,
    PublishValidationError,
)
from src.publisher.youtube_api import (
    AuthenticationError,
    QuotaExceededError,
    YouTubeAPIError,
    YouTubeUploader,
    _require_google_api,
)
from src.shared.models import (
    ContentStatus,
    PublishRequest,
    PublishResult,
    VideoMetadata,
)

# ============================================
# Fixtures
# ============================================


@pytest.fixture
def sample_metadata() -> VideoMetadata:
    """테스트용 VideoMetadata."""
    return VideoMetadata(
        title="테스트 영상 제목",
        description="테스트 영상 설명입니다.",
        tags=["테스트", "파이썬", "자동화"],
        category_id="22",
        language="ko",
    )


@pytest.fixture
def video_file(tmp_path: Path) -> Path:
    """테스트용 영상 파일 (빈 mp4)."""
    video = tmp_path / "test_video.mp4"
    video.write_bytes(b"\x00" * 1024)
    return video


@pytest.fixture
def sample_request(video_file: Path, sample_metadata: VideoMetadata) -> PublishRequest:
    """테스트용 PublishRequest."""
    return PublishRequest(
        video_path=str(video_file),
        metadata=sample_metadata,
        channel_id="test-channel",
        privacy_status="private",
    )


@pytest.fixture
def mock_uploader() -> MagicMock:
    """Mock YouTubeUploader."""
    uploader = MagicMock(spec=YouTubeUploader)
    uploader.upload = AsyncMock(
        return_value=PublishResult(
            video_id="abc123",
            video_url="https://www.youtube.com/watch?v=abc123",
            status=ContentStatus.PUBLISHED,
        )
    )
    uploader.update_metadata = AsyncMock(
        return_value=PublishResult(
            video_id="abc123",
            video_url="https://www.youtube.com/watch?v=abc123",
            status=ContentStatus.PUBLISHED,
        )
    )
    return uploader


@pytest.fixture
def agent(mock_uploader: MagicMock) -> PublisherAgent:
    """Mock uploader를 사용하는 PublisherAgent."""
    return PublisherAgent(uploader=mock_uploader)


# ============================================
# YouTubeUploader 테스트
# ============================================


class TestYouTubeUploader:
    """YouTubeUploader 단위 테스트."""

    def test_init_with_valid_credentials(self) -> None:
        """유효한 자격증명으로 초기화."""
        uploader = YouTubeUploader(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )
        assert uploader._client_id == "test-client-id"
        assert uploader._client_secret == "test-client-secret"

    def test_init_empty_client_id_raises(self) -> None:
        """빈 client_id로 초기화 시 ValueError."""
        with pytest.raises(ValueError, match="client_id는 필수"):
            YouTubeUploader(client_id="", client_secret="secret")

    def test_init_empty_client_secret_raises(self) -> None:
        """빈 client_secret으로 초기화 시 ValueError."""
        with pytest.raises(ValueError, match="client_secret는 필수"):
            YouTubeUploader(client_id="id", client_secret="")

    def test_custom_chunk_size(self) -> None:
        """커스텀 청크 사이즈 설정."""
        uploader = YouTubeUploader(
            client_id="id",
            client_secret="secret",
            chunk_size_mb=20,
        )
        assert uploader._chunk_size == 20 * 1024 * 1024

    def test_validate_video_file_not_found(self) -> None:
        """존재하지 않는 파일 경로 검증."""
        uploader = YouTubeUploader(client_id="id", client_secret="secret")
        with pytest.raises(FileNotFoundError, match="영상 파일을 찾을 수 없습니다"):
            uploader._validate_video_file("/nonexistent/video.mp4")

    def test_validate_video_file_is_directory(self, tmp_path: Path) -> None:
        """디렉토리 경로 검증."""
        uploader = YouTubeUploader(client_id="id", client_secret="secret")
        with pytest.raises(FileNotFoundError, match="유효한 파일이 아닙니다"):
            uploader._validate_video_file(str(tmp_path))

    def test_validate_video_file_exists(self, video_file: Path) -> None:
        """유효한 파일 검증 통과."""
        uploader = YouTubeUploader(client_id="id", client_secret="secret")
        uploader._validate_video_file(str(video_file))

    def test_build_upload_body(self, sample_request: PublishRequest) -> None:
        """업로드 body 빌드 검증."""
        uploader = YouTubeUploader(client_id="id", client_secret="secret")
        body = uploader._build_upload_body(sample_request)

        assert body["snippet"]["title"] == "테스트 영상 제목"
        assert body["snippet"]["description"] == "테스트 영상 설명입니다."
        assert body["snippet"]["tags"] == ["테스트", "파이썬", "자동화"]
        assert body["snippet"]["categoryId"] == "22"
        assert body["status"]["privacyStatus"] == "private"

    def test_build_upload_body_with_schedule(
        self,
        video_file: Path,
        sample_metadata: VideoMetadata,
    ) -> None:
        """예약 업로드 body 빌드 검증."""
        scheduled_time = datetime(2026, 3, 1, 12, 0, 0)
        request = PublishRequest(
            video_path=str(video_file),
            metadata=sample_metadata,
            channel_id="test-channel",
            privacy_status="public",
            scheduled_at=scheduled_time,
        )
        uploader = YouTubeUploader(client_id="id", client_secret="secret")
        body = uploader._build_upload_body(request)

        assert body["status"]["privacyStatus"] == "private"
        assert body["status"]["publishAt"] == scheduled_time.isoformat()

    def test_build_metadata_body(self, sample_metadata: VideoMetadata) -> None:
        """메타데이터 업데이트 body 빌드 검증."""
        uploader = YouTubeUploader(client_id="id", client_secret="secret")
        body = uploader._build_metadata_body("vid123", sample_metadata)

        assert body["id"] == "vid123"
        assert body["snippet"]["title"] == "테스트 영상 제목"

    def test_handle_upload_error_general(self) -> None:
        """일반 에러 처리 결과 검증."""
        uploader = YouTubeUploader(client_id="id", client_secret="secret")
        result = uploader._handle_upload_error(Exception("something went wrong"))

        assert result.status == ContentStatus.FAILED
        assert "something went wrong" in result.error

    def test_handle_upload_error_quota(self) -> None:
        """할당량 초과 에러 처리."""
        uploader = YouTubeUploader(client_id="id", client_secret="secret")
        with pytest.raises(QuotaExceededError, match="할당량"):
            uploader._handle_upload_error(Exception("quotaExceeded"))

    def test_handle_upload_error_auth(self) -> None:
        """인증 실패 에러 처리."""
        uploader = YouTubeUploader(client_id="id", client_secret="secret")
        with pytest.raises(AuthenticationError, match="인증"):
            uploader._handle_upload_error(Exception("401 unauthorized"))

    @pytest.mark.asyncio
    async def test_upload_requires_google_api(
        self,
        sample_request: PublishRequest,
    ) -> None:
        """Google API 미설치 시 ImportError."""
        uploader = YouTubeUploader(client_id="id", client_secret="secret")
        with patch(
            "src.publisher.youtube_api._GOOGLE_API_AVAILABLE",
            False,
        ):
            with pytest.raises(ImportError, match="google-api-python-client"):
                await uploader.upload(sample_request)

    @pytest.mark.asyncio
    async def test_update_metadata_requires_google_api(
        self,
        sample_metadata: VideoMetadata,
    ) -> None:
        """Google API 미설치 시 update_metadata도 ImportError."""
        uploader = YouTubeUploader(client_id="id", client_secret="secret")
        with patch(
            "src.publisher.youtube_api._GOOGLE_API_AVAILABLE",
            False,
        ):
            with pytest.raises(ImportError, match="google-api-python-client"):
                await uploader.update_metadata("vid123", sample_metadata)

    @pytest.mark.asyncio
    async def test_update_metadata_empty_video_id(
        self,
        sample_metadata: VideoMetadata,
    ) -> None:
        """빈 video_id로 update_metadata 호출 시 ValueError."""
        uploader = YouTubeUploader(client_id="id", client_secret="secret")
        with patch(
            "src.publisher.youtube_api._GOOGLE_API_AVAILABLE",
            True,
        ):
            with pytest.raises(ValueError, match="video_id는 필수"):
                await uploader.update_metadata("", sample_metadata)


class TestRequireGoogleApi:
    """_require_google_api 함수 테스트."""

    def test_raises_when_not_available(self) -> None:
        """Google API 미설치 시 ImportError."""
        with patch(
            "src.publisher.youtube_api._GOOGLE_API_AVAILABLE",
            False,
        ):
            with pytest.raises(ImportError, match="google-api-python-client"):
                _require_google_api()

    def test_passes_when_available(self) -> None:
        """Google API 설치 시 에러 없음."""
        with patch(
            "src.publisher.youtube_api._GOOGLE_API_AVAILABLE",
            True,
        ):
            _require_google_api()


class TestYouTubeAPIErrors:
    """YouTube API 에러 클래스 테스트."""

    def test_youtube_api_error_hierarchy(self) -> None:
        """에러 계층 구조 검증."""
        assert issubclass(QuotaExceededError, YouTubeAPIError)
        assert issubclass(AuthenticationError, YouTubeAPIError)

    def test_quota_error_message(self) -> None:
        """QuotaExceededError 메시지."""
        error = QuotaExceededError("할당량 초과")
        assert str(error) == "할당량 초과"

    def test_auth_error_message(self) -> None:
        """AuthenticationError 메시지."""
        error = AuthenticationError("인증 실패")
        assert str(error) == "인증 실패"


# ============================================
# PublisherAgent 테스트
# ============================================


class TestPublisherAgent:
    """PublisherAgent 단위 테스트."""

    def test_init_with_none_uploader_raises(self) -> None:
        """None uploader로 초기화 시 ValueError."""
        with pytest.raises(ValueError, match="uploader는 필수"):
            PublisherAgent(uploader=None)  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_publish_success(
        self,
        agent: PublisherAgent,
        sample_request: PublishRequest,
    ) -> None:
        """정상 업로드 성공."""
        result = await agent.publish(sample_request)

        assert result.status == ContentStatus.PUBLISHED
        assert result.video_id == "abc123"
        assert "youtube.com" in result.video_url

    @pytest.mark.asyncio
    async def test_publish_file_not_found(
        self,
        agent: PublisherAgent,
        sample_metadata: VideoMetadata,
    ) -> None:
        """존재하지 않는 파일로 업로드 시 실패 결과."""
        request = PublishRequest(
            video_path="/nonexistent/video.mp4",
            metadata=sample_metadata,
            channel_id="test-channel",
        )
        result = await agent.publish(request)

        assert result.status == ContentStatus.FAILED
        assert "찾을 수 없습니다" in result.error

    @pytest.mark.asyncio
    async def test_publish_empty_title(
        self,
        agent: PublisherAgent,
        video_file: Path,
    ) -> None:
        """빈 제목으로 업로드 시 실패 결과."""
        request = PublishRequest(
            video_path=str(video_file),
            metadata=VideoMetadata(title=""),
            channel_id="test-channel",
        )
        result = await agent.publish(request)

        assert result.status == ContentStatus.FAILED
        assert "제목은 필수" in result.error

    @pytest.mark.asyncio
    async def test_publish_title_too_long(
        self,
        agent: PublisherAgent,
        video_file: Path,
    ) -> None:
        """너무 긴 제목으로 업로드 시 실패 결과."""
        request = PublishRequest(
            video_path=str(video_file),
            metadata=VideoMetadata(title="A" * 101),
            channel_id="test-channel",
        )
        result = await agent.publish(request)

        assert result.status == ContentStatus.FAILED
        assert "제목이 너무 깁니다" in result.error

    @pytest.mark.asyncio
    async def test_publish_invalid_privacy_status(
        self,
        agent: PublisherAgent,
        video_file: Path,
        sample_metadata: VideoMetadata,
    ) -> None:
        """유효하지 않은 공개 설정으로 업로드 시 실패 결과."""
        request = PublishRequest(
            video_path=str(video_file),
            metadata=sample_metadata,
            channel_id="test-channel",
            privacy_status="invalid_status",
        )
        result = await agent.publish(request)

        assert result.status == ContentStatus.FAILED
        assert "유효하지 않은 공개 설정" in result.error

    @pytest.mark.asyncio
    async def test_publish_empty_channel_id(
        self,
        agent: PublisherAgent,
        video_file: Path,
        sample_metadata: VideoMetadata,
    ) -> None:
        """빈 channel_id로 업로드 시 실패 결과."""
        request = PublishRequest(
            video_path=str(video_file),
            metadata=sample_metadata,
            channel_id="",
        )
        result = await agent.publish(request)

        assert result.status == ContentStatus.FAILED
        assert "channel_id는 필수" in result.error

    @pytest.mark.asyncio
    async def test_publish_unsupported_format(
        self,
        agent: PublisherAgent,
        tmp_path: Path,
        sample_metadata: VideoMetadata,
    ) -> None:
        """지원하지 않는 파일 형식 업로드 시 실패 결과."""
        unsupported_file = tmp_path / "video.xyz"
        unsupported_file.write_bytes(b"\x00" * 100)

        request = PublishRequest(
            video_path=str(unsupported_file),
            metadata=sample_metadata,
            channel_id="test-channel",
        )
        result = await agent.publish(request)

        assert result.status == ContentStatus.FAILED
        assert "지원하지 않는 영상 형식" in result.error

    @pytest.mark.asyncio
    async def test_publish_upload_exception(
        self,
        mock_uploader: MagicMock,
        sample_request: PublishRequest,
    ) -> None:
        """업로드 중 예외 발생 시 실패 결과."""
        mock_uploader.upload = AsyncMock(side_effect=RuntimeError("네트워크 오류"))
        agent = PublisherAgent(uploader=mock_uploader)

        result = await agent.publish(sample_request)

        assert result.status == ContentStatus.FAILED
        assert "네트워크 오류" in result.error

    @pytest.mark.asyncio
    async def test_publish_with_schedule(
        self,
        agent: PublisherAgent,
        video_file: Path,
        sample_metadata: VideoMetadata,
    ) -> None:
        """예약 업로드 테스트."""
        request = PublishRequest(
            video_path=str(video_file),
            metadata=sample_metadata,
            channel_id="test-channel",
            privacy_status="private",
            scheduled_at=datetime(2026, 3, 1, 12, 0, 0),
        )
        result = await agent.publish(request)

        assert result.status == ContentStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_publish_public_privacy(
        self,
        agent: PublisherAgent,
        video_file: Path,
        sample_metadata: VideoMetadata,
    ) -> None:
        """공개 업로드 테스트."""
        request = PublishRequest(
            video_path=str(video_file),
            metadata=sample_metadata,
            channel_id="test-channel",
            privacy_status="public",
        )
        result = await agent.publish(request)

        assert result.status == ContentStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_publish_unlisted_privacy(
        self,
        agent: PublisherAgent,
        video_file: Path,
        sample_metadata: VideoMetadata,
    ) -> None:
        """미등록 업로드 테스트."""
        request = PublishRequest(
            video_path=str(video_file),
            metadata=sample_metadata,
            channel_id="test-channel",
            privacy_status="unlisted",
        )
        result = await agent.publish(request)

        assert result.status == ContentStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_publish_too_many_tags(
        self,
        agent: PublisherAgent,
        video_file: Path,
    ) -> None:
        """태그 수 초과 시 실패 결과."""
        metadata = VideoMetadata(
            title="테스트",
            tags=[f"tag{i}" for i in range(501)],
        )
        request = PublishRequest(
            video_path=str(video_file),
            metadata=metadata,
            channel_id="test-channel",
        )
        result = await agent.publish(request)

        assert result.status == ContentStatus.FAILED
        assert "태그가 너무 많습니다" in result.error

    @pytest.mark.asyncio
    async def test_publish_description_too_long(
        self,
        agent: PublisherAgent,
        video_file: Path,
    ) -> None:
        """설명 길이 초과 시 실패 결과."""
        metadata = VideoMetadata(
            title="테스트",
            description="A" * 5001,
        )
        request = PublishRequest(
            video_path=str(video_file),
            metadata=metadata,
            channel_id="test-channel",
        )
        result = await agent.publish(request)

        assert result.status == ContentStatus.FAILED
        assert "설명이 너무 깁니다" in result.error

    @pytest.mark.asyncio
    async def test_publish_uploader_file_not_found_exception(
        self,
        mock_uploader: MagicMock,
        sample_request: PublishRequest,
    ) -> None:
        """Uploader가 FileNotFoundError를 raise할 때."""
        mock_uploader.upload = AsyncMock(side_effect=FileNotFoundError("파일 없음"))
        agent = PublisherAgent(uploader=mock_uploader)

        result = await agent.publish(sample_request)

        assert result.status == ContentStatus.FAILED
        assert "파일을 찾을 수 없습니다" in result.error

    @pytest.mark.asyncio
    async def test_publish_calls_uploader_upload(
        self,
        agent: PublisherAgent,
        mock_uploader: MagicMock,
        sample_request: PublishRequest,
    ) -> None:
        """publish가 uploader.upload를 호출하는지 검증."""
        await agent.publish(sample_request)
        mock_uploader.upload.assert_awaited_once_with(sample_request)


class TestPublishValidationError:
    """PublishValidationError 테스트."""

    def test_is_value_error(self) -> None:
        """ValueError 하위 클래스인지 검증."""
        assert issubclass(PublishValidationError, ValueError)

    def test_error_message(self) -> None:
        """에러 메시지 검증."""
        error = PublishValidationError("검증 실패")
        assert str(error) == "검증 실패"


class TestSupportedExtensions:
    """지원되는 영상 확장자 테스트."""

    @pytest.mark.parametrize(
        "extension",
        [".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv", ".webm"],
    )
    def test_supported_extensions(self, extension: str) -> None:
        """모든 지원 확장자 확인."""
        assert extension in _SUPPORTED_VIDEO_EXTENSIONS

    @pytest.mark.parametrize(
        "extension",
        [".txt", ".pdf", ".jpg", ".png", ".doc"],
    )
    def test_unsupported_extensions(self, extension: str) -> None:
        """비지원 확장자 확인."""
        assert extension not in _SUPPORTED_VIDEO_EXTENSIONS
