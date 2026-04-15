# YAA (Youtube-AI-Agent-Agency) 핸드오프 문서

> 작성일: 2026-04-12 (9차)
> 이전 핸드오프: 2026-04-11 (8차)

---

## 1. 서비스 URL

| 서비스 | URL | 상태 |
|--------|-----|------|
| 프론트엔드 (Vercel) | https://ytai.hakhamsolution.co.kr | 운영 중 (DNS → Vercel 76.76.21.21) |
| 프론트엔드 (Vercel 직접) | https://ytai-chi.vercel.app | 운영 중 |
| API 서버 | http://134.185.113.58:8001 | 운영 중 (OCI VM, **외부 접속 차단됨**) |
| OCI VM | 134.185.113.58:22 | SSH 가능 |

---

## 2. 이번 세션 완료 작업

### 2-1. Baseline UI 전체 리뷰 및 수정 (~70건)

29개 프론트엔드 파일 수정. 4개 마일스톤 병렬 실행.

| 마일스톤 | 파일 수 | 주요 변경 |
|----------|---------|-----------|
| M1 globals.css | 1 | glass-card→solid bg, glow/gradient/button:active 삭제, prefers-reduced-motion 전역 쿼리, 테마 토큰 |
| M2 UI 프리미티브 | 11 | skeleton/quota-badge motion-reduce, sheet 200ms+ease-out, dialog/alert safe-area, progress transition 범위 축소, tracking 제거, size-* 적용, useSyncExternalStore |
| M3 마케팅 페이지 | 5 | min-h-dvh, backdrop-blur 제거, text-balance/text-pretty, glow/gradient 참조 제거, cn 유틸리티, tabular-nums |
| M4 앱 페이지 | 12 | cn 유틸리티 8곳, AlertDialog 파이프라인 취소, 스켈레톤 로딩, animate-ping→static dot, tabular-nums, 빈 상태 CTA, size-*, text-balance |

**수정하지 않은 항목:**
- `sidebar.tsx` 레이아웃 애니메이션 — collapse UX 파손 위험, 예외 문서화만
- `pipelines/new` checkbox — shadcn Checkbox 미설치, TODO 코멘트
- `login/page.tsx` transition-colors — hover 피드백 표준 패턴

### 2-2. KISA 보안 취약점 분석평가 (173항목)

3개 가이드라인 병렬 점검. 보고서: `reports/kese/`

| 가이드라인 | 항목 | 양호 | 부분이행 | 취약 | 해당없음 |
|-----------|:----:|:----:|:-------:|:----:|:-------:|
| 시큐어코딩 (46 CWE) | 46 | 24 | 9 | 4 | 9 |
| AI 보안 (54항목) | 54 | 18 | 11 | 11 | 14 |
| CII 웹서비스+DB+웹앱 | 73 | 28 | 15 | 10 | 20 |
| **합계** | **173** | **70** | **35** | **25** | **43** |

### 2-3. 보안 취약점 수정 (긴급 4건 + 높음 9건)

4개 그룹 병렬 수정. 린트 + 빌드 모두 통과.

**긴급 (Phase 1):**

| # | 취약점 | 수정 파일 |
|---|--------|----------|
| 1 | CORS `["*"]` | `main.py` — 명시적 메서드/헤더 허용 리스트 |
| 2 | DB 기본 비밀번호 | `docker-compose.yml` — `:-localdevpassword` 폴백 제거 |
| 3 | 프롬프트 인젝션 | `sanitize.py`(신규) + 5개 agent에 sanitize_llm_input() |
| 4 | LLM 입력 길이 | `schemas.py` — topic max 500자, brand_name max 200자 |

**높음 (Phase 2):**

| # | 취약점 | 수정 파일 |
|---|--------|----------|
| 5 | JWT 무조건 admin | `auth.py` — workspace 소유권 검증 |
| 6 | 비밀번호 복잡도 | `routes/auth.py` — 대소문자+숫자+특수문자 필수 |
| 7 | 무차별대입 공격 | `routes/auth.py` — 이메일별 5회 실패 시 15분 잠금 |
| 8 | SHA-256 레거시 | `routes/auth.py` — 로그인 시 bcrypt 자동 마이그레이션 |
| 9 | 에러 정보 노출 | `main.py` — 전역 예외 핸들러 |
| 10 | DB 포트 노출 | `docker-compose.yml` — PG/Redis 127.0.0.1 바인딩 |
| 11 | disable_auth 위험 | `config.py` — 프로덕션 DB 경고 로그 |
| 12 | LLM 출력 검증 | `sanitize.py` — validate_llm_output() |
| 13 | 입력 새니타이징 | 5개 agent에 11개 인젝션 패턴 필터 |

### 2-4. gstack 업그레이드 + 라우팅

- gstack v0.16.2.0 → v0.16.3.0 업그레이드
- CLAUDE.md에 skill routing 규칙 추가 (커밋 `7bc0218`)

---

## 3. 커밋 전 상태 (미커밋)

