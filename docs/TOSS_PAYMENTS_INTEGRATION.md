# Toss Payments 결제 연동 명세서

> **서비스명:** YouTube AI Agent Agency (YAA)
> **운영사:** 하캄솔루션
> **대표자:** 강은구
> **사업자등록번호:** 435-17-01222
> **통신판매업 신고번호:** 2020-대전유성-1677
> **문서 작성일:** 2026-03-28

---

## 1. 서비스 개요

| 항목 | 내용 |
|------|------|
| 서비스명 | YouTube AI Agent Agency |
| 서비스 URL | https://ytai.hakhamsolution.co.kr |
| API 서버 | https://api.ytai.hakhamsolution.co.kr |
| 결제 방식 | 국내 카드 일반결제 (월정액 구독) |
| 결제 통화 | KRW (원화) |
| 판매 상품 | SaaS 구독 플랜 (Pro / Enterprise) |

---

## 2. 상품 및 금액

| 플랜 | 금액 | 주문명 |
|------|------|--------|
| Pro | ₩29,000 / 월 | YAA Pro 구독 |
| Enterprise | ₩99,000 / 월 | YAA Enterprise 구독 |

---

## 3. 결제 플로우

```
[사용자]
  │
  ├─ 1. 플랜 선택 (Settings 페이지)
  │
  ▼
[프론트엔드 → 백엔드]
  POST /api/v1/billing/toss/checkout
  Body: { "plan": "pro" }
  Response: {
    "client_key": "...",
    "customer_key": "{workspace_id}",
    "amount": 29000,
    "order_id": "yaa-pro-{ws_prefix}-{random}",
    "order_name": "YAA Pro 구독"
  }
  │
  ▼
[프론트엔드 → Toss SDK]
  loadTossPayments(client_key)
  payment.requestPayment({
    method: "CARD",
    amount: { currency: "KRW", value: 29000 },
    orderId: "yaa-pro-...",
    orderName: "YAA Pro 구독",
    successUrl: "https://ytai.hakhamsolution.co.kr/billing/success",
    failUrl: "https://ytai.hakhamsolution.co.kr/billing/cancel"
  })
  │
  ├─ 결제 성공 시 → /billing/success?paymentKey=...&orderId=...&amount=...
  │
  ▼
[프론트엔드 → 백엔드] 결제 승인
  POST /api/v1/billing/toss/confirm
  Body: {
    "payment_key": "...",
    "order_id": "yaa-pro-...",
    "amount": 29000
  }
  │
  ▼
[백엔드 → Toss API] 서버사이드 승인
  POST https://api.tosspayments.com/v1/payments/confirm
  Authorization: Basic {base64(secret_key:)}
  Body: { paymentKey, orderId, amount }
  │
  ▼
[백엔드] DB 업데이트
  - subscriptions 테이블: status=active, plan=pro
  - workspaces 테이블: plan=pro, pipeline_quota 업데이트
```

---

## 4. API 엔드포인트

### 4.1 결제 파라미터 생성

```
POST /api/v1/billing/toss/checkout
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request:**
```json
{
  "plan": "pro"
}
```

**Response:**
```json
{
  "client_key": "test_ck_...",
  "customer_key": "ws-uuid-...",
  "amount": 29000,
  "order_id": "yaa-pro-abcd1234-ef567890",
  "order_name": "YAA Pro 구독"
}
```

---

### 4.2 결제 승인 (서버사이드)

```
POST /api/v1/billing/toss/confirm
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request:**
```json
{
  "payment_key": "5zJ4xY7m0kODnyRpQWGrZwvEhCe",
  "order_id": "yaa-pro-abcd1234-ef567890",
  "amount": 29000
}
```

**Response:**
```json
{
  "payment_key": "5zJ4xY7m0kODnyRpQWGrZwvEhCe",
  "order_id": "yaa-pro-abcd1234-ef567890",
  "status": "DONE",
  "plan": "pro"
}
```

---

### 4.3 웹훅 수신

```
POST /api/v1/billing/toss/webhook
```

- 서명 검증: `X-Toss-Signature` 헤더 (HMAC-SHA256)
- 처리 이벤트: `PAYMENT_STATUS_CHANGED`

