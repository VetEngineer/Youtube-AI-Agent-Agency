# Web Application 취약점 분석 평가 보고서

> KISA 주요정보통신기반시설 기술적 취약점 분석 평가 방법 상세가이드 (2026)
> 대상: FastAPI REST API + Next.js 프론트엔드
> 평가일: 2026-04-11

## 요약

| 구분 | 항목 수 |
|------|------:|
| 양호 | 11 |
| 부분이행 | 5 |
| 취약 | 3 |
| 해당없음 | 2 |
| **합계** | **21** |

---

## 1. 입력값 검증 (8항목)

### CI | Command Injection | 중요도: 상

- **판단:** 양호
- **근거:** API 엔드포인트에서 시스템 명령 실행 함수를 직접 호출하지 않음. 미디어 에이전트에서 ffmpeg를 `create_subprocess_exec`로 호출하지만 사용자 입력이 직접 전달되지 않고, 내부 파이프라인 상태에서 생성된 파일 경로만 사용. 모든 사용자 입력은 Pydantic 스키마를 거침.
- **파일:** `packages/agents/yaa_agents/media_editor/video_editor.py:50` (subprocess_exec 사용, 사용자 입력과 분리)
- **참고:** `create_subprocess_exec`는 셸을 경유하지 않아 명령어 주입에 안전.

### SI | SQL Injection | 중요도: 상

- **판단:** 양호
- **근거:** 모든 데이터베이스 접근이 SQLAlchemy ORM과 Repository 패턴을 통해 이루어짐. raw SQL 쿼리나 문자열 포매팅을 사용한 쿼리가 없음. 모든 쿼리가 파라미터 바인딩 방식.
- **파일:** `packages/core/yaa_core/database/repositories.py` (전체)
- **코드:** `select(UserModel).where(UserModel.email == email)` (파라미터 바인딩)

### XS | Cross-Site Scripting (XSS) | 중요도: 상

- **판단:** 양호
- **근거:** 1) 백엔드: FastAPI가 JSON 응답만 반환하며 HTML 렌더링을 하지 않음. 2) 프론트엔드: React(Next.js)가 기본적으로 JSX에서 HTML 이스케이프를 수행. 안전하지 않은 직접 HTML 삽입이 사용되지 않음. 3) 사용자 입력은 Pydantic 스키마의 문자열 길이 제한으로 검증됨.
- **파일:** `packages/frontend/src/` (전체 - 안전하지 않은 HTML 삽입 미사용 확인)

### CF | Cross-Site Request Forgery (CSRF) | 중요도: 상

- **판단:** 취약
- **근거:** API가 `allow_credentials=True`와 함께 CORS를 설정하고 있으나, CSRF 토큰 검증이 구현되어 있지 않음. JWT Bearer 인증은 CSRF에 자연적으로 안전하지만, API 키 인증 방식(X-API-Key 헤더)은 프론트엔드에서 sessionStorage에 저장되어 자동 전송되지 않으므로 위험은 제한적. 그러나 NextAuth.js 세션 쿠키 기반 인증 흐름에서 CSRF 보호가 필요.
- **파일:** `packages/api/yaa_app/api/main.py:89-95`
- **코드:** `allow_methods=["*"], allow_headers=["*"], allow_credentials=True`
- **조치:** 1) CORS origins를 와일드카드가 아닌 정확한 도메인으로 제한 (현재 환경변수로 설정 가능하나 `allow_methods`, `allow_headers`는 `*`). 2) 상태 변경 요청(POST/PUT/DELETE)에 CSRF 토큰 검증 미들웨어 추가 고려. 3) `allow_methods`와 `allow_headers`를 필요한 값으로 제한.

### SF | Server-Side Request Forgery (SSRF) | 중요도: 상

- **판단:** 부분이행
- **근거:** 경쟁 채널 등록 시 사용자가 제공한 YouTube 채널 ID로 YouTube Data API를 호출함. 채널 ID 형식 검증(`min_length=1, max_length=100`)은 있으나 `UC` 접두사 등 YouTube 채널 ID 형식 강제 검증이 없음. Toss Payments API 호출은 고정 URL이라 안전. NextAuth에서 백엔드로의 내부 호출은 고정 URL.
- **파일:** `packages/api/yaa_app/api/routes/competitors.py:118` - `collector.fetch_channel_info(body.youtube_channel_id)`
- **조치:** YouTube 채널 ID에 대한 형식 검증 강화 (정규식 `^UC[a-zA-Z0-9_-]{22}$` 등).

