# YAA (Youtube-AI-Agent-Agency) 핸드오프 문서

> 작성일: 2026-04-10 (6차)
> 이전 핸드오프: 2026-04-10 (5차)

---

## 1. 서비스 URL

| 서비스 | URL | 상태 |
|--------|-----|------|
| 프론트엔드 | https://ytai.hakhamsolution.co.kr | 운영 중 |
| 프론트엔드 (Vercel) | https://ytai-chi.vercel.app | 운영 중 |
| API 서버 | https://api.ytai.hakhamsolution.co.kr | 운영 중 (OCI VM) |
| OCI VM | 134.185.113.58:22 | SSH 가능 |

---

## 2. 완료된 작업 (이번 세션 — Desktop M4+M5)

### 2-0. Desktop M4 — Tauri 네이티브 기능 (커밋 `94a5650`)

- `commands/backend.rs`: Docker 제어 4종 (`check_docker_available`, `start_local_backend`, `stop_local_backend`, `get_local_backend_status`)
  - `generate_local_secret()`: `/dev/urandom` 32바이트 hex (Windows XOR 폴백)
  - `start_local_backend`: `--pull missing` + `SECRET_KEY` 런타임 주입
  - `get_local_backend_status`: NDJSON 파싱 (State/Health 매핑)
- `tray/mod.rs`: 시스템 트레이 (열기/종료 메뉴, 좌클릭 윈도우 복원, CloseRequested → 숨김)
- `lib.rs`: `QuitRequested` AtomicBool 상태, invoke_handler 5종, `on_window_event` 핸들러
- `resources/docker-compose.desktop.yml`: SQLite `////data/yaa.db` 절대경로, `127.0.0.1:8000`, healthcheck
- `lib/tauri-store.ts`: `getRemoteBackendUrl`, `getBackendMode`, `setBackendMode`, `getLocalBackendPort` 추가
- `providers/BackendProvider.tsx`: store 싱글톤 통합, `onUrlChangeRef` 패턴, Docker 미설치 → remote 폴백
- `providers/AuthProvider.tsx`: `clearAuthForBackendSwitch`, `isLocalUrl`, `isSecureUrl` 추가
- `App.tsx`: `BackendBridge` — `clearAuthForBackendSwitch` 연동, `remoteUrl` async 로드
- `pages/settings/BackendSection.tsx`: 백엔드 모드 전환 UI, 5초 폴링, radio 접근성

**10회 codex:review 사이클 핵심 수정:**
- P0: SECRET_KEY 하드코딩 → 런타임 생성
- P0: `isLocalUrl` 127.0.0.1 + ::1 포함
- P1: BackendProvider init → onUrlChange 제거 (AuthProvider 담당)
- P1: `isMountedRef` 레이스 → `cancelled` 패턴
- P1: store 싱글톤 중복 → tauri-store.ts 통합

### 2-0b. Desktop M5 — 패키징 CI/CD (커밋 `9922930`)

- `.github/workflows/desktop-release.yml`: 크로스플랫폼 4-target 매트릭스
  - macOS arm64 / macOS x64 / Ubuntu 22.04 / Windows
  - 트리거: `workflow_dispatch` + `desktop-v*` 태그 push
  - `tauri-apps/tauri-action@v0` — GitHub Release 자동 생성
  - macOS 공증 secrets: `APPLE_CERTIFICATE`, `APPLE_ID`, `APPLE_PASSWORD`, `APPLE_TEAM_ID`
  - 업데이터 서명 secrets: `TAURI_SIGNING_PRIVATE_KEY`, `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`
- `tauri-plugin-updater = "2"` 등록 (Cargo.toml + lib.rs + capabilities/default.json)
- `tauri.conf.json`: `plugins.updater` — GitHub Releases `latest.json` 엔드포인트 (pubkey 플레이스홀더)

### Desktop 릴리즈 전 필수 액션
```bash
# 1. 서명키 생성
tauri signer generate -w ~/.tauri/yaa-desktop.key

# 2. 출력된 공개키 → tauri.conf.json plugins.updater.pubkey 교체

# 3. GitHub Secrets 등록
#    TAURI_SIGNING_PRIVATE_KEY, TAURI_SIGNING_PRIVATE_KEY_PASSWORD
#    APPLE_CERTIFICATE, APPLE_CERTIFICATE_PASSWORD, APPLE_SIGNING_IDENTITY
#    APPLE_ID, APPLE_PASSWORD, APPLE_TEAM_ID

# 4. 첫 릴리즈
git tag desktop-v0.1.0 && git push origin desktop-v0.1.0
```

---

## 이전 세션 완료 작업 (5차)

### 2-1. P0 보안/결제 취약점 15건 수정 (#68, #69)

**커밋 `d14db66`**

