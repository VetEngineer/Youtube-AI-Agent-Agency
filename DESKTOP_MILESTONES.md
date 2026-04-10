# YAA Desktop — Tauri v2 개발 마일스톤

## 아키텍처 요약
- **프론트엔드**: Vite + React 19 (Next.js 대체, shadcn/ui + Tailwind v4)
- **인증**: API Key + Tauri Plugin Store (OS keychain 암호화)
- **백엔드**: 하이브리드 (기본: Railway 원격 / 선택: Docker 로컬)
- **SSE**: fetch ReadableStream (EventSource 헤더 제한 해결)
- **배포**: macOS `.dmg` / Windows `.msi` / Linux `.AppImage`

---

## Milestone 1: Vite + Tauri 기초 설정
**목표**: `packages/desktop/` 패키지 골격 구축 및 Tauri v2 초기화

### 체크리스트
- [x] `packages/desktop/` Vite React TS 초기화
- [x] Tauri v2 의존성 설치 (`@tauri-apps/cli@^2`, `@tauri-apps/api@^2`)
- [x] `src-tauri/tauri.conf.json` 설정 (productName, identifier, window, CSP)
- [x] `src-tauri/capabilities/default.json` 권한 설정
- [x] `src-tauri/Cargo.toml` 의존성 (tauri v2 plugins)
- [x] `vite.config.ts` (포트 1420, @/ alias, tailwindcss 플러그인)
- [x] `tsconfig.json`, `tsconfig.app.json` 설정
- [x] 루트 `package.json` workspace 추가
- [x] `cargo check` 통과 (Rust 컴파일 검증)
- [x] `tsc -b --noEmit` 통과
- [x] `vite build` 통과

### 상태: ✅ 완료
### 완료일: 2026-04-07
### 리뷰 결과: 68 → 75 → 81 → 80 → 96 → 90 → **100/100** PASS (7차 리뷰)

### 리뷰 수정 전체 내역
- C-1: `script-src 'unsafe-inline'` 제거 (CSP 강화)
- C-2: `tauri-plugin-updater` / `tauri-plugin-shell` 제거 (M5에서 추가 예정)
- H: `tokio`, `serde`, `serde_json` M1 미사용 → Cargo.toml 제거
- H: window `"label": "main"` 명시적 선언 추가
- H: `http:allow-fetch` 4개 개별 → URL 스코프 allowlist 적용 (`ytai.hakhamsolution.co.kr`, `*.railway.app`)
- H: `withGlobalTauri: false` 변경 (XSS 공격면 감소)
- H: `.gitignore`에 `packages/desktop/src-tauri/target/` 등 추가
- M: Vite build target `safari13` → `safari16`, Linux도 `chrome105` 적용
- M: `tsconfig.node.json` `noUncheckedIndexedAccess: true` 추가, `lib` ES2022/ES2022 일치
- M: `.dark .glass-card` → Tailwind v4 `@variant dark` 중첩 문법으로 수정
- M: `App.tsx` `useEffect` dark mode 활성화 (prefers-color-scheme → `.dark` on `<html>`)
- M: `removeEventListener` 클로저 참조 버그 수정 (handler 변수 분리)
- L: `React.JSX.Element` → `import type { JSX } from 'react'` + `JSX.Element` (React 19 관용구)

### 주요 결정사항
- `CARGO_TARGET_DIR=/tmp/yaa-desktop-target`: Silvernine 드라이브 공간 부족으로 /tmp 사용
  - **다음 세션 시작 전**: `export CARGO_TARGET_DIR=/tmp/yaa-desktop-target` 필요
- `connect-src`에서 `http://localhost:8000` 제거: 로컬 Docker 모드는 M4에서 추가
- `@fontsource/pretendard@^5.2.4` (v2.x 미존재, v5.x 사용)
- `tauri-plugin-fs` M4에서 추가 예정

---

## Milestone 2: 인증 레이어 (API Key + Tauri Store)
**목표**: NextAuth 없이 API Key 기반 인증 구현

### 아키텍처 결정 (autoplan 리뷰 결과)
- **저장소**: `tauri-plugin-store` = 암호화 JSON 파일 (OS keychain ≠)
- **키 캐시**: AuthProvider 초기화 시 Store → 인메모리 변수 캐시. api.ts는 Store 직접 호출 안 함
- **라우팅**: `createMemoryRouter` (BrowserRouter 아님 — Tauri WebView에 URL bar 없음)
- **401 처리**: `fetchWithAuth`에서 401 수신 시 `clearApiKey()` + LoginPage 리다이렉트
- **첫 실행**: `has_onboarded` store key로 OnboardingPage vs LoginPage 분기
- **Store API**: `Store.load(path)` 사용 (v2 API, `new Store()` 아님)
- **검증 엔드포인트**: `GET /api/v1/users/me` (require_api_key, admin scope 불필요)
- **API Key 발급 경로**: 웹앱 Settings > API Keys (JWT 인증 시 admin 자동 부여)

### 체크리스트
- [x] `react-router-dom@^7` 설치 (`createMemoryRouter` 기반)
- [x] `src/lib/tauri-store.ts` — Store.load() v2 API, getApiKey/setApiKey/clearApiKey/getBackendUrl/hasOnboarded
- [x] `src/lib/api.ts` — 인메모리 키 캐시 + 401 인터셉터 + offline TypeError 처리
- [x] `src/lib/utils.ts` — frontend에서 직접 복사
- [x] `src/components/ui/` — button, card, input, label shadcn 컴포넌트 복사
- [x] `src/providers/AuthProvider.tsx` — Context + init(Store→cache) + setApiKey + clearApiKey
- [x] `src/pages/LoginPage.tsx` — API Key 입력 UI + backend URL 고급 옵션
- [x] `src/pages/OnboardingPage.tsx` — 3단계 마법사 (환영/키입력/출력디렉토리)
- [x] `src/pages/DashboardPage.tsx` — 인증 후 랜딩 스텁
- [x] `src/App.tsx` 업데이트 — createMemoryRouter + AuthProvider + loading 상태 가드

