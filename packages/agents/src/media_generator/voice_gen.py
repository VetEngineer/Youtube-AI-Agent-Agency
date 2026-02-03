"""ElevenLabs TTS 음성 합성 모듈.

VoiceDesign 설정을 기반으로 ElevenLabs API를 호출하여 음성을 생성합니다.
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx

from src.shared.models import VoiceDesign, VoiceGenerationRequest, VoiceGenerationResult

logger = logging.getLogger(__name__)

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"


class ElevenLabsVoiceGeneratorError(Exception):
    """ElevenLabs API 호출 중 발생하는 에러."""


def _build_voice_settings(voice_design: VoiceDesign) -> dict:
    """VoiceDesign에서 ElevenLabs voice_settings를 생성합니다."""
    stability = _speech_rate_to_stability(voice_design.speech_rate)
    similarity_boost = 0.75

    return {
        "stability": stability,
        "similarity_boost": similarity_boost,
        "style": 0.0,
        "use_speaker_boost": True,
    }


def _speech_rate_to_stability(speech_rate: str) -> float:
    """speech_rate 문자열을 ElevenLabs stability 값으로 변환합니다."""
    rate_map = {
        "slow": 0.85,
        "moderate": 0.70,
        "fast": 0.55,
    }
    return rate_map.get(speech_rate, 0.70)


def _resolve_voice_id(voice_design: VoiceDesign) -> str:
    """VoiceDesign에서 voice_id를 추출합니다."""
    voice_id = voice_design.elevenlabs_voice_id
    if not voice_id:
        raise ElevenLabsVoiceGeneratorError(
            "voice_design.elevenlabs_voice_id가 설정되지 않았습니다"
        )
    return voice_id


class ElevenLabsVoiceGenerator:
    """ElevenLabs TTS API를 사용한 음성 합성기.

    Args:
        api_key: ElevenLabs API 키
        timeout: HTTP 요청 타임아웃 (초)
    """

    def __init__(self, api_key: str, timeout: float = 60.0) -> None:
        if not api_key:
            raise ValueError("ElevenLabs API 키가 필요합니다")
        self._api_key = api_key
        self._timeout = timeout

    async def generate(self, request: VoiceGenerationRequest) -> VoiceGenerationResult:
        """텍스트를 음성으로 변환합니다.

        Args:
            request: 음성 합성 요청 (텍스트, VoiceDesign, 출력 경로)

        Returns:
            VoiceGenerationResult (오디오 파일 경로, 길이 등)

        Raises:
            ElevenLabsVoiceGeneratorError: API 호출 실패 시
        """
        voice_id = _resolve_voice_id(request.voice_design)
        url = f"{ELEVENLABS_TTS_URL}/{voice_id}"

        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        body = {
            "text": request.text,
            "model_id": DEFAULT_MODEL_ID,
            "voice_settings": _build_voice_settings(request.voice_design),
        }

        output_path = self._resolve_output_path(request.output_path)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, headers=headers, json=body)
                response.raise_for_status()

                self._write_audio_file(output_path, response.content)

            duration = self._estimate_duration(len(response.content))

            logger.info("음성 생성 완료: %s (%.1f초)", output_path, duration)

            return VoiceGenerationResult(
                audio_path=str(output_path),
                duration_seconds=duration,
                sample_rate=44100,
            )

        except httpx.HTTPStatusError as exc:
            error_detail = self._extract_error_detail(exc)
            raise ElevenLabsVoiceGeneratorError(
                f"ElevenLabs API 에러 (HTTP {exc.response.status_code}): {error_detail}"
            ) from exc
        except httpx.RequestError as exc:
            raise ElevenLabsVoiceGeneratorError(f"ElevenLabs API 연결 실패: {exc}") from exc

    def _resolve_output_path(self, output_path: str) -> Path:
        """출력 경로를 결정합니다. 비어 있으면 기본 경로를 사용합니다."""
        if output_path:
            path = Path(output_path)
        else:
            path = Path("output") / "voice_output.mp3"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _write_audio_file(self, path: Path, content: bytes) -> None:
        """오디오 데이터를 파일로 저장합니다."""
        path.write_bytes(content)

    def _estimate_duration(self, byte_size: int) -> float:
        """MP3 바이트 크기로 대략적인 재생 시간을 추정합니다.

        128kbps MP3 기준: 1초 = 약 16,000 바이트
        """
        bytes_per_second = 16_000
        if byte_size <= 0:
            return 0.0
        return round(byte_size / bytes_per_second, 1)

    def _extract_error_detail(self, exc: httpx.HTTPStatusError) -> str:
        """HTTP 에러 응답에서 상세 메시지를 추출합니다."""
        try:
            error_body = exc.response.json()
            detail = error_body.get("detail", {})
            if isinstance(detail, dict):
                return detail.get("message", str(error_body))
            return str(detail)
        except Exception:
            return exc.response.text[:200]
