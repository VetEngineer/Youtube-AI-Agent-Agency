# Release Notes — 2026-03-18 (Phase 4-2)

## 요약

결제 UI 완성, 채널 쿼터 검증, Docker 자동 마이그레이션, Vercel/Railway 배포 설정 추가.

---

## 신규 기능

### Toss Payments 결제 UI
- Settings > Plans 섹션에 **업그레이드 버튼** 추가
- 언어 감지 기반 결제 분기: 한국어 → Toss Payments, 그 외 → Stripe
- `useTossCheckout()` 훅 추가 (`use-billing.ts`)
- billing/success, billing/cancel 페이지 완성

### 채널 쿼터 검증
- `POST /api/v1/channels` 에서 `workspace.channel_quota` 초과 시 **HTTP 409** 반환
- 메시지: `"채널 한도 초과. 플랜을 업그레이드하세요."`
- `DISABLE_AUTH=true` 환경에서는 쿼터 검사 건너뜀

### Docker Alembic 자동 마이그레이션
- `entrypoint.sh` 신규 추가: 컨테이너 시작 시 `alembic upgrade head` 자동 실행
- `Dockerfile` CMD를 `entrypoint.sh`로 교체

---

## 배포 설정

| 파일 | 내용 |
|------|------|
| `packages/frontend/vercel.json` | Next.js, ICN1(서울) 리전 |
| `railway.toml` | Dockerfile 빌드, 헬스체크, on_failure 재시작 |
| `.env.railway.example` | Railway 환경변수 전체 템플릿 |
| `packages/frontend/.env.example` | Toss 클라이언트 키, NextAuth, OAuth 추가 |

---

## 변경 파일

- `entrypoint.sh` *(신규)*
- `railway.toml` *(신규)*
- `.env.railway.example` *(신규)*
- `packages/frontend/vercel.json` *(신규)*
- `Dockerfile`
- `packages/api/yaa_app/api/routes/channels.py`
- `packages/frontend/src/hooks/use-billing.ts`
- `packages/frontend/src/app/(app)/settings/page.tsx`
- `packages/frontend/src/app/(app)/billing/success/page.tsx`
- `packages/frontend/src/app/(app)/billing/cancel/page.tsx`
- `packages/frontend/.env.example`
- `packages/frontend/package.json`

---

## PR

- [#38 feat/payment-ui-deploy-config](https://github.com/VetEngineer/Youtube-AI-Agent-Agency/pull/38)

---

## 다음 단계 (Phase 4-3)

- E2E 테스트: Toss 결제 → 플랜 동기화 검증
- Railway 초기 배포 및 헬스체크 확인
- Vercel 프로덕션 배포
