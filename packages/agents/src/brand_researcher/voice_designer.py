"""톤앤매너 + Voice 프로필 설계.

브랜드 분석 결과를 기반으로 톤앤매너 가이드와 음성 프로필을 생성합니다.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.shared.llm_utils import parse_json_from_response
from src.shared.models import ToneAndManner, VisualIdentity, VoiceDesign, WritingStyle

from .analyzer import BrandAnalysisResult

VOICE_DESIGN_SYSTEM_PROMPT = """당신은 브랜드 커뮤니케이션 전문가입니다.
브랜드 분석 결과를 기반으로 톤앤매너, 음성 프로필, 비주얼 아이덴티티를 설계합니다.

반드시 아래 JSON 형식으로만 응답하세요:
{
  "tone_and_manner": {
    "personality": "브랜드 성격 설명",
    "formality": "formal|semi-formal|casual",
    "emotion": "warm|neutral|energetic",
    "humor_level": "none|light|moderate|heavy",
    "writing_style": {
      "sentence_length": "short|medium|long",
      "vocabulary": "어휘 스타일 설명",
      "call_to_action": "CTA 스타일"
    },
    "do": ["해야 할 것1", "해야 할 것2"],
    "dont": ["하지 말아야 할 것1", "하지 말아야 할 것2"]
  },
  "voice_design": {
    "narration_style": "나레이션 스타일 설명",
    "speech_rate": "slow|moderate|fast",
    "pitch": "low|medium|high",
    "language": "ko"
  },
  "visual_identity": {
    "color_palette": ["#색상코드1", "#색상코드2", "#색상코드3"],
    "thumbnail_style": "썸네일 스타일 설명",
    "font_preference": "폰트 선호"
  }
}
"""


class VoiceDesigner:
    """브랜드 보이스와 톤앤매너를 설계합니다."""

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm

    async def design(
        self,
        analysis: BrandAnalysisResult,
    ) -> VoiceDesignResult:
        """브랜드 분석 결과를 기반으로 보이스를 설계합니다."""
        user_prompt = (
            "다음 브랜드 분석 결과를 기반으로 "
            "톤앤매너, 음성 프로필, 비주얼 아이덴티티를 설계해주세요:\n\n"
            f"브랜드: {analysis.brand.name}\n"
            f"포지셔닝: {analysis.brand.positioning}\n"
            f"가치: {', '.join(analysis.brand.values)}\n"
            f"타겟 오디언스: {analysis.target_audience.primary}\n"
            f"페인포인트: {', '.join(analysis.target_audience.pain_points)}\n"
            f"콘텐츠 니즈: {', '.join(analysis.target_audience.content_needs)}\n\n"
            "이 브랜드에 맞는 YouTube 채널의 톤앤매너, "
            "나레이션 음성 스타일, 비주얼 아이덴티티를 JSON으로 설계해주세요."
        )

        messages = [
            SystemMessage(content=VOICE_DESIGN_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        response = await self._llm.ainvoke(messages)
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> VoiceDesignResult:
        """LLM 응답을 파싱합니다."""
        data = parse_json_from_response(content)
        if not data:
            return VoiceDesignResult(
                tone_and_manner=ToneAndManner(),
                voice_design=VoiceDesign(),
                visual_identity=VisualIdentity(),
                raw_response=content,
            )

        tone_data = data.get("tone_and_manner", {})
        voice_data = data.get("voice_design", {})
        visual_data = data.get("visual_identity", {})

        writing_style_data = tone_data.pop("writing_style", {})

        return VoiceDesignResult(
            tone_and_manner=ToneAndManner(
                personality=tone_data.get("personality", ""),
                formality=tone_data.get("formality", "semi-formal"),
                emotion=tone_data.get("emotion", "neutral"),
                humor_level=tone_data.get("humor_level", "none"),
                writing_style=(
                    WritingStyle(**writing_style_data) if writing_style_data else WritingStyle()
                ),
                do=tone_data.get("do", []),
                dont=tone_data.get("dont", []),
            ),
            voice_design=VoiceDesign(
                narration_style=voice_data.get("narration_style", ""),
                speech_rate=voice_data.get("speech_rate", "moderate"),
                pitch=voice_data.get("pitch", "medium"),
                language=voice_data.get("language", "ko"),
            ),
            visual_identity=VisualIdentity(
                color_palette=visual_data.get("color_palette", []),
                thumbnail_style=visual_data.get("thumbnail_style", ""),
                font_preference=visual_data.get("font_preference", ""),
            ),
            raw_response=content,
        )


class VoiceDesignResult:
    """보이스 설계 결과."""

    def __init__(
        self,
        tone_and_manner: ToneAndManner,
        voice_design: VoiceDesign,
        visual_identity: VisualIdentity,
        raw_response: str = "",
    ) -> None:
        self.tone_and_manner = tone_and_manner
        self.voice_design = voice_design
        self.visual_identity = visual_identity
        self.raw_response = raw_response
