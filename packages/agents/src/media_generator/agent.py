"""Media Generator Agent.

Script의 텍스트를 음성과 이미지로 변환하는 에이전트입니다.
BrandGuide의 voice_design, visual_identity 설정을 적용합니다.

입력: 텍스트 + VoiceDesign / 프롬프트 + 스타일
출력: VoiceGenerationResult / ImageGenerationResult
"""

from __future__ import annotations

import logging

from src.shared.models import (
    ImageGenerationRequest,
    ImageGenerationResult,
    VoiceDesign,
    VoiceGenerationRequest,
    VoiceGenerationResult,
)

from .image_gen import ImageGenerator, ImageGeneratorError
from .voice_gen import ElevenLabsVoiceGenerator, ElevenLabsVoiceGeneratorError

logger = logging.getLogger(__name__)


class MediaGeneratorError(Exception):
    """Media Generator 에이전트 에러."""


class MediaGeneratorAgent:
    """미디어 생성 에이전트.

    음성 합성과 이미지 생성을 조율합니다.

    Args:
        voice_generator: ElevenLabs 음성 합성기
        image_generator: 이미지 생성기 (Midjourney, 나누바나나프로 등)
    """

    def __init__(
        self,
        voice_generator: ElevenLabsVoiceGenerator,
        image_generator: ImageGenerator,
    ) -> None:
        self._voice_generator = voice_generator
        self._image_generator = image_generator

    async def generate_voice(
        self,
        text: str,
        voice_design: VoiceDesign,
        output_path: str = "",
    ) -> VoiceGenerationResult:
        """텍스트를 음성으로 변환합니다.

        Args:
            text: 변환할 텍스트
            voice_design: 음성 설계 설정 (voice_id, speech_rate 등)
            output_path: 출력 파일 경로 (선택)

        Returns:
            VoiceGenerationResult

        Raises:
            MediaGeneratorError: 음성 생성 실패 시
        """
        if not text.strip():
            raise MediaGeneratorError("변환할 텍스트가 비어 있습니다")

        request = VoiceGenerationRequest(
            text=text,
            voice_design=voice_design,
            output_path=output_path,
        )

        try:
            result = await self._voice_generator.generate(request)
            logger.info(
                "음성 생성 완료: %s (%.1f초)",
                result.audio_path,
                result.duration_seconds,
            )
            return result
        except ElevenLabsVoiceGeneratorError as exc:
            raise MediaGeneratorError(f"음성 생성 실패: {exc}") from exc

    async def generate_image(
        self,
        prompt: str,
        style: str = "",
        aspect_ratio: str = "16:9",
        output_path: str = "",
    ) -> ImageGenerationResult:
        """프롬프트로 이미지를 생성합니다.

        Args:
            prompt: 이미지 생성 프롬프트
            style: 시각 스타일 (BrandGuide의 visual_identity에서 가져옴)
            aspect_ratio: 종횡비 (기본값 16:9)
            output_path: 출력 파일 경로 (선택)

        Returns:
            ImageGenerationResult

        Raises:
            MediaGeneratorError: 이미지 생성 실패 시
        """
        if not prompt.strip():
            raise MediaGeneratorError("이미지 프롬프트가 비어 있습니다")

        full_prompt = self._build_styled_prompt(prompt, style)

        request = ImageGenerationRequest(
            prompt=full_prompt,
            style=style,
            aspect_ratio=aspect_ratio,
            output_path=output_path,
        )

        try:
            result = await self._image_generator.generate(request)
            logger.info(
                "이미지 생성 완료: %s (%dx%d)",
                result.image_path,
                result.width,
                result.height,
            )
            return result
        except ImageGeneratorError as exc:
            raise MediaGeneratorError(f"이미지 생성 실패: {exc}") from exc

    def _build_styled_prompt(self, prompt: str, style: str) -> str:
        """스타일을 프롬프트에 적용합니다."""
        if not style:
            return prompt
        return f"{prompt}, style: {style}"
