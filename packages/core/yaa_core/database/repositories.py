"""Repository 패턴 - 데이터 접근 계층."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from yaa_core.database.models import (
    ApiKeyModel,
    AuditLogModel,
    CompetitorChannelModel,
    CompetitorVideoModel,
    OAuthTokenModel,
    PipelineRunModel,
    SubscriptionModel,
    UsageEventModel,
    UserModel,
    WorkspaceModel,
)


class UserRepository:
    """사용자 저장소."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: str,
        email: str,
        name: str | None = None,
        image: str | None = None,
        provider: str = "email",
        provider_account_id: str | None = None,
    ) -> UserModel:
        """새 사용자를 생성합니다."""
        user = UserModel(
            id=user_id,
            email=email,
            name=name,
            image=image,
            provider=provider,
            provider_account_id=provider_account_id,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def get(self, user_id: str) -> UserModel | None:
        """사용자 ID로 조회합니다."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserModel | None:
        """이메일로 사용자를 조회합니다."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        return result.scalar_one_or_none()

    async def get_or_create_by_oauth(
        self,
        email: str,
        name: str | None,
        image: str | None,
        provider: str,
        provider_account_id: str | None,
    ) -> tuple[UserModel, bool]:
        """OAuth 로그인 시 사용자를 조회하거나 새로 생성합니다.

        Returns:
            (user, created) 튜플
        """
        import uuid

        existing = await self.get_by_email(email)
        if existing:
            return existing, False

        user = await self.create(
            user_id=str(uuid.uuid4()),
            email=email,
            name=name,
            image=image,
            provider=provider,
            provider_account_id=provider_account_id,
        )
        return user, True

    async def update(self, user_id: str, **kwargs: Any) -> None:
        """사용자 정보를 업데이트합니다."""
        kwargs["updated_at"] = datetime.now(UTC)
        await self._session.execute(
            update(UserModel).where(UserModel.id == user_id).values(**kwargs)
        )


class WorkspaceRepository:
    """워크스페이스 저장소."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        workspace_id: str,
        name: str,
        owner_id: str,
        plan: str = "free",
        pipeline_quota: int = 5,
        channel_quota: int = 1,
    ) -> WorkspaceModel:
        """새 워크스페이스를 생성합니다."""
        workspace = WorkspaceModel(
            id=workspace_id,
            name=name,
            owner_id=owner_id,
            plan=plan,
            pipeline_quota=pipeline_quota,
            channel_quota=channel_quota,
        )
        self._session.add(workspace)
        await self._session.flush()
        return workspace

    async def get(self, workspace_id: str) -> WorkspaceModel | None:
        """워크스페이스 ID로 조회합니다."""
        result = await self._session.execute(
            select(WorkspaceModel).where(WorkspaceModel.id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def list_by_owner(self, owner_id: str) -> list[WorkspaceModel]:
        """소유자의 워크스페이스 목록을 조회합니다."""
        result = await self._session.execute(
            select(WorkspaceModel)
            .where(WorkspaceModel.owner_id == owner_id)
            .order_by(WorkspaceModel.created_at.asc())
        )
        return list(result.scalars().all())

    async def update(self, workspace_id: str, **kwargs: Any) -> None:
        """워크스페이스 정보를 업데이트합니다."""
        await self._session.execute(
            update(WorkspaceModel)
            .where(WorkspaceModel.id == workspace_id)
            .values(**kwargs)
        )


class RunRepository:
    """파이프라인 실행 이력 저장소."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        run_id: str,
        channel_id: str,
        topic: str,
        brand_name: str = "",
        dry_run: bool = False,
        workspace_id: str | None = None,
    ) -> PipelineRunModel:
        """새 파이프라인 실행을 생성합니다."""
        run = PipelineRunModel(
            id=run_id,
            channel_id=channel_id,
            topic=topic,
            brand_name=brand_name,
            dry_run=dry_run,
            status="pending",
            workspace_id=workspace_id,
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def get(self, run_id: str) -> PipelineRunModel | None:
        """실행 ID로 조회합니다."""
        result = await self._session.execute(
            select(PipelineRunModel).where(PipelineRunModel.id == run_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        run_id: str,
        status: str,
        current_agent: str | None = None,
        result: dict[str, Any] | None = None,
        errors: list[str] | None = None,
    ) -> None:
        """실행 상태를 업데이트합니다."""
        import json

        values: dict[str, Any] = {
            "status": status,
            "updated_at": datetime.now(UTC),
        }
        if current_agent is not None:
            values["current_agent"] = current_agent
        if result is not None:
            values["result_json"] = json.dumps(result, ensure_ascii=False)
        if errors is not None:
            values["errors_json"] = json.dumps(errors, ensure_ascii=False)
        if status in ("completed", "failed", "cancelled"):
            values["completed_at"] = datetime.now(UTC)

        await self._session.execute(
            update(PipelineRunModel).where(PipelineRunModel.id == run_id).values(**values)
        )

    async def list_by_channel(
        self, channel_id: str, limit: int = 20, offset: int = 0
    ) -> list[PipelineRunModel]:
        """채널별 실행 목록을 조회합니다."""
        result = await self._session.execute(
            select(PipelineRunModel)
            .where(PipelineRunModel.channel_id == channel_id)
            .order_by(PipelineRunModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_recent(
        self, limit: int = 20, offset: int = 0, workspace_id: str | None = None
    ) -> list[PipelineRunModel]:
        """최근 실행 목록을 조회합니다."""
        query = select(PipelineRunModel)
        if workspace_id is not None:
            query = query.where(PipelineRunModel.workspace_id == workspace_id)
        query = query.order_by(PipelineRunModel.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    def _build_filter_query(
        self,
        channel_id: str | None = None,
        status: str | None = None,
        workspace_id: str | None = None,
    ) -> list:
        """필터 조건을 생성합니다."""
        conditions = []
        if channel_id is not None:
            conditions.append(PipelineRunModel.channel_id == channel_id)
        if status is not None:
            conditions.append(PipelineRunModel.status == status)
        if workspace_id is not None:
            conditions.append(PipelineRunModel.workspace_id == workspace_id)
        return conditions

    async def list_with_filters(
        self,
        channel_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
        workspace_id: str | None = None,
    ) -> list[PipelineRunModel]:
        """필터링과 페이지네이션을 지원하는 목록 조회."""
        conditions = self._build_filter_query(channel_id, status, workspace_id)
        query = (
            select(PipelineRunModel)
            .where(*conditions)
            .order_by(PipelineRunModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_with_filters(
        self,
        channel_id: str | None = None,
        status: str | None = None,
        workspace_id: str | None = None,
    ) -> int:
        """필터링된 결과의 총 개수를 반환합니다."""
        conditions = self._build_filter_query(channel_id, status, workspace_id)
        query = select(func.count(PipelineRunModel.id)).where(*conditions)
        result = await self._session.execute(query)
        return result.scalar_one()

    async def get_stats(self, workspace_id: str | None = None) -> dict[str, int]:
        """대시보드용 통계를 조회합니다."""
        base_filter = []
        if workspace_id is not None:
            base_filter.append(PipelineRunModel.workspace_id == workspace_id)

        total_result = await self._session.execute(
            select(func.count(PipelineRunModel.id)).where(*base_filter)
        )
        total = total_result.scalar_one()

        status_counts = {}
        for s in ["pending", "running", "completed", "failed"]:
            result = await self._session.execute(
                select(func.count(PipelineRunModel.id)).where(
                    PipelineRunModel.status == s, *base_filter
                )
            )
            status_counts[s] = result.scalar_one()

        return {
            "total": total,
            "pending": status_counts["pending"],
            "running": status_counts["running"],
            "completed": status_counts["completed"],
            "failed": status_counts["failed"],
        }

    async def get_avg_duration(
        self, days: int = 30, workspace_id: str | None = None
    ) -> float | None:
        """최근 N일간 완료된 실행의 평균 소요시간(초)을 계산합니다."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        conditions = [
            PipelineRunModel.status == "completed",
            PipelineRunModel.completed_at.is_not(None),
            PipelineRunModel.created_at >= cutoff,
        ]
        if workspace_id is not None:
            conditions.append(PipelineRunModel.workspace_id == workspace_id)

        query = select(
            PipelineRunModel.created_at,
            PipelineRunModel.completed_at,
        ).where(*conditions)
        result = await self._session.execute(query)
        rows = result.all()
        if not rows:
            return None
        durations = [
            (row.completed_at - row.created_at).total_seconds()
            for row in rows
        ]
        return sum(durations) / len(durations)

    async def count_monthly(self, workspace_id: str) -> int:
        """이번 달 파이프라인 실행 횟수를 반환합니다."""
        now = datetime.now(UTC)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        result = await self._session.execute(
            select(func.count(PipelineRunModel.id)).where(
                PipelineRunModel.workspace_id == workspace_id,
                PipelineRunModel.created_at >= month_start,
            )
        )
        return result.scalar_one()


class ApiKeyRepository:
    """API 키 저장소."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        key_id: str,
        key_hash: str,
        name: str,
        scopes: list[str] | None = None,
        workspace_id: str | None = None,
    ) -> ApiKeyModel:
        """새 API 키를 생성합니다."""
        import json

        api_key = ApiKeyModel(
            id=key_id,
            key_hash=key_hash,
            name=name,
            scopes_json=json.dumps(scopes or ["read", "write"]),
            workspace_id=workspace_id,
        )
        self._session.add(api_key)
        await self._session.flush()
        return api_key

    async def get_by_hash(self, key_hash: str) -> ApiKeyModel | None:
        """해시로 API 키를 조회합니다."""
        result = await self._session.execute(
            select(ApiKeyModel).where(
                ApiKeyModel.key_hash == key_hash,
                ApiKeyModel.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, key_id: str) -> ApiKeyModel | None:
        """키 ID로 조회합니다."""
        result = await self._session.execute(select(ApiKeyModel).where(ApiKeyModel.id == key_id))
        return result.scalar_one_or_none()

    async def get_all_active(self) -> list[ApiKeyModel]:
        """활성화된 모든 API 키를 조회합니다."""
        result = await self._session.execute(
            select(ApiKeyModel).where(ApiKeyModel.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def get_all(
        self, include_inactive: bool = False, workspace_id: str | None = None
    ) -> list[ApiKeyModel]:
        """API 키 목록을 조회합니다."""
        query = select(ApiKeyModel).order_by(ApiKeyModel.created_at.desc())
        if not include_inactive:
            query = query.where(ApiKeyModel.is_active.is_(True))
        if workspace_id is not None:
            query = query.where(ApiKeyModel.workspace_id == workspace_id)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update_last_used(self, key_id: str) -> None:
        """마지막 사용 시각을 업데이트합니다."""
        await self._session.execute(
            update(ApiKeyModel)
            .where(ApiKeyModel.id == key_id)
            .values(last_used_at=datetime.now(UTC))
        )

    async def deactivate(self, key_id: str) -> None:
        """API 키를 비활성화합니다."""
        await self._session.execute(
            update(ApiKeyModel).where(ApiKeyModel.id == key_id).values(is_active=False)
        )


class AuditLogRepository:
    """감사 로그 저장소."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        method: str,
        path: str,
        status_code: int | None = None,
        api_key_id: str | None = None,
        user_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        duration_ms: float | None = None,
    ) -> AuditLogModel:
        """감사 로그를 생성합니다."""
        log = AuditLogModel(
            method=method,
            path=path,
            status_code=status_code,
            api_key_id=api_key_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            duration_ms=duration_ms,
        )
        self._session.add(log)
        await self._session.flush()
        return log

    async def list_recent(self, limit: int = 100) -> list[AuditLogModel]:
        """최근 감사 로그를 조회합니다."""
        result = await self._session.execute(
            select(AuditLogModel).order_by(AuditLogModel.timestamp.desc()).limit(limit)
        )
        return list(result.scalars().all())

    def _build_filter_query(
        self,
        api_key_id: str | None = None,
        method: str | None = None,
    ) -> list:
        """필터 조건을 생성합니다."""
        conditions = []
        if api_key_id is not None:
            conditions.append(AuditLogModel.api_key_id == api_key_id)
        if method is not None:
            conditions.append(AuditLogModel.method == method.upper())
        return conditions

    async def list_with_filters(
        self,
        api_key_id: str | None = None,
        method: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLogModel]:
        """필터링을 지원하는 감사 로그 목록 조회."""
        conditions = self._build_filter_query(api_key_id, method)
        query = (
            select(AuditLogModel)
            .where(*conditions)
            .order_by(AuditLogModel.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_with_filters(
        self,
        api_key_id: str | None = None,
        method: str | None = None,
    ) -> int:
        """필터링된 로그 개수를 반환합니다."""
        conditions = self._build_filter_query(api_key_id, method)
        query = select(func.count(AuditLogModel.id)).where(*conditions)
        result = await self._session.execute(query)
        return result.scalar_one()


class UsageRepository:
    """LLM 사용량 저장소."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        event_id: str,
        run_id: str,
        agent: str,
        provider: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> UsageEventModel:
        """사용량 이벤트를 생성합니다."""
        event = UsageEventModel(
            id=event_id,
            run_id=run_id,
            agent=agent,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def list_by_run(self, run_id: str) -> list[UsageEventModel]:
        """특정 run의 사용량 이벤트를 조회합니다."""
        result = await self._session.execute(
            select(UsageEventModel)
            .where(UsageEventModel.run_id == run_id)
            .order_by(UsageEventModel.created_at.asc())
        )
        return list(result.scalars().all())

    def _build_filter_query(
        self,
        run_id: str | None = None,
        agent: str | None = None,
        provider: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        workspace_id: str | None = None,
    ) -> list:
        """필터 조건을 생성합니다."""
        conditions = []
        if run_id is not None:
            conditions.append(UsageEventModel.run_id == run_id)
        if agent is not None:
            conditions.append(UsageEventModel.agent == agent)
        if provider is not None:
            conditions.append(UsageEventModel.provider == provider)
        if date_from is not None:
            conditions.append(UsageEventModel.created_at >= date_from)
        if date_to is not None:
            conditions.append(UsageEventModel.created_at <= date_to)
        if workspace_id is not None:
            conditions.append(
                UsageEventModel.run_id.in_(
                    select(PipelineRunModel.id).where(
                        PipelineRunModel.workspace_id == workspace_id
                    )
                )
            )
        return conditions

    async def list_with_filters(
        self,
        run_id: str | None = None,
        agent: str | None = None,
        provider: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
        workspace_id: str | None = None,
    ) -> list[UsageEventModel]:
        """필터링과 페이지네이션을 지원하는 목록 조회."""
        conditions = self._build_filter_query(run_id, agent, provider, date_from, date_to, workspace_id)
        query = (
            select(UsageEventModel)
            .where(*conditions)
            .order_by(UsageEventModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_with_filters(
        self,
        run_id: str | None = None,
        agent: str | None = None,
        provider: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        workspace_id: str | None = None,
    ) -> int:
        """필터링된 결과의 총 개수를 반환합니다."""
        conditions = self._build_filter_query(run_id, agent, provider, date_from, date_to, workspace_id)
        query = select(func.count(UsageEventModel.id)).where(*conditions)
        result = await self._session.execute(query)
        return result.scalar_one()

    async def get_summary(
        self,
        run_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        """사용량 집계 통계를 반환합니다 (단일 쿼리 최적화)."""
        query = select(
            UsageEventModel.agent,
            UsageEventModel.provider,
            UsageEventModel.model,
            func.sum(UsageEventModel.cost_usd).label("cost"),
            func.sum(UsageEventModel.total_tokens).label("tokens"),
        ).group_by(
            UsageEventModel.agent,
            UsageEventModel.provider,
            UsageEventModel.model,
        )

        if run_id:
            query = query.where(UsageEventModel.run_id == run_id)
        if date_from:
            query = query.where(UsageEventModel.created_at >= date_from)
        if date_to:
            query = query.where(UsageEventModel.created_at <= date_to)
        if workspace_id:
            query = query.join(
                PipelineRunModel, UsageEventModel.run_id == PipelineRunModel.id
            ).where(PipelineRunModel.workspace_id == workspace_id)

        result = await self._session.execute(query)
        rows = result.all()

        total_cost = 0.0
        total_tokens = 0
        by_agent: dict[str, float] = {}
        by_provider: dict[str, float] = {}
        by_model: dict[str, float] = {}

        for row in rows:
            cost = float(row.cost or 0)
            tokens = int(row.tokens or 0)
            total_cost += cost
            total_tokens += tokens

            by_agent[row.agent] = by_agent.get(row.agent, 0.0) + cost
            by_provider[row.provider] = by_provider.get(row.provider, 0.0) + cost
            by_model[row.model] = by_model.get(row.model, 0.0) + cost

        return {
            "total_cost_usd": round(total_cost, 6),
            "total_tokens": total_tokens,
            "by_agent": by_agent,
            "by_provider": by_provider,
            "by_model": by_model,
        }

    async def get_total_cost(self, workspace_id: str | None = None) -> float:
        """Dashboard용 총 비용을 조회합니다."""
        if workspace_id:
            query = (
                select(func.coalesce(func.sum(UsageEventModel.cost_usd), 0.0))
                .join(PipelineRunModel, UsageEventModel.run_id == PipelineRunModel.id)
                .where(PipelineRunModel.workspace_id == workspace_id)
            )
        else:
            query = select(func.coalesce(func.sum(UsageEventModel.cost_usd), 0.0))
        result = await self._session.execute(query)
        return float(result.scalar_one())

    async def get_run_cost(self, run_id: str) -> float:
        """특정 파이프라인 실행의 총 LLM 비용을 조회합니다."""
        query = select(func.coalesce(func.sum(UsageEventModel.cost_usd), 0.0)).where(
            UsageEventModel.run_id == run_id
        )
        result = await self._session.execute(query)
        return float(result.scalar_one())


class SubscriptionRepository:
    """Stripe 구독 저장소."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        subscription_id: str,
        workspace_id: str,
        stripe_customer_id: str,
        stripe_subscription_id: str | None = None,
        plan: str = "free",
        status: str = "active",
        current_period_start: datetime | None = None,
        current_period_end: datetime | None = None,
    ) -> SubscriptionModel:
        """새 구독을 생성합니다."""
        subscription = SubscriptionModel(
            id=subscription_id,
            workspace_id=workspace_id,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            plan=plan,
            status=status,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
        )
        self._session.add(subscription)
        await self._session.flush()
        return subscription

    async def get_by_workspace(self, workspace_id: str) -> SubscriptionModel | None:
        """워크스페이스 ID로 구독을 조회합니다."""
        result = await self._session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.workspace_id == workspace_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_stripe_customer(
        self, stripe_customer_id: str
    ) -> SubscriptionModel | None:
        """Stripe 고객 ID로 구독을 조회합니다."""
        result = await self._session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.stripe_customer_id == stripe_customer_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_stripe_subscription(
        self, stripe_subscription_id: str
    ) -> SubscriptionModel | None:
        """Stripe 구독 ID로 구독을 조회합니다."""
        result = await self._session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.stripe_subscription_id == stripe_subscription_id
            )
        )
        return result.scalar_one_or_none()

    async def update(self, subscription_id: str, **kwargs: Any) -> None:
        """구독 정보를 업데이트합니다."""
        await self._session.execute(
            update(SubscriptionModel)
            .where(SubscriptionModel.id == subscription_id)
            .values(**kwargs)
        )


class CompetitorRepository:
    """경쟁 채널 저장소."""


class OAuthTokenRepository:
    """OAuth 토큰 저장소."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        competitor_id: str,
        workspace_id: str,
        youtube_channel_id: str,
        name: str,
    ) -> CompetitorChannelModel:
        """새 경쟁 채널을 등록합니다."""
        competitor = CompetitorChannelModel(
            id=competitor_id,
            workspace_id=workspace_id,
            youtube_channel_id=youtube_channel_id,
            name=name,
        )
        self._session.add(competitor)
        await self._session.flush()
        return competitor

    async def get(self, competitor_id: str) -> CompetitorChannelModel | None:
        """ID로 경쟁 채널을 조회합니다."""
        result = await self._session.execute(
            select(CompetitorChannelModel).where(CompetitorChannelModel.id == competitor_id)
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(
        self, workspace_id: str
    ) -> list[CompetitorChannelModel]:
        """워크스페이스의 경쟁 채널 목록을 조회합니다."""
        result = await self._session.execute(
            select(CompetitorChannelModel)
            .where(CompetitorChannelModel.workspace_id == workspace_id)
            .order_by(CompetitorChannelModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_active_all(self) -> list[CompetitorChannelModel]:
        """모든 워크스페이스의 활성 경쟁 채널을 조회합니다 (cron 수집용)."""
        result = await self._session.execute(
            select(CompetitorChannelModel).where(
                CompetitorChannelModel.is_active.is_(True)
            )
        )
        return list(result.scalars().all())

    async def update_channel_stats(
        self,
        competitor_id: str,
        name: str,
        description: str | None,
        subscriber_count: int,
        video_count: int,
        thumbnail_url: str | None,
    ) -> None:
        """채널 통계 정보를 업데이트합니다."""
        await self._session.execute(
            update(CompetitorChannelModel)
            .where(CompetitorChannelModel.id == competitor_id)
            .values(
                name=name,
                description=description,
                subscriber_count=subscriber_count,
                video_count=video_count,
                thumbnail_url=thumbnail_url,
                last_crawled_at=datetime.now(UTC),
            )
        )

    async def delete(self, competitor_id: str) -> None:
        """경쟁 채널을 삭제합니다 (cascade로 영상도 삭제됨)."""
        competitor = await self.get(competitor_id)
        if competitor is not None:
            await self._session.delete(competitor)
            await self._session.flush()

    async def upsert_video(
        self,
        video_id_internal: str,
        competitor_channel_id: str,
        video_id: str,
        title: str,
        description: str | None,
        view_count: int,
        like_count: int,
        comment_count: int,
        published_at: datetime,
        tags: list[str],
        duration_seconds: int | None,
        thumbnail_url: str | None,
    ) -> None:
        """영상 데이터를 upsert합니다 (신규 추가 또는 통계 업데이트)."""
        result = await self._session.execute(
            select(CompetitorVideoModel).where(
                CompetitorVideoModel.competitor_channel_id == competitor_channel_id,
                CompetitorVideoModel.video_id == video_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            await self._session.execute(
                update(CompetitorVideoModel)
                .where(CompetitorVideoModel.id == existing.id)
                .values(
                    title=title,
                    description=description,
                    view_count=view_count,
                    like_count=like_count,
                    comment_count=comment_count,
                    tags_json=json.dumps(tags, ensure_ascii=False),
                    collected_at=datetime.now(UTC),
                )
            )
        else:
            video = CompetitorVideoModel(
                id=video_id_internal,
                competitor_channel_id=competitor_channel_id,
                video_id=video_id,
                title=title,
                description=description,
                view_count=view_count,
                like_count=like_count,
                comment_count=comment_count,
                published_at=published_at,
                tags_json=json.dumps(tags, ensure_ascii=False),
                duration_seconds=duration_seconds,
                thumbnail_url=thumbnail_url,
            )
            self._session.add(video)
            await self._session.flush()

    async def list_videos(
        self, competitor_channel_id: str, limit: int = 20
    ) -> list[CompetitorVideoModel]:
        """경쟁 채널의 영상 목록을 최신순으로 조회합니다."""
        result = await self._session.execute(
            select(CompetitorVideoModel)
            .where(CompetitorVideoModel.competitor_channel_id == competitor_channel_id)
            .order_by(CompetitorVideoModel.published_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_workspace(
        self, workspace_id: str, provider: str = "youtube"
    ) -> OAuthTokenModel | None:
        """워크스페이스 ID와 프로바이더로 토큰을 조회합니다."""
        result = await self._session.execute(
            select(OAuthTokenModel).where(
                OAuthTokenModel.workspace_id == workspace_id,
                OAuthTokenModel.provider == provider,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self, workspace_id: str, token_json: str, provider: str = "youtube"
    ) -> OAuthTokenModel:
        """토큰을 생성하거나 업데이트합니다."""
        import uuid

        existing = await self.get_by_workspace(workspace_id, provider)
        if existing:
            await self._session.execute(
                update(OAuthTokenModel)
                .where(OAuthTokenModel.id == existing.id)
                .values(token_json=token_json, updated_at=datetime.now(UTC))
            )
            await self._session.flush()
            return existing

        token = OAuthTokenModel(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            provider=provider,
            token_json=token_json,
        )
        self._session.add(token)
        await self._session.flush()
        return token

    async def delete_by_workspace(self, workspace_id: str, provider: str = "youtube") -> None:
        """워크스페이스의 토큰을 삭제합니다."""
        from sqlalchemy import delete as sa_delete

        await self._session.execute(
            sa_delete(OAuthTokenModel).where(
                OAuthTokenModel.workspace_id == workspace_id,
                OAuthTokenModel.provider == provider,
            )
        )
