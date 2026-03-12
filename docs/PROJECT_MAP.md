# Project Map

현재 저장소의 실행 구조를 코드 기준으로 정리한 문서입니다.
`docs/ROADMAP.md`, `docs/PARALLEL_WORK_PLAN.md` 같은 계획 문서는 과거 설계 상태를 포함하므로,
현재 구현 파악에는 이 문서를 우선 사용합니다.

## 1. 워크스페이스 구성

루트 워크스페이스는 다음 3개 Python 패키지를 소스 오브 트루스로 사용합니다.

| 패키지 | 역할 | 대표 모듈 |
|--------|------|-----------|
| `packages/core` | 공용 설정, 채널 레지스트리, DB 모델/저장소 | `yaa_core.shared`, `yaa_core.database` |
| `packages/agents` | LangGraph 오케스트레이터와 각 AI 에이전트 | `yaa_agents.orchestrator`, `yaa_agents.*` |
| `packages/api` | FastAPI API, CLI, Arq 워커 | `yaa_app.api`, `yaa_app.cli`, `yaa_app.worker` |

보조 구성:

- `channels/`: 채널별 `config.yaml`, `brand_guide.yaml`, `sources/` 저장소
- `docs/`: 운영/아키텍처 문서
- `docker-compose.yml`: 로컬 실행용 API + worker + Redis + PostgreSQL
- `packages/frontend/`: 별도 Next.js 앱
- 루트 `package.json`: Parcel 실험 스텁으로, 현재 백엔드 워크스페이스와는 분리되어 있음

## 2. 패키지 책임

### `packages/core`

- `yaa_core.shared.config.AppSettings`
  - `.env` 기반 애플리케이션 설정 로드
- `yaa_core.shared.config.ChannelRegistry`
  - 파일시스템 기반 채널 조회/생성/수정/삭제
- `yaa_core.database.models`
  - ORM 모델 정의
- `yaa_core.database.repositories`
  - API/워커가 사용하는 저장소 계층

### `packages/agents`

- `yaa_agents.orchestrator.state`
  - 파이프라인 공유 상태 `PipelineState`
- `yaa_agents.orchestrator.supervisor`
  - LangGraph 노드/라우팅/그래프 컴파일
- 개별 에이전트
  - `brand_researcher`
  - `script_writer`
  - `seo_optimizer`
  - `media_generator`
  - `media_editor`
  - `publisher`
  - `analyzer`

실제 파이프라인 순서:

```text
brand_research
-> script_writing
-> seo_optimization
-> media_generation
-> media_editing
-> publishing
```

### `packages/api`

- `yaa_app.api.main`
  - FastAPI 앱 생성, DB 초기화, 미들웨어/라우터 등록
- `yaa_app.api.auth`
  - API 키 + JWT 인증, workspace 컨텍스트 해석
- `yaa_app.api.routes.*`
  - REST API 엔드포인트
- `yaa_app.cli`
  - CLI 파서, 에이전트 레지스트리 구성, 로컬 실행 진입점
- `yaa_app.worker.enqueue`
  - Redis/Arq enqueue
- `yaa_app.worker.tasks`
  - 큐 소비, 파이프라인 실행, 사용량 저장

## 3. API 표면

### 상태/기본

| 메서드 | 경로 | 인증 | 기능 |
|--------|------|------|------|
| `GET` | `/api/v1/health` | 없음 | 헬스체크 |
| `GET` | `/api/v1/status/{run_id}` | API 키 또는 JWT | 특정 실행 상태 조회 |

### 채널

| 메서드 | 경로 | 인증 | 기능 |
|--------|------|------|------|
| `GET` | `/api/v1/channels/` | API 키 또는 JWT | 채널 목록 |
| `GET` | `/api/v1/channels/{channel_id}` | API 키 또는 JWT | 채널 상세 |
| `POST` | `/api/v1/channels/` | 관리자 권한 | 템플릿 기반 채널 생성 |
| `PATCH` | `/api/v1/channels/{channel_id}` | 관리자 권한 | 채널 설정 수정 |
| `DELETE` | `/api/v1/channels/{channel_id}` | 관리자 권한 | 채널 삭제 |

채널 데이터는 DB가 아니라 `channels/` 디렉토리에서 읽습니다.

### 파이프라인

| 메서드 | 경로 | 인증 | 기능 |
|--------|------|------|------|
| `POST` | `/api/v1/pipeline/run` | 인증 + workspace | 새 파이프라인 실행 |
| `GET` | `/api/v1/pipeline/runs` | 인증 + workspace | 실행 이력 목록 |
| `GET` | `/api/v1/pipeline/runs/{run_id}` | 인증 + workspace | 실행 상세 |

`POST /run`은 실행 요청을 `pipeline_runs`에 `pending`으로 기록한 뒤:

- Redis가 있으면 Arq 큐로 전달
- Redis가 없으면 `BackgroundTasks`로 폴백

### 대시보드/사용량

| 메서드 | 경로 | 인증 | 기능 |
|--------|------|------|------|
| `GET` | `/api/v1/dashboard/summary` | 인증 + workspace | 실행 통계/최근 실행/비용 |
| `GET` | `/api/v1/usage/events` | API 키 또는 JWT | 사용량 이벤트 목록 |
| `GET` | `/api/v1/usage/summary` | API 키 또는 JWT | 비용/토큰 집계 |

### 사용자/워크스페이스

