"""Publisher Agent.

편집 완료된 영상과 메타데이터를 받아 YouTube에 업로드하는 에이전트입니다.
업로드 전 파일 유효성 검증, 업로드 후 결과 반환을 담당합니다.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.shared.models import (
    ContentStatus,
    PublishRequest,
    PublishResult,
)

from .youtube_api import YouTubeUploader

logger = logging.getLogger(__name__)

_SUPPORTED_VIDEO_EXTENSIONS = frozenset(
    {
        ".mp4",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".mkv",
        ".webm",
    }
)

_MAX_TITLE_LENGTH = 100
_MAX_DESCRIPTION_LENGTH = 5000
_MAX_TAGS_COUNT = 500


class PublishValidationError(ValueError):
    """업로드 요청 유효성 검증 실패."""


class PublisherAgent:
    """YouTube 업로드를 수행하는 Publisher Agent.

    YouTubeUploader를 통해 영상 업로드 및 메타데이터 관리를 수행합니다.
    """

    def __init__(self, uploader: YouTubeUploader) -> None:
        if uploader is None:
            raise ValueError("uploader는 필수입니다")
        self._uploader = uploader

    async def publish(self, request: PublishRequest) -> PublishResult:
        """영상을 YouTube에 업로드합니다.

        업로드 전 요청 유효성을 검증하고, YouTubeUploader를 통해 업로드합니다.

        Args:
            request: 업로드 요청 (영상 경로, 메타데이터, 공개 설정 등)

        Returns:
            업로드 결과 (video_id, URL, 상태)

        Raises:
            PublishValidationError: 요청 유효성 검증 실패
        """
        try:
            self._validate_request(request)
        except PublishValidationError as error:
            logger.error("업로드 요청 검증 실패: %s", error)
            return PublishResult(
                status=ContentStatus.FAILED,
                error=str(error),
            )

        logger.info(
            "영상 업로드 시작: channel=%s, title=%s",
            request.channel_id,
            request.metadata.title,
        )

        try:
            result = await self._uploader.upload(request)
            self._log_result(result)
            return result
        except FileNotFoundError as error:
            logger.error("영상 파일 없음: %s", error)
            return PublishResult(
                status=ContentStatus.FAILED,
                error=f"영상 파일을 찾을 수 없습니다: {error}",
            )
        except Exception as error:
            logger.error("업로드 중 예외 발생: %s", error)
            return PublishResult(
                status=ContentStatus.FAILED,
                error=f"업로드 실패: {error}",
            )

    def _validate_request(self, request: PublishRequest) -> None:
        """업로드 요청의 유효성을 검증합니다."""
        self._validate_video_path(request.video_path)
        self._validate_metadata(request)
        self._validate_privacy_status(request.privacy_status)

    def _validate_video_path(self, video_path: str) -> None:
        """영상 파일 경로를 검증합니다."""
        if not video_path:
            raise PublishValidationError("video_path는 필수입니다")

        path = Path(video_path)
        if not path.exists():
            raise PublishValidationError(f"영상 파일을 찾을 수 없습니다: {video_path}")
        if not path.is_file():
            raise PublishValidationError(f"유효한 파일이 아닙니다: {video_path}")

        extension = path.suffix.lower()
        if extension not in _SUPPORTED_VIDEO_EXTENSIONS:
            raise PublishValidationError(
                f"지원하지 않는 영상 형식입니다: {extension}. "
                f"지원 형식: {', '.join(sorted(_SUPPORTED_VIDEO_EXTENSIONS))}"
            )

    def _validate_metadata(self, request: PublishRequest) -> None:
        """메타데이터 유효성을 검증합니다."""
        metadata = request.metadata

        if not metadata.title:
            raise PublishValidationError("영상 제목은 필수입니다")

        if len(metadata.title) > _MAX_TITLE_LENGTH:
            raise PublishValidationError(
                f"영상 제목이 너무 깁니다: {len(metadata.title)}자 (최대 {_MAX_TITLE_LENGTH}자)"
            )

        if len(metadata.description) > _MAX_DESCRIPTION_LENGTH:
            raise PublishValidationError(
                f"설명이 너무 깁니다: {len(metadata.description)}자 "
                f"(최대 {_MAX_DESCRIPTION_LENGTH}자)"
            )

        if len(metadata.tags) > _MAX_TAGS_COUNT:
            raise PublishValidationError(
                f"태그가 너무 많습니다: {len(metadata.tags)}개 (최대 {_MAX_TAGS_COUNT}개)"
            )

        if not request.channel_id:
            raise PublishValidationError("channel_id는 필수입니다")

    def _validate_privacy_status(self, privacy_status: str) -> None:
        """공개 설정 유효성을 검증합니다."""
        valid_statuses = {"private", "public", "unlisted"}
        if privacy_status not in valid_statuses:
            raise PublishValidationError(
                f"유효하지 않은 공개 설정입니다: {privacy_status}. "
                f"허용 값: {', '.join(sorted(valid_statuses))}"
            )

    def _log_result(self, result: PublishResult) -> None:
        """업로드 결과를 로깅합니다."""
        if result.status == ContentStatus.PUBLISHED:
            logger.info(
                "업로드 성공: video_id=%s, url=%s",
                result.video_id,
                result.video_url,
            )
        else:
            logger.warning(
                "업로드 실패: error=%s",
                result.error,
            )
