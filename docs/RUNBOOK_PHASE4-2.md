# Runbook: Phase 4-2 — 결제 UI, 채널 쿼터 검증, 배포 설정

> 작성일: 2026-03-18
> PR: [#38](https://github.com/VetEngineer/Youtube-AI-Agent-Agency/pull/38)
> 브랜치: `feat/payment-ui-deploy-config`

---

## 1. 개요

Phase 4-2에서 구현된 기능의 운영 가이드.

| 기능 | 파일 | 설명 |
|------|------|------|
| 채널 쿼터 검증 | `packages/api/yaa_app/api/routes/channels.py` | 플랜별 채널 생성 제한 |
| Docker 자동 마이그레이션 | `entrypoint.sh`, `Dockerfile` | 컨테이너 시작 시 DB 마이그레이션 자동 실행 |
| Toss 결제 UI | `packages/frontend/src/hooks/use-billing.ts` | 한국어 사용자 결제창 |
| Vercel 배포 | `packages/frontend/vercel.json` | 서울(ICN1) 리전 배포 |
| Railway 배포 | `railway.toml` | 백엔드 컨테이너 배포 |

---

## 2. 채널 쿼터 검증

### 동작 방식
- `POST /api/v1/channels` 호출 시 현재 채널 수와 `workspace.channel_quota` 비교
- `channel_quota == -1`: 무제한 (Enterprise 플랜)
- `channel_quota >= 현재 채널 수`: HTTP 409 반환

### 플랜별 쿼터
| 플랜 | channel_quota |
|------|--------------|
| Free | 1 |
| Pro | 5 |
| Enterprise | -1 (무제한) |

### 테스트
```bash
# Free 플랜 워크스페이스에서 채널 2개 생성 시도
curl -X POST http://localhost:8000/api/v1/channels \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-channel"}'
# 두 번째 요청 → HTTP 409 {"detail": "채널 한도 초과. 플랜을 업그레이드하세요."}
```

### auth 비활성 환경
`DISABLE_AUTH=true` 설정 시 쿼터 검사를 건너뜀 (개발/테스트 환경).

---

## 3. Docker 자동 마이그레이션 (entrypoint.sh)

### 파일 위치
`/entrypoint.sh` (프로젝트 루트)

### 실행 순서
1. `alembic upgrade head` — DB 스키마를 최신으로 마이그레이션
2. `uvicorn yaa_app.api.main:app` — FastAPI 서버 시작

### 주의사항
- `DATABASE_URL` 환경변수가 설정되어 있어야 함
- 마이그레이션 실패 시 `set -e`에 의해 컨테이너가 종료됨 → Railway가 on_failure 정책으로 재시작

### 수동 마이그레이션 (긴급 시)
```bash
docker exec -it <container_id> bash
cd /app/packages/api && uv run alembic upgrade head
```

### 마이그레이션 롤백
```bash
docker exec -it <container_id> bash
cd /app/packages/api && uv run alembic downgrade -1
```

---

## 4. Toss Payments 결제 UI

### 결제 흐름
```
사용자 클릭 "업그레이드"
  → navigator.language.startsWith('ko') 체크
  ├── 한국어: POST /billing/toss/checkout → client_key, amount, order_id 수령
  │           → loadTossPayments(client_key).requestPayment()
  │           → 성공: /billing/success, 실패: /billing/cancel
  └── 그 외: useCheckout() (Stripe Checkout)
```

### 환경변수
```
NEXT_PUBLIC_TOSS_CLIENT_KEY=test_ck_...   # 테스트: test_ck_ 접두사
                                           # 프로덕션: live_ck_ 접두사
```

### Toss 테스트 결제 (개발)
- 테스트 카드: `4330000000000000`, 유효기간 아무거나, 비밀번호 00
- 테스트 환경에서는 실제 결제 발생 안 함

### 결제 후 플랜 동기화
- Toss webhook → `POST /billing/toss/webhook` → DB 플랜 업데이트
- `TOSS_WEBHOOK_SECRET` 환경변수 필수 (서명 검증)

---

## 5. Vercel 배포 (프론트엔드)

### 설정 파일
`packages/frontend/vercel.json`

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install",
  "regions": ["icn1"]
}
```

### 최초 배포
```bash
cd packages/frontend
npx vercel --prod
```

### 필수 환경변수 (Vercel 대시보드에서 설정)
```
NEXT_PUBLIC_API_BASE_URL=https://your-backend.railway.app/api/v1
NEXTAUTH_URL=https://your-app.vercel.app
NEXTAUTH_SECRET=<랜덤 32자 이상 문자열>
NEXT_PUBLIC_TOSS_CLIENT_KEY=live_ck_...
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

### 배포 확인
```bash
curl https://your-app.vercel.app/api/health
# → 200 OK
```

---

## 6. Railway 배포 (백엔드)

### 설정 파일
`railway.toml` (프로젝트 루트)

### 배포 순서
1. Railway 대시보드에서 New Project → Deploy from GitHub
2. `VetEngineer/Youtube-AI-Agent-Agency` 연결
3. `.env.railway.example`을 참고해 환경변수 설정
4. PostgreSQL + Redis 플러그인 추가 → `DATABASE_URL`, `REDIS_URL` 자동 주입

### 헬스체크
- 경로: `GET /api/v1/health`
- 타임아웃: 60초
- 실패 시 컨테이너 자동 재시작

### 환경변수 템플릿
`.env.railway.example` 참조.

---

## 7. 트러블슈팅

| 증상 | 원인 | 조치 |
|------|------|------|
| 채널 생성 시 409 | 쿼터 초과 | 플랜 업그레이드 또는 기존 채널 삭제 |
| Docker 시작 실패 | 마이그레이션 실패 | `DATABASE_URL` 확인, DB 접속 테스트 |
| Toss 결제창 미오픈 | `NEXT_PUBLIC_TOSS_CLIENT_KEY` 미설정 | Vercel 환경변수 확인 |
| Railway 헬스체크 실패 | 서버 시작 지연 | `healthcheckTimeout` 늘리기 (railway.toml) |
