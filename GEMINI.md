# Youtube-AI-Agent-Agency Context

## Project Overview
**Project Name:** Youtube-AI-Agent-Agency
**Author/Owner:** VetEngineer
**License:** MIT


## 🏛️ Council & Roles

This project follows a Council-based development process.

### Your Role: Gemini (Frontend Designer)
- **Responsibility:** Frontend Design & UI/UX.
- **Rules:**
  - Create designs optimized for UI/UX.
  - Focus on aesthetics and usability.
  - Coordinate with Claude-code (Developer) for implementation details.


## Current Status
**Phase 5 완료** - 핵심 기능 구현 완료

- Phase 2: LangGraph 기반 AI 에이전트 파이프라인
- Phase 3: E2E 실행 환경 (Docker Compose, GitHub Actions CI)
- Phase 4: DB 영속화 (SQLAlchemy async), API 키 인증, 감사 로그 미들웨어
- Phase 5: Admin API CRUD, 파이프라인 이력 조회, 채널 CRUD, Alembic 마이그레이션

## Tech Stack
- **Language:** Python 3.11+
- **Package Manager:** uv
- **AI Framework:** LangGraph (StateGraph) for multi-agent orchestration
- **LLMs:** Claude (Anthropic) for script writing, GPT-4o (OpenAI) for SEO
- **API:** FastAPI + Pydantic v2
- **Database:** SQLAlchemy 2.0 async (SQLite dev / PostgreSQL 16 prod) + Alembic migrations
- **Auth:** API Key (SHA-256 hashing) with scope-based authorization
- **Middleware:** Rate limiting (slowapi), Audit logging, CORS
- **Testing:** pytest + pytest-asyncio (371+ tests)
- **Lint/Format:** ruff
- **Container:** Docker Compose (PostgreSQL + FastAPI)
- **CI:** GitHub Actions (lint, test, docker build)

## Development Conventions
- **Architecture:** Repository pattern for DB access, Dependency Injection via FastAPI
- **Config:** YAML-based channel settings via ChannelRegistry, env vars via pydantic-settings
- **API:** RESTful, versioned (`/api/v1/`), Pydantic schemas for request/response
- **Testing:** All new features require tests, 80%+ coverage target
- **Documentation:** `CLAUDE.md` / `GEMINI.md` for AI context, `docs/MANUAL.md` for user guide

## Common Commands
```bash
make test          # Run all tests
make lint          # Lint check
make format        # Code formatting
make server        # FastAPI dev server (reload)
make db-upgrade    # Apply DB migrations
make db-migrate msg="description"  # Create new migration
```

## Project Structure
```
packages/agents/src/
├── api/                    # FastAPI REST API
│   ├── auth.py             # API key auth + scope verification
│   ├── middleware.py        # Audit log + rate limiting
│   ├── routes/admin.py     # API key management + audit logs
│   ├── routes/channels.py  # Channel CRUD
│   ├── routes/pipeline.py  # Pipeline execution + history
│   └── routes/status.py    # Status + health check
├── database/               # SQLAlchemy async ORM + repositories
├── orchestrator/           # LangGraph pipeline supervisor
├── brand_researcher/       # Brand research agent
├── script_writer/          # Script writing agent (Claude)
├── seo_optimizer/          # SEO optimization agent (GPT-4o)
├── media_generator/        # TTS + image generation
├── media_editor/           # FFmpeg video editing
├── publisher/              # YouTube upload
└── shared/                 # Config, models, LLM clients
```
