# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Project Name:** Youtube-AI-Agent-Agency
**Author/Owner:** VetEngineer
**License:** MIT

YouTube 콘텐츠 자동 생성 파이프라인 시스템입니다. LangGraph 기반 6단계 AI 에이전트 파이프라인(브랜드 리서치 → 원고 → SEO → 미디어 생성 → 편집 → 업로드)을 FastAPI REST API와 CLI로 제어합니다.

## Current Status

**Phase 5 완료** - 핵심 기능 구현 완료 상태

| Phase | 설명 | 상태 |
|-------|------|------|
| Phase 2 | LangGraph 기반 AI 에이전트 파이프라인 | 완료 |
| Phase 3 | E2E 실행 환경 구축 (Docker, CI) | 완료 |
| Phase 4 | DB 영속화, API 인증, 미들웨어 | 완료 |
| Phase 5 | API CRUD 완성, Alembic 마이그레이션 | 완료 |

## Tech Stack

- **Language:** Python 3.11+
- **Package Manager:** uv
- **AI Framework:** LangGraph (StateGraph)
- **LLM:** Claude (Anthropic) + GPT-4o (OpenAI)
- **API:** FastAPI + Pydantic v2
- **Database:** SQLAlchemy 2.0 async + Alembic (SQLite dev / PostgreSQL prod)
- **Auth:** SHA-256 API Key 인증 + 스코프 기반 권한
- **Testing:** pytest + pytest-asyncio (371+ 테스트)
- **Lint:** ruff
- **Container:** Docker Compose (PostgreSQL 16 + FastAPI)
- **CI:** GitHub Actions

## Common Commands

```bash
make test          # 전체 테스트 실행
make lint          # 린트 검사
make format        # 코드 포맷팅
make server        # FastAPI 서버 (reload 모드)
make db-upgrade    # DB 마이그레이션 적용
make db-migrate msg="설명"  # 새 마이그레이션 생성
```

## Architecture

```
packages/agents/src/
├── api/                    # FastAPI REST API
│   ├── main.py             # 앱 팩토리 + 라우터 등록
│   ├── auth.py             # API 키 인증 + 스코프 검증
│   ├── middleware.py        # 감사 로그 + Rate Limiting
│   ├── schemas.py          # Pydantic 요청/응답 스키마
│   ├── dependencies.py     # 의존성 주입
│   └── routes/             # 엔드포인트
│       ├── admin.py        # API 키 관리 + 감사 로그
│       ├── channels.py     # 채널 CRUD
│       ├── pipeline.py     # 파이프라인 실행 + 이력
│       └── status.py       # 상태 조회 + 헬스체크
├── database/               # 데이터 영속화
│   ├── engine.py           # 비동기 세션 팩토리
│   ├── models.py           # SQLAlchemy ORM 모델
│   └── repositories.py     # Repository 패턴 (CRUD + 필터링)
├── orchestrator/           # LangGraph Supervisor
├── brand_researcher/       # 브랜드 리서치 에이전트
├── script_writer/          # 원고 생성 에이전트 (Claude)
├── seo_optimizer/          # SEO 최적화 에이전트 (GPT-4o)
├── media_generator/        # 미디어 생성 에이전트 (TTS + 이미지)
├── media_editor/           # 영상 편집 에이전트 (FFmpeg)
├── publisher/              # YouTube 업로드 에이전트
└── shared/                 # 공유 모듈 (config, models, LLM clients)
```

## Key Patterns

- **Repository Pattern:** 모든 DB 접근은 `repositories.py`의 Repository 클래스를 통해 수행
- **Dependency Injection:** FastAPI의 `Depends()`를 활용한 의존성 주입
- **API Key Auth:** `yaa_` 접두사 + SHA-256 해싱, `require_api_key` / `require_admin_scope` 의존성
- **ChannelRegistry:** YAML 기반 채널 설정 관리 (파일시스템 + 캐싱)
- **Alembic:** `packages/agents/alembic/`에서 DB 스키마 마이그레이션 관리
