"""오디오 믹싱 모듈.

나레이션과 BGM을 믹싱하고 오디오 정규화 기능을 제공합니다.
내부적으로 FFmpeg를 사용합니다.
"""

from __future__ import annotations

import asyncio
import logging
import shlex
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioMixerError(Exception):
    """오디오 믹싱 중 발생하는 에러."""


def _validate_path(path: str, label: str) -> Path:
    """경로 문자열을 검증하고 Path 객체로 반환한다."""
    if not path or not path.strip():
        raise AudioMixerError(f"{label} 경로가 비어 있습니다")
    return Path(path)


def _validate_volume(volume: float) -> float:
    """볼륨 값을 검증한다 (0.0 ~ 1.0)."""
    if not 0.0 <= volume <= 1.0:
        raise AudioMixerError(f"볼륨은 0.0에서 1.0 사이여야 합니다: {volume}")
    return volume


def _ensure_parent_dir(path: Path) -> None:
    """출력 경로의 부모 디렉토리가 존재하는지 확인한다."""
    path.parent.mkdir(parents=True, exist_ok=True)


async def _run_ffmpeg(args: list[str]) -> str:
    """ffmpeg 명령을 비동기로 실행한다.

    Args:
        args: ffmpeg에 전달할 인자 목록.

    Returns:
        실행된 전체 명령 문자열.

    Raises:
        AudioMixerError: ffmpeg 실행 실패 시.
    """
    cmd = ["ffmpeg", "-y", *args]
    cmd_str = " ".join(shlex.quote(c) for c in cmd)
    logger.info("ffmpeg 실행: %s", cmd_str)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
    except FileNotFoundError as exc:
        raise AudioMixerError("ffmpeg가 설치되어 있지 않습니다") from exc

    if process.returncode != 0:
        error_msg = stderr.decode(errors="replace").strip()
        raise AudioMixerError(f"ffmpeg 실행 실패 (code={process.returncode}): {error_msg}")

    return cmd_str


class AudioMixer:
    """FFmpeg 기반 오디오 믹서."""

    async def mix(
        self,
        narration_path: str,
        bgm_path: str | None,
        bgm_volume: float,
        output_path: str,
    ) -> str:
        """나레이션과 BGM을 믹싱한다.

        나레이션은 원본 볼륨을 유지하고, BGM은 지정된 볼륨으로 조절됩니다.
        BGM이 없으면 나레이션만 복사합니다.

        Args:
            narration_path: 나레이션 오디오 파일 경로.
            bgm_path: BGM 오디오 파일 경로 (None이면 나레이션만 사용).
            bgm_volume: BGM 볼륨 (0.0 ~ 1.0).
            output_path: 출력 오디오 파일 경로.

        Returns:
            출력 파일 경로.

        Raises:
            AudioMixerError: 잘못된 입력이거나 ffmpeg 실행 실패 시.
        """
        narration = _validate_path(narration_path, "나레이션")
        out = _validate_path(output_path, "출력")
        _ensure_parent_dir(out)
        _validate_volume(bgm_volume)

        if bgm_path is None:
            return await self._copy_audio(str(narration), str(out))

        bgm = _validate_path(bgm_path, "BGM")
        return await self._mix_two_tracks(str(narration), str(bgm), bgm_volume, str(out))

    async def normalize(
        self,
        audio_path: str,
        output_path: str,
    ) -> str:
        """오디오 라우드니스를 EBU R128 기준으로 정규화한다.

        Args:
            audio_path: 입력 오디오 파일 경로.
            output_path: 출력 오디오 파일 경로.

        Returns:
            출력 파일 경로.

        Raises:
            AudioMixerError: 잘못된 입력이거나 ffmpeg 실행 실패 시.
        """
        src = _validate_path(audio_path, "입력 오디오")
        out = _validate_path(output_path, "출력 오디오")
        _ensure_parent_dir(out)

        args = [
            "-i",
            str(src),
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            str(out),
        ]

        await _run_ffmpeg(args)
        logger.info("오디오 정규화 완료: %s", out)
        return str(out)

    async def _copy_audio(self, src: str, dst: str) -> str:
        """오디오를 코덱 복사로 전달한다."""
        args = ["-i", src, "-c", "copy", dst]
        await _run_ffmpeg(args)
        logger.info("오디오 복사 완료: %s", dst)
        return dst

    async def _mix_two_tracks(
        self,
        narration: str,
        bgm: str,
        bgm_volume: float,
        output: str,
    ) -> str:
        """나레이션과 BGM 두 트랙을 믹싱한다."""
        filter_complex = (
            f"[1:a]volume={bgm_volume}[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[out]"
        )

        args = [
            "-i",
            narration,
            "-i",
            bgm,
            "-filter_complex",
            filter_complex,
            "-map",
            "[out]",
            output,
        ]

        await _run_ffmpeg(args)
        logger.info("오디오 믹싱 완료: %s", output)
        return output
