"""GuidelinesLoader 단위 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest
from yaa_agents.script_writer.guidelines import format_references, load_guidelines, load_references


@pytest.fixture
def channel_dir(tmp_path: Path) -> Path:
    """임시 채널 디렉토리."""
    return tmp_path / "test-channel"


def test_load_guidelines_exists(channel_dir: Path):
    """guidelines.md가 존재하면 내용을 반환한다."""
    channel_dir.mkdir()
    (channel_dir / "guidelines.md").write_text("# 가이드라인\n구어체 사용 필수", encoding="utf-8")

    result = load_guidelines(channel_dir)

    assert "# 가이드라인" in result
    assert "구어체 사용 필수" in result


def test_load_guidelines_not_found(channel_dir: Path):
    """guidelines.md가 없으면 빈 문자열을 반환한다."""
    channel_dir.mkdir()

    result = load_guidelines(channel_dir)

    assert result == ""


def test_load_guidelines_dir_not_found(tmp_path: Path):
    """채널 디렉토리 자체가 없어도 빈 문자열을 반환한다."""
    result = load_guidelines(tmp_path / "nonexistent")

    assert result == ""


def test_load_references_with_files(channel_dir: Path):
    """references/ 폴더에 txt 파일이 있으면 모두 로드한다."""
    ref_dir = channel_dir / "references"
    ref_dir.mkdir(parents=True)
    (ref_dir / "sample_a.txt").write_text("레퍼런스 A", encoding="utf-8")
    (ref_dir / "sample_b.txt").write_text("레퍼런스 B", encoding="utf-8")

    result = load_references(channel_dir)

    assert len(result) == 2
    assert "레퍼런스 A" in result
    assert "레퍼런스 B" in result


def test_load_references_no_dir(channel_dir: Path):
    """references/ 폴더가 없으면 빈 리스트를 반환한다."""
    channel_dir.mkdir()

    result = load_references(channel_dir)

    assert result == []


def test_load_references_empty_dir(channel_dir: Path):
    """references/ 폴더가 비어 있으면 빈 리스트를 반환한다."""
    (channel_dir / "references").mkdir(parents=True)

    result = load_references(channel_dir)

    assert result == []


def test_format_references_empty():
    """빈 리스트면 안내 문자열을 반환한다."""
    result = format_references([])

    assert result == "(레퍼런스 대본 없음)"


def test_format_references_with_content():
    """레퍼런스가 있으면 번호를 붙여 포맷한다."""
    result = format_references(["첫 번째 대본", "두 번째 대본"])

    assert "레퍼런스 1" in result
    assert "첫 번째 대본" in result
    assert "레퍼런스 2" in result
