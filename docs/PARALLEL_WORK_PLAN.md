# Phase 7/8 병렬 작업 계획

> **작성일**: 2026-02-06
> **상태**: Active
> **기반**: Phase 5(백엔드) + Phase 6(프론트엔드 대시보드) 완료

## 에이전트 구성

| 에이전트 | 역할 | 담당 |
|----------|------|------|
| **Claude Code #1** | 백엔드 인프라 개발 | Stream A: Task Queue (P7-1) |
| **Claude Code #2** | 백엔드 AI/DB 개발 | Stream B: RAG (P7-2) → Stream D: Cost Tracking (P8-3) |
| **Gemini** | 프론트엔드 + 인프라 | Stream C: Monitoring/Logging (P8-1+P8-2) |
| **Codex** | PM / 코드 리뷰어 | 모든 PR 리뷰, 머지 순서 관리 |

---

## Work Streams

### Stream A: 비동기 작업 큐 (P7-1)

- **브랜치**: `feature/p7-1-async-task-queue`
- **담당**: Claude Code #1

**작업 내용**:
1. Redis + Arq 기반 worker 서비스 구현
2. `POST /pipeline/run` → 큐 enqueue 방식으로 전환
3. Worker가 파이프라인 실행, DB status 업데이트
4. docker-compose에 Redis + Worker 서비스 추가
5. 테스트 및 `docs/QUEUES.md` 작성

**소유 파일** (이 스트림만 수정):
- `docker-compose.yml` ← Primary Owner
- `packages/agents/src/api/routes/pipeline.py`
- `Makefile` (worker/redis 타겟 추가)
- NEW: `packages/agents/src/worker/` (tasks.py, config.py)
- NEW: `docs/QUEUES.md`
- `packages/agents/pyproject.toml` (queue 의존성 그룹 추가)

---

### Stream B: 브랜드 리서치 RAG (P7-2)

- **브랜치**: `feature/p7-2-brand-rag`
- **담당**: Claude Code #2

**작업 내용**:
1. ChromaDB 기반 벡터 스토리지 선택 및 설정
2. brand_guide.yaml + 리서치 결과 인덱싱 파이프라인
3. Brand Researcher에 RAG 컨텍스트 주입
4. RAG on/off 품질 비교 문서화
5. 테스트 작성

**소유 파일**:
- `packages/agents/src/brand_researcher/agent.py`
- `packages/agents/src/brand_researcher/collector.py`
- NEW: `packages/agents/src/brand_researcher/rag/` (indexer.py, retriever.py, config.py)
- NEW: `packages/agents/tests/test_rag.py`
- `packages/agents/pyproject.toml` (rag 의존성 그룹 추가 - 별도 섹션)

---

### Stream C: 모니터링 + 로깅 (P8-1+P8-2)

- **브랜치**: `feature/p8-1-2-monitoring-logging`
- **담당**: Gemini

**작업 내용**:
1. Prometheus metrics 노출 (`/metrics` 엔드포인트)
2. Grafana 대시보드 JSON 작성
3. Loki 기반 중앙 로그 수집 설정
4. 구조화(JSON) 로깅 적용
5. docker-compose 프래그먼트 파일 제공
6. `docs/MONITORING.md`, `docs/LOGGING.md` 작성
7. (선택) 프론트엔드 채널 페이지 API 연동, 테스트 보강

**소유 파일**:
- `packages/agents/src/api/main.py` (metrics 미들웨어 추가)
- NEW: `infra/prometheus/prometheus.yml`
- NEW: `infra/grafana/dashboards/*.json`
- NEW: `infra/loki/loki-config.yml`
- NEW: `infra/docker-compose.monitoring.yml`
- NEW: `docs/MONITORING.md`, `docs/LOGGING.md`
- `packages/agents/pyproject.toml` (monitoring 의존성 그룹 추가 - 별도 섹션)
- `packages/frontend/` (채널 페이지 개선 - 선택)

---

### Stream D: 비용/사용량 추적 (P8-3)

- **브랜치**: `feature/p8-3-cost-tracking`
- **담당**: Claude Code #2 (Stream B 완료 후)

**작업 내용**:
1. `usage_events` 테이블 + Alembic 마이그레이션
2. LLM 콜백으로 토큰/비용 자동 기록
3. `GET /api/v1/usage` API 엔드포인트
4. dashboard/summary의 `estimated_cost_usd` 필드 연동
5. 테스트 작성

**소유 파일**:
- `packages/agents/src/database/models.py` (UsageEventModel 추가)
- `packages/agents/src/database/repositories.py` (UsageRepository 추가)
- `packages/agents/src/shared/llm_clients.py` (토큰 카운팅 콜백)
- `packages/agents/src/api/routes/dashboard.py` (estimated_cost_usd 연동)
- `packages/agents/src/api/schemas.py` (usage 스키마 추가)
- NEW: `packages/agents/src/api/routes/usage.py`
- NEW: `packages/agents/alembic/versions/xxxx_add_usage_events.py`
- NEW: `packages/agents/tests/test_usage.py`