### FU | File Upload 취약점 | 중요도: 상

- **판단:** 해당없음
- **근거:** 파일 업로드 API 엔드포인트가 존재하지 않음. UploadFile 사용 없음.

### FD | File Download 취약점 | 중요도: 상

- **판단:** 해당없음
- **근거:** 파일 다운로드 API 엔드포인트가 존재하지 않음. FileResponse 사용 없음.

### DI | 디렉터리 인덱싱 | 중요도: 중

- **판단:** 양호
- **근거:** FastAPI는 디렉터리 인덱싱 기능을 제공하지 않음. StaticFiles 마운트가 없음. Nginx에서도 autoindex가 기본 비활성.

---

## 2. 인증/세션 관리 (6항목)

### BF | Brute Force 공격 | 중요도: 상

- **판단:** 부분이행
- **근거:** IP 기반 Rate Limiting이 slowapi로 구현되어 있음 (기본 60/분). Nginx에서 인증 엔드포인트에 별도 rate limit(5r/s, burst=10) 적용. 그러나 계정별 로그인 실패 횟수 제한이나 계정 잠금 기능이 없어 분산 brute force에 취약.
- **파일:** `packages/api/yaa_app/api/middleware.py:70-104` (slowapi), `infra/nginx.conf:8,63-64` (auth zone 5r/s)
- **조치:** 1) 계정별 로그인 실패 횟수 카운터 추가. 2) 연속 5회 실패 시 15분 잠금. 3) CAPTCHA 연동 검토.

### IA | 불충분한 인증 (Insufficient Authentication) | 중요도: 상

- **판단:** 양호
- **근거:** 1) 모든 보호된 엔드포인트에 `require_api_key`, `get_auth_context`, `require_admin_scope` 의존성이 적용됨. 2) Health check(`/health`)만 인증 없이 접근 가능. 3) Stripe/Toss 웹훅은 서명 검증으로 대체. 4) JWT 토큰 유효기간 24시간. 5) disable_auth 옵션은 개발 환경에서만 사용.
- **파일:** `packages/api/yaa_app/api/auth.py:204-226`, 각 라우터 파일

### PR | 비밀번호 복구 취약점 | 중요도: 중

- **판단:** 취약
- **근거:** 비밀번호 찾기/재설정 기능이 구현되어 있지 않음. 이메일 인증 기반 비밀번호 복구 프로세스가 없어, 비밀번호 분실 시 대응 방법이 없음. (현재 OAuth 소셜 로그인이 주요 인증 수단이나, 이메일/패스워드 등록도 지원)
- **파일:** `packages/api/yaa_app/api/routes/auth.py` (비밀번호 복구 엔드포인트 없음)
- **조치:** 비밀번호 재설정 기능 구현 (이메일 인증 토큰 발급 -> 새 비밀번호 설정 플로우).

### IS | 불충분한 세션 관리 | 중요도: 상

- **판단:** 양호
- **근거:** 1) JWT 기반 무상태 인증으로 서버 사이드 세션을 사용하지 않음. 2) Access Token 유효기간 24시간. 3) Refresh Token 유효기간 7일. 4) 만료된 JWT/API 키는 즉시 거부. 5) NextAuth.js에서 JWT 세션 전략 사용.
- **파일:** `packages/api/yaa_app/api/routes/auth.py:23-24`, `packages/frontend/src/lib/auth.ts:153-155`

### CC | 세션 고정 (Credential/Session Prediction) | 중요도: 상

- **판단:** 양호
- **근거:** 1) JWT 토큰은 서버 사이드에서 `jwt.encode()`로 생성되어 예측 불가. 2) API 키는 `secrets.token_urlsafe(32)`로 생성 (256비트 랜덤). 3) UUID v4를 키 ID로 사용. 4) NextAuth.js가 세션 쿠키를 안전하게 관리.
- **파일:** `packages/api/yaa_app/api/auth.py:42-43` (secrets.token_urlsafe), `packages/api/yaa_app/api/routes/auth.py:100-112` (jwt.encode)

