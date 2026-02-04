"""Repository 패턴 - 데이터 접근 계층."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ApiKeyModel, AuditLogModel, PipelineRunModel


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
    ) -> PipelineRunModel:
        """새 파이프라인 실행을 생성합니다."""
        run = PipelineRunModel(
            id=run_id,
            channel_id=channel_id,
            topic=topic,
            brand_name=brand_name,
            dry_run=dry_run,
            status="pending",
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
        if status in ("completed", "failed"):
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

    async def list_recent(self, limit: int = 20, offset: int = 0) -> list[PipelineRunModel]:
        """최근 실행 목록을 조회합니다."""
        result = await self._session.execute(
            select(PipelineRunModel)
            .order_by(PipelineRunModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    def _build_filter_query(
        self,
        channel_id: str | None = None,
        status: str | None = None,
    ) -> list:
        """필터 조건을 생성합니다."""
        conditions = []
        if channel_id is not None:
            conditions.append(PipelineRunModel.channel_id == channel_id)
        if status is not None:
            conditions.append(PipelineRunModel.status == status)
        return conditions

    async def list_with_filters(
        self,
        channel_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[PipelineRunModel]:
        """필터링과 페이지네이션을 지원하는 목록 조회."""
        conditions = self._build_filter_query(channel_id, status)
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
    ) -> int:
        """필터링된 결과의 총 개수를 반환합니다."""
        conditions = self._build_filter_query(channel_id, status)
        query = select(func.count(PipelineRunModel.id)).where(*conditions)
        result = await self._session.execute(query)
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
    ) -> ApiKeyModel:
        """새 API 키를 생성합니다."""
        import json

        api_key = ApiKeyModel(
            id=key_id,
            key_hash=key_hash,
            name=name,
            scopes_json=json.dumps(scopes or ["read", "write"]),
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

    async def get_all(self, include_inactive: bool = False) -> list[ApiKeyModel]:
        """모든 API 키를 조회합니다."""
        query = select(ApiKeyModel).order_by(ApiKeyModel.created_at.desc())
        if not include_inactive:
            query = query.where(ApiKeyModel.is_active.is_(True))
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
