# YAA (Youtube-AI-Agent-Agency) 핸드오프 문서

> 작성일: 2026-03-28
> 다음 세션에서 이어서 작업할 수 있도록 현재 상태를 정리한 문서

---

## 1. 서비스 URL

| 서비스 | URL | 상태 |
|--------|-----|------|
| 프론트엔드 | https://ytai.hakhamsolution.co.kr | ✅ 운영 중 |
| API 서버 | https://api.ytai.hakhamsolution.co.kr | ⚠️ VM 재시작 필요 |
| OCI VM | 134.185.113.58 | ⚠️ SSH 접속 불가 (재부팅 후에도 타임아웃) |

---

## 2. 인프라 구성

```
[Vercel] ytai.hakhamsolution.co.kr
  Next.js 16 + React 19

[OCI VM - 134.185.113.58]
  OS: Oracle Linux (opc 사용자)
  SSH 키: ~/Downloads/OCI ssh key_XEO/ssh-key-2026-03-11.key

  /home/opc/YAA/
    docker-compose.yml     ← API + Worker 컨테이너
    .env.oracle            ← 환경변수 파일

  /home/opc/XEO-Analyzer/infra/Caddyfile
    → api.ytai.hakhamsolution.co.kr → localhost:8001 리버스 프록시

[Supabase] PostgreSQL DB
[Upstash] Redis 큐 (Arq Worker)
```

---

## 3. 이번 세션에서 완료한 작업

### 3-1. CI/CD 수정 (완료 ✅)
- ruff lint 오류 전체 수정 (E501, UP042, F401, I001)
- ruff format 22개 파일 적용
- 테스트 패치 오류 수정 (module-level imports)
- CI #52 이후 Test + Lint + Docker Build 모두 통과

### 3-2. OCI VM 백엔드 배포 (완료 ✅, 현재 VM 불안정)
- Dockerfile.prod: `psycopg2-binary`, `packages/core[db-prod]` 추가
- entrypoint.sh: `uv run` → `python -m` 변경
- worker-entrypoint.sh: `WorkerSettings` → `WorkerConfig` 수정
- Supabase pgbouncer 호환: `statement_cache_size=0` 추가
- Alembic 마이그레이션 체인 수정 (중복 revision ID 해결)
- `alembic stamp` + `create_all()` 로 기존 DB 초기화
- Caddy: `api.ytai.hakhamsolution.co.kr` 도메인 설정

### 3-3. Vercel Analytics (완료 ✅)
- `@vercel/analytics`, `@vercel/speed-insights` layout.tsx에 추가

### 3-4. 사업자 정보 고시 (완료 ✅)
- 마케팅 푸터에 전자상거래법 필수 항목 추가
  - 상호: 하캄솔루션 | 대표자: 강은구
  - 사업자등록번호: 435-17-01222
  - 통신판매업 신고번호: 2020-대전유성-1677
  - 사업장: 대전광역시 유성구 은구비남로33번길 13-8, 3층 3043호
  - 문의: 카카오톡 채널 http://pf.kakao.com/_GxmxcTG/chat

### 3-5. Toss Payments 연동 명세서 (완료 ✅)
- `docs/TOSS_PAYMENTS_INTEGRATION.md` 생성 및 push
- PG사 전달용 결제 플로우, API 엔드포인트, 인프라 구성 문서화

### 3-6. 카카오 로그인 + 우회 로그인 (완료 ✅)
- `src/lib/auth.ts`: Google/GitHub → Kakao 커스텀 OAuth 프로바이더
- `src/app/login/page.tsx`: 카카오 버튼 + 베타 접근 코드 폼
- `src/proxy.ts`: 실제 라우트 보호 미들웨어 (비로그인 → /login 리디렉션)
- Vercel 환경변수: `BYPASS_LOGIN_SECRET=yaa-beta-2026` 설정 완료

---

## 4. 남은 작업 (다음 세션)

### 4-1. 🔴 OCI VM SSH 복구 (최우선)
**증상:** VM Running 상태이나 SSH 배너 교환에서 타임아웃
**의심 원인:** 재부팅 후에도 동일 증상 → OCI Security List 또는 VM 내부 iptables 문제

**확인 방법 (OCI Console에서):**
1. Networking → Virtual Cloud Networks → VCN 클릭
2. Security Lists → Default Security List
3. Ingress Rules에서 SSH(22) 규칙 확인
   - Source: 0.0.0.0/0, Protocol: TCP, Dest Port: 22 있어야 함
