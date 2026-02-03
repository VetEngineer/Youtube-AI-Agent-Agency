"""이미지 생성 모듈.

ImageGenerator ABC를 정의하고, Midjourney와 NanubananPro의 구체 구현을 제공합니다.
실제 API 연동은 추후 구현하며, 현재는 인터페이스와 기본 구조만 정의합니다.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from src.shared.models import ImageGenerationRequest, ImageGenerationResult

logger = logging.getLogger(__name__)


class ImageGeneratorError(Exception):
    """이미지 생성 중 발생하는 에러."""


class ImageGenerator(ABC):
    """이미지 생성기 추상 베이스 클래스.

    모든 이미지 생성 백엔드는 이 인터페이스를 구현해야 합니다.
    """

    @abstractmethod
    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """이미지 생성 요청을 처리합니다.

        Args:
            request: 이미지 생성 요청 (프롬프트, 스타일, 비율, 출력 경로)

        Returns:
            ImageGenerationResult (이미지 파일 경로, 크기)

        Raises:
            ImageGeneratorError: 생성 실패 시
        """

    def _resolve_output_path(self, output_path: str, suffix: str = ".png") -> Path:
        """출력 경로를 결정합니다."""
        if output_path:
            path = Path(output_path)
        else:
            path = Path("output") / f"image_output{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _parse_aspect_ratio(self, aspect_ratio: str) -> tuple[int, int]:
        """비율 문자열을 (width, height) 튜플로 파싱합니다."""
        dimension_map = {
            "16:9": (1920, 1080),
            "9:16": (1080, 1920),
            "1:1": (1024, 1024),
            "4:3": (1440, 1080),
            "3:4": (1080, 1440),
        }
        return dimension_map.get(aspect_ratio, (1920, 1080))


class MidjourneyGenerator(ImageGenerator):
    """Midjourney API 기반 이미지 생성기.

    실제 Midjourney API 연동은 추후 구현합니다.
    현재는 인터페이스만 정의합니다.

    Args:
        api_key: Midjourney API 키
        timeout: HTTP 요청 타임아웃 (초)
    """

    def __init__(self, api_key: str, timeout: float = 120.0) -> None:
        if not api_key:
            raise ValueError("Midjourney API 키가 필요합니다")
        self._api_key = api_key
        self._timeout = timeout

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Midjourney를 사용하여 이미지를 생성합니다.

        Args:
            request: 이미지 생성 요청

        Returns:
            ImageGenerationResult

        Raises:
            ImageGeneratorError: API가 아직 구현되지 않음
        """
        raise ImageGeneratorError(
            "Midjourney API 연동은 아직 구현되지 않았습니다. 추후 API가 공개되면 구현할 예정입니다."
        )


class NanubananGenerator(ImageGenerator):
    """나누바나나프로 API 기반 이미지 생성기.

    실제 API 연동은 추후 구현합니다.
    현재는 인터페이스만 정의합니다.

    Args:
        api_key: 나누바나나프로 API 키
        timeout: HTTP 요청 타임아웃 (초)
    """

    def __init__(self, api_key: str, timeout: float = 120.0) -> None:
        if not api_key:
            raise ValueError("나누바나나프로 API 키가 필요합니다")
        self._api_key = api_key
        self._timeout = timeout

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """나누바나나프로를 사용하여 이미지를 생성합니다.

        Args:
            request: 이미지 생성 요청

        Returns:
            ImageGenerationResult

        Raises:
            ImageGeneratorError: API가 아직 구현되지 않음
        """
        raise ImageGeneratorError(
            "나누바나나프로 API 연동은 아직 구현되지 않았습니다. "
            "추후 API 문서가 확보되면 구현할 예정입니다."
        )