| 메서드 | 경로 | 인증 | 기능 |
|--------|------|------|------|
| `POST` | `/api/v1/users/oauth/callback` | 없음 | OAuth 사용자 동기화 + 첫 workspace 생성 |
| `GET` | `/api/v1/users/me` | JWT | 현재 사용자 조회 |
| `GET` | `/api/v1/users/me/workspace` | JWT | 현재 workspace 조회 |

### 요금제/결제

| 메서드 | 경로 | 인증 | 기능 |
|--------|------|------|------|
| `GET` | `/api/v1/plans` | 없음 | 요금제 정의 |
| `GET` | `/api/v1/plans/usage` | 인증 + workspace | 월간 사용량/기능 한도 |
| `POST` | `/api/v1/billing/checkout` | 인증 + workspace | Stripe Checkout 세션 |
| `POST` | `/api/v1/billing/portal` | 인증 + workspace | Stripe 포털 세션 |
| `GET` | `/api/v1/billing/subscription` | 인증 + workspace | 현재 구독 상태 |
| `POST` | `/api/v1/billing/webhook` | Stripe 서명 | 결제 웹훅 |

### 관리자

| 메서드 | 경로 | 인증 | 기능 |
|--------|------|------|------|
| `POST` | `/api/v1/admin/api-keys` | 관리자 권한 | API 키 생성 |
| `GET` | `/api/v1/admin/api-keys` | 관리자 권한 | API 키 목록 |
| `DELETE` | `/api/v1/admin/api-keys/{key_id}` | 관리자 권한 | API 키 비활성화 |
| `GET` | `/api/v1/admin/audit-logs` | 관리자 권한 | 감사 로그 조회 |

## 4. 인증 모델

지원 인증 방식:

- API 키
  - `X-API-Key` 헤더
  - SHA-256 해시를 DB의 `api_keys.key_hash`와 비교
- JWT Bearer
  - `Authorization: Bearer <token>`
  - 토큰에서 사용자 식별 후 소유 workspace 해석
- 개발용 인증 비활성화
  - `DISABLE_AUTH=true`

관리자 권한 규칙:

- JWT 인증 사용자는 자기 workspace에 대해 관리자 취급
- API 키 인증은 `admin` 스코프가 필요

## 5. DB 스키마 맵

### 핵심 엔터티

| 테이블 | 목적 | 주요 필드 |
|--------|------|-----------|
| `users` | 사용자 계정 | `email`, `provider`, `plan`, `is_active` |
| `workspaces` | 멀티테넌시 단위 | `owner_id`, `plan`, `pipeline_quota`, `channel_quota` |
| `subscriptions` | Stripe 구독 상태 | `workspace_id`, `stripe_customer_id`, `plan`, `status` |
| `pipeline_runs` | 파이프라인 실행 이력 | `channel_id`, `workspace_id`, `topic`, `status`, `result_json`, `errors_json` |
| `api_keys` | API 키 인증 정보 | `key_hash`, `workspace_id`, `scopes_json`, `expires_at` |
| `audit_logs` | 요청 감사 로그 | `method`, `path`, `status_code`, `api_key_id`, `duration_ms` |
| `usage_events` | LLM 사용량 추적 | `run_id`, `agent`, `provider`, `model`, `total_tokens`, `cost_usd` |

### 관계

- `users 1:N workspaces`
- `workspaces 1:N pipeline_runs`
- `workspaces 1:N api_keys`
- `workspaces 1:N subscriptions` 실사용은 보통 1:1
- `pipeline_runs 1:N usage_events` 논리 관계

### 상태 전이

`pipeline_runs.status`는 보통 다음 순서로 전이됩니다.

```text
pending -> running -> completed
pending -> running -> failed
```

콘텐츠 도메인 상태(`ContentStatus`)는 LangGraph 내부 결과에 포함되고,
API 레벨 실행 상태는 `pipeline_runs.status`에 별도로 저장됩니다.

## 6. 요청 흐름

`POST /api/v1/pipeline/run` 기준 실제 실행 흐름:

1. FastAPI가 요청을 수신합니다.
2. `get_auth_context()`가 API 키 또는 JWT를 해석합니다.
3. workspace가 있으면 요금제 한도를 검사합니다.
4. `RunRepository.create()`로 `pipeline_runs`에 `pending` 레코드를 생성합니다.
5. `enqueue_pipeline()`이 Redis 연결을 시도합니다.
6. 분기:
   - 성공: Arq worker가 `execute_pipeline_task()`를 실행
   - 실패: FastAPI `BackgroundTasks`가 `_execute_pipeline()`를 실행
7. 실행 측은 공통으로:
   - 상태를 `running`으로 갱신
   - `_build_agent_registry()`로 LLM/에이전트 인스턴스를 구성
   - `compile_pipeline()` 후 `ainvoke()` 실행
8. 완료 후:
   - `pipeline_runs.status`를 `completed` 또는 `failed`로 갱신
   - `result_json`, `errors_json`, `completed_at` 기록
   - `UsageCollector` 이벤트를 `usage_events`에 저장
9. 이후 `dashboard`, `status`, `usage` 엔드포인트가 같은 DB를 읽어 결과를 노출합니다.

## 7. 운영 메모

- 채널 설정은 파일시스템 기반이므로 백업 대상은 DB와 `channels/` 둘 다입니다.
- 로컬 기본 DB는 SQLite지만 Docker 기본 구성은 PostgreSQL + Redis입니다.
- `packages/frontend`는 별도 Next.js 앱이며, 현재 `uv` 워크스페이스 멤버는 아닙니다.
- 과거 구조를 설명하는 문서를 볼 때는 파일 경로가 `packages/agents/src/...`인지 먼저 확인하세요.
