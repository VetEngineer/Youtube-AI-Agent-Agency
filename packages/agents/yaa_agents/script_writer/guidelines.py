"""채널별 가이드라인 및 레퍼런스 대본 로더.

채널 디렉토리에서 guidelines.md와 references/*.txt를 로드합니다.
파일이 없으면 빈 문자열/빈 리스트를 반환합니다.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 채널 루트 기준 상대 경로
_GUIDELINES_FILENAME = "guidelines.md"
_REFERENCES_SUBDIR = "references"


def _resolve_channel_dir(channels_root: Path, channel_id: str) -> Path:
    return channels_root / channel_id


def load_guidelines(channel_dir: Path) -> str:
    """채널 디렉토리에서 guidelines.md를 로드합니다.

    Args:
        channel_dir: 채널 디렉토리 경로 (예: channels/deepure-cattery/)

    Returns:
        가이드라인 텍스트. 파일 없으면 빈 문자열.
    """
    path = channel_dir / _GUIDELINES_FILENAME
    if not path.exists():
        logger.debug("guidelines.md 없음: %s", path)
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        logger.warning("guidelines.md 읽기 실패: %s", e)
        return ""


def load_references(channel_dir: Path) -> list[str]:
    """채널 디렉토리의 references/ 폴더에서 .txt 파일을 모두 로드합니다.

    Args:
        channel_dir: 채널 디렉토리 경로

    Returns:
        레퍼런스 대본 텍스트 리스트. 파일 없으면 빈 리스트.
    """
    ref_dir = channel_dir / _REFERENCES_SUBDIR
    if not ref_dir.is_dir():
        logger.debug("references/ 디렉토리 없음: %s", ref_dir)
        return []

    texts: list[str] = []
    for txt_file in sorted(ref_dir.glob("*.txt")):
        try:
            texts.append(txt_file.read_text(encoding="utf-8"))
        except OSError as e:
            logger.warning("레퍼런스 파일 읽기 실패 %s: %s", txt_file, e)

    return texts


def format_references(references: list[str]) -> str:
    """레퍼런스 대본 리스트를 프롬프트용 문자열로 포맷합니다."""
    if not references:
        return "(레퍼런스 대본 없음)"
    parts = [f"### 레퍼런스 {i + 1}\n{text}" for i, text in enumerate(references)]
    return "\n\n".join(parts)