### SN | 세션 만료 미설정 | 중요도: 중

- **판단:** 부분이행
- **근거:** Access Token은 24시간, Refresh Token은 7일 만료가 설정되어 있으나, 토큰 블랙리스트(Token Revocation) 기능이 없음. 사용자 탈퇴나 권한 변경 시 기존 발급 토큰이 만료까지 유효함. API 키는 `expires_at` 필드로 만료 지원.
- **파일:** `packages/api/yaa_app/api/routes/auth.py:23-24`
- **조치:** 1) Redis 기반 JWT 블랙리스트 구현. 2) 로그아웃 시 refresh_token 무효화. 3) 비밀번호 변경 시 기존 토큰 전체 무효화.

---

## 3. 접근제어 (4항목)

### IN | 불충분한 인가 (Insufficient Authorization) | 중요도: 상

- **판단:** 양호
- **근거:** 1) workspace_id 기반 멀티테넌시 격리가 모든 CRUD에 적용됨. 2) 채널 관리, 경쟁 채널 등록/삭제는 admin 스코프 필요. 3) 파이프라인 조회/취소/재시도 시 workspace_id 일치 확인. 4) API 키 삭제 시 workspace 소유권 확인. 5) OAuth 콜백은 내부 API 시크릿으로 보호.
- **파일:** `packages/api/yaa_app/api/routes/pipeline.py:267-268`, `packages/api/yaa_app/api/routes/competitors.py:161-162`

### PV | 경로 조작 (Path Traversal) | 중요도: 상

- **판단:** 양호
- **근거:** 1) `ChannelRegistry._validate_channel_id()`에서 `^[a-zA-Z0-9_-]+$` 정규식으로 경로 조작 문자 차단. 2) `_validate_workspace_id()`도 동일 패턴. 3) `get_channel_path()`에서 `resolve()` 후 기준 디렉토리 범위 확인. 4) `CreateChannelRequest` 스키마에서도 동일 패턴 검증.
- **파일:** `packages/core/yaa_core/shared/config.py:166-176`, `packages/api/yaa_app/api/schemas.py:127-131`

### AE | 관리자 페이지 노출 | 중요도: 상

- **판단:** 양호
- **근거:** 1) 프로덕션에서 OpenAPI 문서(`/docs`, `/redoc`, `/openapi.json`) 비활성화. 2) 관리자 API(`/api/v1/admin/`)는 `require_admin_scope` 의존성으로 보호. 3) `/metrics` 엔드포인트는 API 키 필요. 4) NextAuth.js 미들웨어에서 인증되지 않은 사용자를 `/login`으로 리디렉션.
- **파일:** `packages/api/yaa_app/api/main.py:73-75`, `packages/frontend/src/proxy.ts:5-27`

### WM | HTTP Method 제한 미설정 | 중요도: 중

- **판단:** 부분이행
- **근거:** FastAPI 라우터에서 각 엔드포인트가 특정 HTTP 메서드만 허용하므로 허용되지 않은 메서드는 405 Method Not Allowed 반환. 그러나 CORS 설정에서 `allow_methods=["*"]`로 모든 메서드를 허용하고 있어, OPTIONS 외에도 TRACE, HEAD 등이 CORS 수준에서 통과됨.
- **파일:** `packages/api/yaa_app/api/main.py:93` - `allow_methods=["*"]`
- **조치:** `allow_methods`를 `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]`로 명시적 제한.

---

## 4. 정보노출 (3항목)

### EP | 에러 페이지를 통한 정보 노출 | 중요도: 중

- **판단:** 취약
- **근거:** 1) FastAPI 기본 422 Validation Error에서 필드 이름, 타입, 제약 조건 등 상세 정보가 응답에 포함됨. 2) 일부 HTTPException에서 내부 오류 메시지가 노출될 수 있음. 3) DB 연결 실패 등 인프라 오류 시 상세 메시지가 노출됨.
- **파일:** 모든 라우터 파일의 HTTPException(detail=...) 사용
- **코드 예시:** `raise HTTPException(status_code=502, detail=f"YouTube API 오류: {exc}")` (competitors.py:220)
- **조치:** 1) 글로벌 exception handler에서 프로덕션 모드 시 내부 오류 상세를 숨기기. 2) 422 에러 핸들러를 오버라이드하여 필드 구조 노출 최소화. 3) 외부 서비스 오류 메시지를 사용자에게 직접 전달하지 않기.

