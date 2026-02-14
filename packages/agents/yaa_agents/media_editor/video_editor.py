"""FFmpeg 기반 영상 편집 모듈.

컷 편집, 영상 결합, 인트로/아웃트로 삽입 기능을 제공합니다.
내부적으로 subprocess를 사용하여 ffmpeg CLI를 호출합니다.
"""

from __future__ import annotations

import asyncio
import logging
import shlex
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoEditorError(Exception):
    """영상 편집 중 발생하는 에러."""


def _validate_path(path: str, label: str) -> Path:
    """경로 문자열을 검증하고 Path 객체로 반환한다."""
    if not path or not path.strip():
        raise VideoEditorError(f"{label} 경로가 비어 있습니다")
    return Path(path)


def _ensure_parent_dir(path: Path) -> None:
    """출력 경로의 부모 디렉토리가 존재하는지 확인한다."""
    path.parent.mkdir(parents=True, exist_ok=True)


async def _run_ffmpeg(args: list[str]) -> str:
    """ffmpeg 명령을 비동기로 실행한다.

    Args:
        args: ffmpeg에 전달할 인자 목록 (ffmpeg 자체는 포함하지 않음).

    Returns:
        실행된 전체 명령 문자열.

    Raises:
        VideoEditorError: ffmpeg 실행 실패 시.
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
        raise VideoEditorError("ffmpeg가 설치되어 있지 않습니다") from exc

    if process.returncode != 0:
        error_msg = stderr.decode(errors="replace").strip()
        raise VideoEditorError(f"ffmpeg 실행 실패 (code={process.returncode}): {error_msg}")

    return cmd_str


class VideoEditor:
    """FFmpeg를 사용한 영상 편집기."""

    async def cut_video(
        self,
        input_path: str,
        segments: list[tuple[float, float]],
        output_path: str,
    ) -> str:
        """영상에서 지정된 구간들을 추출하고 결합한다.

        Args:
            input_path: 원본 영상 파일 경로.
            segments: (시작초, 끝초) 튜플 리스트.
            output_path: 출력 영상 파일 경로.

        Returns:
            출력 파일 경로.

        Raises:
            VideoEditorError: 잘못된 입력이거나 ffmpeg 실행 실패 시.
        """
        src = _validate_path(input_path, "입력 영상")
        out = _validate_path(output_path, "출력 영상")
        _ensure_parent_dir(out)

        if not segments:
            raise VideoEditorError("segments가 비어 있습니다")

        for start, end in segments:
            if start < 0 or end <= start:
                raise VideoEditorError(f"잘못된 구간: start={start}, end={end}")

        filter_parts = []
        for idx, (start, end) in enumerate(segments):
            filter_parts.append(
                f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{idx}];"
                f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{idx}];"
            )

        concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(len(segments)))
        filter_complex = (
            "".join(filter_parts) + f"{concat_inputs}concat=n={len(segments)}:v=1:a=1[outv][outa]"
        )

        args = [
            "-i",
            str(src),
            "-filter_complex",
            filter_complex,
            "-map",
            "[outv]",
            "-map",
            "[outa]",
            str(out),
        ]

        await _run_ffmpeg(args)
        logger.info("컷 편집 완료: %s", out)
        return str(out)

    async def concatenate(
        self,
        video_paths: list[str],
        output_path: str,
    ) -> str:
        """여러 영상을 순서대로 결합한다.

        Args:
            video_paths: 결합할 영상 파일 경로 리스트.
            output_path: 출력 영상 파일 경로.

        Returns:
            출력 파일 경로.

        Raises:
            VideoEditorError: 잘못된 입력이거나 ffmpeg 실행 실패 시.
        """
        if not video_paths:
            raise VideoEditorError("결합할 영상 목록이 비어 있습니다")

        out = _validate_path(output_path, "출력 영상")
        _ensure_parent_dir(out)

        validated_paths = [str(_validate_path(p, f"영상[{i}]")) for i, p in enumerate(video_paths)]

        input_args: list[str] = []
        for p in validated_paths:
            input_args.extend(["-i", p])

        n = len(validated_paths)
        streams = "".join(f"[{i}:v:0][{i}:a:0]" for i in range(n))
        filter_complex = f"{streams}concat=n={n}:v=1:a=1[outv][outa]"

        args = [
            *input_args,
            "-filter_complex",
            filter_complex,
            "-map",
            "[outv]",
            "-map",
            "[outa]",
            str(out),
        ]

        await _run_ffmpeg(args)
        logger.info("영상 결합 완료: %s", out)
        return str(out)

    async def add_intro_outro(
        self,
        video_path: str,
        intro_path: str | None,
        outro_path: str | None,
        output_path: str,
    ) -> str:
        """메인 영상에 인트로/아웃트로를 추가한다.

        Args:
            video_path: 메인 영상 파일 경로.
            intro_path: 인트로 영상 경로 (None이면 생략).
            outro_path: 아웃트로 영상 경로 (None이면 생략).
            output_path: 출력 영상 파일 경로.

        Returns:
            출력 파일 경로.

        Raises:
            VideoEditorError: 잘못된 입력이거나 ffmpeg 실행 실패 시.
        """
        parts: list[str] = []

        if intro_path:
            parts.append(str(_validate_path(intro_path, "인트로")))

        parts.append(str(_validate_path(video_path, "메인 영상")))

        if outro_path:
            parts.append(str(_validate_path(outro_path, "아웃트로")))

        if len(parts) == 1:
            raise VideoEditorError(
                "인트로와 아웃트로가 모두 없으면 add_intro_outro를 호출할 필요가 없습니다"
            )

        return await self.concatenate(parts, output_path)

    async def merge_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
    ) -> str:
        """영상과 오디오를 합성한다.

        Args:
            video_path: 영상 파일 경로.
            audio_path: 오디오 파일 경로.
            output_path: 출력 영상 파일 경로.

        Returns:
            출력 파일 경로.

        Raises:
            VideoEditorError: ffmpeg 실행 실패 시.
        """
        src_video = _validate_path(video_path, "영상")
        src_audio = _validate_path(audio_path, "오디오")
        out = _validate_path(output_path, "출력 영상")
        _ensure_parent_dir(out)

        args = [
            "-i",
            str(src_video),
            "-i",
            str(src_audio),
            "-c:v",
            "copy",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-shortest",
            str(out),
        ]

        await _run_ffmpeg(args)
        logger.info("영상+오디오 합성 완료: %s", out)
        return str(out)
