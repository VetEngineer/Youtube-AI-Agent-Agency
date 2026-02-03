"""Media Editor 모듈 단위 테스트.

FFmpeg/Whisper가 없는 환경에서도 동작하도록
asyncio.create_subprocess_exec와 Path.mkdir를 Mock하여 테스트합니다.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.media_editor.agent import MediaEditorAgent, MediaEditorError
from src.media_editor.audio_mixer import AudioMixer, AudioMixerError
from src.media_editor.subtitle import SubtitleError, SubtitleGenerator
from src.media_editor.video_editor import VideoEditor, VideoEditorError
from src.shared.models import EditingConfig, EditProject, EditResult

# ============================================
# 공통 Fixture
# ============================================


def _make_mock_process(returncode: int = 0, stderr: bytes = b"") -> AsyncMock:
    """성공/실패하는 mock subprocess를 생성한다."""
    mock_proc = AsyncMock()
    mock_proc.returncode = returncode
    mock_proc.communicate = AsyncMock(return_value=(b"", stderr))
    return mock_proc


@pytest.fixture()
def mock_subprocess_success():
    """성공하는 subprocess mock fixture."""
    mock_proc = _make_mock_process(returncode=0)
    with (
        patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec,
        patch.object(Path, "mkdir"),
    ):
        yield mock_exec


@pytest.fixture()
def mock_subprocess_failure():
    """실패하는 subprocess mock fixture."""
    mock_proc = _make_mock_process(returncode=1, stderr=b"ffmpeg error occurred")
    with (
        patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec,
        patch.object(Path, "mkdir"),
    ):
        yield mock_exec


# ============================================
# VideoEditor 테스트
# ============================================


class TestVideoEditor:
    """VideoEditor 클래스 테스트."""

    async def test_cut_video_success(self, mock_subprocess_success):
        """정상적인 컷 편집이 성공해야 한다."""
        editor = VideoEditor()
        result = await editor.cut_video(
            input_path="/input/video.mp4",
            segments=[(0.0, 5.0), (10.0, 20.0)],
            output_path="/output/cut.mp4",
        )

        assert result == "/output/cut.mp4"
        mock_subprocess_success.assert_called_once()
        call_args = mock_subprocess_success.call_args[0]
        assert call_args[0] == "ffmpeg"
        assert "-filter_complex" in call_args

    async def test_cut_video_single_segment(self, mock_subprocess_success):
        """단일 구간 컷 편집이 성공해야 한다."""
        editor = VideoEditor()
        result = await editor.cut_video(
            input_path="/input/video.mp4",
            segments=[(2.0, 8.0)],
            output_path="/output/cut.mp4",
        )

        assert result == "/output/cut.mp4"

    async def test_cut_video_empty_segments_raises(self, mock_subprocess_success):
        """빈 segments가 주어지면 에러가 발생해야 한다."""
        editor = VideoEditor()
        with pytest.raises(VideoEditorError, match="segments가 비어 있습니다"):
            await editor.cut_video(
                input_path="/input/video.mp4",
                segments=[],
                output_path="/output/cut.mp4",
            )

    async def test_cut_video_invalid_segment_raises(self, mock_subprocess_success):
        """잘못된 구간이 주어지면 에러가 발생해야 한다."""
        editor = VideoEditor()
        with pytest.raises(VideoEditorError, match="잘못된 구간"):
            await editor.cut_video(
                input_path="/input/video.mp4",
                segments=[(5.0, 3.0)],
                output_path="/output/cut.mp4",
            )

    async def test_cut_video_negative_start_raises(self, mock_subprocess_success):
        """음수 시작 시간이 주어지면 에러가 발생해야 한다."""
        editor = VideoEditor()
        with pytest.raises(VideoEditorError, match="잘못된 구간"):
            await editor.cut_video(
                input_path="/input/video.mp4",
                segments=[(-1.0, 5.0)],
                output_path="/output/cut.mp4",
            )

    async def test_cut_video_empty_input_path_raises(self, mock_subprocess_success):
        """빈 입력 경로가 주어지면 에러가 발생해야 한다."""
        editor = VideoEditor()
        with pytest.raises(VideoEditorError, match="경로가 비어 있습니다"):
            await editor.cut_video(
                input_path="",
                segments=[(0.0, 5.0)],
                output_path="/output/cut.mp4",
            )

    async def test_cut_video_ffmpeg_failure(self, mock_subprocess_failure):
        """ffmpeg 실패 시 에러가 발생해야 한다."""
        editor = VideoEditor()
        with pytest.raises(VideoEditorError, match="ffmpeg 실행 실패"):
            await editor.cut_video(
                input_path="/input/video.mp4",
                segments=[(0.0, 5.0)],
                output_path="/output/cut.mp4",
            )

    async def test_concatenate_success(self, mock_subprocess_success):
        """영상 결합이 성공해야 한다."""
        editor = VideoEditor()
        result = await editor.concatenate(
            video_paths=["/input/a.mp4", "/input/b.mp4"],
            output_path="/output/concat.mp4",
        )

        assert result == "/output/concat.mp4"
        mock_subprocess_success.assert_called_once()

    async def test_concatenate_three_videos(self, mock_subprocess_success):
        """세 개 영상 결합 시 concat 필터가 올바르게 구성되어야 한다."""
        editor = VideoEditor()
        result = await editor.concatenate(
            video_paths=["/input/a.mp4", "/input/b.mp4", "/input/c.mp4"],
            output_path="/output/concat.mp4",
        )

        assert result == "/output/concat.mp4"
        call_args = mock_subprocess_success.call_args[0]
        assert call_args.count("-i") == 3

    async def test_concatenate_empty_list_raises(self, mock_subprocess_success):
        """빈 영상 목록이 주어지면 에러가 발생해야 한다."""
        editor = VideoEditor()
        with pytest.raises(VideoEditorError, match="비어 있습니다"):
            await editor.concatenate(
                video_paths=[],
                output_path="/output/concat.mp4",
            )

    async def test_add_intro_outro_both(self, mock_subprocess_success):
        """인트로와 아웃트로 모두 추가되어야 한다."""
        editor = VideoEditor()
        result = await editor.add_intro_outro(
            video_path="/input/main.mp4",
            intro_path="/input/intro.mp4",
            outro_path="/input/outro.mp4",
            output_path="/output/final.mp4",
        )

        assert result == "/output/final.mp4"
        mock_subprocess_success.assert_called_once()

    async def test_add_intro_only(self, mock_subprocess_success):
        """인트로만 추가되어야 한다."""
        editor = VideoEditor()
        result = await editor.add_intro_outro(
            video_path="/input/main.mp4",
            intro_path="/input/intro.mp4",
            outro_path=None,
            output_path="/output/final.mp4",
        )

        assert result == "/output/final.mp4"

    async def test_add_outro_only(self, mock_subprocess_success):
        """아웃트로만 추가되어야 한다."""
        editor = VideoEditor()
        result = await editor.add_intro_outro(
            video_path="/input/main.mp4",
            intro_path=None,
            outro_path="/input/outro.mp4",
            output_path="/output/final.mp4",
        )

        assert result == "/output/final.mp4"

    async def test_add_intro_outro_none_raises(self, mock_subprocess_success):
        """인트로와 아웃트로가 모두 없으면 에러가 발생해야 한다."""
        editor = VideoEditor()
        with pytest.raises(VideoEditorError, match="호출할 필요가 없습니다"):
            await editor.add_intro_outro(
                video_path="/input/main.mp4",
                intro_path=None,
                outro_path=None,
                output_path="/output/final.mp4",
            )

    async def test_ffmpeg_not_installed(self):
        """ffmpeg가 없으면 명확한 에러가 발생해야 한다."""
        mock_exec = AsyncMock(side_effect=FileNotFoundError)
        with (
            patch("asyncio.create_subprocess_exec", mock_exec),
            patch.object(Path, "mkdir"),
        ):
            editor = VideoEditor()
            with pytest.raises(VideoEditorError, match="설치되어 있지 않습니다"):
                await editor.cut_video(
                    input_path="/input/video.mp4",
                    segments=[(0.0, 5.0)],
                    output_path="/output/cut.mp4",
                )


# ============================================
# SubtitleGenerator 테스트
# ============================================


class TestSubtitleGenerator:
    """SubtitleGenerator 클래스 테스트."""

    async def test_generate_srt_success(self, mock_subprocess_success):
        """SRT 자막 생성이 성공해야 한다."""
        generator = SubtitleGenerator()
        result = await generator.generate_srt(
            audio_path="/input/audio.wav",
            output_path="/output/subtitles.srt",
        )

        assert result == "/output/subtitles.srt"
        mock_subprocess_success.assert_called_once()
        call_args = mock_subprocess_success.call_args[0]
        assert call_args[0] == "whisper"

    async def test_generate_srt_whisper_args(self, mock_subprocess_success):
        """Whisper 호출 시 올바른 인자가 전달되어야 한다."""
        generator = SubtitleGenerator()
        await generator.generate_srt(
            audio_path="/input/audio.wav",
            output_path="/output/subtitles.srt",
        )

        call_args = mock_subprocess_success.call_args[0]
        assert "--model" in call_args
        assert "--language" in call_args
        assert "ko" in call_args
        assert "--output_format" in call_args
        assert "srt" in call_args

    async def test_generate_srt_empty_path_raises(self, mock_subprocess_success):
        """빈 경로가 주어지면 에러가 발생해야 한다."""
        generator = SubtitleGenerator()
        with pytest.raises(SubtitleError, match="경로가 비어 있습니다"):
            await generator.generate_srt(
                audio_path="",
                output_path="/output/subtitles.srt",
            )

    async def test_generate_srt_whisper_failure(self, mock_subprocess_failure):
        """Whisper 실패 시 에러가 발생해야 한다."""
        generator = SubtitleGenerator()
        with pytest.raises(SubtitleError, match="Whisper STT 실행 실패"):
            await generator.generate_srt(
                audio_path="/input/audio.wav",
                output_path="/output/subtitles.srt",
            )

    async def test_burn_subtitles_success(self, mock_subprocess_success):
        """자막 삽입이 성공해야 한다."""
        generator = SubtitleGenerator()
        result = await generator.burn_subtitles(
            video_path="/input/video.mp4",
            srt_path="/input/subtitles.srt",
            output_path="/output/subtitled.mp4",
            style="default",
        )

        assert result == "/output/subtitled.mp4"
        mock_subprocess_success.assert_called_once()

    async def test_burn_subtitles_bold_style(self, mock_subprocess_success):
        """bold 스타일 자막 삽입이 성공해야 한다."""
        generator = SubtitleGenerator()
        result = await generator.burn_subtitles(
            video_path="/input/video.mp4",
            srt_path="/input/subtitles.srt",
            output_path="/output/subtitled.mp4",
            style="bold",
        )

        assert result == "/output/subtitled.mp4"
        call_args = mock_subprocess_success.call_args[0]
        vf_idx = list(call_args).index("-vf")
        filter_str = call_args[vf_idx + 1]
        assert "Bold=1" in filter_str

    async def test_burn_subtitles_minimal_style(self, mock_subprocess_success):
        """minimal 스타일 자막 삽입이 성공해야 한다."""
        generator = SubtitleGenerator()
        await generator.burn_subtitles(
            video_path="/input/video.mp4",
            srt_path="/input/subtitles.srt",
            output_path="/output/subtitled.mp4",
            style="minimal",
        )

        call_args = mock_subprocess_success.call_args[0]
        vf_idx = list(call_args).index("-vf")
        filter_str = call_args[vf_idx + 1]
        assert "Arial" in filter_str

    async def test_burn_subtitles_unknown_style_uses_default(self, mock_subprocess_success):
        """알 수 없는 스타일이면 default가 사용되어야 한다."""
        generator = SubtitleGenerator()
        result = await generator.burn_subtitles(
            video_path="/input/video.mp4",
            srt_path="/input/subtitles.srt",
            output_path="/output/subtitled.mp4",
            style="nonexistent",
        )

        assert result == "/output/subtitled.mp4"
        call_args = mock_subprocess_success.call_args[0]
        vf_idx = list(call_args).index("-vf")
        filter_str = call_args[vf_idx + 1]
        assert "NanumGothic" in filter_str

    async def test_burn_subtitles_empty_srt_path_raises(self, mock_subprocess_success):
        """빈 SRT 경로가 주어지면 에러가 발생해야 한다."""
        generator = SubtitleGenerator()
        with pytest.raises(SubtitleError, match="경로가 비어 있습니다"):
            await generator.burn_subtitles(
                video_path="/input/video.mp4",
                srt_path="",
                output_path="/output/subtitled.mp4",
            )

    async def test_burn_subtitles_empty_video_path_raises(self, mock_subprocess_success):
        """빈 영상 경로가 주어지면 에러가 발생해야 한다."""
        generator = SubtitleGenerator()
        with pytest.raises(SubtitleError, match="경로가 비어 있습니다"):
            await generator.burn_subtitles(
                video_path="",
                srt_path="/input/subtitles.srt",
                output_path="/output/subtitled.mp4",
            )


# ============================================
# AudioMixer 테스트
# ============================================


class TestAudioMixer:
    """AudioMixer 클래스 테스트."""

    async def test_mix_with_bgm_success(self, mock_subprocess_success):
        """나레이션 + BGM 믹싱이 성공해야 한다."""
        mixer = AudioMixer()
        result = await mixer.mix(
            narration_path="/input/narration.wav",
            bgm_path="/input/bgm.mp3",
            bgm_volume=0.15,
            output_path="/output/mixed.wav",
        )

        assert result == "/output/mixed.wav"
        mock_subprocess_success.assert_called_once()
        call_args = mock_subprocess_success.call_args[0]
        assert "-filter_complex" in call_args

    async def test_mix_without_bgm_copies_narration(self, mock_subprocess_success):
        """BGM 없이 나레이션만 복사해야 한다."""
        mixer = AudioMixer()
        result = await mixer.mix(
            narration_path="/input/narration.wav",
            bgm_path=None,
            bgm_volume=0.15,
            output_path="/output/mixed.wav",
        )

        assert result == "/output/mixed.wav"
        call_args = mock_subprocess_success.call_args[0]
        assert "-c" in call_args
        assert "copy" in call_args

    async def test_mix_invalid_volume_raises(self, mock_subprocess_success):
        """잘못된 볼륨(>1.0)이 주어지면 에러가 발생해야 한다."""
        mixer = AudioMixer()
        with pytest.raises(AudioMixerError, match="0.0에서 1.0 사이"):
            await mixer.mix(
                narration_path="/input/narration.wav",
                bgm_path="/input/bgm.mp3",
                bgm_volume=1.5,
                output_path="/output/mixed.wav",
            )

    async def test_mix_negative_volume_raises(self, mock_subprocess_success):
        """음수 볼륨이 주어지면 에러가 발생해야 한다."""
        mixer = AudioMixer()
        with pytest.raises(AudioMixerError, match="0.0에서 1.0 사이"):
            await mixer.mix(
                narration_path="/input/narration.wav",
                bgm_path="/input/bgm.mp3",
                bgm_volume=-0.1,
                output_path="/output/mixed.wav",
            )

    async def test_mix_empty_narration_path_raises(self, mock_subprocess_success):
        """빈 나레이션 경로가 주어지면 에러가 발생해야 한다."""
        mixer = AudioMixer()
        with pytest.raises(AudioMixerError, match="경로가 비어 있습니다"):
            await mixer.mix(
                narration_path="",
                bgm_path=None,
                bgm_volume=0.15,
                output_path="/output/mixed.wav",
            )

    async def test_normalize_success(self, mock_subprocess_success):
        """오디오 정규화가 성공해야 한다."""
        mixer = AudioMixer()
        result = await mixer.normalize(
            audio_path="/input/audio.wav",
            output_path="/output/normalized.wav",
        )

        assert result == "/output/normalized.wav"
        call_args = mock_subprocess_success.call_args[0]
        assert "-af" in call_args
        af_idx = list(call_args).index("-af")
        assert "loudnorm" in call_args[af_idx + 1]

    async def test_normalize_failure(self, mock_subprocess_failure):
        """ffmpeg 실패 시 에러가 발생해야 한다."""
        mixer = AudioMixer()
        with pytest.raises(AudioMixerError, match="ffmpeg 실행 실패"):
            await mixer.normalize(
                audio_path="/input/audio.wav",
                output_path="/output/normalized.wav",
            )

    async def test_mix_boundary_volume_zero(self, mock_subprocess_success):
        """볼륨 0.0이 허용되어야 한다."""
        mixer = AudioMixer()
        result = await mixer.mix(
            narration_path="/input/narration.wav",
            bgm_path="/input/bgm.mp3",
            bgm_volume=0.0,
            output_path="/output/mixed.wav",
        )

        assert result == "/output/mixed.wav"

    async def test_mix_boundary_volume_one(self, mock_subprocess_success):
        """볼륨 1.0이 허용되어야 한다."""
        mixer = AudioMixer()
        result = await mixer.mix(
            narration_path="/input/narration.wav",
            bgm_path="/input/bgm.mp3",
            bgm_volume=1.0,
            output_path="/output/mixed.wav",
        )

        assert result == "/output/mixed.wav"

    async def test_normalize_loudnorm_params(self, mock_subprocess_success):
        """정규화 시 EBU R128 파라미터가 올바르게 설정되어야 한다."""
        mixer = AudioMixer()
        await mixer.normalize(
            audio_path="/input/audio.wav",
            output_path="/output/normalized.wav",
        )

        call_args = mock_subprocess_success.call_args[0]
        af_idx = list(call_args).index("-af")
        loudnorm_str = call_args[af_idx + 1]
        assert "I=-16" in loudnorm_str
        assert "TP=-1.5" in loudnorm_str
        assert "LRA=11" in loudnorm_str


# ============================================
# MediaEditorAgent 테스트
# ============================================


class TestMediaEditorAgent:
    """MediaEditorAgent 클래스 테스트."""

    async def test_edit_minimal_project(self, mock_subprocess_success):
        """최소 구성의 프로젝트가 성공해야 한다."""
        project = EditProject(
            source_videos=["/input/video.mp4"],
            audio_tracks=[],
            subtitle_file="",
            output_path="/output/final.mp4",
        )

        agent = MediaEditorAgent()
        result = await agent.edit(project)

        assert isinstance(result, EditResult)
        assert result.resolution == "1920x1080"

    async def test_edit_with_audio_tracks(self, mock_subprocess_success):
        """오디오 트랙이 포함된 프로젝트가 성공해야 한다."""
        project = EditProject(
            source_videos=["/input/video.mp4"],
            audio_tracks=["/input/narration.wav", "/input/bgm.mp3"],
            subtitle_file="",
            output_path="/output/final.mp4",
            editing_config=EditingConfig(bgm_volume=0.2),
        )

        agent = MediaEditorAgent()
        result = await agent.edit(project)

        assert isinstance(result, EditResult)

    async def test_edit_with_subtitle_file(self, mock_subprocess_success):
        """자막 파일이 포함된 프로젝트가 성공해야 한다."""
        project = EditProject(
            source_videos=["/input/video.mp4"],
            audio_tracks=[],
            subtitle_file="/input/subtitles.srt",
            output_path="/output/final.mp4",
        )

        agent = MediaEditorAgent()
        result = await agent.edit(project)

        assert isinstance(result, EditResult)

    async def test_edit_with_multiple_videos(self, mock_subprocess_success):
        """여러 영상이 포함된 프로젝트가 성공해야 한다."""
        project = EditProject(
            source_videos=["/input/a.mp4", "/input/b.mp4", "/input/c.mp4"],
            audio_tracks=[],
            output_path="/output/final.mp4",
        )

        agent = MediaEditorAgent()
        result = await agent.edit(project)

        assert isinstance(result, EditResult)

    async def test_edit_with_intro_outro(self, mock_subprocess_success):
        """인트로/아웃트로가 포함된 프로젝트가 성공해야 한다."""
        project = EditProject(
            source_videos=["/input/video.mp4"],
            audio_tracks=[],
            output_path="/output/final.mp4",
            editing_config=EditingConfig(
                intro_template="/input/intro.mp4",
                outro_template="/input/outro.mp4",
            ),
        )

        agent = MediaEditorAgent()
        result = await agent.edit(project)

        assert isinstance(result, EditResult)

    async def test_edit_empty_source_videos_raises(self, mock_subprocess_success):
        """빈 source_videos가 주어지면 에러가 발생해야 한다."""
        project = EditProject(
            source_videos=[],
            output_path="/output/final.mp4",
        )

        agent = MediaEditorAgent()
        with pytest.raises(MediaEditorError, match="source_videos가 비어 있습니다"):
            await agent.edit(project)

    async def test_edit_empty_output_path_raises(self, mock_subprocess_success):
        """빈 output_path가 주어지면 에러가 발생해야 한다."""
        project = EditProject(
            source_videos=["/input/video.mp4"],
            output_path="",
        )

        agent = MediaEditorAgent()
        with pytest.raises(MediaEditorError, match="output_path가 비어 있습니다"):
            await agent.edit(project)

    async def test_edit_ffmpeg_failure_wraps_error(self, mock_subprocess_failure):
        """ffmpeg 실패 시 MediaEditorError로 래핑되어야 한다."""
        project = EditProject(
            source_videos=["/input/a.mp4", "/input/b.mp4"],
            audio_tracks=[],
            output_path="/output/final.mp4",
        )

        agent = MediaEditorAgent()
        with pytest.raises(MediaEditorError, match="편집 실패"):
            await agent.edit(project)

    async def test_edit_custom_injected_components(self, mock_subprocess_success):
        """의존성 주입된 컴포넌트가 사용되어야 한다."""
        mock_video_editor = MagicMock(spec=VideoEditor)
        mock_subtitle_gen = MagicMock(spec=SubtitleGenerator)
        mock_audio_mixer = MagicMock(spec=AudioMixer)

        mock_audio_mixer.mix = AsyncMock(return_value="/tmp/mixed.wav")
        mock_audio_mixer.normalize = AsyncMock(return_value="/tmp/norm.wav")
        mock_subtitle_gen.generate_srt = AsyncMock(return_value="/tmp/sub.srt")
        mock_subtitle_gen.burn_subtitles = AsyncMock(return_value="/tmp/sub.mp4")
        mock_video_editor.merge_audio = AsyncMock(return_value="/output/final.mp4")

        project = EditProject(
            source_videos=["/input/video.mp4"],
            audio_tracks=["/input/narration.wav"],
            output_path="/output/final.mp4",
        )

        agent = MediaEditorAgent(
            video_editor=mock_video_editor,
            subtitle_generator=mock_subtitle_gen,
            audio_mixer=mock_audio_mixer,
        )

        result = await agent.edit(project)

        assert isinstance(result, EditResult)
        mock_audio_mixer.mix.assert_called_once()
        mock_audio_mixer.normalize.assert_called_once()

    async def test_edit_narration_only_no_bgm(self, mock_subprocess_success):
        """나레이션만 있고 BGM이 없는 경우 성공해야 한다."""
        project = EditProject(
            source_videos=["/input/video.mp4"],
            audio_tracks=["/input/narration.wav"],
            output_path="/output/final.mp4",
        )

        agent = MediaEditorAgent()
        result = await agent.edit(project)

        assert isinstance(result, EditResult)


# ============================================
# 모델 검증 테스트
# ============================================


class TestModels:
    """입출력 모델 검증 테스트."""

    def test_edit_project_defaults(self):
        """EditProject의 기본값이 올바르게 설정되어야 한다."""
        project = EditProject()

        assert project.source_videos == []
        assert project.audio_tracks == []
        assert project.subtitle_file == ""
        assert project.output_path == ""
        assert isinstance(project.editing_config, EditingConfig)

    def test_editing_config_defaults(self):
        """EditingConfig의 기본값이 올바르게 설정되어야 한다."""
        config = EditingConfig()

        assert config.intro_template == ""
        assert config.outro_template == ""
        assert config.subtitle_style == "default"
        assert config.bgm_volume == 0.15

    def test_edit_result_creation(self):
        """EditResult가 올바르게 생성되어야 한다."""
        result = EditResult(
            output_path="/output/final.mp4",
            duration_seconds=120.5,
            resolution="1920x1080",
            file_size_mb=45.3,
        )

        assert result.output_path == "/output/final.mp4"
        assert result.duration_seconds == 120.5
        assert result.resolution == "1920x1080"
        assert result.file_size_mb == 45.3

    def test_edit_result_defaults(self):
        """EditResult의 기본값이 올바르게 설정되어야 한다."""
        result = EditResult(output_path="/output/final.mp4")

        assert result.duration_seconds == 0.0
        assert result.resolution == "1920x1080"
        assert result.file_size_mb == 0.0

    def test_edit_project_with_config(self):
        """EditProject에 EditingConfig가 올바르게 설정되어야 한다."""
        config = EditingConfig(
            intro_template="/templates/intro.mp4",
            outro_template="/templates/outro.mp4",
            subtitle_style="bold",
            bgm_volume=0.3,
        )
        project = EditProject(
            source_videos=["/input/a.mp4"],
            output_path="/output/final.mp4",
            editing_config=config,
        )

        assert project.editing_config.intro_template == "/templates/intro.mp4"
        assert project.editing_config.bgm_volume == 0.3
        assert project.editing_config.subtitle_style == "bold"

    def test_edit_project_immutability(self):
        """EditProject는 Pydantic 모델로 불변성을 보장해야 한다."""
        project = EditProject(
            source_videos=["/input/a.mp4"],
            output_path="/output/final.mp4",
        )

        new_project = project.model_copy(update={"output_path": "/output/new.mp4"})

        assert project.output_path == "/output/final.mp4"
        assert new_project.output_path == "/output/new.mp4"
