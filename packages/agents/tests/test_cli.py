"""CLI 엔트리포인트 테스트."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from src.cli import _build_parser, _cmd_channels_create, _cmd_channels_list, main

# ============================================
# Parser 테스트
# ============================================


class TestBuildParser:
    """CLI 파서 빌드 테스트."""

    def test_파서_생성(self):
        parser = _build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_run_명령어_파싱(self):
        parser = _build_parser()
        args = parser.parse_args(["run", "--channel", "test-channel", "--topic", "테스트 주제"])
        assert args.command == "run"
        assert args.channel == "test-channel"
        assert args.topic == "테스트 주제"
        assert args.dry_run is False

    def test_run_dry_run_플래그(self):
        parser = _build_parser()
        args = parser.parse_args(["run", "--channel", "ch", "--topic", "t", "--dry-run"])
        assert args.dry_run is True

    def test_channels_list_파싱(self):
        parser = _build_parser()
        args = parser.parse_args(["channels", "list"])
        assert args.command == "channels"
        assert args.channels_command == "list"

    def test_channels_create_파싱(self):
        parser = _build_parser()
        args = parser.parse_args(["channels", "create", "new-channel"])
        assert args.command == "channels"
        assert args.channels_command == "create"
        assert args.channel_id == "new-channel"

    def test_brand_research_파싱(self):
        parser = _build_parser()
        args = parser.parse_args(["brand-research", "--channel", "ch", "--brand", "브랜드"])
        assert args.command == "brand-research"
        assert args.channel == "ch"
        assert args.brand == "브랜드"


# ============================================
# 채널 명령어 테스트
# ============================================


class TestChannelsList:
    """channels list 명령어 테스트."""

    @pytest.fixture()
    def _channels_dir(self, tmp_path: Path) -> Path:
        ch_dir = tmp_path / "channels"
        ch_dir.mkdir()
        return ch_dir

    async def test_빈_채널_목록(self, _channels_dir: Path, capsys):
        with patch(
            "src.cli.AppSettings",
            return_value=type("S", (), {"channels_dir": str(_channels_dir), "log_level": "INFO"})(),
        ):
            result = await _cmd_channels_list(argparse.Namespace())

        assert result == 0
        captured = capsys.readouterr()
        assert "등록된 채널이 없습니다" in captured.out

    async def test_채널_목록_출력(self, _channels_dir: Path, capsys):
        # 채널 디렉토리 + config.yaml 생성
        ch = _channels_dir / "test-ch"
        ch.mkdir()
        (ch / "config.yaml").write_text(
            "channel:\n  name: '테스트'\n  category: 'test'\n",
            encoding="utf-8",
        )

        with patch(
            "src.cli.AppSettings",
            return_value=type("S", (), {"channels_dir": str(_channels_dir), "log_level": "INFO"})(),
        ):
            result = await _cmd_channels_list(argparse.Namespace())

        assert result == 0
        captured = capsys.readouterr()
        assert "test-ch" in captured.out
        assert "테스트" in captured.out


class TestChannelsCreate:
    """channels create 명령어 테스트."""

    async def test_채널_생성(self, tmp_path: Path, capsys):
        ch_dir = tmp_path / "channels"
        ch_dir.mkdir()
        # 템플릿 디렉토리 생성
        template = ch_dir / "_template"
        template.mkdir()
        (template / "config.yaml").write_text("channel:\n  name: ''\n", encoding="utf-8")

        with patch(
            "src.cli.AppSettings",
            return_value=type("S", (), {"channels_dir": str(ch_dir), "log_level": "INFO"})(),
        ):
            args = argparse.Namespace(channel_id="new-channel")
            result = await _cmd_channels_create(args)

        assert result == 0
        assert (ch_dir / "new-channel" / "config.yaml").exists()

    async def test_중복_채널_생성_실패(self, tmp_path: Path, capsys):
        ch_dir = tmp_path / "channels"
        ch_dir.mkdir()
        (ch_dir / "existing").mkdir()

        with patch(
            "src.cli.AppSettings",
            return_value=type("S", (), {"channels_dir": str(ch_dir), "log_level": "INFO"})(),
        ):
            args = argparse.Namespace(channel_id="existing")
            result = await _cmd_channels_create(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "이미 존재합니다" in captured.out


# ============================================
# main() 테스트
# ============================================


class TestMain:
    """main() 엔트리포인트 테스트."""

    def test_명령어_없으면_도움말(self):
        with patch("sys.argv", ["youtube-agent"]):
            result = main()
        assert result == 1

    def test_channels_list_호출(self, tmp_path: Path):
        ch_dir = tmp_path / "channels"
        ch_dir.mkdir()

        with (
            patch("sys.argv", ["youtube-agent", "channels", "list"]),
            patch(
                "src.cli.AppSettings",
                return_value=type(
                    "S",
                    (),
                    {"channels_dir": str(ch_dir), "log_level": "INFO"},
                )(),
            ),
        ):
            result = main()

        assert result == 0
