"""shared 모듈 단위 테스트."""

from pathlib import Path

import pytest
import yaml

from src.shared.config import ChannelRegistry, load_yaml
from src.shared.models import (
    AgencyState,
    BrandGuide,
    BrandInfo,
    ChannelSettings,
    ContentPlan,
    ContentStatus,
    Script,
    ScriptSection,
    ToneAndManner,
    VoiceDesign,
)

# ============================================
# models.py 테스트
# ============================================


class TestBrandGuide:
    def test_brand_guide_minimal(self):
        guide = BrandGuide(brand=BrandInfo(name="테스트 브랜드"))
        assert guide.brand.name == "테스트 브랜드"
        assert guide.tone_and_manner.formality == "semi-formal"

    def test_brand_guide_full(self):
        guide = BrandGuide(
            brand=BrandInfo(
                name="딥퓨어캐터리",
                tagline="건강한 혈통, 따뜻한 가족",
                positioning="프리미엄 고양이 브리더",
                values=["전문성", "신뢰"],
            ),
            tone_and_manner=ToneAndManner(
                personality="따뜻하지만 전문적인",
                formality="semi-formal",
                emotion="warm",
                do=["전문 지식 풀어 설명"],
                dont=["과도한 판매 압박"],
            ),
            voice_design=VoiceDesign(
                narration_style="차분한 여성 목소리",
                language="ko",
            ),
        )
        assert guide.brand.positioning == "프리미엄 고양이 브리더"
        assert len(guide.tone_and_manner.do_rules) == 1
        assert guide.voice_design.language == "ko"

    def test_brand_guide_serialization(self):
        guide = BrandGuide(brand=BrandInfo(name="테스트"))
        data = guide.model_dump()
        restored = BrandGuide(**data)
        assert restored.brand.name == "테스트"


class TestChannelSettings:
    def test_channel_settings_from_dict(self):
        data = {
            "channel": {
                "name": "딥퓨어캐터리",
                "youtube_channel_id": "UC123",
                "category": "pets",
            },
            "seo": {
                "primary_keywords": ["고양이 브리더"],
            },
        }
        settings = ChannelSettings(**data)
        assert settings.channel.name == "딥퓨어캐터리"
        assert settings.channel.category == "pets"
        assert settings.seo.primary_keywords == ["고양이 브리더"]


class TestScript:
    def test_script_creation(self):
        script = Script(
            title="고양이 건강 관리 팁",
            sections=[
                ScriptSection(heading="인트로", body="안녕하세요", duration_seconds=10),
                ScriptSection(heading="본론", body="건강 관리 방법은...", duration_seconds=120),
            ],
            full_text="안녕하세요. 건강 관리 방법은...",
            estimated_duration_seconds=130,
        )
        assert len(script.sections) == 2
        assert script.estimated_duration_seconds == 130


class TestAgencyState:
    def test_initial_state(self):
        state = AgencyState(channel_id="deepure-cattery")
        assert state.status == ContentStatus.DRAFT
        assert state.script is None
        assert state.errors == []

    def test_state_with_plan(self):
        state = AgencyState(
            channel_id="deepure-cattery",
            content_plan=ContentPlan(
                channel_id="deepure-cattery",
                topic="고양이 건강 관리",
                target_keywords=["고양이 건강"],
            ),
        )
        assert state.content_plan is not None
        assert state.content_plan.topic == "고양이 건강 관리"


# ============================================
# config.py 테스트
# ============================================


class TestLoadYaml:
    def test_load_valid_yaml(self, tmp_path: Path):
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\nlist:\n  - a\n  - b", encoding="utf-8")
        data = load_yaml(yaml_file)
        assert data["key"] == "value"
        assert data["list"] == ["a", "b"]

    def test_load_nonexistent_yaml(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_yaml(tmp_path / "missing.yaml")


class TestChannelRegistry:
    @pytest.fixture
    def registry_with_channels(self, tmp_path: Path) -> ChannelRegistry:
        channels_dir = tmp_path / "channels"
        channels_dir.mkdir()

        # 템플릿
        template_dir = channels_dir / "_template"
        template_dir.mkdir()
        (template_dir / "config.yaml").write_text(
            yaml.dump({"channel": {"name": "", "youtube_channel_id": "", "category": ""}}),
            encoding="utf-8",
        )
        (template_dir / "brand_guide.yaml").write_text(
            yaml.dump({"brand": {"name": ""}}),
            encoding="utf-8",
        )

        # 딥퓨어캐터리 채널
        cattery_dir = channels_dir / "deepure-cattery"
        cattery_dir.mkdir()
        (cattery_dir / "config.yaml").write_text(
            yaml.dump(
                {
                    "channel": {
                        "name": "딥퓨어캐터리",
                        "youtube_channel_id": "UC123",
                        "category": "pets",
                    },
                    "seo": {"primary_keywords": ["고양이"]},
                }
            ),
            encoding="utf-8",
        )
        (cattery_dir / "brand_guide.yaml").write_text(
            yaml.dump(
                {
                    "brand": {
                        "name": "딥퓨어캐터리",
                        "tagline": "건강한 혈통",
                        "positioning": "프리미엄 브리더",
                        "values": ["전문성"],
                    },
                }
            ),
            encoding="utf-8",
        )

        return ChannelRegistry(channels_dir)

    def test_list_channels(self, registry_with_channels: ChannelRegistry):
        channels = registry_with_channels.list_channels()
        assert "deepure-cattery" in channels
        assert "_template" not in channels

    def test_load_settings(self, registry_with_channels: ChannelRegistry):
        settings = registry_with_channels.load_settings("deepure-cattery")
        assert settings.channel.name == "딥퓨어캐터리"
        assert settings.channel.category == "pets"

    def test_load_brand_guide(self, registry_with_channels: ChannelRegistry):
        guide = registry_with_channels.load_brand_guide("deepure-cattery")
        assert guide.brand.name == "딥퓨어캐터리"
        assert guide.brand.positioning == "프리미엄 브리더"

    def test_has_brand_guide(self, registry_with_channels: ChannelRegistry):
        assert registry_with_channels.has_brand_guide("deepure-cattery") is True

    def test_save_brand_guide(self, registry_with_channels: ChannelRegistry):
        guide = BrandGuide(
            brand=BrandInfo(name="새 브랜드", tagline="새 태그라인"),
        )
        path = registry_with_channels.save_brand_guide("deepure-cattery", guide)
        assert path.exists()

        reloaded_data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert reloaded_data["brand"]["name"] == "새 브랜드"

    def test_create_channel_from_template(self, registry_with_channels: ChannelRegistry):
        new_path = registry_with_channels.create_channel_from_template("new-channel")
        assert new_path.exists()
        assert (new_path / "config.yaml").exists()
        assert (new_path / "brand_guide.yaml").exists()
        assert (new_path / "sources").is_dir()

    def test_create_duplicate_channel_raises(self, registry_with_channels: ChannelRegistry):
        with pytest.raises(FileExistsError):
            registry_with_channels.create_channel_from_template("deepure-cattery")

    def test_load_nonexistent_channel_raises(self, registry_with_channels: ChannelRegistry):
        with pytest.raises(FileNotFoundError):
            registry_with_channels.load_settings("nonexistent")

    def test_cache_invalidation(self, registry_with_channels: ChannelRegistry):
        registry_with_channels.load_settings("deepure-cattery")
        assert "deepure-cattery" in registry_with_channels._settings_cache
        registry_with_channels.clear_cache()
        assert "deepure-cattery" not in registry_with_channels._settings_cache