#### #68 인증/보안 (8건)
- IDOR: admin API 키 삭제 `get_auth_context` 의존성 주입, 소유권 체크 강화
- `.env.example` DISABLE_AUTH 기본값 `false`
- `__dev__` workspace_id → `None`
- ChannelRegistry workspace_id 정규식 검증 (경로 순회 방지)
- `encrypt_value()` 평문 fallback → `RuntimeError`
- JWT 시크릿 최소 32자 검증
- `Dockerfile.prod` 비-root 사용자 (`appuser`)
- `/metrics` 인증 + 프로덕션 OpenAPI `/docs` 비활성화

#### #69 결제 보안 (6건)
- Toss confirm `SELECT FOR UPDATE` 멱등성
- Toss API 응답 금액/주문ID 교차 검증
- 취소된 구독 DONE 웹훅 재활성화 방지
- Stripe 웹훅 이벤트 ID LRU 캐시 (중복 방지)
- checkout plan `PLAN_QUOTAS` 유효성 검증
- `_price_id_to_plan` 문자열 폴백 → `free` 안전 폴백

### 2-2. P1 백엔드/프론트엔드/DB 이슈 25건 (#70, #71, #72)

**커밋 `38d2068`**

#### #70 백엔드 (11건)
- pipeline cancel 후 명시적 commit
- competitors RuntimeError 내부 정보 노출 제거
- `response.content` list 타입 처리 (4개 에이전트)
- 수정 프롬프트 `previous_draft` 파라미터 추가
- 비-Anthropic LLM용 cache_control 제거 로직
- Auditor JSON 파싱 실패 → FAIL 안전 처리
- `batch_openai`: `AsyncOpenAI` + `time.monotonic` + 임시파일 정리
- `oauth_tokens` UNIQUE(workspace_id, provider)

#### #71 프론트엔드 (9건)
- SSE API 키 쿼리 파라미터 전달
- `video_url` XSS 방지 (https 프로토콜 검증)
- signOut 시 sessionStorage API 키 삭제
- signIn 백엔드 실패 경고 로그
- `useApiKeys` retry `ApiError.status` 체크
- SSE esRef cleanup null 리셋
- `console.error` 4곳 제거
- API 키 삭제 버튼 `aria-label` 추가
- `useRetryPipeline` dashboard 캐시 무효화

#### #72 DB 스키마 (5건)
- API 키 컬럼 `String(200)` → `String(500)`
- `CompetitorVideo` 유니크 제약 추가
- `engine.py` 비공개 API → 모듈 변수 + `get_engine()` 공개 API

### 2-3. 회귀 테스트 23건 추가 (#73)

**커밋 `ea210aa`**

- ChannelRegistry 경로순회 방지 테스트
- 암호화 라운드트립 + ENCRYPTION_KEY 미설정 RuntimeError
- JWT 시크릿 최소 길이 검증
- Toss 주문 소유권/멱등성 검증
- `_price_id_to_plan` 안전 폴백 확인

### 2-4. Baseline UI 위반 86건 수정

**커밋 `3336be3` + `d4b6063`**

- gradient 제거 (대시보드 stat 카드 4개)
- glow 효과 제거 (sidebar, empty state, glow-red)
- `font-tabular` → `tabular-nums`
- `tracking-tight` 제거 (모든 heading)
- `text-balance` 추가 (모든 heading)
- `text-pretty` 추가 (모든 paragraph)
- `min-h-screen` → `min-h-dvh` (login, onboarding)
- icon-only 버튼 `aria-label` 추가 (전체)
- `h-* w-*` → `size-*` (정사각형 요소)
- competitors `confirm()` → AlertDialog 전환

### 2-5. CI 수정

**커밋 `539b24d`**

- `/metrics` 엔드포인트: `get_settings()` 직접 호출 → `Depends(get_settings)` (테스트 override 적용)
- `ruff format` 7개 파일 적용

### 2-6. GitHub 이슈 정리
- **종료**: #68, #69, #70, #71, #72, #73
- **열림**: #64 (채널 마이그레이션, 보류), #67 (ElevenLabs, 수동)

---

## 3. 다음에 해야 할 작업

### 채널 데이터 마이그레이션 (#64, 보류)
- 사용자 가입 후 OCI VM SSH 접속
- `channels/{channel_id}` → `channels/{workspace_id}/{channel_id}` 이동
- DB에서 workspace_id 조회: `SELECT id FROM workspaces`

### ElevenLabs Scale 플랜 전환 (#67, 수동)
- elevenlabs.io 콘솔에서 현재 사용량 확인
- Scale 플랜 비용 대비 비교 후 전환
- 코드 변경 불필요

### OCI VM 배포 (신규 커밋 6건 미배포)
- 현재 OCI VM: 커밋 `0385580`
- 최신 main: 커밋 `539b24d`
- SSH 접속 후 `git pull` → Docker 빌드 → 컨테이너 재시작