### 검증 시나리오 (M2 완료 기준)
1. 최초 실행: OnboardingPage 표시 (has_onboarded=false)
2. 유효 API Key 입력 → GET /users/me 200 → DashboardPage 이동
3. 잘못된 키 → 에러 메시지 (401 표시)
4. 앱 재시작 → 인증 상태 유지 (store 지속성)
5. 네트워크 오프라인 → "연결 불가" 에러 (TypeError 처리)
6. `npm run build` TypeScript strict 에러 0개

### 상태: ✅ 완료
### 완료일: 2026-04-10
### 리뷰 결과: 10회 codex:review 사이클 완료 — **96+/100 PASS**

### 주요 수정 내역 (10회 사이클)
- ValidateResult 판별 유니온 + FailReason 타입 (`'invalid'|'network'|'insecure'|'server'`)
- `isSecureUrl()` HTTPS 강제 + `yaa_` API 키 형식 검증
- `_authVersion` ref 카운터 — setApiKey/clearApiKey 경쟁 조건 방지
- URL 영속화: 인증 성공 후 store 쓰기 (순서 보장)
- StrictMode 안전 401 핸들러 (`clearApiKeyRef` 패턴)
- ErrorBoundary 클래스 컴포넌트 (App.tsx)
- CSP: `connect-src 'self' https:` — M2 커스텀 URL 지원을 위한 와일드카드
- `dark --destructive`: `0 85% 62%` — WCAG AA 4.6:1 대비 확보
- `min-h-screen` → `min-h-dvh` 전역 적용
- aria-busy / aria-expanded / role="alert" / aria-label 접근성 완비
- tauri-plugin-http 완전 제거 (네이티브 fetch 사용)
- 불필요한 CSS 유틸리티 제거 (text-gradient-brand, glass-card 등)

---

## Milestone 3: 컴포넌트 이식 (Next.js → React Router v7)
**목표**: 기존 shadcn/ui 컴포넌트 및 훅 이식, 라우팅 구성

### 체크리스트
- [ ] shadcn/ui 컴포넌트 전체 복사 (`components/ui/`)
- [ ] 훅 이식 (`use-pipeline`, `use-channels`, `use-competitors` 등)
- [ ] `use-pipeline.ts`: `useRouter` → `useNavigate` 1줄 수정
- [ ] `app-sidebar.tsx`: `useSession` → `useAuth` 교체
- [ ] SSE 스트리밍: `EventSource` → `fetch ReadableStream`
- [ ] 페이지 이식 (Dashboard, Pipelines, Channels, Competitors, Settings)
- [ ] React Router v7 라우팅 구성 (`src/App.tsx`)
- [ ] `globals.css` 이식

### 상태: ⏳ 대기
### 완료일: -
### 리뷰 결과: -

---

## Milestone 4: Tauri 네이티브 기능
**목표**: Rust 커맨드, Docker 제어, 시스템 트레이 구현

### 체크리스트
- [ ] `src-tauri/src/commands/backend.rs` (Docker 제어)
  - `check_docker_available()`
  - `start_local_backend()`
  - `stop_local_backend()`
  - `get_local_backend_status()`
- [ ] `src-tauri/src/commands/file_system.rs` (파일 다이얼로그)
- [ ] `src-tauri/src/tray/mod.rs` (시스템 트레이)
- [ ] `src-tauri/resources/docker-compose.desktop.yml`
- [ ] Settings 페이지 백엔드 연결 탭 추가
- [ ] `src/providers/BackendProvider.tsx` (원격/로컬 모드 전환)

### 상태: ⏳ 대기
### 완료일: -
### 리뷰 결과: -

---

## Milestone 5: 패키징 및 CI/CD
**목표**: GitHub Actions로 크로스플랫폼 빌드 자동화

### 체크리스트
- [ ] `tauri.conf.json` 번들 설정 (macOS/Windows/Linux)
- [ ] 앱 아이콘 생성 (`src-tauri/icons/`)
- [ ] `.github/workflows/desktop-release.yml`
- [ ] macOS 공증 설정 (Apple Developer)
- [ ] Tauri Updater 설정 (`latest.json` endpoint)
- [ ] 전체 빌드 테스트 (`npm run tauri build`)

### 상태: ⏳ 대기
### 완료일: -
### 리뷰 결과: -

---

## 진행 로그

| 날짜 | 마일스톤 | 이벤트 | 메모 |
|------|----------|--------|------|
| 2026-04-05 | M1 | 시작 | Vite + Tauri 기초 설정 |
| 2026-04-05 | M1 | 리뷰 1차 | 68/100 → CRITICAL/HIGH 수정
| 2026-04-07 | M1 | 리뷰 7차 | **100/100 PASS** |
| 2026-04-07 | M1 | 완료 | cargo check + tsc + vite build 전체 통과 |
| 2026-04-07 | M2 | 시작 | 인증 레이어 구현 시작 |
| 2026-04-10 | M2 | 리뷰 10차 | **96+/100 PASS** — 보안/접근성/아키텍처 전반 |
| 2026-04-10 | M2 | 완료 | tsc + vite build 통과, lint/CI 이상 없음 |
