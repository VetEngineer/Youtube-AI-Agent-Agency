"""모든 모듈의 입출력 데이터 모델 (인터페이스 계약).

각 에이전트 모듈은 이 파일의 모델만 참조하여 모듈 간 결합도를 낮춥니다.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ============================================
# 공통 Enum
# ============================================


class AgentRole(str, Enum):
    BRAND_RESEARCHER = "brand_researcher"
    SCRIPT_WRITER = "script_writer"
    MEDIA_GENERATOR = "media_generator"
    MEDIA_EDITOR = "media_editor"
    SEO_OPTIMIZER = "seo_optimizer"
    PUBLISHER = "publisher"
    ANALYZER = "analyzer"


class ContentStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    FAILED = "failed"


class Formality(str, Enum):
    FORMAL = "formal"
    SEMI_FORMAL = "semi-formal"
    CASUAL = "casual"


class Emotion(str, Enum):
    WARM = "warm"
    NEUTRAL = "neutral"
    ENERGETIC = "energetic"


class HumorLevel(str, Enum):
    NONE = "none"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"


# ============================================
# Brand Researcher 출력 모델
# ============================================


class BrandInfo(BaseModel):
    name: str
    tagline: str = ""
    positioning: str = ""
    values: list[str] = Field(default_factory=list)


class TargetAudience(BaseModel):
    primary: str = ""
    pain_points: list[str] = Field(default_factory=list)
    content_needs: list[str] = Field(default_factory=list)


class WritingStyle(BaseModel):
    sentence_length: str = "medium"
    vocabulary: str = ""
    call_to_action: str = ""


class ToneAndManner(BaseModel):
    personality: str = ""
    formality: Formality = Formality.SEMI_FORMAL
    emotion: Emotion = Emotion.NEUTRAL
    humor_level: HumorLevel = HumorLevel.NONE
    writing_style: WritingStyle = Field(default_factory=WritingStyle)
    do_rules: list[str] = Field(default_factory=list, alias="do")
    dont_rules: list[str] = Field(default_factory=list, alias="dont")

    model_config = {"populate_by_name": True}


class VoiceDesign(BaseModel):
    narration_style: str = ""
    elevenlabs_voice_id: str = ""
    speech_rate: str = "moderate"
    pitch: str = "medium"
    language: str = "ko"
    reference_samples: list[str] = Field(default_factory=list)


class VisualIdentity(BaseModel):
    color_palette: list[str] = Field(default_factory=list)
    thumbnail_style: str = ""
    font_preference: str = ""


class CompetitorInfo(BaseModel):
    channel: str = ""
    strengths: list[str] = Field(default_factory=list)
    differentiation: str = ""


class BrandGuide(BaseModel):
    """Brand Researcher Agent의 최종 출력물."""

    brand: BrandInfo
    target_audience: TargetAudience = Field(default_factory=TargetAudience)
    tone_and_manner: ToneAndManner = Field(default_factory=ToneAndManner)
    voice_design: VoiceDesign = Field(default_factory=VoiceDesign)
    visual_identity: VisualIdentity = Field(default_factory=VisualIdentity)
    competitors: list[CompetitorInfo] = Field(default_factory=list)


# ============================================
# Channel 설정 모델
# ============================================


class ChannelConfig(BaseModel):
    """채널 기본 설정 (config.yaml)."""

    name: str
    youtube_channel_id: str = ""
    category: str = ""
    language: str = "ko"


class SEOConfig(BaseModel):
    primary_keywords: list[str] = Field(default_factory=list)
    secondary_keywords: list[str] = Field(default_factory=list)


class EditingConfig(BaseModel):
    intro_template: str = ""
    outro_template: str = ""
    subtitle_style: str = "default"
    bgm_volume: float = 0.15


class ChannelSettings(BaseModel):
    """채널의 전체 설정 (config.yaml 파싱 결과)."""

    channel: ChannelConfig
    seo: SEOConfig = Field(default_factory=SEOConfig)
    editing: EditingConfig = Field(default_factory=EditingConfig)


# ============================================
# Script Writer 입출력
# ============================================


class ContentPlan(BaseModel):
    """콘텐츠 기획안 (Supervisor → Script Writer)."""

    channel_id: str
    topic: str
    content_type: str = "long_form"
    target_keywords: list[str] = Field(default_factory=list)
    notes: str = ""


class Script(BaseModel):
    """생성된 원고 (Script Writer 출력)."""

    title: str
    sections: list[ScriptSection] = Field(default_factory=list)
    full_text: str = ""
    estimated_duration_seconds: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ScriptSection(BaseModel):
    heading: str = ""
    body: str = ""
    visual_notes: str = ""
    duration_seconds: int = 0


# Script에서 ScriptSection을 참조하므로 모델 재빌드
Script.model_rebuild()


# ============================================
# Media Generator 입출력
# ============================================


class VoiceGenerationRequest(BaseModel):
    """음성 합성 요청."""

    text: str
    voice_design: VoiceDesign
    output_path: str = ""


class VoiceGenerationResult(BaseModel):
    """음성 합성 결과."""

    audio_path: str
    duration_seconds: float = 0.0
    sample_rate: int = 44100


class ImageGenerationRequest(BaseModel):
    """이미지 생성 요청."""

    prompt: str
    style: str = ""
    aspect_ratio: str = "16:9"
    output_path: str = ""


class ImageGenerationResult(BaseModel):
    """이미지 생성 결과."""

    image_path: str
    width: int = 0
    height: int = 0


# ============================================
# Media Editor 입출력
# ============================================


class EditProject(BaseModel):
    """영상 편집 프로젝트."""

    source_videos: list[str] = Field(default_factory=list)
    audio_tracks: list[str] = Field(default_factory=list)
    subtitle_file: str = ""
    output_path: str = ""
    editing_config: EditingConfig = Field(default_factory=EditingConfig)


class EditResult(BaseModel):
    """편집 완료 결과."""

    output_path: str
    duration_seconds: float = 0.0
    resolution: str = "1920x1080"
    file_size_mb: float = 0.0


# ============================================
# SEO Optimizer 입출력
# ============================================


class SEOAnalysis(BaseModel):
    """SEO 분석 결과."""

    primary_keywords: list[str] = Field(default_factory=list)
    secondary_keywords: list[str] = Field(default_factory=list)
    search_volume: dict[str, int] = Field(default_factory=dict)
    competition_level: dict[str, str] = Field(default_factory=dict)


class VideoMetadata(BaseModel):
    """YouTube 업로드용 메타데이터."""

    title: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    category_id: str = "22"
    thumbnail_path: str = ""
    language: str = "ko"


# ============================================
# Publisher 입출력
# ============================================


class PublishRequest(BaseModel):
    """YouTube 업로드 요청."""

    video_path: str
    metadata: VideoMetadata
    channel_id: str
    privacy_status: str = "private"
    scheduled_at: datetime | None = None


class PublishResult(BaseModel):
    """업로드 결과."""

    video_id: str = ""
    video_url: str = ""
    status: ContentStatus = ContentStatus.PUBLISHED
    published_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: str = ""


# ============================================
# Analyzer 입출력
# ============================================


class VideoAnalytics(BaseModel):
    """개별 영상 분석 데이터."""

    video_id: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    watch_time_hours: float = 0.0
    average_view_duration_seconds: float = 0.0
    click_through_rate: float = 0.0
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChannelAnalytics(BaseModel):
    """채널 전체 분석 데이터."""

    channel_id: str
    subscriber_count: int = 0
    total_views: int = 0
    video_count: int = 0
    recent_videos: list[VideoAnalytics] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    """분석 리포트."""

    channel_id: str
    period: str = ""
    summary: str = ""
    insights: list[str] = Field(default_factory=list)
    recommended_topics: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ============================================
# Orchestrator 공유 상태
# ============================================


class AgencyState(BaseModel):
    """LangGraph Supervisor의 공유 상태.

    모든 에이전트가 이 상태를 읽고 자신의 출력을 기록합니다.
    """

    channel_id: str
    content_plan: ContentPlan | None = None
    brand_guide: BrandGuide | None = None
    script: Script | None = None
    voice_result: VoiceGenerationResult | None = None
    image_results: list[ImageGenerationResult] = Field(default_factory=list)
    edit_result: EditResult | None = None
    seo_analysis: SEOAnalysis | None = None
    metadata: VideoMetadata | None = None
    publish_result: PublishResult | None = None
    status: ContentStatus = ContentStatus.DRAFT
    current_agent: AgentRole | None = None
    errors: list[str] = Field(default_factory=list)
    messages: list[dict[str, Any]] = Field(default_factory=list)
