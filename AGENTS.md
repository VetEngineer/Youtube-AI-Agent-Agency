# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

**Project Name:** Youtube-AI-Agent-Agency
**Author/Owner:** VetEngineer
**License:** MIT

YouTube 콘텐츠 자동 생성 파이프라인 시스템입니다. LangGraph 기반 6단계 AI 에이전트 파이프라인(브랜드 리서치 → 원고 → SEO → 미디어 생성 → 편집 → 업로드)을 FastAPI REST API와 CLI로 제어합니다.

## Council & Roles

This project follows a Council-based development process.

### Your Role: Codex (Developer)
- **Responsibility:** Main developer. You write code and implement features.
- **Rules:**
  - Check issues assigned to you.
  - Implement the code.
  - **MANDATORY:** Request review from **Codex** (PM) after implementation. Do not merge without review.


## Current Status

**Phase 8-3 완료 + P7-3 UV Workspace Migration 완료**

| Phase | 설명 | 상태 |
|-------|------|------|
| Phase 2 | LangGraph 기반 AI 에이전트 파이프라인 | 완료 |
| Phase 3 | E2E 실행 환경 구축 (Docker, CI) | 완료 |
| Phase 4 | DB 영속화, API 인증, 미들웨어 | 완료 |
| Phase 5 | API CRUD 완성, Alembic 마이그레이션 | 완료 |
| Phase 6 | Web Dashboard (Frontend) | 완료 |
| Phase 8-3 | LLM 비용/사용량 추적 | 완료 |
| Phase 7-3 | UV Workspace Migration (3-Package Split) | 완료 |

## Tech Stack

- **Language:** Python 3.11+
- **Package Manager:** uv (workspace)
- **AI Framework:** LangGraph (StateGraph)
- **LLM:** Codex (Anthropic) + GPT-4o (OpenAI)
- **API:** FastAPI + Pydantic v2
- **Database:** SQLAlchemy 2.0 async + Alembic (SQLite dev / PostgreSQL prod)
- **Auth:** SHA-256 API Key 인증 + 스코프 기반 권한
- **Testing:** pytest + pytest-asyncio (453+ 테스트)
- **Lint:** ruff
- **Container:** Docker Compose (PostgreSQL 16 + FastAPI)
- **CI:** GitHub Actions

## Common Commands

```bash
make install       # 의존성 설치 (uv sync --all-packages --all-extras)
make test          # 전체 테스트 실행
make lint          # 린트 검사
make format        # 코드 포맷팅
make server        # FastAPI 서버 (reload 모드)
make db-upgrade    # DB 마이그레이션 적용
make db-migrate msg="설명"  # 새 마이그레이션 생성
```

## Architecture (UV Workspace)

3개 독립 패키지로 구성. 의존성 방향: `yaa_core ← yaa_agents ← yaa_app`

```
packages/
├── core/              (yaa-core → yaa_core)
│   ├── pyproject.toml
│   └── yaa_core/
│       ├── shared/    # config, models, llm_clients, logging_config
│       └── database/  # models, engine, repositories
├── agents/            (yaa-agents → yaa_agents)
│   ├── pyproject.toml
│   └── yaa_agents/
│       ├── orchestrator/      # LangGraph Supervisor
│       ├── brand_researcher/  # 브랜드 리서치 에이전트
│       ├── script_writer/     # 원고 생성 에이전트 (Codex)
│       ├── seo_optimizer/     # SEO 최적화 에이전트 (GPT-4o)
│       ├── media_generator/   # 미디어 생성 에이전트 (TTS + 이미지)
│       ├── media_editor/      # 영상 편집 에이전트 (FFmpeg)
│       ├── publisher/         # YouTube 업로드 에이전트
│       └── analyzer/          # 분석 에이전트
└── api/               (yaa-app → yaa_app)
    ├── pyproject.toml
    ├── alembic.ini
    ├── alembic/       # DB 마이그레이션
    ├── tests/         # 전체 테스트
    └── yaa_app/
        ├── api/       # FastAPI REST API
        ├── worker/    # Arq 비동기 워커
        └── cli.py     # CLI 엔트리포인트
```

### Import 규칙

| 패키지 | import 접두사 |
|--------|--------------|
| core | `from yaa_core.shared.*`, `from yaa_core.database.*` |
| agents | `from yaa_agents.{agent_name}.*` |
| api | `from yaa_app.api.*`, `from yaa_app.worker.*`, `from yaa_app.cli` |

## Key Patterns

- **Repository Pattern:** 모든 DB 접근은 `yaa_core.database.repositories`의 Repository 클래스를 통해 수행
- **Dependency Injection:** FastAPI의 `Depends()`를 활용한 의존성 주입
- **API Key Auth:** `yaa_` 접두사 + SHA-256 해싱, `require_api_key` / `require_admin_scope` 의존성
- **ChannelRegistry:** YAML 기반 채널 설정 관리 (파일시스템 + 캐싱)
- **Alembic:** `packages/api/alembic/`에서 DB 스키마 마이그레이션 관리
- **UsageCollector:** LangChain 콜백 기반 LLM 토큰/비용 인메모리 수집 → 파이프라인 완료 후 DB 일괄 저장
