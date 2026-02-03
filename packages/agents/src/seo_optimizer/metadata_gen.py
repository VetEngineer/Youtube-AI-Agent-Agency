"""메타데이터 생성 모듈.

스크립트와 SEO 분석 결과를 바탕으로 YouTube 업로드용 메타데이터를 생성합니다.
클릭을 유도하는 제목, SEO 최적화 설명, 관련 태그를 포함합니다.
"""

from __future__ import annotations

import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.shared.llm_utils import parse_json_from_response
from src.shared.models import BrandGuide, SEOAnalysis, VideoMetadata

logger = logging.getLogger(__name__)

METADATA_SYSTEM_PROMPT = """당신은 YouTube 메타데이터 최적화 전문가입니다.
스크립트 내용, SEO 키워드, 브랜드 톤앤매너를 바탕으로
클릭률(CTR)과 검색 노출을 극대화하는 메타데이터를 생성합니다.

제목 작성 규칙:
- 60자 이내 (YouTube 검색 결과에서 잘리지 않도록)
- 호기심을 유발하거나 명확한 가치를 전달
- 핵심 키워드를 자연스럽게 포함
- 숫자, 질문형, 비교형 등 클릭 유도 패턴 활용

설명 작성 규칙:
- 첫 2줄에 핵심 내용 요약 (검색 결과 미리보기에 표시)
- 주요 키워드를 자연스럽게 배치
- 영상 내용의 타임스탬프 포함
- CTA(Call-to-Action) 포함
- 관련 링크/해시태그 영역 포함
- 총 500~1500자

태그 규칙:
- 핵심 키워드 + 보조 키워드 + 관련 키워드
- 10~20개
- 구체적인 것에서 일반적인 것 순서로

반드시 아래 JSON 형식으로만 응답하세요:
{
  "title": "영상 제목",
  "description": "영상 설명 전체 텍스트",
  "tags": ["태그1", "태그2", "태그3"]
}
"""


class MetadataGenerator:
    """YouTube 업로드용 메타데이터를 생성합니다."""

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm

    async def generate(
        self,
        script_title: str,
        script_text: str,
        seo_analysis: SEOAnalysis,
        brand_guide: BrandGuide,
    ) -> VideoMetadata:
        """스크립트와 SEO 분석 결과를 바탕으로 메타데이터를 생성합니다.

        Args:
            script_title: 원고 제목
            script_text: 원고 전문
            seo_analysis: 키워드 리서치 결과
            brand_guide: 브랜드 가이드

        Returns:
            최적화된 VideoMetadata
        """
        user_prompt = self._build_prompt(
            script_title,
            script_text,
            seo_analysis,
            brand_guide,
        )

        messages = [
            SystemMessage(content=METADATA_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = await self._llm.ainvoke(messages)
            return self._parse_response(response.content, script_title)
        except Exception as error:
            logger.error("메타데이터 생성 LLM 호출 실패: %s", error)
            raise RuntimeError(f"메타데이터 생성 중 오류가 발생했습니다: {error}") from error

    def _build_prompt(
        self,
        script_title: str,
        script_text: str,
        seo_analysis: SEOAnalysis,
        brand_guide: BrandGuide,
    ) -> str:
        """LLM에 전달할 사용자 프롬프트를 구성합니다."""
        tone = brand_guide.tone_and_manner
        truncated_script = self._truncate_script(script_text)

        primary_kw = ", ".join(seo_analysis.primary_keywords)
        secondary_kw = ", ".join(seo_analysis.secondary_keywords)

        parts = [
            f"## 원고 제목\n{script_title}",
            f"## 원고 내용 (요약)\n{truncated_script}",
            f"## 핵심 키워드\n{primary_kw}",
            f"## 보조 키워드\n{secondary_kw}",
            f"## 브랜드 톤\n- 성격: {tone.personality}",
            f"- 격식: {tone.formality.value}",
            f"- 감정: {tone.emotion.value}",
        ]

        if tone.writing_style.call_to_action:
            parts.append(f"- CTA 스타일: {tone.writing_style.call_to_action}")

        parts.append("\n위 정보를 바탕으로 YouTube 메타데이터를 JSON으로 생성해주세요.")

        return "\n\n".join(parts)

    def _truncate_script(self, script_text: str, max_length: int = 2000) -> str:
        """스크립트가 너무 길면 앞부분만 잘라서 사용합니다."""
        if len(script_text) <= max_length:
            return script_text
        return script_text[:max_length] + "\n\n... (이하 생략)"

    def _parse_response(
        self,
        content: str,
        fallback_title: str,
    ) -> VideoMetadata:
        """LLM 응답을 VideoMetadata로 파싱합니다."""
        data = parse_json_from_response(content)
        if not data:
            logger.warning("메타데이터 JSON 파싱 실패, 기본값 반환")
            return VideoMetadata(title=fallback_title)

        return VideoMetadata(
            title=data.get("title", fallback_title),
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )
