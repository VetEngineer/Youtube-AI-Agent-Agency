# 웹 서비스 취약점 분석 평가 보고서

> KISA 주요정보통신기반시설 기술적 취약점 분석 평가 방법 상세가이드 (2026)
> 대상: FastAPI (Uvicorn) + Nginx 리버스 프록시
> 평가일: 2026-04-11

## 요약

| 구분 | 항목 수 |
|------|------:|
| 양호 | 12 |
| 부분이행 | 5 |
| 취약 | 2 |
| 해당없음 | 7 |
| **합계** | **26** |

---

## 1. 계정 관리 (3항목)

### WEB-01 | Default 관리자 계정명 변경 | 중요도: 상

- **판단:** 양호
- **근거:** FastAPI/Uvicorn은 웹 서버 자체에 기본 관리자 계정이 없음. 애플리케이션 레벨 인증은 커스텀 API Key + JWT를 사용하며 기본 계정이 하드코딩되어 있지 않음.
- **파일:** `packages/api/yaa_app/api/auth.py`

### WEB-02 | 취약한 비밀번호 사용 제한 | 중요도: 상

- **판단:** 부분이행
- **근거:** 회원가입 시 `min_length=8` 제약만 적용됨. 비밀번호 복잡도(대소문자, 특수문자, 숫자 혼합) 정책이 없으며, 사전 단어 제한이 없음.
- **파일:** `packages/api/yaa_app/api/routes/auth.py:35` - `password: str = Field(..., min_length=8)`
- **조치:** 비밀번호 복잡도 검증 추가 필요 (대문자 1+, 소문자 1+, 숫자 1+, 특수문자 1+ 포함). Pydantic validator 또는 별도 함수로 구현 권장.

### WEB-03 | 비밀번호 파일 권한 관리 | 중요도: 상

- **판단:** 양호
- **근거:** 비밀번호는 bcrypt로 해싱되어 DB에 저장됨. 파일 기반 비밀번호 관리를 사용하지 않음. `.env` 파일은 `.gitignore`에 포함되어 있으며, Docker 이미지에서는 env_file로 마운트.
- **파일:** `packages/api/yaa_app/api/routes/auth.py:77` - `bcrypt.hashpw()`

---

## 2. 서비스 관리 (15항목)

### WEB-04 | 웹 서비스 디렉터리 리스팅 방지 설정 | 중요도: 상

- **판단:** 양호
- **근거:** FastAPI는 기본적으로 디렉터리 리스팅 기능을 제공하지 않음. StaticFiles 마운트가 없고, Nginx 설정에도 autoindex가 비활성화되어 있음(기본값 off).
- **파일:** `infra/nginx.conf`, `packages/api/yaa_app/api/main.py`

### WEB-05 | 지정하지 않은 CGI/ISAPI 실행 제한 | 중요도: 상

- **판단:** 해당없음
- **근거:** FastAPI/Python 기반 애플리케이션으로 CGI/ISAPI를 사용하지 않음.

### WEB-06 | 웹 서비스 상위 디렉터리 접근 제한 설정 | 중요도: 상

- **판단:** 양호
- **근거:** ChannelRegistry에서 경로 순회(path traversal) 방지를 위한 검증이 구현되어 있음. workspace_id와 channel_id 모두 정규식 `^[a-zA-Z0-9_-]+$`로 검증하며, `resolve()` 후 기준 디렉토리 내 경로인지 확인함.
- **파일:** `packages/core/yaa_core/shared/config.py:122-123,166-176`
- **코드:** `if not str(path).startswith(str(self._channels_dir.resolve())): raise ValueError`

### WEB-07 | 웹 서비스 경로 내 불필요한 파일 제거 | 중요도: 중

- **판단:** 양호
- **근거:** Docker 이미지에 불필요한 파일(테스트, 문서, 샘플 등)이 포함되지 않음. Dockerfile.prod에서 필요한 패키지만 설치하며 `.dockerignore` 사용.
- **파일:** `Dockerfile.prod`

