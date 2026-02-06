# Claude-code 작업 계획 (Phase 6+)

## 배경
- **현재 상태:** Phase 5 완료 (핵심 기능 구현 완료)
- **다음 단계:** Phase 6~8 (Web Dashboard, 확장 아키텍처, 운영 안정화)
- **역할:** Claude-code = 개발 구현 담당 (API/백엔드/프론트엔드 구현 및 통합)
- **프론트 디자인 협업:** Gemini가 UI/UX 디자인 제공 → Claude-code가 구현

## 단계별 작업 목록 (GitHub Issue 동기화)
- 본 문서는 GitHub Issue #1~#10과 동일한 요구사항을 유지합니다.
- 각 Phase는 순서대로 진행합니다.

---

### Phase 6: Web Dashboard (Frontend)

#### P6-1 | 프론트엔드 기본 세팅 정비 (Issue #1)
목표
- Phase 6 Web Dashboard 구현을 위한 프론트 기반 정비

요구사항
1) 디자인 토큰 반영
- Pretendard + Inter 폰트 적용 (next/font/local + next/font/google 또는 @fontsource)
- 색상 토큰(--primary, --secondary, --background 등)을 globals.css/tailwind에 정리
- 다크 테마 기본 적용 유지 (html.dark)

2) 기본 레이아웃 구조 정리
- Sidebar/Topbar/Content 영역을 공통 레이아웃으로 분리
- Dashboard, Pipelines/New, Channels, Settings 라우트 스켈레톤 생성

3) 데이터 계층/환경 설정
- TanStack Query 설치 및 Provider 추가 (예: src/app/providers.tsx)
- API base URL 환경변수 `NEXT_PUBLIC_API_BASE_URL` 사용
- 공통 fetch 유틸 (예: src/lib/api.ts) 작성: X-API-Key 헤더 주입 가능 구조

4) 개발 편의
- .env.example에 프론트 관련 변수 명시
- 기본 Error/Loading UI 스켈레톤 추가 (error.tsx, loading.tsx)

비범위
- 실제 API 연동/데이터 바인딩 (P6-3에서 처리)

완료 조건
- `npm run dev`로 실행 가능
- 라우트 4개 접근 가능 (Dashboard / Pipelines/New / Channels / Settings)
- QueryClientProvider 적용 확인
- docs/DESIGN.md의 폰트/색상 기준 반영

---

#### P6-2 | 대시보드 API 계약 점검 및 보완 (Issue #2)
목표
- Dashboard 및 파이프라인 UI가 필요로 하는 API 계약을 명확화하고 누락 엔드포인트 보완

요구사항
1) API 계약 문서화
- docs/API_DASHBOARD.md 신규 작성 또는 docs/MANUAL.md 업데이트
- 화면별 필요한 엔드포인트/필드/에러/인증 요구사항 명시

2) 신규/보완 엔드포인트
- GET /api/v1/dashboard/summary (require_api_key)
  - Response 필드:
    - total_runs (int)
    - active_runs (pending+running)
    - success_runs, failed_runs
    - avg_duration_sec (completed_at - created_at 평균, 없으면 null)
    - estimated_cost_usd (P8-3 전까지 null)
    - recent_runs: PipelineRunSummary[] (기본 limit 5)

- GET /api/v1/pipeline/runs/{run_id} (require_api_key)
  - Response 필드:
    - run_id, channel_id, topic, brand_name, status, current_agent
    - dry_run, created_at, updated_at, completed_at
    - result, errors

- 기존 목록 API(`/api/v1/pipeline/runs`)는 필터/페이지네이션 규격을 문서화

3) 테스트
- pytest로 신규 endpoint 정상/에러 케이스 1개 이상 추가

완료 조건
- OpenAPI에 신규 엔드포인트 노출
- 계약 문서에 요청/응답 예시 포함
- 테스트 통과

---

#### P6-3 | 대시보드 핵심 화면 구현 + API 연동 (Issue #3)
목표
- 대시보드 핵심 화면을 실제 API 데이터로 동작시키고 파이프라인 실행 플로우 완성

