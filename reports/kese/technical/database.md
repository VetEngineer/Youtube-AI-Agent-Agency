# DBMS 취약점 분석 평가 보고서

> KISA 주요정보통신기반시설 기술적 취약점 분석 평가 방법 상세가이드 (2026)
> 대상: PostgreSQL 16 (prod) / SQLite (dev) + SQLAlchemy 2.0 async
> 평가일: 2026-04-11

## 요약

| 구분 | 항목 수 |
|------|------:|
| 양호 | 5 |
| 부분이행 | 5 |
| 취약 | 5 |
| 해당없음 | 11 |
| **합계** | **26** |

---

## 1. 계정 관리 (9항목)

### D-01 | 기본 계정의 비밀번호, 정책 등을 변경하여 사용 | 중요도: 상

- **판단:** 취약
- **근거:** docker-compose.yml에서 PostgreSQL 기본 비밀번호가 `localdevpassword`로 하드코딩되어 있음. 환경변수 `DB_PASSWORD`가 설정되지 않으면 기본값이 사용됨. 프로덕션에서는 `.env.oracle` 파일을 사용하지만 기본값 폴백이 존재.
- **파일:** `docker-compose.yml:20,46` - `${DB_PASSWORD:-localdevpassword}`
- **조치:** 1) 기본 비밀번호 폴백 제거 - DB_PASSWORD 미설정 시 컨테이너 시작 실패하도록 변경. 2) 프로덕션 비밀번호는 20자 이상, 특수문자 포함으로 설정.

### D-02 | 불필요 계정 제거 또는 잠금설정 | 중요도: 상

- **판단:** 부분이행
- **근거:** PostgreSQL에서 `agency` 사용자 하나만 생성됨 (불필요 계정 없음). 그러나 postgres 수퍼유저 계정의 잠금/비밀번호 변경 설정이 Docker Compose에 명시되어 있지 않음.
- **파일:** `docker-compose.yml:75-77`
- **조치:** Docker PostgreSQL 초기화 스크립트에서 postgres 수퍼유저 비밀번호 설정 또는 `POSTGRES_HOST_AUTH_METHOD=scram-sha-256` 설정.

### D-03 | 비밀번호 사용기간 및 복잡도 설정 | 중요도: 상

- **판단:** 취약
- **근거:** PostgreSQL에 비밀번호 만료 정책이 설정되어 있지 않음. `VALID UNTIL` 절이나 `passwordcheck` 모듈이 설정되어 있지 않음.
- **파일:** `docker-compose.yml` (PostgreSQL 설정 없음)
- **조치:** PostgreSQL 초기화 스크립트에서 `ALTER ROLE agency VALID UNTIL '날짜'` 설정 또는 `shared_preload_libraries = 'passwordcheck'` 추가.

### D-04 | 관리자 권한을 필요한 계정/그룹에만 허용 | 중요도: 상

- **판단:** 부분이행
- **근거:** `agency` 사용자가 `youtube_agency` 데이터베이스에 대한 전체 권한을 갖고 있지만, 수퍼유저(SUPERUSER) 권한인지 확인할 수 없음. 최소 권한 원칙이 명시적으로 적용되지 않음.
- **파일:** `docker-compose.yml:75-77`
- **조치:** 초기화 SQL에서 `agency` 사용자에게 필요한 최소 권한만 부여 (CREATEDB, SUPERUSER 제거). `GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO agency;`

### D-05 | 비밀번호 재사용 제약 설정 | 중요도: 중

- **판단:** 해당없음
- **근거:** PostgreSQL 기본 설치에서는 비밀번호 이력 관리 기능이 없음. 컨테이너 기반 배포에서 비밀번호 변경은 환경변수로 관리.

### D-06 | DB 사용자 계정 개별 부여 | 중요도: 중

- **판단:** 부분이행
- **근거:** API 서버와 워커 모두 동일한 `agency` 계정을 사용함. 서비스별(API, Worker, Migration) 별도 DB 계정이 분리되지 않음.
- **파일:** `docker-compose.yml:20,46`
- **조치:** API 서버용 `agency_api` (SELECT, INSERT, UPDATE, DELETE), 워커용 `agency_worker` (SELECT, INSERT, UPDATE), 마이그레이션용 `agency_admin` (DDL 권한) 분리 권장.

### D-07 | root 권한으로 서비스 구동 제한 | 중요도: 중

- **판단:** 양호
- **근거:** PostgreSQL Docker 이미지(`postgres:16-alpine`)는 기본적으로 `postgres` 시스템 사용자로 실행됨 (root가 아님). Dockerfile.prod에서 FastAPI도 `appuser`로 실행.
- **파일:** `Dockerfile.prod:44-46`, `docker-compose.yml:69` (postgres:16-alpine)

### D-08 | 안전한 암호화 알고리즘 사용 | 중요도: 상