### WEB-08 | 웹 서비스 파일 업로드 및 다운로드 용량 제한 | 중요도: 하

- **판단:** 양호
- **근거:** Nginx에서 `client_max_body_size 50M` 설정으로 요청 크기를 제한함. FastAPI에서는 파일 업로드 엔드포인트(UploadFile)가 없어 별도 제한이 불필요함.
- **파일:** `infra/nginx.conf:116` - `client_max_body_size 50M;`

### WEB-09 | 웹 서비스 프로세스 권한 제한 | 중요도: 상

- **판단:** 양호
- **근거:** Dockerfile.prod에서 비-root 사용자(appuser, UID 1000)로 실행하도록 설정됨.
- **파일:** `Dockerfile.prod:44-46`
- **코드:** `RUN groupadd --gid 1000 appuser && useradd --uid 1000 --gid appuser ... USER appuser`

### WEB-10 | 불필요한 프록시 설정 제한 | 중요도: 상

- **판단:** 양호
- **근거:** Nginx 리버스 프록시가 특정 경로(`/api/`, `/health`, `/`)에 대해서만 프록시를 설정함. 포워드 프록시나 CONNECT 메서드를 허용하지 않음.
- **파일:** `infra/nginx.conf:63-106`

### WEB-11 | 웹 서비스 경로 설정 | 중요도: 중

- **판단:** 양호
- **근거:** 웹 서비스 루트가 `/app`(Docker 워킹 디렉토리)으로 시스템 디렉토리와 분리되어 있음.
- **파일:** `Dockerfile.prod:10` - `WORKDIR /app`

### WEB-12 | 웹 서비스 링크 사용 금지 | 중요도: 중

- **판단:** 해당없음
- **근거:** 심볼릭 링크를 통한 디렉토리 접근이 해당되는 Apache/Nginx 정적 파일 서빙을 사용하지 않음. FastAPI는 API 서버로만 동작.

### WEB-13 | 웹 서비스 설정 파일 노출 제한 | 중요도: 상

- **판단:** 부분이행
- **근거:** 프로덕션에서 OpenAPI 문서(`/docs`, `/redoc`, `/openapi.json`)를 `disable_auth=False`일 때 비활성화함. 그러나 `/metrics` 엔드포인트의 인증이 API 키 존재 여부만 체크하고 실제 검증(해시 비교)을 하지 않음.
- **파일:** `packages/api/yaa_app/api/main.py:73-75`, `packages/api/yaa_app/api/metrics.py:154-155`
- **코드:** `if not settings.disable_auth and not api_key: return 401` (API 키 값만 확인, 해시 검증 없음)
- **조치:** `/metrics` 엔드포인트에 require_api_key 의존성을 사용하거나, 별도의 메트릭 시크릿으로 보호 필요.

### WEB-14 | 웹 서비스 경로 내 파일의 접근 통제 | 중요도: 상

- **판단:** 양호
- **근거:** 소스 볼륨은 `:ro`(읽기 전용)로 마운트되며, 채널/출력 디렉토리만 쓰기 가능. Docker 컨테이너 내 파일 접근이 제한됨.
- **파일:** `docker-compose.yml:10-14`

### WEB-15 | 웹 서비스의 불필요한 스크립트 매핑 제거 | 중요도: 상

- **판단:** 해당없음
- **근거:** IIS 스크립트 매핑 항목. FastAPI/Python 환경에서 해당 없음.

### WEB-16 | 웹 서비스 헤더 정보 노출 제한 | 중요도: 중

