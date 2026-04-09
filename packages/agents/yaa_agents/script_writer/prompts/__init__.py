"""Script Writer 프롬프트 템플릿.

톤앤매너 가이드를 동적으로 주입하여 브랜드 일관성을 유지합니다.
Strategist / Auditor / Editor 프롬프트도 포함합니다.

Anthropic Prompt Caching:
  정적 시스템 프롬프트에 cache_control을 적용하여 입력 토큰 비용 90% 절감.
  - Auditor/Editor: 100% 정적 → 전체 캐시
  - Strategist/Writer: 정적 베이스 + 동적 톤가이드 → 베이스만 캐시
"""

from __future__ import annotations

from langchain_core.messages import SystemMessage
from yaa_core.shared.models import ToneAndManner

_CACHE_CONTROL = {"type": "ephemeral"}

# ============================================
# Script Writer 프롬프트 (동적 - 톤가이드 주입)
# ============================================

_SCRIPT_SYSTEM_BASE = """\
당신은 YouTube 영상 원고를 작성하는 전문 스크립트 라이터입니다.

## 역할
- 시청자의 관심을 끌고 끝까지 유지하는 구조화된 원고를 작성합니다.
- 인트로, 본론, 아웃트로의 3단 구조로 원고를 구성합니다.
- 브랜드 톤앤매너를 철저히 지킵니다.

## 출력 규칙
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트를 포함하지 마세요.

```json
{
  "title": "영상 제목",
  "sections": [
    {
      "heading": "섹션 제목 (예: 인트로)",
      "body": "원고 본문 텍스트",
      "visual_notes": "이 섹션에 어울리는 영상/이미지 연출 메모",
      "duration_seconds": 30
    }
  ],
  "estimated_duration_seconds": 600
}
```

## 섹션 구성 가이드
1. **인트로** (15-30초): 시청자의 관심을 즉시 끌어야 합니다. 질문, 놀라운 사실, 공감 유발.
2. **본론** (여러 섹션): 주제를 깊이 있게 다룹니다. 각 섹션은 하나의 핵심 포인트를 전달합니다.
3. **아웃트로** (15-30초): 핵심 요약 + 구독/좋아요 유도 + 다음 영상 예고."""

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


def build_system_prompt(tone: ToneAndManner) -> SystemMessage:
    """톤앤매너가 주입된 시스템 메시지를 생성합니다 (정적 베이스 캐시)."""
    tone_guide = build_tone_guide(tone)
    return SystemMessage(
        content=[
            {"type": "text", "text": _SCRIPT_SYSTEM_BASE, "cache_control": _CACHE_CONTROL},
            {"type": "text", "text": f"\n\n## 톤앤매너 가이드\n{tone_guide}"},
        ]
    )


def build_user_prompt(
    topic: str,
    content_type: str,
    keywords: list[str],
    notes: str,
    outline: str = "",
    references: str = "",
    guidelines: str = "",
) -> str:
    """콘텐츠 기획안 기반 유저 프롬프트를 생성합니다."""
    keywords_text = ", ".join(keywords) if keywords else "없음"
    notes_text = notes if notes else "없음"
    base = SCRIPT_USER_PROMPT.format(
        topic=topic,
        content_type=content_type,
        keywords=keywords_text,
        notes=notes_text,
    )
    extras: list[str] = []
    if guidelines:
        extras.append(f"## 제작 가이드라인\n{guidelines}")
    if references:
        extras.append(f"## 레퍼런스 대본 (이 톤앤매너를 참고하세요)\n{references}")
    if outline:
        extras.append(f"## 아웃라인 (이 구조를 따라 작성하세요)\n{outline}")
    return base + ("\n\n" + "\n\n".join(extras) if extras else "")


def build_revision_user_prompt(
    draft_script: str,
    audit_feedback: str,
    guidelines: str = "",
    references: str = "",
) -> str:
    """Auditor 피드백 반영 수정 요청 프롬프트를 생성합니다."""
    parts = ["아래 초안을 검수자 피드백에 따라 수정해주세요."]
    if guidelines:
        parts.append(f"## 제작 가이드라인\n{guidelines}")
    if references:
        parts.append(f"## 레퍼런스 대본\n{references}")
    parts.append(f"## 기존 초안\n{draft_script}")
    parts.append(f"## 검수자 피드백\n{audit_feedback}")
    parts.append("위 피드백을 반영하여 수정된 원고를 JSON 형식으로 작성하세요.")
    return "\n\n".join(parts)


# ============================================
# Strategist 프롬프트 (동적 - 톤가이드 주입)
# ============================================

_STRATEGIST_SYSTEM_BASE = """\
당신은 유튜브 콘텐츠 기획자입니다.
주어진 주제와 기획 정보를 바탕으로 영상의 전체 아웃라인을 기획합니다.

## 출력 규칙
반드시 아래 JSON 형식으로만 응답하세요.

```json
{
  "opening_hook": "시청자가 3초 안에 관심을 가질 훅 멘트 방향",
  "opening_promise": "시청자가 얻을 핵심 가치",
  "main_points": [
    {
      "title": "첫 번째 포인트 소제목",
      "key_message": "핵심 메시지",
      "example": "예시 또는 근거"
    }
  ],
  "closing_summary": "핵심 내용 3줄 요약",
  "closing_action": "시청자 액션 아이템 1개"
}
```"""

