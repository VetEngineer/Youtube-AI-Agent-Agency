"""SQLAlchemy ORM 모델 정의."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """모든 ORM 모델의 기반 클래스."""


class UserModel(Base):
    """사용자."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, default="email")
    provider_account_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    workspaces: Mapped[list[WorkspaceModel]] = relationship(back_populates="owner", lazy="selectin")

    def to_dict(self) -> dict:
        """딕셔너리로 변환합니다."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "image": self.image,
            "provider": self.provider,
            "plan": self.plan,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WorkspaceModel(Base):
    """워크스페이스 (멀티테넌시 단위)."""

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    pipeline_quota: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    channel_quota: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    youtube_api_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    elevenlabs_api_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    owner: Mapped[UserModel] = relationship(back_populates="workspaces", lazy="selectin")

    def to_dict(self) -> dict:
        """딕셔너리로 변환합니다."""
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "plan": self.plan,
            "pipeline_quota": self.pipeline_quota,
            "channel_quota": self.channel_quota,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SubscriptionModel(Base):
    """Stripe 구독 정보."""

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stripe_customer_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, unique=True
    )
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, canceled, past_due
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        """딕셔너리로 변환합니다."""
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "stripe_customer_id": self.stripe_customer_id,
            "stripe_subscription_id": self.stripe_subscription_id,
            "plan": self.plan,
            "status": self.status,
            "current_period_start": (
                self.current_period_start.isoformat() if self.current_period_start else None
            ),
            "current_period_end": (
                self.current_period_end.isoformat() if self.current_period_end else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PipelineRunModel(Base):
    """파이프라인 실행 이력."""

    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    channel_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True
    )
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    brand_name: Mapped[str] = mapped_column(String(200), default="")
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    current_agent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    errors_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def result(self) -> dict | None:
        if self.result_json is None:
            return None
        return json.loads(self.result_json)

    @result.setter
    def result(self, value: dict | None) -> None:
        self.result_json = json.dumps(value, ensure_ascii=False) if value else None

    @property
    def errors(self) -> list[str]:
        return json.loads(self.errors_json) if self.errors_json else []

    @errors.setter
    def errors(self, value: list[str]) -> None:
        self.errors_json = json.dumps(value, ensure_ascii=False)

    def to_dict(self) -> dict:
        """딕셔너리로 변환합니다."""
        return {
            "run_id": self.id,
            "channel_id": self.channel_id,
            "workspace_id": self.workspace_id,
            "topic": self.topic,
            "brand_name": self.brand_name,
            "dry_run": self.dry_run,
            "status": self.status,
            "current_agent": self.current_agent,
            "result": self.result,
            "errors": self.errors,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ApiKeyModel(Base):
    """API 키."""

    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    key_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True
    )
    scopes_json: Mapped[str] = mapped_column(Text, default='["read","write"]')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def scopes(self) -> list[str]:
        return json.loads(self.scopes_json) if self.scopes_json else []

    @scopes.setter
    def scopes(self, value: list[str]) -> None:
        self.scopes_json = json.dumps(value)

    def to_dict(self) -> dict:
        """딕셔너리로 변환합니다."""
        return {
            "id": self.id,
            "name": self.name,
            "workspace_id": self.workspace_id,
            "scopes": self.scopes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }


class AuditLogModel(Base):
    """요청 감사 로그."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), index=True
    )
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    api_key_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    workspace_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)


class CompetitorChannelModel(Base):
    """경쟁 채널 모니터링."""

    __tablename__ = "competitor_channels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    youtube_channel_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subscriber_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    video_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    videos: Mapped[list[CompetitorVideoModel]] = relationship(
        back_populates="channel", lazy="selectin", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        """딕셔너리로 변환합니다."""
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "youtube_channel_id": self.youtube_channel_id,
            "name": self.name,
            "description": self.description,
            "subscriber_count": self.subscriber_count,
            "video_count": self.video_count,
            "thumbnail_url": self.thumbnail_url,
            "last_crawled_at": self.last_crawled_at.isoformat() if self.last_crawled_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CompetitorVideoModel(Base):
    """경쟁 채널 영상 데이터."""

    __tablename__ = "competitor_videos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    competitor_channel_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("competitor_channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    video_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    channel: Mapped[CompetitorChannelModel] = relationship(back_populates="videos")

    __table_args__ = (
        UniqueConstraint(
            "competitor_channel_id", "video_id", name="uq_competitor_video"
        ),
    )

    @property
    def tags(self) -> list[str]:
        return json.loads(self.tags_json) if self.tags_json else []

    @tags.setter
    def tags(self, value: list[str]) -> None:
        self.tags_json = json.dumps(value, ensure_ascii=False)

    def to_dict(self) -> dict:
        """딕셔너리로 변환합니다."""
        return {
            "id": self.id,
            "competitor_channel_id": self.competitor_channel_id,
            "video_id": self.video_id,
            "title": self.title,
            "description": self.description,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "tags": self.tags,
            "duration_seconds": self.duration_seconds,
            "thumbnail_url": self.thumbnail_url,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
        }


class OAuthTokenModel(Base):
    """OAuth 토큰 (YouTube 등) DB 저장."""

    __tablename__ = "oauth_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False, default="youtube")

    __table_args__ = (
        UniqueConstraint("workspace_id", "provider", name="uq_oauth_tokens_ws_provider"),
    )
    token_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class UsageEventModel(Base):
    """LLM 사용량 이벤트."""

    __tablename__ = "usage_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    agent: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, index=True, default=lambda: datetime.now(UTC)
    )

    def to_dict(self) -> dict:
        """딕셔너리로 변환합니다."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "agent": self.agent,
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