- **판단:** 부분이행
- **근거:** Nginx 설정에 `server_tokens off`가 명시되어 있지 않음. Uvicorn의 기본 서버 헤더가 노출될 수 있음. FastAPI에서 `Server` 응답 헤더를 제거하거나 변경하는 설정이 없음.
- **파일:** `infra/nginx.conf` (server_tokens off 누락), `entrypoint.sh:8`
- **조치:** Nginx 설정에 `server_tokens off;` 추가. Uvicorn 실행 시 `--server-header` 옵션 비활성화 또는 FastAPI 미들웨어에서 `Server` 헤더 제거.

### WEB-17 | 웹 서비스 가상 디렉토리 삭제 | 중요도: 중

- **판단:** 해당없음
- **근거:** IIS 가상 디렉토리 항목. FastAPI/Python 환경에서 해당 없음.

### WEB-18 | 웹 서비스 WebDAV 비활성화 | 중요도: 상

- **판단:** 해당없음
- **근거:** FastAPI/Nginx 구성에서 WebDAV 모듈을 사용하지 않음.

---

## 3. 보안 설정 (5항목)

### WEB-19 | 웹 서비스 SSI 사용 제한 | 중요도: 중

- **판단:** 해당없음
- **근거:** Server-Side Includes를 사용하지 않음. FastAPI는 API 서버로만 동작.

### WEB-20 | SSL/TLS 활성화 | 중요도: 상

- **판단:** 양호
- **근거:** Nginx에서 TLSv1.2/TLSv1.3만 허용하며, 강력한 암호화 스위트를 사용. Let's Encrypt 인증서 적용. HTTP->HTTPS 리디렉션 설정됨. HSTS 헤더 포함.
- **파일:** `infra/nginx.conf:40-42,49`
- **코드:** `ssl_protocols TLSv1.2 TLSv1.3;`

### WEB-21 | HTTP 리디렉션 | 중요도: 중

- **판단:** 양호
- **근거:** Nginx에서 포트 80의 모든 요청을 HTTPS(443)로 301 리디렉션.
- **파일:** `infra/nginx.conf:28-30`
- **코드:** `return 301 https://$host$request_uri;`

### WEB-22 | 에러 페이지 관리 | 중요도: 하

- **판단:** 취약
- **근거:** FastAPI의 기본 에러 핸들러를 사용하며, 커스텀 에러 페이지가 설정되어 있지 않음. 422 Validation Error 응답에서 필드명과 상세 오류 정보가 노출됨. 500 에러 발생 시 스택 트레이스가 포함될 수 있음 (개발 모드).
- **파일:** `packages/api/yaa_app/api/main.py` (커스텀 exception_handler 미설정)
- **조치:** 글로벌 exception_handler를 추가하여 프로덕션에서 상세 에러 메시지 대신 일반적인 오류 메시지를 반환하도록 구현. 422 에러의 detail 필드에서 내부 모델 구조 노출 최소화.

### WEB-23 | LDAP 알고리즘 적절하게 구성 | 중요도: 중

- **판단:** 해당없음
- **근거:** LDAP 인증을 사용하지 않음.

---

## 4. 패치 및 로그 관리 (3항목)

### WEB-24 | 별도의 업로드 경로 사용 및 권한 설정 | 중요도: 중

- **판단:** 양호
- **근거:** 파일 업로드 API 엔드포인트가 없음. 미디어 생성은 내부 에이전트 파이프라인에서 처리하며 사용자 업로드를 받지 않음.

### WEB-25 | 주기적 보안 패치 및 벤더 권고사항 적용 | 중요도: 상

- **판단:** 취약
- **근거:** CI/CD 파이프라인에 의존성 취약점 스캔(dependabot, Snyk, Trivy 등)이 설정되어 있지 않음. Docker 베이스 이미지(`python:3.11-slim`)의 정기적 업데이트 자동화가 없음. GitHub Actions CI에서는 lint/test/docker build만 수행.
- **파일:** `.github/workflows/ci.yml`
- **조치:** 1) GitHub Dependabot 설정 추가 (Python, npm, Docker). 2) CI에 `trivy image scan` 또는 `pip-audit` 추가. 3) Docker 베이스 이미지 자동 업데이트 설정.

