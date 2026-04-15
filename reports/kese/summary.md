# KISA 보안 취약점 분석평가 종합 보고서

**프로젝트:** Youtube-AI-Agent-Agency
**평가일:** 2026-04-12
**평가 기준:** KISA 시큐어코딩 가이드, AI 보안 안내서, 주요정보통신기반시설(CII) 기술적 취약점 분석평가
**평가 도구:** kesekit (KESE)

---

## 1. 평가 범위

| 가이드라인 | 점검 항목 수 | 대상 |
|-----------|:----------:|------|
| 시큐어코딩 | 46 CWE | Python(FastAPI/SQLAlchemy) + JavaScript(Next.js) |
| AI 보안 | 54 | LangGraph 파이프라인 (Claude/GPT-4o) 6단계 생명주기 |
| CII 웹 서비스 | 26 | FastAPI REST API |
| CII DBMS | 26 | PostgreSQL 16 + SQLAlchemy |
| CII 웹 애플리케이션 | 21 | FastAPI + Next.js |
| **합계** | **173** | |

---

## 2. 종합 결과

| 판단 | 시큐어코딩 | AI 보안 | CII 웹서비스 | CII DBMS | CII 웹앱 | **합계** |
|------|:---------:|:------:|:----------:|:------:|:------:|:------:|
| 양호 | 24 | 18 | 12 | 5 | 11 | **70** |
| 부분이행 | 9 | 11 | 5 | 5 | 5 | **35** |
| 취약 | 4 | 11 | 2 | 5 | 3 | **25** |
| 해당없음 | 9 | 14 | 7 | 11 | 2 | **43** |

**적용 가능 항목 대비 양호율:** 70/130 = **53.8%**
**취약 항목:** 25건 (긴급 4건, 높음 12건, 보통 9건)

---

## 3. 긴급 취약점 (즉시 조치 필요)

| # | 출처 | ID | 취약점 | 파일 |
|---|------|-----|--------|------|
| 1 | AI 보안 | F-01 | **프롬프트 인젝션 방어 부재** — 사용자 입력(topic, brand_name)이 LLM 프롬프트에 직접 삽입 | `yaa_agents/*/agent.py` |
| 2 | AI 보안 | F-02 | **LLM 출력 미검증** — AI 생성 콘텐츠가 검증 없이 YouTube 업로드 | `yaa_agents/publisher/` |
| 3 | CII DB | D-01 | **기본 DB 비밀번호** — `localdevpassword` docker-compose에 하드코딩 | `docker-compose.yml` |
| 4 | CII 웹앱 | CF | **CSRF 미보호 + CORS 과다 허용** — `allow_methods=["*"]` + `allow_credentials=True` | `yaa_app/api/app.py` |

---

## 4. 높음 취약점 (일정 내 조치)

| # | 출처 | ID | 취약점 |
|---|------|-----|--------|
| 5 | AI 보안 | F-03 | 입력 길이 제한 없음 — 토큰 비용 폭증 공격 가능 |
| 6 | AI 보안 | F-05 | JWT 사용자에게 무조건 admin 권한 부여 |
| 7 | AI 보안 | F-11 | `disable_auth=True` 설정 시 모든 인증 비활성화 |
| 8 | 시큐어코딩 | CWE-352 | 쿠키 인증 엔드포인트 CSRF 미보호 |
| 9 | 시큐어코딩 | CWE-521 | 비밀번호 최소 8자만 검증, 복잡도 요구 없음 |
| 10 | 시큐어코딩 | CWE-759 | 레거시 SHA-256 비밀번호 해싱에 salt 미사용 |
| 11 | 시큐어코딩 | CWE-307 | 로그인 무차별 대입 공격 방어 부재 (이메일별 잠금 없음) |
| 12 | CII DB | D-09 | DB/앱 수준 계정 잠금 미구현 |
| 13 | CII DB | D-10 | PostgreSQL 5432 포트 호스트 네트워크 노출 |
| 14 | CII 웹서비스 | WEB-22 | 커스텀 에러 핸들러 없음, 내부 구조 노출 |
| 15 | CII 웹앱 | EP | 에러 응답에 내부 상세 정보 노출 |
| 16 | CII 웹앱 | PR | 비밀번호 찾기/재설정 기능 미구현 |

---

## 5. 강점 (양호 항목)

- **SQL 인젝션 완전 방어** — SQLAlchemy ORM + 파라미터화 쿼리 전수 사용
- **코드 인젝션 없음** — eval/exec 사용자 입력 없음
- **경로 탐색 방지** — 정규식 + resolve + startswith 검증
- **OS 명령어 인젝션 방지** — subprocess list args, shell=False
- **API 키 보안** — SHA-256 해싱 + Fernet 암호화
- **멀티테넌트 격리** — workspace_id 필터 전 엔드포인트 적용
- **LLM 비용 추적** — UsageCollector로 토큰/비용 모니터링
- **암호학적 안전한 난수** — secrets 모듈, uuid4 사용
- **결제 검증** — Stripe/Toss 웹훅 서명 검증

---

## 6. 조치 우선순위 로드맵

### Phase 1: 긴급 (1주 이내)
- [ ] CORS 설정 강화 (`allow_methods`, `allow_headers` 명시적 리스트로 변경)
- [ ] DB 기본 비밀번호 제거 (환경변수 필수화)
- [ ] 프롬프트 인젝션 방어 레이어 추가 (입력 새니타이징 + 시스템/유저 프롬프트 분리)
- [ ] LLM 출력 콘텐츠 검증 파이프라인 추가

### Phase 2: 높음 (2주 이내)
- [ ] 비밀번호 정책 강화 (복잡도 요구 + bcrypt/argon2 마이그레이션)
- [ ] 로그인 실패 횟수 제한 (이메일별 5회 실패 시 15분 잠금)
- [ ] JWT 역할 기반 권한 분리 (admin 무조건 부여 제거)
- [ ] 전역 예외 핸들러 추가 (프로덕션 에러 응답 새니타이징)
- [ ] PipelineRunRequest.topic max_length 제한 추가

### Phase 3: 보통 (1개월 이내)
- [ ] CI에 의존성 취약점 스캐닝 추가 (Dependabot + pip-audit)
- [ ] PostgreSQL 포트 바인딩을 127.0.0.1로 제한
- [ ] 비밀번호 재설정 기능 구현
- [ ] disable_auth 설정을 프로덕션에서 비활성화 강제

---

## 7. 상세 보고서

| 보고서 | 경로 |
|--------|------|
| 시큐어코딩 (46 CWE) | `reports/kese/technical/secure-coding.md` |
| AI 보안 (54항목) | `reports/kese/technical/ai-security.md` |
| CII 웹 서비스 (26항목) | `reports/kese/technical/web-service.md` |
| CII DBMS (26항목) | `reports/kese/technical/database.md` |
| CII 웹 애플리케이션 (21항목) | `reports/kese/technical/webapp.md` |
