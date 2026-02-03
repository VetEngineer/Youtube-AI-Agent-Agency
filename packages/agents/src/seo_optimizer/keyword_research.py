"""키워드 리서치 모듈.

AEO/SEO/GEO 관점에서 토픽을 분석하여 최적의 키워드를 추천합니다.
LLM을 사용하여 타겟 오디언스와 브랜드 포지셔닝을 반영한 키워드를 생성합니다.
"""

from __future__ import annotations

import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.shared.llm_utils import parse_json_from_response
from src.shared.models import BrandGuide, SEOAnalysis

logger = logging.getLogger(__name__)

KEYWORD_RESEARCH_SYSTEM_PROMPT = """당신은 YouTube SEO/AEO/GEO 키워드 전문가입니다.
주어진 토픽, 타겟 오디언스, 브랜드 포지셔닝 정보를 바탕으로
YouTube 검색 최적화에 효과적인 키워드를 추천합니다.

키워드 전략:
- SEO: YouTube 검색에서 노출되는 전통적 검색 키워드
- AEO (Answer Engine Optimization): AI 검색 엔진(ChatGPT, Perplexity 등)에서 답변으로 채택될 키워드
- GEO (Generative Engine Optimization): AI가 생성하는 콘텐츠 추천에 포함될 키워드

반드시 아래 JSON 형식으로만 응답하세요:
{
  "primary_keywords": ["핵심키워드1", "핵심키워드2", "핵심키워드3"],
  "secondary_keywords": ["보조키워드1", "보조키워드2", "보조키워드3", "보조키워드4", "보조키워드5"],
  "search_volume": {
    "핵심키워드1": 5000,
    "핵심키워드2": 3000,
    "보조키워드1": 1500
  },
  "competition_level": {
    "핵심키워드1": "medium",
    "핵심키워드2": "low",
    "보조키워드1": "high"
  }
}

규칙:
- primary_keywords: 3~5개의 핵심 키워드 (검색 의도에 정확히 부합)
- secondary_keywords: 5~10개의 보조/롱테일 키워드
- search_volume: 예상 월간 검색량 (추정치)
- competition_level: "low", "medium", "high" 중 하나
- 기존 채널 키워드와 시너지가 나는 키워드 우선 추천
"""


class KeywordResearcher:
    """YouTube SEO/AEO/GEO 키워드 리서치를 수행합니다."""

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm

    async def research(
        self,
        topic: str,
        brand_guide: BrandGuide,
        existing_keywords: list[str] | None = None,
    ) -> SEOAnalysis:
        """토픽에 대한 키워드 리서치를 수행합니다.

        Args:
            topic: 콘텐츠 주제
            brand_guide: 브랜드 가이드 (타겟 오디언스, 포지셔닝 참조)
            existing_keywords: 채널에서 이미 사용 중인 키워드

        Returns:
            키워드 분석 결과
        """
        safe_keywords = existing_keywords or []
        user_prompt = self._build_prompt(topic, brand_guide, safe_keywords)

        messages = [
            SystemMessage(content=KEYWORD_RESEARCH_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = await self._llm.ainvoke(messages)
            return self._parse_response(response.content)
        except Exception as error:
            logger.error("키워드 리서치 LLM 호출 실패: %s", error)
            raise RuntimeError(f"키워드 리서치 중 오류가 발생했습니다: {error}") from error

    def _build_prompt(
        self,
        topic: str,
        brand_guide: BrandGuide,
        existing_keywords: list[str],
    ) -> str:
        """LLM에 전달할 사용자 프롬프트를 구성합니다."""
        audience = brand_guide.target_audience
        brand = brand_guide.brand

        parts = [
            f"## 토픽\n{topic}",
            f"## 브랜드 포지셔닝\n{brand.positioning}",
            f"## 타겟 오디언스\n{audience.primary}",
        ]

        if audience.pain_points:
            pain_points_text = ", ".join(audience.pain_points)
            parts.append(f"## 오디언스 페인포인트\n{pain_points_text}")

        if audience.content_needs:
            needs_text = ", ".join(audience.content_needs)
            parts.append(f"## 콘텐츠 니즈\n{needs_text}")

        if existing_keywords:
            keywords_text = ", ".join(existing_keywords)
            parts.append(f"## 기존 채널 키워드\n{keywords_text}")

        parts.append("\n위 정보를 바탕으로 YouTube SEO/AEO/GEO에 최적화된 키워드를 추천해주세요.")

        return "\n\n".join(parts)

    def _parse_response(self, content: str) -> SEOAnalysis:
        """LLM 응답을 SEOAnalysis로 파싱합니다."""
        data = parse_json_from_response(content)
        if not data:
            logger.warning("키워드 리서치 JSON 파싱 실패, 기본값 반환")
            return SEOAnalysis()

        return SEOAnalysis(
            primary_keywords=data.get("primary_keywords", []),
            secondary_keywords=data.get("secondary_keywords", []),
            search_volume=data.get("search_volume", {}),
            competition_level=data.get("competition_level", {}),
        )