### IL | 불필요한 정보 노출 | 중요도: 중

- **판단:** 부분이행
- **근거:** 1) 프로덕션에서 OpenAPI 문서 비활성화 (양호). 2) Nginx `server_tokens off` 미설정으로 서버 버전 노출 가능. 3) FastAPI 응답 헤더에 프레임워크 정보가 포함될 수 있음. 4) 로그인 실패 시 "이메일 또는 패스워드가 올바르지 않습니다"로 통합 메시지를 사용하여 계정 존재 여부 노출을 방지 (양호). 5) 에러 응답에서 내부 오류 상세가 일부 노출됨.
- **파일:** `packages/api/yaa_app/api/routes/auth.py:225-226` (통합 에러 메시지 - 양호)
- **조치:** Nginx에 `server_tokens off;` 추가. FastAPI 미들웨어에서 `Server`, `X-Powered-By` 헤더 제거.

### AU | 부적절한 감사 로깅 | 중요도: 중

- **판단:** 양호
- **근거:** 1) AuditLogMiddleware가 모든 API 요청을 DB에 기록. 2) 기록 항목: timestamp, HTTP method, path, status_code, api_key_id, workspace_id, ip_address, user_agent, duration_ms. 3) Health check 등 일부 경로는 제외. 4) 관리자만 감사 로그 조회 가능 (require_admin_scope). 5) 워크스페이스별 격리 조회.
- **파일:** `packages/api/yaa_app/api/middleware.py:22-67`, `packages/api/yaa_app/api/routes/admin.py:139-183`
- **참고:** 로그인 실패 이벤트에 대한 별도 로깅이 없어 보안 모니터링 관점에서 보강 검토 필요.

---

## 상세 결과 요약표

| 코드 | 항목 | 중요도 | 판단 | 비고 |
|------|------|:------:|------|------|
| CI | Command Injection | 상 | 양호 | subprocess_exec 사용, 사용자 입력 분리 |
| SI | SQL Injection | 상 | 양호 | SQLAlchemy ORM 파라미터 바인딩 |
| XS | XSS | 상 | 양호 | React 자동 이스케이프, JSON 응답 |
| CF | CSRF | 상 | 취약 | CSRF 토큰 없음, CORS 와일드카드 |
| SF | SSRF | 상 | 부분이행 | YouTube ID 형식 검증 미흡 |
| FU | File Upload | 상 | 해당없음 | 업로드 기능 없음 |
| FD | File Download | 상 | 해당없음 | 다운로드 기능 없음 |
| DI | 디렉터리 인덱싱 | 중 | 양호 | FastAPI 기본 비활성 |
| BF | Brute Force | 상 | 부분이행 | IP rate limit만, 계정별 잠금 없음 |
| IA | 불충분한 인증 | 상 | 양호 | 모든 엔드포인트 인증 적용 |
| PR | 비밀번호 복구 | 중 | 취약 | 비밀번호 재설정 미구현 |
| IS | 불충분한 세션 관리 | 상 | 양호 | JWT + 만료 설정 |
| CC | 세션 고정 | 상 | 양호 | 예측 불가 토큰 생성 |
| SN | 세션 만료 미설정 | 중 | 부분이행 | 토큰 블랙리스트 없음 |
| IN | 불충분한 인가 | 상 | 양호 | workspace 격리 + scope 검증 |
| PV | 경로 조작 | 상 | 양호 | 정규식 + resolve 검증 |
| AE | 관리자 페이지 노출 | 상 | 양호 | 프로덕션 docs 비활성화 |
| WM | HTTP Method 제한 | 중 | 부분이행 | CORS allow_methods=* |
| EP | 에러 정보 노출 | 중 | 취약 | 상세 에러 메시지 노출 |
| IL | 불필요한 정보 노출 | 중 | 부분이행 | server_tokens off 누락 |
| AU | 부적절한 감사 로깅 | 중 | 양호 | AuditLogMiddleware 전체 기록 |
