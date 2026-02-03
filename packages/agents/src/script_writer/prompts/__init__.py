"""Script Writer 프롬프트 템플릿.

톤앤매너 가이드를 동적으로 주입하여 브랜드 일관성을 유지합니다.
"""

from __future__ import annotations

from src.shared.models import ToneAndManner

SCRIPT_SYSTEM_PROMPT = """\
당신은 YouTube 영상 원고를 작성하는 전문 스크립트 라이터입니다.

## 역할
- 시청자의 관심을 끌고 끝까지 유지하는 구조화된 원고를 작성합니다.
- 인트로, 본론, 아웃트로의 3단 구조로 원고를 구성합니다.
- 브랜드 톤앤매너를 철저히 지킵니다.

## 톤앤매너 가이드
{tone_guide}

## 출력 규칙
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트를 포함하지 마세요.

```json
{{
  "title": "영상 제목",
  "sections": [
    {{
      "heading": "섹션 제목 (예: 인트로)",
      "body": "원고 본문 텍스트",
      "visual_notes": "이 섹션에 어울리는 영상/이미지 연출 메모",
      "duration_seconds": 30
    }}
  ],
  "estimated_duration_seconds": 600
}}
```

## 섹션 구성 가이드
1. **인트로** (15-30초): 시청자의 관심을 즉시 끌어야 합니다. 질문, 놀라운 사실, 공감 유발.
2. **본론** (여러 섹션): 주제를 깊이 있게 다룹니다. 각 섹션은 하나의 핵심 포인트를 전달합니다.
3. **아웃트로** (15-30초): 핵심 요약 + 구독/좋아요 유도 + 다음 영상 예고.
"""

SCRIPT_USER_PROMPT = """\
다음 콘텐츠 기획안을 바탕으로 YouTube 영상 원고를 작성해주세요.

## 콘텐츠 기획안
- **주제**: {topic}
- **콘텐츠 유형**: {content_type}
- **타겟 키워드**: {keywords}
- **추가 메모**: {notes}

위 기획안을 바탕으로, 톤앤매너 가이드를 준수하며 구조화된 원고를 JSON 형식으로 작성하세요.
"""


def build_tone_guide(tone: ToneAndManner) -> str:
    """ToneAndManner 모델에서 프롬프트에 주입할 가이드 텍스트를 생성합니다."""
    lines = [
        f"- **퍼스널리티**: {tone.personality}" if tone.personality else "",
        f"- **격식 수준**: {tone.formality.value}",
        f"- **감정 톤**: {tone.emotion.value}",
        f"- **유머 수준**: {tone.humor_level.value}",
    ]

    style = tone.writing_style
    if style.sentence_length:
        lines.append(f"- **문장 길이**: {style.sentence_length}")
    if style.vocabulary:
        lines.append(f"- **어휘 스타일**: {style.vocabulary}")
    if style.call_to_action:
        lines.append(f"- **CTA 스타일**: {style.call_to_action}")

    if tone.do_rules:
        lines.append("\n### 반드시 지켜야 할 것 (Do)")
        for rule in tone.do_rules:
            lines.append(f"  - {rule}")

    if tone.dont_rules:
        lines.append("\n### 하지 말아야 할 것 (Don't)")
        for rule in tone.dont_rules:
            lines.append(f"  - {rule}")

    return "\n".join(line for line in lines if line)


def build_system_prompt(tone: ToneAndManner) -> str:
    """톤앤매너가 주입된 시스템 프롬프트를 생성합니다."""
    tone_guide = build_tone_guide(tone)
    return SCRIPT_SYSTEM_PROMPT.format(tone_guide=tone_guide)


def build_user_prompt(
    topic: str,
    content_type: str,
    keywords: list[str],
    notes: str,
) -> str:
    """콘텐츠 기획안 기반 유저 프롬프트를 생성합니다."""
    keywords_text = ", ".join(keywords) if keywords else "없음"
    notes_text = notes if notes else "없음"
    return SCRIPT_USER_PROMPT.format(
        topic=topic,
        content_type=content_type,
        keywords=keywords_text,
        notes=notes_text,
    )