STRATEGIST_USER_PROMPT = """\
다음 정보를 바탕으로 YouTube 영상 아웃라인을 기획해주세요.

## 영상 정보
- **주제**: {topic}
- **콘텐츠 유형**: {content_type}
- **타겟 키워드**: {keywords}
- **메모**: {notes}
{guidelines_section}
JSON 형식으로 아웃라인을 작성하세요.
"""


def build_strategist_system_prompt(tone: ToneAndManner) -> SystemMessage:
    """Strategist 시스템 메시지를 생성합니다 (정적 베이스 캐시)."""
    tone_guide = build_tone_guide(tone)
    return SystemMessage(
        content=[
            {
                "type": "text",
                "text": _STRATEGIST_SYSTEM_BASE,
                "cache_control": _CACHE_CONTROL,
            },
            {"type": "text", "text": f"\n\n## 톤앤매너 가이드\n{tone_guide}"},
        ]
    )


def build_strategist_user_prompt(
    topic: str,
    content_type: str,
    keywords: list[str],
    notes: str,
    guidelines: str = "",
) -> str:
    """Strategist 유저 프롬프트를 생성합니다."""
    keywords_text = ", ".join(keywords) if keywords else "없음"
    guidelines_section = f"\n## 제작 가이드라인\n{guidelines}\n" if guidelines else ""
    return STRATEGIST_USER_PROMPT.format(
        topic=topic,
        content_type=content_type,
        keywords=keywords_text,
        notes=notes or "없음",
        guidelines_section=guidelines_section,
    )


# ============================================
# Auditor 프롬프트 (100% 정적 - 전체 캐시)
# ============================================

_AUDITOR_SYSTEM_TEXT = """\
당신은 유튜브 대본 검수 전문가입니다.
작성된 대본이 가이드라인을 준수하는지 엄격하게 검사합니다.

## 검사 항목
1. **구조**: 오프닝-본론(3포인트)-클로징 구조 준수
2. **문체**: 구어체 사용, 문장 길이, 쉬운 표현
3. **금지어**: 가이드라인에 명시된 금지 표현 사용 여부
4. **시청 지속률**: 예고 멘트, 질문 등 리텐션 장치 포함 여부

## 출력 규칙
반드시 아래 JSON 형식으로만 응답하세요.

```json
{
  "passed": true,
  "structure_ok": true,
  "style_ok": true,
  "forbidden_words_ok": true,
  "retention_hooks_ok": true,
  "feedback": "전체 평가 요약",
  "revision_instructions": []
}
```

passed가 false인 경우 revision_instructions에 구체적인 수정 지시를 작성하세요."""

AUDITOR_USER_PROMPT = """\
아래 대본을 가이드라인에 따라 검수해주세요.
{guidelines_section}
## 검수할 대본
{draft_script}

JSON 형식으로 검수 결과를 반환하세요.
"""


def build_auditor_system_prompt() -> SystemMessage:
    """Auditor 시스템 메시지를 생성합니다 (100% 정적, 전체 캐시)."""
    return SystemMessage(
        content=[
            {"type": "text", "text": _AUDITOR_SYSTEM_TEXT, "cache_control": _CACHE_CONTROL},
        ]
    )


def build_auditor_user_prompt(draft_script: str, guidelines: str = "") -> str:
    """Auditor 유저 프롬프트를 생성합니다."""
    guidelines_section = f"\n## 제작 가이드라인\n{guidelines}\n" if guidelines else ""
    return AUDITOR_USER_PROMPT.format(
        draft_script=draft_script,
        guidelines_section=guidelines_section,
    )


# ============================================
# Editor 프롬프트 (100% 정적 - 전체 캐시)
# ============================================

_EDITOR_SYSTEM_TEXT = """\
당신은 유튜브 대본 최종 편집자입니다.
검수를 통과한 대본을 자연스럽고 말맛 있게 다듬습니다.

## 규칙
- 내용(정보, 구조)은 변경하지 않고 표현만 다듬습니다
- 읽었을 때 자연스럽게 흐르도록 리듬감을 살립니다
- 섹션 구분을 명확히 유지합니다

## 출력
다듬어진 최종 원고를 원본과 동일한 JSON 형식으로 반환하세요."""

EDITOR_USER_PROMPT = """\
아래 대본을 자연스럽게 다듬어 최종 버전을 작성해주세요.
{guidelines_section}
## 다듬을 대본
{draft_script}

원본과 동일한 JSON 형식으로 최종 원고를 반환하세요.
"""


def build_editor_system_prompt() -> SystemMessage:
    """Editor 시스템 메시지를 생성합니다 (100% 정적, 전체 캐시)."""
    return SystemMessage(
        content=[
            {"type": "text", "text": _EDITOR_SYSTEM_TEXT, "cache_control": _CACHE_CONTROL},
        ]
    )


def build_editor_user_prompt(draft_script: str, guidelines: str = "") -> str:
    """Editor 유저 프롬프트를 생성합니다."""
    guidelines_section = f"\n## 제작 가이드라인\n{guidelines}\n" if guidelines else ""
    return EDITOR_USER_PROMPT.format(
        draft_script=draft_script,
        guidelines_section=guidelines_section,
    )
