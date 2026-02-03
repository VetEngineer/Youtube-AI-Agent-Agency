"""자막 생성 및 삽입 모듈.

Whisper STT를 사용하여 SRT 자막 파일을 생성하고,
FFmpeg를 사용하여 영상에 자막을 하드코딩합니다.
"""

from __future__ import annotations

import asyncio
import logging
import shlex
from pathlib import Path

logger = logging.getLogger(__name__)


class SubtitleError(Exception):
    """자막 처리 중 발생하는 에러."""


def _validate_path(path: str, label: str) -> Path:
    """경로 문자열을 검증하고 Path 객체로 반환한다."""
    if not path or not path.strip():
        raise SubtitleError(f"{label} 경로가 비어 있습니다")
    return Path(path)


def _ensure_parent_dir(path: Path) -> None:
    """출력 경로의 부모 디렉토리가 존재하는지 확인한다."""
    path.parent.mkdir(parents=True, exist_ok=True)


async def _run_command(cmd: list[str], error_prefix: str) -> str:
    """외부 명령을 비동기로 실행한다.

    Args:
        cmd: 실행할 명령 리스트.
        error_prefix: 에러 메시지 접두사.

    Returns:
        실행된 전체 명령 문자열.

    Raises:
        SubtitleError: 명령 실행 실패 시.
    """
    cmd_str = " ".join(shlex.quote(c) for c in cmd)
    logger.info("명령 실행: %s", cmd_str)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
    except FileNotFoundError as exc:
        raise SubtitleError(f"{error_prefix}: {cmd[0]}이(가) 설치되어 있지 않습니다") from exc

    if process.returncode != 0:
        error_msg = stderr.decode(errors="replace").strip()
        raise SubtitleError(f"{error_prefix} (code={process.returncode}): {error_msg}")

    return cmd_str


class SubtitleGenerator:
    """Whisper STT 기반 자막 생성 및 FFmpeg 자막 삽입기."""

    async def generate_srt(
        self,
        audio_path: str,
        output_path: str,
    ) -> str:
        """오디오에서 Whisper STT를 사용하여 SRT 자막 파일을 생성한다.

        Args:
            audio_path: 입력 오디오 파일 경로.
            output_path: 출력 SRT 파일 경로.

        Returns:
            출력 SRT 파일 경로.

        Raises:
            SubtitleError: 잘못된 입력이거나 Whisper 실행 실패 시.
        """
        src = _validate_path(audio_path, "오디오")
        out = _validate_path(output_path, "출력 SRT")
        _ensure_parent_dir(out)

        output_dir = str(out.parent)
        output_stem = out.stem

        cmd = [
            "whisper",
            str(src),
            "--model",
            "base",
            "--language",
            "ko",
            "--output_format",
            "srt",
            "--output_dir",
            output_dir,
        ]

        await _run_command(cmd, "Whisper STT 실행 실패")

        whisper_output = Path(output_dir) / f"{Path(src).stem}.srt"
        expected_output = Path(output_dir) / f"{output_stem}.srt"

        if whisper_output != expected_output and whisper_output.exists():
            whisper_output.rename(expected_output)

        logger.info("SRT 자막 생성 완료: %s", out)
        return str(out)

    async def burn_subtitles(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
        style: str = "default",
    ) -> str:
        """영상에 자막을 하드코딩(burn-in)한다.

        Args:
            video_path: 입력 영상 파일 경로.
            srt_path: SRT 자막 파일 경로.
            output_path: 출력 영상 파일 경로.
            style: 자막 스타일 이름.

        Returns:
            출력 파일 경로.

        Raises:
            SubtitleError: 잘못된 입력이거나 ffmpeg 실행 실패 시.
        """
        video = _validate_path(video_path, "입력 영상")
        srt = _validate_path(srt_path, "SRT 자막")
        out = _validate_path(output_path, "출력 영상")
        _ensure_parent_dir(out)

        subtitle_filter = _build_subtitle_filter(str(srt), style)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-vf",
            subtitle_filter,
            "-c:a",
            "copy",
            str(out),
        ]

        await _run_command(cmd, "자막 삽입 실패")
        logger.info("자막 삽입 완료: %s", out)
        return str(out)


# -- 스타일 헬퍼 --

_SUBTITLE_STYLES: dict[str, str] = {
    "default": "FontName=NanumGothic,FontSize=24,PrimaryColour=&H00FFFFFF",
    "bold": "FontName=NanumGothicBold,FontSize=28,PrimaryColour=&H00FFFFFF,Bold=1",
    "minimal": "FontName=Arial,FontSize=20,PrimaryColour=&H00FFFFFF",
}


def _build_subtitle_filter(srt_path: str, style: str) -> str:
    """FFmpeg subtitles 필터 문자열을 빌드한다.

    Args:
        srt_path: SRT 파일 경로.
        style: 스타일 이름.

    Returns:
        ffmpeg -vf 인자용 문자열.
    """
    escaped_path = srt_path.replace("\\", "\\\\").replace(":", "\\:")
    style_options = _SUBTITLE_STYLES.get(style, _SUBTITLE_STYLES["default"])
    return f"subtitles={escaped_path}:force_style='{style_options}'"
