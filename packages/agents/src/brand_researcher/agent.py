"""Brand Researcher Agent.

채널 온보딩의 첫 단계로, 브랜드 자료를 수집/분석하여 brand_guide.yaml을 생성합니다.

입력: 채널 ID + 브랜드명 + (선택) 추가 검색어
출력: BrandGuide (→ brand_guide.yaml로 저장)
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.language_models import BaseChatModel

from src.shared.config import ChannelRegistry
from src.shared.models import BrandGuide

from .analyzer import BrandAnalyzer
from .collector import BrandCollector, CollectionResult
from .voice_designer import VoiceDesigner


class BrandResearcherAgent:
    """브랜드 리서치 에이전트.

    수집 → 분석 → 보이스 설계 → brand_guide.yaml 저장의 4단계 파이프라인을 실행합니다.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        registry: ChannelRegistry,
        collector: BrandCollector | None = None,
    ) -> None:
        self._llm = llm
        self._registry = registry
        self._collector = collector or BrandCollector()
        self._analyzer = BrandAnalyzer(llm)
        self._voice_designer = VoiceDesigner(llm)

    async def research(
        self,
        channel_id: str,
        brand_name: str,
        additional_queries: list[str] | None = None,
    ) -> BrandGuide:
        """브랜드 리서치를 실행하여 BrandGuide를 생성합니다.

        Args:
            channel_id: 채널 디렉토리명 (예: "deepure-cattery")
            brand_name: 브랜드명 (예: "딥퓨어캐터리")
            additional_queries: 추가 웹 검색 쿼리

        Returns:
            생성된 BrandGuide
        """
        # 1. 수집 (Collect)
        channel_path = self._registry.get_channel_path(channel_id)
        sources_dir = channel_path / "sources"

        collection = await self._collector.collect_all(
            brand_name=brand_name,
            channel_sources_dir=sources_dir if sources_dir.exists() else None,
            additional_queries=additional_queries,
        )

        # 2. 분석 (Analyze)
        analysis = await self._analyzer.analyze(brand_name, collection)

        # 3. 보이스 설계 (Design)
        voice_result = await self._voice_designer.design(analysis)

        # 4. BrandGuide 조합
        guide = BrandGuide(
            brand=analysis.brand,
            target_audience=analysis.target_audience,
            tone_and_manner=voice_result.tone_and_manner,
            voice_design=voice_result.voice_design,
            visual_identity=voice_result.visual_identity,
            competitors=analysis.competitors,
        )

        return guide

    async def research_and_save(
        self,
        channel_id: str,
        brand_name: str,
        additional_queries: list[str] | None = None,
    ) -> tuple[BrandGuide, Path]:
        """리서치 실행 후 brand_guide.yaml로 저장합니다.

        Returns:
            (BrandGuide, 저장된 파일 경로) 튜플
        """
        guide = await self.research(channel_id, brand_name, additional_queries)
        saved_path = self._registry.save_brand_guide(channel_id, guide)
        return guide, saved_path

    async def research_from_collection(
        self,
        brand_name: str,
        collection: CollectionResult,
    ) -> BrandGuide:
        """이미 수집된 자료로 분석/설계만 수행합니다 (테스트용)."""
        analysis = await self._analyzer.analyze(brand_name, collection)
        voice_result = await self._voice_designer.design(analysis)

        return BrandGuide(
            brand=analysis.brand,
            target_audience=analysis.target_audience,
            tone_and_manner=voice_result.tone_and_manner,
            voice_design=voice_result.voice_design,
            visual_identity=voice_result.visual_identity,
            competitors=analysis.competitors,
        )
