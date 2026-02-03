"""Media Editor Agent 모듈.

EditProject를 입력받아 영상 컷편집, 자막 생성/삽입,
오디오 믹싱을 수행하고 EditResult를 반환합니다.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.media_editor.audio_mixer import AudioMixer, AudioMixerError
from src.media_editor.subtitle import SubtitleError, SubtitleGenerator
from src.media_editor.video_editor import VideoEditor, VideoEditorError
from src.shared.models import EditingConfig, EditProject, EditResult

logger = logging.getLogger(__name__)


class MediaEditorError(Exception):
    """Media Editor 에이전트 실행 중 발생하는 에러."""


def _resolve_output_dir(output_path: str) -> Path:
    """출력 경로에서 작업 디렉토리를 결정한다."""
    out = Path(output_path)
    return out.parent


def _build_temp_path(output_dir: Path, suffix: str) -> str:
    """작업 디렉토리 내 임시 파일 경로를 생성한다."""
    return str(output_dir / f"_temp_{suffix}")


class MediaEditorAgent:
    """영상 편집 파이프라인을 오케스트레이션하는 에이전트.

    편집 흐름:
      1. 오디오 믹싱 (나레이션 + BGM)
      2. 영상 결합 (소스 영상들)
      3. 인트로/아웃트로 추가
      4. 자막 생성 및 삽입
      5. 최종 출력 파일 생성
    """

    def __init__(
        self,
        video_editor: VideoEditor | None = None,
        subtitle_generator: SubtitleGenerator | None = None,
        audio_mixer: AudioMixer | None = None,
    ) -> None:
        self._video_editor = video_editor or VideoEditor()
        self._subtitle_generator = subtitle_generator or SubtitleGenerator()
        self._audio_mixer = audio_mixer or AudioMixer()

    async def edit(self, project: EditProject) -> EditResult:
        """EditProject를 처리하여 EditResult를 생성한다.

        Args:
            project: 편집 프로젝트 정보.

        Returns:
            편집 완료 결과.

        Raises:
            MediaEditorError: 편집 파이프라인 실행 중 에러 발생 시.
        """
        try:
            return await self._run_pipeline(project)
        except (VideoEditorError, SubtitleError, AudioMixerError) as exc:
            raise MediaEditorError(f"편집 실패: {exc}") from exc

    async def _run_pipeline(self, project: EditProject) -> EditResult:
        """편집 파이프라인을 순차적으로 실행한다."""
        _validate_project(project)

        output_dir = _resolve_output_dir(project.output_path)
        config = project.editing_config

        mixed_audio = await self._step_mix_audio(
            project.audio_tracks, config.bgm_volume, output_dir
        )

        combined_video = await self._step_combine_videos(project.source_videos, output_dir)

        with_intro_outro = await self._step_add_intro_outro(combined_video, config, output_dir)

        with_subtitles = await self._step_add_subtitles(
            with_intro_outro,
            project.subtitle_file,
            mixed_audio,
            config.subtitle_style,
            output_dir,
        )

        final_path = await self._step_finalize(with_subtitles, mixed_audio, project.output_path)

        return EditResult(
            output_path=final_path,
            duration_seconds=0.0,
            resolution="1920x1080",
            file_size_mb=0.0,
        )

    async def _step_mix_audio(
        self,
        audio_tracks: list[str],
        bgm_volume: float,
        output_dir: Path,
    ) -> str | None:
        """오디오 트랙들을 믹싱한다."""
        if not audio_tracks:
            logger.info("오디오 트랙 없음 - 믹싱 건너뜀")
            return None

        narration = audio_tracks[0]
        bgm = audio_tracks[1] if len(audio_tracks) > 1 else None
        mixed_path = _build_temp_path(output_dir, "mixed_audio.wav")

        result = await self._audio_mixer.mix(
            narration_path=narration,
            bgm_path=bgm,
            bgm_volume=bgm_volume,
            output_path=mixed_path,
        )

        normalized_path = _build_temp_path(output_dir, "normalized_audio.wav")
        return await self._audio_mixer.normalize(result, normalized_path)

    async def _step_combine_videos(
        self,
        source_videos: list[str],
        output_dir: Path,
    ) -> str:
        """소스 영상들을 결합한다."""
        if not source_videos:
            raise MediaEditorError("소스 영상이 없습니다")

        if len(source_videos) == 1:
            return source_videos[0]

        combined_path = _build_temp_path(output_dir, "combined.mp4")
        return await self._video_editor.concatenate(source_videos, combined_path)

    async def _step_add_intro_outro(
        self,
        video_path: str,
        config: EditingConfig,
        output_dir: Path,
    ) -> str:
        """인트로/아웃트로를 추가한다."""
        intro = config.intro_template or None
        outro = config.outro_template or None

        if not intro and not outro:
            logger.info("인트로/아웃트로 없음 - 건너뜀")
            return video_path

        io_path = _build_temp_path(output_dir, "with_intro_outro.mp4")
        return await self._video_editor.add_intro_outro(
            video_path=video_path,
            intro_path=intro,
            outro_path=outro,
            output_path=io_path,
        )

    async def _step_add_subtitles(
        self,
        video_path: str,
        subtitle_file: str,
        mixed_audio: str | None,
        subtitle_style: str,
        output_dir: Path,
    ) -> str:
        """자막을 생성하고 영상에 삽입한다."""
        srt_path = subtitle_file

        if not srt_path and mixed_audio:
            srt_path = _build_temp_path(output_dir, "subtitles.srt")
            srt_path = await self._subtitle_generator.generate_srt(
                audio_path=mixed_audio,
                output_path=srt_path,
            )

        if not srt_path:
            logger.info("자막 파일 없음 - 자막 삽입 건너뜀")
            return video_path

        subtitled_path = _build_temp_path(output_dir, "subtitled.mp4")
        return await self._subtitle_generator.burn_subtitles(
            video_path=video_path,
            srt_path=srt_path,
            output_path=subtitled_path,
            style=subtitle_style,
        )

    async def _step_finalize(
        self,
        video_path: str,
        audio_path: str | None,
        output_path: str,
    ) -> str:
        """최종 영상을 생성한다 (영상 + 믹싱된 오디오 결합)."""
        if audio_path is None:
            logger.info("별도 오디오 없음 - 영상을 최종 출력으로 사용")
            return video_path

        return await self._video_editor.merge_audio(
            video_path=video_path,
            audio_path=audio_path,
            output_path=output_path,
        )


def _validate_project(project: EditProject) -> None:
    """EditProject의 필수 필드를 검증한다."""
    if not project.source_videos:
        raise MediaEditorError("source_videos가 비어 있습니다")

    if not project.output_path:
        raise MediaEditorError("output_path가 비어 있습니다")
