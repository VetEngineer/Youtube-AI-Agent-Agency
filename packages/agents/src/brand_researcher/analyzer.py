"""브랜드 포지셔닝 분석기.

수집된 자료를 LLM으로 분석하여 브랜드 포지셔닝, 타겟 오디언스, 경쟁 환경을 파악합니다.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.shared.llm_utils import parse_json_from_response
from src.shared.models import BrandInfo, CompetitorInfo, TargetAudience

from .collector import CollectionResult

ANALYSIS_SYSTEM_PROMPT = """당신은 브랜드 전략 전문가입니다.
제공된 자료를 분석하여 브랜드의 포지셔닝, 타겟 오디언스, 경쟁 환경을 파악합니다.

반드시 아래 JSON 형식으로만 응답하세요:
{
  "brand": {
    "name": "브랜드명",
    "tagline": "슬로건/태그라인",
    "positioning": "브랜드 포지셔닝 설명",
    "values": ["가치1", "가치2"]
  },
  "target_audience": {
    "primary": "주요 타겟 설명",
    "pain_points": ["페인포인트1", "페인포인트2"],
    "content_needs": ["콘텐츠 니즈1", "콘텐츠 니즈2"]
  },
  "competitors": [
    {
      "channel": "경쟁사명",
      "strengths": ["강점1"],
      "differentiation": "차별화 포인트"
    }
  ]
}
"""


class BrandAnalyzer:
    """수집된 자료를 분석하여 브랜드 정보를 추출합니다."""

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm

    async def analyze(
        self,
        brand_name: str,
        collection: CollectionResult,
    ) -> BrandAnalysisResult:
        """수집된 자료를 분석합니다."""
        user_prompt = f"""다음은 '{brand_name}' 브랜드에 대해 수집한 자료입니다:

{collection.combined_text}

위 자료를 분석하여 브랜드 포지셔닝, 타겟 오디언스, 경쟁 환경을 JSON으로 정리해주세요."""

        messages = [
            SystemMessage(content=ANALYSIS_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        response = await self._llm.ainvoke(messages)
        return self._parse_response(brand_name, response.content)

    def _parse_response(self, brand_name: str, content: str) -> BrandAnalysisResult:
        """LLM 응답을 파싱합니다."""
        data = parse_json_from_response(content)
        if not data:
            return BrandAnalysisResult(
                brand=BrandInfo(name=brand_name),
                target_audience=TargetAudience(),
                competitors=[],
                raw_response=content,
            )

        brand_data = data.get("brand", {})
        audience_data = data.get("target_audience", {})
        competitors_data = data.get("competitors", [])

        return BrandAnalysisResult(
            brand=BrandInfo(
                name=brand_data.get("name", brand_name),
                tagline=brand_data.get("tagline", ""),
                positioning=brand_data.get("positioning", ""),
                values=brand_data.get("values", []),
            ),
            target_audience=TargetAudience(
                primary=audience_data.get("primary", ""),
                pain_points=audience_data.get("pain_points", []),
                content_needs=audience_data.get("content_needs", []),
            ),
            competitors=[CompetitorInfo(**comp) for comp in competitors_data],
            raw_response=content,
        )


class BrandAnalysisResult:
    """브랜드 분석 결과."""

    def __init__(
        self,
        brand: BrandInfo,
        target_audience: TargetAudience,
        competitors: list[CompetitorInfo],
        raw_response: str = "",
    ) -> None:
        self.brand = brand
        self.target_audience = target_audience
        self.competitors = competitors
        self.raw_response = raw_response