**43개 파일 변경됨** (454 insertions / 407 deletions). 아직 커밋되지 않은 상태.

주요 변경 카테고리:
- `packages/frontend/src/` — Baseline UI 수정 29파일
- `packages/api/yaa_app/api/` — 보안 수정 (main.py, auth.py, routes/auth.py, schemas.py)
- `packages/agents/yaa_agents/` — 프롬프트 인젝션 방어 5파일
- `packages/core/yaa_core/shared/` — sanitize.py(신규), config.py
- `docker-compose.yml` — DB 비밀번호/포트 보안
- `reports/kese/` — 보안 평가 보고서 5개 (untracked)

---

## 4. 다음에 해야 할 작업

### 즉시 (커밋 필요)
1. [ ] 이번 세션 변경사항 커밋 및 푸시
2. [ ] `.env.example` 업데이트 — `DB_PASSWORD` 필수 설정 안내 추가
3. [ ] OCI 서버에 재배포 (docker-compose.yml 변경 반영, DB_PASSWORD 환경변수 설정)

### Phase 3 보안 (보통, 1개월 이내)
4. [ ] CI에 의존성 취약점 스캐닝 추가 (Dependabot + pip-audit)
5. [ ] 비밀번호 재설정 기능 구현
6. [ ] `disable_auth` 프로덕션 비활성화 강제 (현재는 경고만)
7. [ ] shadcn Checkbox 컴포넌트 설치 + pipelines/new 적용

### 기존 블로커 (이전 세션)
8. [ ] OCI 포트 8001 외부 개방 — Vercel→OCI API 프록시 동작 필수

---

## 5. 주의사항

### DB_PASSWORD 필수화
`docker-compose.yml`에서 기본 비밀번호 폴백을 제거함. OCI 서버에 재배포 시 반드시 `.env`에 `DB_PASSWORD=<강력한비밀번호>` 설정 필요. 없으면 DB 컨테이너 시작 실패.

### Docker 포트 변경
PostgreSQL/Redis가 `127.0.0.1`에만 바인딩됨. 외부에서 직접 DB 접속 불가 (의도된 보안 조치).

### 비밀번호 정책 변경
회원가입 시 대문자+소문자+숫자+특수문자 필수. 기존 사용자는 영향 없음 (로그인 시 자동 bcrypt 마이그레이션).

### 로그인 잠금
이메일당 5회 실패 시 15분 잠금 (인메모리). 서버 재시작 시 초기화됨.

### globals.css 클래스 삭제
`glow-red`, `glow-blue`, `text-gradient-brand` 삭제됨. 다른 곳에서 참조하면 스타일 누락.

### sidebar 애니메이션 예외
`sidebar.tsx`의 layout property 애니메이션(width/height/padding)은 의도적으로 유지. 코멘트로 문서화됨.

### OCI VM 메모리 (951MB)
- **서버에서 Next.js 빌드 절대 금지** — OOM 발생
- 프론트엔드는 GitHub Actions 또는 로컬 빌드만

### 포트 충돌 (OCI)
- 3000: flowscript-SaaS
- 3001: yaa-frontend Docker
- 8001: yaa-api Docker

---

## 6. 신규 파일

| 파일 | 용도 |
|------|------|
| `packages/core/yaa_core/shared/sanitize.py` | LLM 입력 새니타이징 + 출력 검증 유틸리티 |
| `reports/kese/summary.md` | KISA 보안 평가 종합 보고서 |
| `reports/kese/technical/secure-coding.md` | 시큐어코딩 46 CWE 상세 |
| `reports/kese/technical/ai-security.md` | AI 보안 54항목 상세 |
| `reports/kese/technical/web-service.md` | CII 웹서비스 26항목 |
| `reports/kese/technical/database.md` | CII DBMS 26항목 |
| `reports/kese/technical/webapp.md` | CII 웹앱 21항목 |

---

## 7. 아키텍처 결정 사항

### Vercel 프론트엔드 + OCI API (기존 유지)

```
브라우저 → Vercel (76.76.21.21)
  ├── /login, /pipelines, ... → Next.js SSR (Vercel)
  ├── /api/auth/* → NextAuth (Vercel)
  └── /api/v1/* → [rewrites] → http://134.185.113.58:8001 (OCI FastAPI)
```

### 프롬프트 인젝션 방어 구조

```
사용자 입력 → Pydantic max_length 검증 → sanitize_llm_input() → Agent 프롬프트
                                                                      ↓
                                                              LLM API 호출
                                                                      ↓
                                                         validate_llm_output()
```

---

## 8. 마지막 상태

- 브랜치: `main`
- 마지막 커밋: `7bc0218` — chore: add gstack skill routing rules to CLAUDE.md
- **미커밋 변경**: 43파일 (Baseline UI + 보안 수정)
- 린트: `ruff check` 통과
- 프론트엔드 빌드: `next build` 통과
- 테스트: 미실행 (커밋 전 `make test` 권장)
- GitHub Issues: #64, #67 열림