---

## 5. 주문 ID 규칙

```
형식: yaa-{plan}-{workspace_id_prefix_8자리}-{random_8자리}
예시: yaa-pro-abcd1234-ef567890
```

| 파트 | 설명 |
|------|------|
| `yaa` | 서비스 접두사 (고정) |
| `pro` / `enterprise` | 구독 플랜 |
| 8자리 hex | 워크스페이스 ID 앞 8자리 |
| 8자리 hex | 무작위 UUID 앞 8자리 |

---

## 6. 결제 금액 검증

백엔드에서 서버사이드로 금액 위변조를 방지합니다:

1. `/toss/checkout` 호출 시 서버가 플랜에 따른 금액을 결정 (하드코딩)
2. `/toss/confirm` 에서 전달받은 `amount`와 서버 내부 금액 비교
3. 불일치 시 `400 Bad Request` 반환 후 승인 거부

---

## 7. 멱등성 처리

동일 `payment_key`로 중복 승인 요청이 오면:
- DB에서 이미 처리된 결제인지 확인
- 이미 `active` 상태면 즉시 동일 응답 반환 (중복 처리 없음)

---

## 8. 환경변수

### 백엔드 (FastAPI / OCI VM)

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `TOSS_CLIENT_KEY` | Toss 클라이언트 키 | `test_ck_...` |
| `TOSS_SECRET_KEY` | Toss 시크릿 키 | `test_sk_...` |
| `TOSS_WEBHOOK_SECRET` | 웹훅 서명 시크릿 | (선택) |

> **적용 위치:** `/home/opc/YAA/.env.oracle` → Docker 컨테이너 재시작 필요

### 프론트엔드 (Vercel)

| 변수명 | 설명 |
|--------|------|
| `NEXT_PUBLIC_TOSS_CLIENT_KEY` | (현재 미사용 - 백엔드에서 전달) |

---

## 9. 테스트 계정 및 키 적용 방법

1. [Toss Payments 개발자 센터](https://developers.tosspayments.com) 가입
2. 내 계정 → API 키 → **테스트 클라이언트 키** / **테스트 시크릿 키** 복사
3. OCI VM 적용:
   ```bash
   ssh opc@134.185.113.58
   vi /home/opc/YAA/.env.oracle
   # TOSS_CLIENT_KEY=test_ck_...
   # TOSS_SECRET_KEY=test_sk_...
   cd /home/opc/YAA && docker compose restart api
   ```
4. 테스트 카드번호: `4242424242424242` (유효기간 임의, CVC 임의)

---

## 10. 라이브 전환 체크리스트

- [ ] Toss Payments 사업자 심사 완료
- [ ] 라이브 클라이언트 키 / 시크릿 키 발급
- [ ] OCI `.env.oracle` 라이브 키로 교체
- [ ] 웹훅 URL 등록: `https://api.ytai.hakhamsolution.co.kr/api/v1/billing/toss/webhook`
- [ ] 웹훅 서명 시크릿(`TOSS_WEBHOOK_SECRET`) 설정
- [ ] 실결제 테스트 (1원 결제 후 환불)

---

## 11. 인프라 구성

```
[사용자 브라우저]
       │ HTTPS
       ▼
[Vercel] ytai.hakhamsolution.co.kr
  - Next.js 15 / React 19
  - Toss Payments JS SDK (@tosspayments/tosspayments-sdk)
       │ HTTPS API 호출
       ▼
[OCI VM - Caddy 리버스 프록시]
  api.ytai.hakhamsolution.co.kr → localhost:8001
       │
       ▼
[Docker: FastAPI + Arq Worker]
  - FastAPI (포트 8001)
  - Arq Worker (Redis 큐)
       │
       ├── Supabase PostgreSQL (DB)
       ├── Upstash Redis (큐)
       └── Toss Payments API (결제 승인)
```

---

## 12. 문의

| 항목 | 내용 |
|------|------|
| 담당자 | 강은구 |
| 카카오톡 채널 | http://pf.kakao.com/_GxmxcTG/chat |
| 사업장 | 대전광역시 유성구 은구비남로33번길 13-8, 3층 3043호 |