4. 없으면 Add Ingress Rule로 추가

**또는 VM Serial Console 사용:**
- OCI Console → Instance → Resources → Console connection → Launch Cloud Shell

### 4-2. 🟡 Toss Payments 테스트키 적용
**현황:** `.env.oracle`에 TOSS 키 미설정 (나머지 키는 모두 정상)
**발급처:** https://developers.tosspayments.com → 내 개발정보 → API 키

```bash
# SSH 복구 후 실행
ssh -i ~/Downloads/"OCI ssh key_XEO"/ssh-key-2026-03-11.key opc@134.185.113.58
vi /home/opc/YAA/.env.oracle
# 아래 줄 추가:
# TOSS_CLIENT_KEY=test_ck_...
# TOSS_SECRET_KEY=test_sk_...
cd /home/opc/YAA && docker compose restart api
```

### 4-3. 🟡 카카오 로그인 키 등록
**현황:** 코드 구현 완료, 환경변수 미설정
**발급처:** https://developers.kakao.com

**Vercel에 추가할 환경변수:**
```
KAKAO_CLIENT_ID=발급받은_REST_API_키
KAKAO_CLIENT_SECRET=발급받은_클라이언트_시크릿
```

**카카오 디벨로퍼스 설정:**
- 카카오 로그인 활성화
- Redirect URI 등록: `https://ytai.hakhamsolution.co.kr/api/auth/callback/kakao`
- 동의항목: 닉네임, 이메일(선택), 프로필 이미지(선택)

### 4-4. 🟢 Toss Payments 라이브키 전환 (나중에)
- 사업자 심사 완료 후
- 웹훅 URL 등록: `https://api.ytai.hakhamsolution.co.kr/api/v1/billing/toss/webhook`
- `TOSS_WEBHOOK_SECRET` 설정

---

## 5. 환경변수 현황

### OCI VM `/home/opc/YAA/.env.oracle`
| 변수 | 상태 |
|------|------|
| DATABASE_URL | ✅ 설정됨 (Supabase) |
| REDIS_URL | ✅ 설정됨 (Upstash) |
| ANTHROPIC_API_KEY | ✅ 설정됨 |
| OPENAI_API_KEY | ✅ 설정됨 |
| JWT_SECRET | ✅ 설정됨 |
| CORS_ORIGINS | ✅ ytai.hakhamsolution.co.kr |
| TOSS_CLIENT_KEY | ❌ 미설정 |
| TOSS_SECRET_KEY | ❌ 미설정 |
| TOSS_WEBHOOK_SECRET | ❌ 미설정 |

### Vercel 환경변수
| 변수 | 상태 |
|------|------|
| NEXT_PUBLIC_API_BASE_URL | ✅ api.ytai.hakhamsolution.co.kr |
| NEXTAUTH_SECRET | ✅ 설정됨 |
| BYPASS_LOGIN_SECRET | ✅ yaa-beta-2026 |
| KAKAO_CLIENT_ID | ❌ 미설정 |
| KAKAO_CLIENT_SECRET | ❌ 미설정 |

---

## 6. 주요 파일 경로

```
packages/frontend/src/
  lib/auth.ts                          ← NextAuth 설정 (Kakao + Bypass)
  proxy.ts                             ← Next.js 미들웨어 (라우트 보호)
  app/login/page.tsx                   ← 로그인 페이지
  app/(marketing)/layout.tsx           ← 푸터 사업자 정보
  app/(app)/billing/success/page.tsx   ← Toss 결제 성공 콜백
  hooks/use-billing.ts                 ← 결제 훅 (useTossCheckout)

packages/api/yaa_app/api/routes/
  billing.py                           ← Toss + Stripe 결제 API

docs/
  TOSS_PAYMENTS_INTEGRATION.md         ← PG사 전달용 명세서

Dockerfile.prod                        ← 프로덕션 Docker 이미지
entrypoint.sh                          ← API 서버 시작 스크립트
worker-entrypoint.sh                   ← Arq 워커 시작 스크립트
```

---

## 7. 결제 플로우 요약

```
설정 → useTossCheckout 버튼 클릭
  → POST /api/v1/billing/toss/checkout (플랜 선택)
  → Toss SDK requestPayment() 팝업
  → 결제 완료 → /billing/success
  → POST /api/v1/billing/toss/confirm (서버 승인)
  → DB 플랜 업데이트
```

**요금제:**
- Pro: ₩29,000/월
- Enterprise: ₩99,000/월
