"""Media Generator 모듈 단위 테스트.

ElevenLabs API 호출을 Mock으로 대체하여 테스트합니다.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.media_generator.agent import MediaGeneratorAgent, MediaGeneratorError
from src.media_generator.image_gen import (
    ImageGenerator,
    ImageGeneratorError,
    MidjourneyGenerator,
    NanubananGenerator,
)
from src.media_generator.voice_gen import (
    ElevenLabsVoiceGenerator,
    ElevenLabsVoiceGeneratorError,
    _build_voice_settings,
    _resolve_voice_id,
    _speech_rate_to_stability,
)
from src.shared.models import (
    ImageGenerationRequest,
    ImageGenerationResult,
    VoiceDesign,
    VoiceGenerationRequest,
    VoiceGenerationResult,
)

# ============================================
# Fixtures
# ============================================


@pytest.fixture
def voice_design() -> VoiceDesign:
    """테스트용 VoiceDesign 객체."""
    return VoiceDesign(
        narration_style="calm narration",
        elevenlabs_voice_id="test-voice-id-123",
        speech_rate="moderate",
        pitch="medium",
        language="ko",
    )


@pytest.fixture
def voice_design_no_id() -> VoiceDesign:
    """voice_id가 없는 VoiceDesign 객체."""
    return VoiceDesign(
        narration_style="calm narration",
        elevenlabs_voice_id="",
        speech_rate="moderate",
    )


@pytest.fixture
def voice_request(voice_design: VoiceDesign) -> VoiceGenerationRequest:
    """테스트용 VoiceGenerationRequest."""
    return VoiceGenerationRequest(
        text="안녕하세요, 테스트 음성입니다.",
        voice_design=voice_design,
        output_path="/tmp/test_voice_output.mp3",
    )


@pytest.fixture
def image_request() -> ImageGenerationRequest:
    """테스트용 ImageGenerationRequest."""
    return ImageGenerationRequest(
        prompt="A cute cat sitting on a desk",
        style="photorealistic",
        aspect_ratio="16:9",
        output_path="/tmp/test_image_output.png",
    )


@pytest.fixture
def mock_image_generator() -> AsyncMock:
    """Mock ImageGenerator 구현체."""
    generator = AsyncMock(spec=ImageGenerator)
    generator.generate.return_value = ImageGenerationResult(
        image_path="/tmp/test_image_output.png",
        width=1920,
        height=1080,
    )
    return generator


# ============================================
# voice_gen.py 유틸리티 함수 테스트
# ============================================


class TestVoiceGenUtilities:
    """voice_gen 모듈의 유틸리티 함수 테스트."""

    def test_speech_rate_to_stability_slow(self) -> None:
        assert _speech_rate_to_stability("slow") == 0.85

    def test_speech_rate_to_stability_moderate(self) -> None:
        assert _speech_rate_to_stability("moderate") == 0.70

    def test_speech_rate_to_stability_fast(self) -> None:
        assert _speech_rate_to_stability("fast") == 0.55

    def test_speech_rate_to_stability_unknown_returns_default(self) -> None:
        assert _speech_rate_to_stability("unknown") == 0.70

    def test_build_voice_settings(self, voice_design: VoiceDesign) -> None:
        settings = _build_voice_settings(voice_design)

        assert settings["stability"] == 0.70
        assert settings["similarity_boost"] == 0.75
        assert settings["style"] == 0.0
        assert settings["use_speaker_boost"] is True

    def test_build_voice_settings_slow_rate(self) -> None:
        design = VoiceDesign(speech_rate="slow", elevenlabs_voice_id="v1")
        settings = _build_voice_settings(design)
        assert settings["stability"] == 0.85

    def test_resolve_voice_id_success(self, voice_design: VoiceDesign) -> None:
        assert _resolve_voice_id(voice_design) == "test-voice-id-123"

    def test_resolve_voice_id_missing_raises(self, voice_design_no_id: VoiceDesign) -> None:
        with pytest.raises(ElevenLabsVoiceGeneratorError, match="설정되지 않았습니다"):
            _resolve_voice_id(voice_design_no_id)


# ============================================
# ElevenLabsVoiceGenerator 테스트
# ============================================


class TestElevenLabsVoiceGenerator:
    """ElevenLabsVoiceGenerator 클래스 테스트."""

    def test_init_with_empty_api_key_raises(self) -> None:
        with pytest.raises(ValueError, match="API 키가 필요합니다"):
            ElevenLabsVoiceGenerator(api_key="")

    def test_init_success(self) -> None:
        generator = ElevenLabsVoiceGenerator(api_key="test-key")
        assert generator._api_key == "test-key"

    async def test_generate_success(self, voice_request: VoiceGenerationRequest) -> None:
        generator = ElevenLabsVoiceGenerator(api_key="test-key")

        fake_audio = b"\x00" * 160_000  # 10초 분량

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = fake_audio
        mock_response.raise_for_status = MagicMock()

        with patch("src.media_generator.voice_gen.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await generator.generate(voice_request)

        assert result.audio_path == "/tmp/test_voice_output.mp3"
        assert result.duration_seconds == 10.0
        assert result.sample_rate == 44100

    async def test_generate_http_error(self, voice_request: VoiceGenerationRequest) -> None:
        generator = ElevenLabsVoiceGenerator(api_key="test-key")

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.json.return_value = {"detail": {"message": "Invalid API key"}}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(spec=httpx.Request),
            response=mock_response,
        )

        with patch("src.media_generator.voice_gen.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(ElevenLabsVoiceGeneratorError, match="HTTP 401"):
                await generator.generate(voice_request)

    async def test_generate_connection_error(self, voice_request: VoiceGenerationRequest) -> None:
        generator = ElevenLabsVoiceGenerator(api_key="test-key")

        with patch("src.media_generator.voice_gen.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(ElevenLabsVoiceGeneratorError, match="연결 실패"):
                await generator.generate(voice_request)

    async def test_generate_missing_voice_id_raises(self, voice_design_no_id: VoiceDesign) -> None:
        generator = ElevenLabsVoiceGenerator(api_key="test-key")
        request = VoiceGenerationRequest(
            text="테스트",
            voice_design=voice_design_no_id,
        )

        with pytest.raises(ElevenLabsVoiceGeneratorError, match="설정되지 않았습니다"):
            await generator.generate(request)

    def test_estimate_duration(self) -> None:
        generator = ElevenLabsVoiceGenerator(api_key="test-key")

        assert generator._estimate_duration(16_000) == 1.0
        assert generator._estimate_duration(160_000) == 10.0
        assert generator._estimate_duration(0) == 0.0
        assert generator._estimate_duration(-100) == 0.0

    def test_extract_error_detail_with_dict(self) -> None:
        generator = ElevenLabsVoiceGenerator(api_key="test-key")

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {"detail": {"message": "Quota exceeded"}}

        exc = httpx.HTTPStatusError(
            "429",
            request=MagicMock(spec=httpx.Request),
            response=mock_response,
        )

        detail = generator._extract_error_detail(exc)
        assert detail == "Quota exceeded"

    def test_extract_error_detail_with_string(self) -> None:
        generator = ElevenLabsVoiceGenerator(api_key="test-key")

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {"detail": "Simple error message"}

        exc = httpx.HTTPStatusError(
            "400",
            request=MagicMock(spec=httpx.Request),
            response=mock_response,
        )

        detail = generator._extract_error_detail(exc)
        assert detail == "Simple error message"

    def test_extract_error_detail_json_parse_error(self) -> None:
        generator = ElevenLabsVoiceGenerator(api_key="test-key")

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = "Internal Server Error"

        exc = httpx.HTTPStatusError(
            "500",
            request=MagicMock(spec=httpx.Request),
            response=mock_response,
        )

        detail = generator._extract_error_detail(exc)
        assert detail == "Internal Server Error"


# ============================================
# ImageGenerator 구현체 테스트
# ============================================


class TestImageGenerators:
    """이미지 생성기 테스트."""

    def test_midjourney_init_empty_key_raises(self) -> None:
        with pytest.raises(ValueError, match="API 키가 필요합니다"):
            MidjourneyGenerator(api_key="")

    def test_nanubanan_init_empty_key_raises(self) -> None:
        with pytest.raises(ValueError, match="API 키가 필요합니다"):
            NanubananGenerator(api_key="")

    async def test_midjourney_generate_not_implemented(
        self, image_request: ImageGenerationRequest
    ) -> None:
        generator = MidjourneyGenerator(api_key="test-key")
        with pytest.raises(ImageGeneratorError, match="아직 구현되지 않았습니다"):
            await generator.generate(image_request)

    async def test_nanubanan_generate_not_implemented(
        self, image_request: ImageGenerationRequest
    ) -> None:
        generator = NanubananGenerator(api_key="test-key")
        with pytest.raises(ImageGeneratorError, match="아직 구현되지 않았습니다"):
            await generator.generate(image_request)

    def test_parse_aspect_ratio_16_9(self) -> None:
        gen = MidjourneyGenerator(api_key="test-key")
        assert gen._parse_aspect_ratio("16:9") == (1920, 1080)

    def test_parse_aspect_ratio_1_1(self) -> None:
        gen = MidjourneyGenerator(api_key="test-key")
        assert gen._parse_aspect_ratio("1:1") == (1024, 1024)

    def test_parse_aspect_ratio_unknown_returns_default(self) -> None:
        gen = MidjourneyGenerator(api_key="test-key")
        assert gen._parse_aspect_ratio("unknown") == (1920, 1080)

    def test_parse_aspect_ratio_9_16(self) -> None:
        gen = NanubananGenerator(api_key="test-key")
        assert gen._parse_aspect_ratio("9:16") == (1080, 1920)


# ============================================
# MediaGeneratorAgent 테스트
# ============================================


class TestMediaGeneratorAgent:
    """MediaGeneratorAgent 클래스 테스트."""

    async def test_generate_voice_success(
        self,
        voice_design: VoiceDesign,
        mock_image_generator: AsyncMock,
    ) -> None:
        voice_gen = AsyncMock(spec=ElevenLabsVoiceGenerator)
        voice_gen.generate.return_value = VoiceGenerationResult(
            audio_path="/tmp/output.mp3",
            duration_seconds=5.0,
            sample_rate=44100,
        )

        agent = MediaGeneratorAgent(
            voice_generator=voice_gen,
            image_generator=mock_image_generator,
        )

        result = await agent.generate_voice(
            text="테스트 음성입니다.",
            voice_design=voice_design,
        )

        assert result.audio_path == "/tmp/output.mp3"
        assert result.duration_seconds == 5.0
        voice_gen.generate.assert_awaited_once()

    async def test_generate_voice_empty_text_raises(
        self,
        voice_design: VoiceDesign,
        mock_image_generator: AsyncMock,
    ) -> None:
        voice_gen = AsyncMock(spec=ElevenLabsVoiceGenerator)

        agent = MediaGeneratorAgent(
            voice_generator=voice_gen,
            image_generator=mock_image_generator,
        )

        with pytest.raises(MediaGeneratorError, match="텍스트가 비어 있습니다"):
            await agent.generate_voice(text="", voice_design=voice_design)

    async def test_generate_voice_whitespace_only_raises(
        self,
        voice_design: VoiceDesign,
        mock_image_generator: AsyncMock,
    ) -> None:
        voice_gen = AsyncMock(spec=ElevenLabsVoiceGenerator)

        agent = MediaGeneratorAgent(
            voice_generator=voice_gen,
            image_generator=mock_image_generator,
        )

        with pytest.raises(MediaGeneratorError, match="텍스트가 비어 있습니다"):
            await agent.generate_voice(text="   ", voice_design=voice_design)

    async def test_generate_voice_api_error_wraps(
        self,
        voice_design: VoiceDesign,
        mock_image_generator: AsyncMock,
    ) -> None:
        voice_gen = AsyncMock(spec=ElevenLabsVoiceGenerator)
        voice_gen.generate.side_effect = ElevenLabsVoiceGeneratorError("API rate limit exceeded")

        agent = MediaGeneratorAgent(
            voice_generator=voice_gen,
            image_generator=mock_image_generator,
        )

        with pytest.raises(MediaGeneratorError, match="음성 생성 실패"):
            await agent.generate_voice(
                text="테스트",
                voice_design=voice_design,
            )

    async def test_generate_image_success(
        self,
        mock_image_generator: AsyncMock,
    ) -> None:
        voice_gen = AsyncMock(spec=ElevenLabsVoiceGenerator)

        agent = MediaGeneratorAgent(
            voice_generator=voice_gen,
            image_generator=mock_image_generator,
        )

        result = await agent.generate_image(
            prompt="A serene landscape",
            style="watercolor",
        )

        assert result.image_path == "/tmp/test_image_output.png"
        assert result.width == 1920
        assert result.height == 1080
        mock_image_generator.generate.assert_awaited_once()

    async def test_generate_image_empty_prompt_raises(
        self,
        mock_image_generator: AsyncMock,
    ) -> None:
        voice_gen = AsyncMock(spec=ElevenLabsVoiceGenerator)

        agent = MediaGeneratorAgent(
            voice_generator=voice_gen,
            image_generator=mock_image_generator,
        )

        with pytest.raises(MediaGeneratorError, match="프롬프트가 비어 있습니다"):
            await agent.generate_image(prompt="")

    async def test_generate_image_api_error_wraps(
        self,
        mock_image_generator: AsyncMock,
    ) -> None:
        mock_image_generator.generate.side_effect = ImageGeneratorError("Service unavailable")
        voice_gen = AsyncMock(spec=ElevenLabsVoiceGenerator)

        agent = MediaGeneratorAgent(
            voice_generator=voice_gen,
            image_generator=mock_image_generator,
        )

        with pytest.raises(MediaGeneratorError, match="이미지 생성 실패"):
            await agent.generate_image(prompt="A landscape")

    def test_build_styled_prompt_with_style(self) -> None:
        voice_gen = MagicMock(spec=ElevenLabsVoiceGenerator)
        image_gen = MagicMock(spec=ImageGenerator)

        agent = MediaGeneratorAgent(
            voice_generator=voice_gen,
            image_generator=image_gen,
        )

        result = agent._build_styled_prompt("sunset over mountains", "oil painting")
        assert result == "sunset over mountains, style: oil painting"

    def test_build_styled_prompt_without_style(self) -> None:
        voice_gen = MagicMock(spec=ElevenLabsVoiceGenerator)
        image_gen = MagicMock(spec=ImageGenerator)

        agent = MediaGeneratorAgent(
            voice_generator=voice_gen,
            image_generator=image_gen,
        )

        result = agent._build_styled_prompt("sunset over mountains", "")
        assert result == "sunset over mountains"

    async def test_generate_image_styled_prompt_passed_to_request(
        self,
        mock_image_generator: AsyncMock,
    ) -> None:
        voice_gen = AsyncMock(spec=ElevenLabsVoiceGenerator)

        agent = MediaGeneratorAgent(
            voice_generator=voice_gen,
            image_generator=mock_image_generator,
        )

        await agent.generate_image(
            prompt="A cat",
            style="anime",
            aspect_ratio="1:1",
        )

        call_args = mock_image_generator.generate.call_args
        request = call_args[0][0]
        assert request.prompt == "A cat, style: anime"
        assert request.style == "anime"
        assert request.aspect_ratio == "1:1"