- **판단:** 양호
- **근거:** 1) API 키: SHA-256 해싱. 2) 패스워드: bcrypt 해싱. 3) 민감 데이터(워크스페이스 API 키): Fernet(AES-128-CBC) 암호화. 4) JWT: HS256 알고리즘. 5) PostgreSQL 기본 인증 방식은 scram-sha-256 (v16 기본).
- **파일:** `packages/api/yaa_app/api/auth.py:47` (SHA-256), `packages/api/yaa_app/api/routes/auth.py:80` (bcrypt), `packages/core/yaa_core/shared/encryption.py:38` (Fernet)

### D-09 | 로그인 실패 시 잠금정책 설정 | 중요도: 중

- **판단:** 취약
- **근거:** 1) PostgreSQL에 `failed_login_attempts`/잠금 정책이 설정되어 있지 않음. 2) 애플리케이션 레벨에서도 로그인 실패 횟수 카운트나 계정 잠금 메커니즘이 없음. Rate Limiting(slowapi)이 있으나 분당 60회로 계정별 제한이 아닌 IP별 제한.
- **파일:** `packages/api/yaa_app/api/routes/auth.py:209-258` (login 엔드포인트)
- **조치:** 1) 연속 5회 로그인 실패 시 계정 잠금(15분) 구현. 2) `UserModel`에 `failed_login_count`, `locked_until` 필드 추가. 3) Nginx 인증 엔드포인트에 별도 rate limit 존재(5r/s)하나 애플리케이션 레벨 보강 필요.

---

## 2. 접근 관리 (7항목)

### D-10 | 원격에서 DB 서버 접속 제한 | 중요도: 상

- **판단:** 취약
- **근거:** docker-compose.yml에서 PostgreSQL 포트(5432)를 호스트에 바인딩하고 있음 (`ports: - "5432:5432"`). 프로덕션 docker-compose.prod.yml에서는 DB 컨테이너가 없지만(외부 DB 사용), 개발 환경에서 외부 접근이 가능.
- **파일:** `docker-compose.yml:79` - `- "5432:5432"`
- **조치:** 1) 개발 환경에서도 `127.0.0.1:5432:5432`로 로컬 바인딩. 2) `pg_hba.conf`에서 접근 허용 IP를 Docker 네트워크 대역으로 제한.

### D-11 | 비인가 사용자의 시스템 테이블 접근 차단 | 중요도: 상

- **판단:** 부분이행
- **근거:** `agency` 사용자에 대해 `pg_catalog`, `information_schema` 접근 제한이 명시적으로 설정되지 않음. PostgreSQL 기본 설정에서 일반 사용자도 시스템 카탈로그 조회 가능.
- **조치:** `REVOKE SELECT ON ALL TABLES IN SCHEMA pg_catalog FROM agency;` 설정 또는 최소 권한 적용.

### D-12 | 안전한 리스너 비밀번호 설정 | 중요도: 상

- **판단:** 해당없음
- **근거:** Oracle DB의 리스너 항목. PostgreSQL에는 별도 리스너 비밀번호 개념이 없음.

### D-13 | 불필요한 ODBC/OLE-DB 데이터 소스 제거 | 중요도: 중

- **판단:** 해당없음
- **근거:** ODBC/OLE-DB를 사용하지 않음. SQLAlchemy async + asyncpg 드라이버 사용.

### D-14 | 주요 파일 접근 권한 설정 | 중요도: 중

- **판단:** 양호
- **근거:** Docker 컨테이너 내에서 PostgreSQL 데이터 파일은 `postgres` 사용자 소유로 제한됨. 볼륨은 Docker 관리형(`pgdata`).
- **파일:** `docker-compose.yml:72-73`

### D-15 | 리스너 로그/trace 파일 변경 제한 | 중요도: 하

- **판단:** 해당없음
- **근거:** Oracle DB 리스너 항목.

### D-16 | Windows 인증 모드 사용 | 중요도: 하

- **판단:** 해당없음
- **근거:** Linux 컨테이너 환경. Windows 인증 비해당.

---

## 3. 옵션 관리 (8항목)

### D-17 | Audit Table 관리자 접근 제한 | 중요도: 하

- **판단:** 양호
- **근거:** 감사 로그는 `audit_logs` 테이블에 저장되며, API를 통한 접근은 `require_admin_scope` 의존성으로 관리자만 조회 가능. 감사 로그 삭제 API는 존재하지 않음.
- **파일:** `packages/api/yaa_app/api/routes/admin.py:139-183`

### D-18 | Role이 Public으로 설정되지 않도록 조정 | 중요도: 상

- **판단:** 부분이행
- **근거:** PostgreSQL 초기화 시 `public` 스키마에 대한 PUBLIC 권한 제거가 명시적으로 설정되지 않음. PostgreSQL 16에서는 기본적으로 PUBLIC에 CREATE 권한이 부여됨.
- **조치:** `REVOKE CREATE ON SCHEMA public FROM PUBLIC;` 초기화 스크립트에 추가.

### D-19 | OS_ROLES 등 원격 인증 FALSE 설정 | 중요도: 상

- **판단:** 해당없음
- **근거:** Oracle DB 항목 (OS_ROLES, OS_AUTHENT_PREFIX).

### D-20 | 인가되지 않은 Object owner 제한 | 중요도: 하

- **판단:** 해당없음
- **근거:** Oracle DB 항목.