### Desktop 첫 릴리즈 (M1~M5 완료, 릴리즈 태그만 남음)
- `tauri signer generate` → `tauri.conf.json` pubkey 교체 → GitHub Secrets 등록 → `git tag desktop-v0.1.0`
- 상세: `DESKTOP_MILESTONES.md` 참조

---

## 4. 주의사항

- **GitHub push**: `gh auth switch --user VetEngineer` 필수 (기본 hakhamsolution)
- **OCI VM SSH**: `ssh -i '/Volumes/Silvernine/Users/eungu/Downloads/OCI ssh key_XEO/ssh-key-2026-03-11.key' opc@134.185.113.58`
- **OCI VM Docker**: `docker compose -f docker-compose.prod.yml --env-file .env.oracle up -d`
- **Docker 빌드**: 반드시 `Dockerfile.prod` 사용 (dev Dockerfile은 PyTorch OOM)
- **Docker USER**: `appuser`로 실행됨 (커밋 `d14db66`부터) — 권한 문제 시 `chown` 필요
- **환경변수**: `INTERNAL_API_SECRET`, `ENCRYPTION_KEY` → OCI `.env.oracle` 설정 완료
- **Vercel 환경변수**: `INTERNAL_API_SECRET` → production/preview 설정 완료
- **Worker 테스트**: `arq` 미설치로 test_worker.py 실패 (기존 이슈)

---

## 5. 마지막 상태

- 브랜치: `main`
- 마지막 커밋: `15e4880` [docs] DESKTOP_MILESTONES.md — M5 완료 기록
- GitHub Push: 완료
- Desktop: M1~M5 전체 완료 (`cargo check` + `tsc --noEmit` + `vite build` 통과)
- OCI VM: API healthy, Worker started (커밋 `0385580` — 미배포 6건 이상)
- Vercel: 자동 배포 완료
- GitHub Issues: #64, #67만 열림

---

## 6. 주요 파일 변경 내역

### 커밋 `d14db66` — P0 보안/결제

| 파일 | 변경 |
|------|------|
| `.env.example` | DISABLE_AUTH=false |
| `Dockerfile.prod` | USER appuser 추가 |
| `auth.py` | __dev__→None, JWT 최소 32자 |
| `main.py` | 프로덕션 OpenAPI 비활성화 |
| `metrics.py` | /metrics 인증 |
| `admin.py` | IDOR 수정 (get_auth_context) |
| `billing.py` | Toss/Stripe 멱등성, 금액 검증, 안전 폴백 |
| `repositories.py` | SELECT FOR UPDATE |
| `config.py` | workspace_id 정규식 검증 |
| `encryption.py` | 평문 fallback → RuntimeError |

### 커밋 `38d2068` — P1 백엔드/프론트엔드/DB

| 파일 | 변경 |
|------|------|
| `agent.py` | response.content list 처리, previous_draft, cache_control 비-Anthropic 폴백 |
| `auditor.py` | 파싱 실패 FAIL 처리, content list |
| `editor.py`, `strategist.py` | content list 처리 |
| `batch_openai.py` | AsyncOpenAI, time.monotonic, tempfile 안전 |
| `pipeline.py` | cancel 명시적 commit |
| `competitors.py` | RuntimeError 정보 제거 |
| `models.py` | String(500), UniqueConstraint, oauth_tokens |
| `engine.py` | 비공개 API → get_engine() |
| `use-pipeline.ts` | SSE API키, esRef, retry 캐시 |
| `use-api-keys.ts` | ApiError.status retry |
| `pipelines/[id]/page.tsx` | video_url XSS |
| `settings/page.tsx` | console.error 제거, aria-label |
| `app-sidebar.tsx` | signOut API키 삭제 |
| `auth.ts` | signIn 경고 로그 |

### 커밋 `3336be3` + `d4b6063` — Baseline UI

| 파일 | 변경 |
|------|------|
| `page.tsx` (dashboard) | gradient/glow 제거, tabular-nums, text-balance |
| `app-sidebar.tsx` | glow shadow 제거, size-* |
| `pipelines/page.tsx` | glow 제거, text-balance |
| `pipelines/[id]/page.tsx` | text-balance, aria-label |
| `pipelines/new/page.tsx` | text-balance, aria-label, size-* |
| `channels/page.tsx` | text-balance, text-pretty |
| `competitors/page.tsx` | confirm→AlertDialog, aria-label, size-* |
| `settings/page.tsx` | text-balance, text-pretty, aria-label, size-* |
| `onboarding/page.tsx` | 100vh→100dvh |
| `login/page.tsx` | min-h-dvh, size-* |
| `guide/page.tsx` | text-balance, text-pretty |