### WEB-26 | 로그 디렉터리 및 파일 권한 설정 | 중요도: 중

- **판단:** 부분이행
- **근거:** 구조화 로깅(`logging_config.py`)이 구현되어 있고 감사 로그가 DB에 저장됨. 그러나 Uvicorn/Nginx 로그 파일의 접근 권한 설정이 명시적으로 구성되어 있지 않음. Docker 컨테이너 환경에서는 stdout/stderr로 출력되므로 파일 권한 이슈는 제한적.
- **파일:** `packages/core/yaa_core/shared/logging_config.py`, `packages/api/yaa_app/api/middleware.py`
- **조치:** Nginx 로그 파일 권한을 640 이하로 설정. 프로덕션 환경에서 로그 로테이션 설정 확인.

---

## 상세 결과 요약표

| 코드 | 항목 | 중요도 | 판단 | 비고 |
|------|------|:------:|------|------|
| WEB-01 | Default 관리자 계정명 변경 | 상 | 양호 | 기본 계정 없음 |
| WEB-02 | 취약한 비밀번호 사용 제한 | 상 | 부분이행 | 복잡도 정책 미설정 |
| WEB-03 | 비밀번호 파일 권한 관리 | 상 | 양호 | bcrypt 해싱, DB 저장 |
| WEB-04 | 디렉터리 리스팅 방지 | 상 | 양호 | FastAPI 기본 비활성 |
| WEB-05 | CGI/ISAPI 실행 제한 | 상 | 해당없음 | Python 환경 |
| WEB-06 | 상위 디렉터리 접근 제한 | 상 | 양호 | 경로 순회 방지 구현 |
| WEB-07 | 불필요한 파일 제거 | 중 | 양호 | 프로덕션 Docker 최소화 |
| WEB-08 | 업로드/다운로드 용량 제한 | 하 | 양호 | Nginx 50M 제한 |
| WEB-09 | 프로세스 권한 제한 | 상 | 양호 | 비-root 사용자 실행 |
| WEB-10 | 불필요한 프록시 제한 | 상 | 양호 | 특정 경로만 프록시 |
| WEB-11 | 웹 서비스 경로 설정 | 중 | 양호 | /app 격리 |
| WEB-12 | 링크 사용 금지 | 중 | 해당없음 | 정적 파일 서빙 없음 |
| WEB-13 | 설정 파일 노출 제한 | 상 | 부분이행 | /metrics 인증 불완전 |
| WEB-14 | 파일 접근 통제 | 상 | 양호 | 읽기전용 볼륨 마운트 |
| WEB-15 | 불필요한 스크립트 매핑 | 상 | 해당없음 | IIS 항목 |
| WEB-16 | 헤더 정보 노출 제한 | 중 | 부분이행 | server_tokens off 누락 |
| WEB-17 | 가상 디렉토리 삭제 | 중 | 해당없음 | IIS 항목 |
| WEB-18 | WebDAV 비활성화 | 상 | 해당없음 | 미사용 |
| WEB-19 | SSI 사용 제한 | 중 | 해당없음 | 미사용 |
| WEB-20 | SSL/TLS 활성화 | 상 | 양호 | TLSv1.2+ 적용 |
| WEB-21 | HTTP 리디렉션 | 중 | 양호 | HTTP->HTTPS 301 |
| WEB-22 | 에러 페이지 관리 | 하 | 취약 | 커스텀 에러 핸들러 없음 |
| WEB-23 | LDAP 알고리즘 | 중 | 해당없음 | LDAP 미사용 |
| WEB-24 | 업로드 경로 권한 | 중 | 양호 | 파일 업로드 없음 |
| WEB-25 | 주기적 보안 패치 | 상 | 취약 | 취약점 스캔 미설정 |
| WEB-26 | 로그 권한 설정 | 중 | 부분이행 | 로그 파일 권한 미설정 |
