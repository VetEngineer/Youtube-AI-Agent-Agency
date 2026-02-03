"""SEO Optimizer Agent.

스크립트와 브랜드 가이드를 입력받아 YouTube SEO 최적화를 수행합니다.
키워드 리서치 → 메타데이터 생성의 2단계 파이프라인을 실행합니다.

입력: topic, script_title, script_text, BrandGuide
출력: (SEOAnalysis, VideoMetadata)
"""

from __future__ import annotations

import logging

from langchain_core.language_models import BaseChatModel

from src.shared.models import BrandGuide, SEOAnalysis, VideoMetadata

from .keyword_research import KeywordResearcher
from .metadata_gen import MetadataGenerator

logger = logging.getLogger(__name__)


class SEOOptimizerAgent:
    """YouTube SEO 최적화 에이전트.

    키워드 리서치와 메타데이터 생성을 순차적으로 수행합니다.
    """

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm
        self._keyword_researcher = KeywordResearcher(llm)
        self._metadata_generator = MetadataGenerator(llm)

    async def optimize(
        self,
        topic: str,
        script_title: str,
        script_text: str,
        brand_guide: BrandGuide,
        existing_keywords: list[str] | None = None,
    ) -> tuple[SEOAnalysis, VideoMetadata]:
        """SEO 최적화를 수행합니다.

        Args:
            topic: 콘텐츠 주제
            script_title: 원고 제목
            script_text: 원고 전문
            brand_guide: 브랜드 가이드
            existing_keywords: 채널에서 이미 사용 중인 키워드

        Returns:
            (SEOAnalysis, VideoMetadata) 튜플

        Raises:
            RuntimeError: LLM 호출 또는 파싱에 실패한 경우
        """
        try:
            # 1단계: 키워드 리서치
            logger.info("키워드 리서치 시작: topic=%s", topic)
            seo_analysis = await self._keyword_researcher.research(
                topic=topic,
                brand_guide=brand_guide,
                existing_keywords=existing_keywords,
            )
            logger.info(
                "키워드 리서치 완료: primary=%d, secondary=%d",
                len(seo_analysis.primary_keywords),
                len(seo_analysis.secondary_keywords),
            )

            # 2단계: 메타데이터 생성
            logger.info("메타데이터 생성 시작: title=%s", script_title)
            metadata = await self._metadata_generator.generate(
                script_title=script_title,
                script_text=script_text,
                seo_analysis=seo_analysis,
                brand_guide=brand_guide,
            )
            logger.info("메타데이터 생성 완료: title=%s", metadata.title)

            return seo_analysis, metadata

        except RuntimeError:
            raise
        except Exception as error:
            logger.error("SEO 최적화 실패: %s", error)
            raise RuntimeError(f"SEO 최적화 중 오류가 발생했습니다: {error}") from error
