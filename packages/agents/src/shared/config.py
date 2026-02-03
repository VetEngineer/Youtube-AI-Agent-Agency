"""채널 설정 관리 - YAML 로더 및 ChannelRegistry."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings

from .models import BrandGuide, ChannelSettings


class AppSettings(BaseSettings):
    """애플리케이션 전역 설정 (.env에서 로드)."""

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    elevenlabs_api_key: str = ""
    tavily_api_key: str = ""
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    channels_dir: str = "./channels"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def load_yaml(path: Path) -> dict[str, Any]:
    """YAML 파일을 딕셔너리로 로드합니다."""
    if not path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {path}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


class ChannelRegistry:
    """채널 설정을 관리하는 레지스트리.

    channels/ 디렉토리에서 채널별 config.yaml과 brand_guide.yaml을 로드합니다.
    """

    def __init__(self, channels_dir: str | Path = "./channels") -> None:
        self._channels_dir = Path(channels_dir)
        self._settings_cache: dict[str, ChannelSettings] = {}
        self._brand_guide_cache: dict[str, BrandGuide] = {}

    @property
    def channels_dir(self) -> Path:
        return self._channels_dir

    def list_channels(self) -> list[str]:
        """등록된 채널 ID 목록을 반환합니다 (디렉토리명 기준)."""
        if not self._channels_dir.exists():
            return []
        return [
            d.name
            for d in sorted(self._channels_dir.iterdir())
            if d.is_dir() and not d.name.startswith("_")
        ]

    @staticmethod
    def _validate_channel_id(channel_id: str) -> None:
        """channel_id의 유효성을 검증합니다 (경로 순회 방지)."""
        if not channel_id or not re.match(r"^[a-zA-Z0-9_-]+$", channel_id):
            raise ValueError(f"유효하지 않은 channel_id입니다: {channel_id!r}")

    def get_channel_path(self, channel_id: str) -> Path:
        """채널 디렉토리 경로를 반환합니다."""
        self._validate_channel_id(channel_id)
        path = (self._channels_dir / channel_id).resolve()
        if not str(path).startswith(str(self._channels_dir.resolve())):
            raise ValueError(f"잘못된 경로 접근: {channel_id}")
        if not path.exists():
            raise FileNotFoundError(f"채널을 찾을 수 없습니다: {channel_id}")
        return path

    def load_settings(self, channel_id: str) -> ChannelSettings:
        """채널의 config.yaml을 로드합니다."""
        if channel_id in self._settings_cache:
            return self._settings_cache[channel_id]

        config_path = self.get_channel_path(channel_id) / "config.yaml"
        data = load_yaml(config_path)
        settings = ChannelSettings(**data)
        self._settings_cache[channel_id] = settings
        return settings

    def load_brand_guide(self, channel_id: str) -> BrandGuide:
        """채널의 brand_guide.yaml을 로드합니다."""
        if channel_id in self._brand_guide_cache:
            return self._brand_guide_cache[channel_id]

        guide_path = self.get_channel_path(channel_id) / "brand_guide.yaml"
        data = load_yaml(guide_path)
        guide = BrandGuide(**data)
        self._brand_guide_cache[channel_id] = guide
        return guide

    def has_brand_guide(self, channel_id: str) -> bool:
        """채널에 brand_guide.yaml이 존재하는지 확인합니다."""
        try:
            guide_path = self.get_channel_path(channel_id) / "brand_guide.yaml"
            return guide_path.exists()
        except FileNotFoundError:
            return False

    def save_brand_guide(self, channel_id: str, guide: BrandGuide) -> Path:
        """brand_guide.yaml을 채널 디렉토리에 저장합니다."""
        channel_path = self.get_channel_path(channel_id)
        guide_path = channel_path / "brand_guide.yaml"

        data = guide.model_dump(mode="json", by_alias=True, exclude_none=True)
        with open(guide_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        self._brand_guide_cache[channel_id] = guide
        return guide_path

    def clear_cache(self) -> None:
        """캐시를 초기화합니다."""
        self._settings_cache.clear()
        self._brand_guide_cache.clear()

    def create_channel_from_template(self, channel_id: str) -> Path:
        """템플릿에서 새 채널 디렉토리를 생성합니다."""
        self._validate_channel_id(channel_id)
        template_dir = self._channels_dir / "_template"
        new_channel_dir = self._channels_dir / channel_id

        if new_channel_dir.exists():
            raise FileExistsError(f"채널이 이미 존재합니다: {channel_id}")

        new_channel_dir.mkdir(parents=True)
        (new_channel_dir / "sources").mkdir()

        if template_dir.exists():
            for template_file in template_dir.glob("*.yaml"):
                content = template_file.read_text(encoding="utf-8")
                (new_channel_dir / template_file.name).write_text(content, encoding="utf-8")

        return new_channel_dir