### D-21 | 인가되지 않은 GRANT OPTION 사용 제한 | 중요도: 중

- **판단:** 해당없음
- **근거:** 단일 DB 사용자 환경에서 GRANT OPTION 남용 위험이 낮음. 향후 계정 분리 시 검토 필요.

### D-22 | 자원 제한 기능 TRUE 설정 | 중요도: 하

- **판단:** 해당없음
- **근거:** Oracle DB의 RESOURCE_LIMIT 항목.

### D-23 | xp_cmdshell 사용 제한 | 중요도: 상

- **판단:** 해당없음
- **근거:** MSSQL 항목. PostgreSQL 미해당.

### D-24 | Registry Procedure 권한 제한 | 중요도: 상

- **판단:** 해당없음
- **근거:** MSSQL 항목. PostgreSQL 미해당.

---

## 4. 패치 관리 (2항목)

### D-25 | 주기적 보안 패치 및 벤더 권고사항 적용 | 중요도: 상

- **판단:** 취약
- **근거:** PostgreSQL Docker 이미지(`postgres:16-alpine`)의 자동 업데이트 메커니즘이 없음. `docker-compose.yml`에서 `:16-alpine` 태그를 사용하여 마이너 패치는 자동 반영되지만, 메이저 보안 패치 적용을 위한 정기적 이미지 갱신 프로세스가 없음.
- **조치:** 1) Dependabot 또는 Renovate로 Docker 이미지 자동 업데이트 PR 생성. 2) 정기적(월 1회) Docker 이미지 리빌드 스케줄.

### D-26 | 감사 기록 정책 적합 설정 | 중요도: 상

- **판단:** 양호
- **근거:** 1) 애플리케이션 레벨 감사 로그가 AuditLogMiddleware로 구현됨 (모든 API 요청 기록). 2) 감사 로그에 timestamp, method, path, status_code, api_key_id, workspace_id, ip_address, user_agent, duration_ms 기록. 3) 관리자만 감사 로그 조회 가능.
- **파일:** `packages/api/yaa_app/api/middleware.py:22-67`, `packages/core/yaa_core/database/models.py:228-245`
- **참고:** PostgreSQL 레벨의 `pgaudit` 확장은 설치되어 있지 않으나, 애플리케이션 레벨 감사 로그로 주요 활동이 커버됨.

---

## 상세 결과 요약표

| 코드 | 항목 | 중요도 | 판단 | 비고 |
|------|------|:------:|------|------|
| D-01 | 기본 계정 비밀번호 변경 | 상 | 취약 | 기본 비밀번호 하드코딩 |
| D-02 | 불필요 계정 제거/잠금 | 상 | 부분이행 | postgres 수퍼유저 미관리 |
| D-03 | 비밀번호 기간/복잡도 | 상 | 취약 | 만료 정책 없음 |
| D-04 | 관리자 권한 제한 | 상 | 부분이행 | 최소 권한 미적용 |
| D-05 | 비밀번호 재사용 제약 | 중 | 해당없음 | PostgreSQL 미지원 |
| D-06 | 개별 계정 부여 | 중 | 부분이행 | 서비스별 미분리 |
| D-07 | root 구동 제한 | 중 | 양호 | postgres 사용자 실행 |
| D-08 | 암호화 알고리즘 | 상 | 양호 | bcrypt, SHA-256, Fernet |
| D-09 | 로그인 실패 잠금 | 중 | 취약 | 잠금 정책 없음 |
| D-10 | 원격 접속 제한 | 상 | 취약 | 포트 외부 노출 |
| D-11 | 시스템 테이블 접근 차단 | 상 | 부분이행 | 명시적 제한 없음 |
| D-12 | 리스너 비밀번호 | 상 | 해당없음 | Oracle 항목 |
| D-13 | ODBC/OLE-DB 제거 | 중 | 해당없음 | 미사용 |
| D-14 | 파일 접근 권한 | 중 | 양호 | Docker 볼륨 관리 |
| D-15 | 리스너 로그 제한 | 하 | 해당없음 | Oracle 항목 |
| D-16 | Windows 인증 모드 | 하 | 해당없음 | Linux 환경 |
| D-17 | Audit Table 접근 제한 | 하 | 양호 | admin scope 보호 |
| D-18 | Public Role 제한 | 상 | 부분이행 | PUBLIC 권한 미제거 |
| D-19 | OS_ROLES 원격 인증 | 상 | 해당없음 | Oracle 항목 |
| D-20 | Object owner 제한 | 하 | 해당없음 | Oracle 항목 |
| D-21 | GRANT OPTION 제한 | 중 | 해당없음 | 단일 계정 환경 |
| D-22 | 자원 제한 기능 | 하 | 해당없음 | Oracle 항목 |
| D-23 | xp_cmdshell 제한 | 상 | 해당없음 | MSSQL 항목 |
| D-24 | Registry Procedure | 상 | 해당없음 | MSSQL 항목 |
| D-25 | 주기적 보안 패치 | 상 | 취약 | 자동 업데이트 없음 |
| D-26 | 감사 기록 정책 | 상 | 양호 | 애플리케이션 레벨 감사 로그 |
