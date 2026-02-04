"""FastAPI 의존성 주입."""

from __future__ import annotations

from functools import lru_cache

from src.shared.config import AppSettings, ChannelRegistry


@lru_cache
def get_settings() -> AppSettings:
    """애플리케이션 설정 싱글톤."""
    return AppSettings()


@lru_cache
def get_channel_registry() -> ChannelRegistry:
    """ChannelRegistry 싱글톤."""
    settings = get_settings()
    return ChannelRegistry(settings.channels_dir)