요구사항
1) Dashboard (/)
- dashboard/summary 또는 관련 API 기반으로 카드/최근활동/상태 렌더링
- 로딩/에러/빈 상태 UI 제공

2) Pipeline 생성 (/pipelines/new)
- 채널 목록 API로 채널 선택
- Form validation (topic 필수, channel 필수)
- POST /pipeline/run 호출 후 run_id 반환 → /pipelines/[run_id] 이동
- 실패 시 에러 메시지 표시

3) Pipeline 상세 (/pipelines/[run_id])
- status 폴링(5~10초)으로 상태 갱신
- 단계별 타임라인(Research→Script→SEO→Media→Edit→Publish) 표시
- 결과 탭: result JSON에서 script/images/video_url 존재 시 뷰 제공, 없으면 placeholder
- 재시도/새 파이프라인 링크 제공

4) 데이터 훅 구성
- TanStack Query hooks (`useDashboardSummary`, `usePipelineRuns`, `usePipelineDetail`, `useRunPipeline`)
- 캐시 키/리페치 정책 정의

테스트
- 프론트 테스트 1건 이상 추가 (Playwright 스모크 또는 React Testing Library 중 택1, 선택한 방식 명시)

완료 조건
- Dashboard/파이프라인 생성/상세가 실제 API와 동작
- 에러/빈 상태 처리
- 테스트 추가 및 통과

---

#### P6-4 | 설정 화면 구현 (API 키/채널) + 권한 처리 (Issue #4)
목표
- 설정 화면에서 API 키/채널 관리가 가능하고 권한 흐름이 명확해야 함

요구사항
1) API 키 관리 (admin scope)
- 목록: GET /admin/api-keys
- 생성: POST /admin/api-keys (name, scopes, expires_days)
  - 생성된 plaintext key 1회 표시 + 복사 버튼
- 비활성화: DELETE /admin/api-keys/{key_id} (확인 모달)

2) 채널 관리
- 목록: GET /channels
- 생성: POST /channels (channel_id 패턴 검증)
- 수정: PATCH /channels/{channel_id}
- 삭제: DELETE /channels/{channel_id} (확인 모달)

3) 인증 UX
- API Key 입력/저장 UI (localStorage)
- 401/403 발생 시 안내 배너 + 재입력 유도
- X-API-Key 헤더 사용

4) Error/Edge
- 409/400/404 에러 메시지 표시
- 작업 중 로딩/비활성 상태 표시

완료 조건
- API 키/채널 CRUD 정상 동작
- 권한 오류 UX 처리 완료

---

### Phase 7: Advanced Architecture & Scalability

#### P7-1 | 비동기 작업 큐 도입 (Redis + Worker) (Issue #5)
목표
- 파이프라인 실행을 비동기 작업 큐로 전환하여 확장성 확보

요구사항
1) 큐 도입 설계 결정
- Redis 기반 큐 라이브러리 선택 (예: Arq 또는 Celery)
- 선택 이유와 운영 방법을 docs/QUEUES.md에 기록

2) 실행 흐름 변경
- POST /pipeline/run → 즉시 run_id 반환, 작업은 큐에 enqueue
- Worker가 실제 파이프라인 실행, DB status 업데이트
- 실패 시 status=failed, errors 기록

3) Infra
- docker-compose에 Redis + worker 서비스 추가
- 로컬 dev 명령/스크립트 정리 (Makefile or scripts)

4) 테스트
- enqueue → worker 처리 → status 업데이트 통합 테스트 1개 이상

완료 조건
- 큐 기반 실행이 로컬에서 정상 동작
- Docker Compose로 Redis/Worker 구동 가능
- 테스트 통과

---

#### P7-2 | 브랜드 리서치 RAG 도입 (Issue #6)
목표
- 브랜드 리서치 단계에 RAG를 도입하여 컨텍스트 품질 향상

요구사항
1) 스토리지 선택
- Chroma(로컬) 또는 Pinecone(관리형) 중 선택, 설정값 추가

2) 인덱싱 파이프라인
- brand_guide.yaml 및 리서치 결과를 chunking/embedding 후 저장
- 재인덱싱 CLI 또는 관리 API 제공 (예: `make rag-index channel_id=...`)