---

## 의존성 그래프

```
              main (P6-4 머지 후)
              ┌──────┼──────────┐
              v      v          v
         Stream A  Stream B   Stream C
         (P7-1)   (P7-2)    (P8-1+2)
              |      |          |
              |      v          |
              |   Stream D     |
              |   (P8-3)       |
              |      |          |
              v      v          v
         ---- 순서대로 main에 머지 ----
                     |
                     v
              Stream E: P7-3
            (Workspace 마이그레이션)
```

**하드 의존성**:
- Stream D(P8-3)는 Stream B(P7-2) 완료 후 시작
- P7-3은 모든 스트림 머지 후 진행

**소프트 의존성** (병렬 진행 가능):
- Stream A, B, C는 완전 독립 - 동시 시작

---

## 공유 파일 충돌 해결 프로토콜

### `docker-compose.yml` - Owner: Stream A
- Stream A: Redis + Worker 서비스 추가
- Stream C: `infra/docker-compose.monitoring.yml`로 별도 제공
- 머지 시: `docker compose -f docker-compose.yml -f infra/docker-compose.monitoring.yml` 패턴

### `packages/agents/pyproject.toml` - 각 스트림이 별도 섹션에 추가
```toml
# Stream A:
[project.optional-dependencies]
queue = ["arq>=0.26", "redis>=5.0"]

# Stream B:
rag = ["chromadb>=0.5", "langchain-chroma>=0.2"]

# Stream C:
monitoring = ["prometheus-fastapi-instrumentator>=7.0", "python-json-logger>=3.0"]
```
- 각 스트림은 새 그룹만 추가, 기존 그룹 수정 금지
- `all` 그룹은 마지막 머지 시 한번에 업데이트

### `packages/agents/src/api/main.py` - Owner: Stream C
- Stream C: metrics 미들웨어 + 구조화 로깅 설정
- Stream D: `usage.router` 등록 1줄 추가
- 머지 순서: Stream C 먼저, Stream D가 rebase

### `Makefile` - 각 스트림이 파일 끝에 독립 블록 추가
- Stream A: `worker`, `redis-up` 타겟
- Stream B: `rag-index` 타겟
- Stream C: `monitoring-up`, `monitoring-down` 타겟

---

## 인터페이스 계약

### 1. Usage Event 스키마
```python
class UsageEventModel:
    id: str          # UUID
    run_id: str      # FK -> pipeline_runs.id
    agent: str       # "script_writer", "seo_optimizer" 등
    provider: str    # "openai" | "anthropic"
    model: str       # "gpt-4o", "claude-sonnet-4-20250514"
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    created_at: datetime
```

### 2. Prometheus 메트릭 네이밍
```
yaa_pipeline_runs_total{status="completed|failed|pending"}
yaa_pipeline_duration_seconds{channel_id="..."}
yaa_http_requests_total{method, path, status}
yaa_queue_depth{queue="pipeline"}      # Stream A 머지 후 추가
yaa_llm_tokens_total{provider, model}  # Stream D 머지 후 추가
```

### 3. Docker Compose 프래그먼트 패턴
```bash
# 개발 환경 (전체 스택)
docker compose -f docker-compose.yml -f infra/docker-compose.monitoring.yml up

# 기본만
docker compose up
```

---

## 머지 순서

1. **P7-2** (Brand RAG) - 가장 독립적, brand_researcher/ 내부만 수정
2. **P8-3** (Cost Tracking) - DB 모델 추가, 독립 라우트
3. **P8-1+P8-2** (Monitoring/Logging) - main.py 수정, infra 설정
4. **P7-1** (Task Queue) - docker-compose owner, pipeline.py 수정

> 각 머지 후 `make test` + `make lint` 실행하여 전체 테스트 통과 확인

5. **P7-3** (Workspace Migration) - 모든 머지 완료 후 별도 진행

---

## 커밋 메시지 규칙

```
[타입](스코프): 제목

본문

Co-Authored-By: Claude <noreply@anthropic.com>
```

예시:
- `feat(worker): Redis + Arq 기반 비동기 작업 큐 구현`
- `feat(rag): ChromaDB 벡터 스토리지 인덱싱 파이프라인`
- `feat(monitoring): Prometheus metrics 엔드포인트 추가`
- `feat(usage): LLM 비용/사용량 추적 시스템 구현`

---

## 검증 방법

- 각 스트림 PR에서 `make test` 통과 확인
- 각 스트림 PR에서 `make lint` 통과 확인
- Codex가 모든 PR 리뷰 후 머지 승인
- 머지 후 통합 테스트: `docker compose up`으로 전체 스택 구동 확인
- P7-3 이후: workspace 기준으로 개별 패키지 테스트 실행 확인