3) 검색/컨텍스트 주입
- Brand Researcher가 질의 시 top-k 컨텍스트를 받아 프롬프트에 삽입

4) 평가
- 간단한 품질 지표/비교(RAG on/off) 결과 문서화

5) 테스트
- retrieval 결과 형식/수량 검증 unit test

완료 조건
- RAG 컨텍스트가 리서치 단계에 반영됨
- 인덱싱/검색 파이프라인 실행 가능
- 테스트 통과

---

#### P7-3 | 독립 패키지 구조(Workspace) 전환 (Issue #7)
목표
- UV Workspace 기반으로 패키지 구조를 분리하여 독립 개발/테스트 지원

요구사항
1) 구조 분리
- packages/core, packages/api, packages/orchestrator, packages/brand_researcher 등 최소 2개 패키지 분리
- 기존 packages/agents/src 코드를 새 패키지로 이동

2) pyproject/uv
- 루트 pyproject.toml에 workspace 정의
- 각 패키지 pyproject.toml/의존성/entrypoints 설정

3) import/paths 정리
- 내부 import 경로 업데이트
- 공통 모듈은 core로 이동

4) CI/테스트
- GitHub Actions / Makefile에 workspace 기준 테스트 실행

5) 문서
- docs/WORKSPACE_MIGRATION.md에 변경 내용 기록

완료 조건
- 최소 2개 패키지 분리 완료
- CI 통과
- 마이그레이션 문서 작성

---

### Phase 8: Production Operations

#### P8-1 | 모니터링/메트릭 수집 (Prometheus + Grafana) (Issue #8)
목표
- 프로덕션 모니터링을 위한 Prometheus + Grafana 기본 구성

요구사항
1) Metrics
- FastAPI에 Prometheus metrics 노출 (/metrics)
- 파이프라인 실행 수/상태/시간, HTTP 요청/에러 지표 포함

2) Grafana
- Grafana 대시보드 JSON 추가 (assets/grafana 또는 docs/monitoring)
- 주요 패널: 요청량, 에러율, pipeline status, queue depth

3) Infra
- docker-compose에 Prometheus + Grafana 추가
- 샘플 설정 파일(prometheus.yml) 포함

4) 문서
- docs/MONITORING.md에 로컬 실행/접속 방법 정리

완료 조건
- 로컬에서 Prometheus/Grafana 구동 가능
- 주요 메트릭 확인 가능

---

#### P8-2 | 중앙 로그 수집 (Loki/ELK) (Issue #9)
목표
- 중앙 로그 수집을 통해 운영 관측성 확보

요구사항
1) 로그 포맷
- 구조화(JSON) 로깅
- request_id/run_id 포함

2) 수집 파이프라인
- Loki(권장) 또는 ELK 중 선택
- docker-compose에 로그 스택 추가
- FastAPI/worker 로그가 중앙에서 조회되도록 설정

3) 대시보드/쿼리
- 기본 쿼리/필터 예시 문서화

4) 문서
- docs/LOGGING.md에 설정/운영 방법 정리

완료 조건
- 중앙 로그 조회 가능
- 문서화 완료

---

#### P8-3 | 비용/사용량 추적 (Issue #10)
목표
- LLM 비용/사용량을 파이프라인 단위로 추적

요구사항
1) 데이터 모델
- usage_events 테이블 추가
  - id, run_id, agent, provider, model
  - prompt_tokens, completion_tokens, total_tokens
  - cost_usd, created_at
- Alembic 마이그레이션 포함

2) 계측
- LangChain 콜백/래퍼로 모든 LLM 호출에서 토큰/비용 기록

3) API
- GET /api/v1/usage?run_id=...&from=...&to=...
- GET /api/v1/usage/summary (run/day/agent 기준 집계)

4) UI Hook
- dashboard/summary의 estimated_cost_usd 필드 채우기

5) 테스트
- usage 저장/집계 단위 테스트

완료 조건
- 사용량 데이터 저장 및 조회 가능
- 대시보드 요약에 비용 표시 가능
- 테스트 통과
