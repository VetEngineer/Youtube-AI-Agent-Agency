# KISA AI 보안 안내서 기반 보안 평가 보고서

> 평가 기준: 과학기술정보통신부/한국인터넷진흥원 「인공지능(AI) 보안 안내서」
> 평가 대상: Youtube-AI-Agent-Agency (LangGraph 기반 6단계 AI 에이전트 파이프라인)
> 평가 일시: 2026-04-11
> AI 유형: Gen AI (생성형 AI) - LLM 기반

---

## 평가 요약

| 생명주기 단계 | 검증항목 수 | 양호 | 부분이행 | 취약 | 해당없음 |
|:---|:---:|:---:|:---:|:---:|:---:|
| 1. 계획 및 설계 | 6 | 2 | 2 | 0 | 2 |
| 2. 데이터 수집 및 준비 | 8 | 3 | 2 | 1 | 2 |
| 3. 모델 개발 | 21 | 4 | 3 | 7 | 7 |
| 4. 모델 배포 | 8 | 5 | 2 | 1 | 0 |
| 5. 모니터링 및 유지보수 | 8 | 4 | 2 | 1 | 1 |
| 6. 파기 | 3 | 0 | 0 | 1 | 2 |
| **합계** | **54** | **18** | **11** | **11** | **14** |

### 위험도 분포

| 위험도 | 건수 |
|:---|:---:|
| 긴급 | 2 |
| 높음 | 5 |
| 보통 | 4 |

---

## 1단계: 계획 및 설계

### 1.1 AI 보안 거버넌스 체계 구축

| 검증항목 | 판단 | 비고 |
|:---|:---:|:---|
| 1.1.1 보안 거버넌스 조직 구성 | 해당없음 | 조직 체계 평가 범위 외 (코드베이스 평가) |
| 1.1.2 보안 정책/절차/프로세스 구현 | 부분이행 | CLAUDE.md에 보안 가이드라인 존재하나, 별도 AI 보안 정책 문서 미수립 |
| 1.1.3 보안 전문인력 확보 | 해당없음 | 조직 인력 평가 범위 외 |

### 1.2 AI 모델 개발에 대한 위험관리 계획 수립

| 검증항목 | 판단 | 비고 |
|:---|:---:|:---|
| 1.2.1 위험요소 분석/도출 | 부분이행 | 멀티테넌트 격리, API 인증 등 주요 위협 대응 구현되어 있으나 공식 위협 분석 문서 미존재 |
| 1.2.2 위협 모델링 및 위험 평가 수행 | 양호 | workspace_id 기반 격리, 경로 순회 방지, scope 기반 권한 제어 등 설계 수준 보안 내재 |
| 1.2.3 위험요소 제거/완화 방안 마련 | 양호 | Rate limiting, 요금제 quota, API 키 해싱, JWT 인증 등 다층 방어 구현 |

---

## 2단계: 데이터 수집 및 준비

### 2.1 데이터 수집 및 전처리

| 검증항목 | 판단 | 비고 |
|:---|:---:|:---|
| 2.1.1 네트워크 프로토콜 보안 | 양호 | ElevenLabs/OpenAI/Anthropic API 호출 시 HTTPS 사용 (httpx, langchain SDK) |
| 2.1.2 데이터 보관 및 삭제 절차 | 취약 | 생성된 미디어 파일(음성, 영상), LLM 응답 텍스트에 대한 보존/삭제 정책 미수립 |
| 2.1.3 전처리 시 암호화 | 양호 | 워크스페이스 API 키는 Fernet 대칭 암호화로 DB 저장 (`encryption.py`) |

### 2.2 데이터 무결성 검증

| 검증항목 | 판단 | 비고 |
|:---|:---:|:---|
| 2.2.1 데이터 무결성 검증 | 부분이행 | API 키는 SHA-256 해싱으로 무결성 보장, 그러나 채널 YAML 설정 파일 무결성 검증 없음 |
| 2.2.2 데이터 접근 권한 제한 | 양호 | workspace_id 기반 격리, RBAC(scope 기반), `_validate_workspace_id()` 경로 순회 방지 |

### 2.3 데이터 공격에 대한 방어

| 검증항목 | 판단 | 비고 |
|:---|:---:|:---|
| 2.3.1 데이터 중독 공격 방어 | 해당없음 | 자체 모델 학습 없음 (외부 LLM API 사용) |
| 2.3.2 데이터 회피 공격 방어 | 해당없음 | 자체 모델 학습 없음 |
| 2.3.3 데이터 유출/변조 방지 | 부분이행 | DB 레벨 암호화(API 키)는 있으나, LLM에 전달되는 brand_guide/script 데이터에 대한 접근 로깅 부재 |

---

## 3단계: 모델 개발

### 3.1 학습/검증 환경 보안

| 검증항목 | 판단 | 비고 |
|:---|:---:|:---|
| 3.1.1 모델 학습 환경 보안 | 해당없음 | 자체 모델 학습 없음 (외부 LLM API 활용) |
| 3.1.2 허위 데이터 삽입 차단 | 해당없음 | 자체 학습 없음 |
| 3.1.3 연합 학습 장치 검증 | 해당없음 | 연합 학습 미사용 |

### 3.2 모델 공격에 대한 방어

| ID | 검증항목 | 판단 | 심각도 | 비고 |
|:---|:---|:---:|:---:|:---|
| 3.2.1 | Prompt Injection 방어 | **취약** | **긴급** | 아래 상세 참조 |
| 3.2.2 | 적대적 예제 공격 방어 | 해당없음 | - | 분류/예측 모델 미사용 |
| 3.2.3 | 모델 회피 공격 방어 | 해당없음 | - | 분류/예측 모델 미사용 |
| 3.2.4 | 모델 오염 공격 방어 | 해당없음 | - | 자체 학습 없음 |
| 3.2.5 | 모델 추출/리버스 엔지니어링 방어 | 해당없음 | - | 외부 LLM 사용, 자체 모델 없음 |
| 3.2.6 | 반복적 질의 방어 | **취약** | **높음** | 아래 상세 참조 |
| 3.2.7 | ML 기반 모델 공격 능동 방어 | 해당없음 | - | 자체 모델 없음 |

### 3.3 오픈소스 라이브러리 보안

| 검증항목 | 판단 | 비고 |
|:---|:---:|:---|
| 3.3.1 라이브러리 업데이트/취약점 관리 | 부분이행 | uv lock 파일로 의존성 고정, 그러나 자동화된 CVE 스캔(Dependabot/Snyk) 미확인 |
| 3.3.2 소스 코드 검토/보안 검증 | 부분이행 | ruff 린트 사용, 그러나 보안 전문 정적 분석 도구(bandit, semgrep) 미적용 |
| 3.3.3 격리된 환경 실행 | 양호 | Docker Compose 기반 컨테이너 격리 환경 운영 |

### 3.4 LLM 보안

| ID | 검증항목 | 판단 | 심각도 | 비고 |
|:---|:---|:---:|:---:|:---|
| 3.4.1 | LLM 애플리케이션 공격 예방 | **취약** | **긴급** | 아래 상세 참조 |
| 3.4.2 | Model DoS 공격 방어 | 부분이행 | - | Rate limiting 존재하나 LLM별 토큰 제한 미설정 |
| 3.4.3 | LLM API 보안 | 양호 | - | API 키 환경변수 로드, SHA-256 해싱 저장, HTTPS 통신 |
| 3.4.4 | LLM 인터페이스 공격 예방 | 양호 | - | Pydantic 모델로 입출력 스키마 강제, JSON 파싱 실패 시 fallback 처리 |
| 3.4.5 | 안전한 코딩 관행/지침 | 양호 | - | 코딩 스타일 가이드라인 존재 (CLAUDE.md), typing 적극 활용 |
| 3.4.6 | LLM 출력 결과 모니터링/검토 | **취약** | **높음** | 아래 상세 참조 |
| 3.4.7 | Prompt Injection 방어 | **취약** | **긴급** | 3.2.1과 동일 |
| 3.4.8 | 벡터/임베딩 취약점 방어 | **취약** | **보통** | 아래 상세 참조 |

---

## 4단계: 모델 배포

### 4.1 모델 파일 및 배포 환경 보호

| 검증항목 | 판단 | 비고 |
|:---|:---:|:---|
| 4.1.1 배포 전 코드/모델 스캔 | 부분이행 | CI에 ruff lint 존재, 보안 전용 스캐너(bandit, Trivy) 미확인 |
| 4.1.2 모델 파일 암호화 | 양호 | 자체 모델 파일 없음. API 키는 Fernet 암호화 저장 |
| 4.1.3 배포 인프라 보안 | 양호 | Docker Compose + GitHub Actions CI/CD, 프로덕션 OpenAPI 문서 비활성화 (`main.py:73-75`) |

### 4.2 API 및 인터페이스 보안

| 검증항목 | 판단 | 비고 |
|:---|:---:|:---|
| 4.2.1 외부 시스템 상호작용 보안 | 양호 | LLM API는 SDK 기본 HTTPS, ElevenLabs는 httpx + HTTPS |
| 4.2.2 MITM 대응 | 양호 | 모든 외부 API 호출이 HTTPS 사용 |
| 4.2.3 API 접근 권한 제한/강한 인증 | 양호 | API Key(SHA-256) + JWT Bearer 이중 인증, scope 기반 권한 |
| 4.2.4 최소 권한 원칙 | **취약** | **높음** | 아래 상세 참조 |
| 4.2.5 연결 장치 인증 | 부분이행 | CORS origin 제한 있으나, IP 기반 허용 목록 없음 |

---

## 5단계: 모니터링 및 유지보수

### 5.1 실시간 모니터링

| 검증항목 | 판단 | 비고 |
|:---|:---:|:---|
| 5.1.1 모델 입출력 비정상 동작 탐지 | **취약** | **높음** | 아래 상세 참조 |
| 5.1.2 응답 시간/사용 패턴 추적 | 양호 | AuditLogMiddleware에 duration_ms 기록, UsageCollector로 토큰/비용 추적 |
| 5.1.3 서버/네트워크 트래픽 모니터링 | 양호 | Prometheus 메트릭 미들웨어 (`setup_metrics`), 구조화 JSON 로깅 |
| 5.1.4 API 호출/입출력 로그 정기 분석 | 양호 | AuditLogRepository에 모든 API 요청 기록 (method, path, status, IP, duration) |
| 5.1.5 AI 모델/배포 환경 모의 해킹 | 해당없음 | 코드 평가 범위 외 (운영 프로세스) |

### 5.2 보안 패치 및 업데이트 관리

| 검증항목 | 판단 | 비고 |
|:---|:---:|:---|
| 5.2.1 패치/업데이트 관리 프로세스 | 부분이행 | uv lock 파일로 의존성 버전 고정, 패치 프로세스 문서화 미확인 |
| 5.2.2 정기적 업데이트 | 부분이행 | uv workspace 구조로 관리 가능하나, 자동 의존성 업데이트(Renovate/Dependabot) 미확인 |
| 5.2.3 스테이징 환경 테스트 | 양호 | 453+ 테스트 존재, CI에서 테스트 실행 |

---

## 6단계: 파기

### 6.1 파기 시 보안

| 검증항목 | 판단 | 비고 |
|:---|:---:|:---|
| 6.1.1 모델 파일 안전 삭제 | 해당없음 | 자체 모델 파일 없음 |
| 6.1.2 사용 데이터 안전 삭제 | **취약** | **보통** | 아래 상세 참조 |
| 6.1.3 폐기 API/인터페이스 비활성화 | 해당없음 | 현재 운영 중인 서비스 |

---

## 주요 발견 사항 (Top Findings)

### F-01: LLM 프롬프트 인젝션 방어 부재 [긴급]

- **검증항목**: 3.2.1, 3.4.1, 3.4.7
- **심각도**: 긴급
- **파일 및 위치**:
  - `packages/agents/yaa_agents/script_writer/prompts/__init__.py` (전체)
  - `packages/agents/yaa_agents/seo_optimizer/keyword_research.py:109-139`
  - `packages/agents/yaa_agents/seo_optimizer/metadata_gen.py:113-148`
  - `packages/agents/yaa_agents/brand_researcher/analyzer.py:54-58`
- **설명**: 사용자 입력(`topic`, `brand_name`, `notes`, `keywords`)이 **어떠한 필터링/검증 없이** 직접 LLM 프롬프트에 삽입됩니다. `PipelineRunRequest`의 `topic` 필드는 Pydantic 기본 `str`로만 선언되어 있어 길이 제한이나 특수 문자 필터링이 없습니다.
  - `build_user_prompt()`: 사용자 입력 `topic`, `notes`, `keywords`를 f-string으로 직접 프롬프트에 삽입
  - `KeywordResearcher._build_prompt()`: `topic`, `brand.positioning`, `audience.primary` 등을 프롬프트에 직접 삽입
  - `BrandAnalyzer.analyze()`: `brand_name`과 `collection.combined_text`를 프롬프트에 직접 삽입
  - 공격자가 `topic` 필드에 시스템 프롬프트를 무효화하는 지시문을 포함할 수 있음
- **판단**: 취약
- **개선 방안**:
  1. 사용자 입력에 대한 프롬프트 인젝션 탐지 필터 구현 (패턴 매칭 + ML 기반)
  2. `PipelineRunRequest.topic`에 `max_length=500` 및 특수 패턴 필터링 추가
  3. 시스템 프롬프트와 사용자 입력을 명확히 분리하는 방어적 프롬프팅 기법 적용 (예: XML 태그 래핑, delimiter)
  4. LLM 응답에 대한 콘텐츠 안전성 검증 레이어 추가

### F-02: LLM 출력 검증/살균 부재 [긴급]

- **검증항목**: 3.4.1, 3.4.6
- **심각도**: 긴급
- **파일 및 위치**:
  - `packages/agents/yaa_agents/script_writer/agent.py:123-134` (`_parse_response`)
  - `packages/agents/yaa_agents/seo_optimizer/metadata_gen.py:150-165` (`_parse_response`)
  - `packages/agents/yaa_agents/seo_optimizer/keyword_research.py:141-153` (`_parse_response`)
  - `packages/agents/yaa_agents/brand_researcher/analyzer.py:68-97` (`_parse_response`)
- **설명**: 모든 에이전트에서 LLM 출력이 JSON 파싱만 수행되고, **콘텐츠 수준 검증이 전혀 없습니다**.
  - `ScriptWriterAgent._parse_response()`: JSON 파싱 후 필드 존재 여부만 확인, 본문 내용 검증 없음
  - `MetadataGenerator._parse_response()`: title/description/tags를 LLM 출력 그대로 사용
  - LLM이 유해하거나 부적절한 콘텐츠, 개인정보, 민감 정보를 생성해도 필터링 없이 YouTube에 업로드될 수 있음
  - `_build_fallback_script()`에서 LLM 원시 응답을 그대로 Script에 담아 후속 파이프라인에 전달
- **판단**: 취약
- **개선 방안**:
  1. LLM 출력에 대한 콘텐츠 필터링 레이어 구현 (유해 콘텐츠, 개인정보, 금지어 탐지)
  2. YouTube 메타데이터(title, description, tags) 생성 시 YouTube 커뮤니티 가이드라인 준수 검증
  3. `_build_fallback_script()`에서 원시 LLM 응답을 그대로 사용하지 않고 안전한 기본값 반환
  4. 출력 길이 제한 (title: 100자, description: 5000자, tags: 개별 500자)

### F-03: 파이프라인 요청 입력 길이 제한 미비 [높음]

- **검증항목**: 3.2.6, 3.4.2
- **심각도**: 높음
- **파일 및 위치**:
  - `packages/api/yaa_app/api/schemas.py:14-21` (`PipelineRunRequest`)
- **설명**: `PipelineRunRequest`의 핵심 필드에 길이 제한이 없습니다:
  - `topic: str` -- 길이 제한 없음. 수십만 자의 텍스트 입력 가능
  - `brand_name: str` -- 길이 제한 없음
  - `channel_id: str` -- 패턴/길이 검증 없음 (반면 `CreateChannelRequest.channel_id`에는 패턴 검증 존재)
  - 대량 텍스트를 `topic`에 삽입하면 LLM에 전달되어 토큰 비용 폭증(Model DoS) 유발 가능
- **판단**: 취약
- **개선 방안**:
  1. `PipelineRunRequest` 필드에 `max_length` 제한 추가:
     - `topic`: `max_length=2000`
     - `brand_name`: `max_length=200`
     - `channel_id`: `max_length=100, pattern=r"^[a-zA-Z0-9_-]+$"`
  2. 파이프라인별 LLM 토큰 사용량 상한(hard cap) 설정

### F-04: 워크스페이스 간 LLM 비용 격리 부재 [높음]

- **검증항목**: 4.2.4
- **심각도**: 높음
- **파일 및 위치**:
  - `packages/core/yaa_core/shared/llm_clients.py:149-192` (`create_openai_client`, `create_anthropic_client`)
  - `packages/api/yaa_app/api/routes/pipeline.py:35-131` (`_execute_pipeline`)
- **설명**: LLM API 키가 전역 설정(`AppSettings`)에서 로드되며, 모든 워크스페이스가 **동일한 OpenAI/Anthropic API 키를 공유**합니다. 한 워크스페이스의 과도한 사용이 다른 워크스페이스에 영향을 줄 수 있습니다.
  - `create_openai_client()`와 `create_anthropic_client()`는 전역 `get_settings()` 싱글턴에서 키를 가져옴
  - 요금제별 파이프라인 실행 횟수(`check_pipeline_quota`)는 제한되지만, 실행 당 LLM 토큰 사용량 제한 없음
  - ElevenLabs 키는 워크스페이스별 저장 가능하지만, OpenAI/Anthropic은 공유
- **판단**: 취약
- **개선 방안**:
  1. 워크스페이스별 월간/일간 LLM 토큰 사용량 한도 설정
  2. `UsageCollector`에 실시간 비용 모니터링 + 한도 초과 시 파이프라인 중단 로직 추가
  3. 워크스페이스별 LLM API 키 지원 (현재 ElevenLabs만 지원)

### F-05: JWT 인증의 admin 권한 과도 부여 [높음]

- **검증항목**: 4.2.4
- **심각도**: 높음
- **파일 및 위치**:
  - `packages/api/yaa_app/api/auth.py:315-316` (`require_admin_scope`)
- **설명**: `require_admin_scope` 함수에서 JWT 인증 사용자에게 조건 없이 admin 권한을 부여합니다:
  ```python
  # JWT 인증 사용자는 자기 workspace에 대해 admin 권한을 가짐
  if ctx.auth_method == "jwt":
      request.state.auth_context = ctx
      return None
  ```
  JWT로 인증된 모든 사용자가 admin 엔드포인트에 접근 가능하며, 이는 최소 권한 원칙 위반입니다.
- **판단**: 취약
- **개선 방안**:
  1. JWT 페이로드에 roles/permissions 필드 추가
  2. admin 라우트에서 사용자 역할(role) 기반 권한 검사 수행
  3. workspace owner만 해당 workspace의 admin 작업을 수행하도록 제한

### F-06: LLM 입출력 모니터링 부재 [높음]

- **검증항목**: 5.1.1, 3.4.6
- **심각도**: 높음
- **파일 및 위치**:
  - `packages/core/yaa_core/shared/llm_clients.py:83-135` (`UsageTrackingCallback`)
  - `packages/agents/yaa_agents/script_writer/agent.py:102-121` (`_invoke_llm`)
- **설명**: `UsageTrackingCallback`은 토큰 수와 비용만 추적합니다. LLM에 전달되는 **프롬프트 내용**과 **응답 내용** 자체에 대한 로깅이 없습니다.
  - 프롬프트에 포함된 사용자 입력이 기록되지 않아, 프롬프트 인젝션 공격 탐지 불가
  - LLM 출력이 로깅되지 않아, 부적절한 출력 사후 감사 불가
  - 비정상적 패턴(반복 요청, 대량 토큰 사용) 탐지 메커니즘 없음
- **판단**: 취약
- **개선 방안**:
  1. LLM 입출력 요약 로깅 추가 (전문이 아닌 해시 또는 요약)
  2. 비정상 패턴 탐지: 토큰 사용량 급증, 반복 실패, 비정상 응답 크기 등에 대한 경고
  3. 정기적 LLM 출력 샘플 검토 프로세스 수립

### F-07: RAG 벡터 스토리지 접근 제어 미흡 [보통]

- **검증항목**: 3.4.8
- **심각도**: 보통
- **파일 및 위치**:
  - `packages/agents/yaa_agents/brand_researcher/rag/retriever.py`
  - `packages/agents/yaa_agents/brand_researcher/rag/indexer.py`
  - `packages/api/yaa_app/api/routes/channels.py:161-186` (`rag_index_channel`)
- **설명**: RAG 벡터 스토리지(ChromaDB)에 대한 워크스페이스 수준 격리가 불명확합니다.
  - `rag_index_channel` 엔드포인트에서 `channel_id`만으로 인덱싱 수행
  - 워크스페이스 A의 브랜드 데이터가 워크스페이스 B의 RAG 검색 결과에 포함될 수 있는 잠재적 위험
  - `BrandRetriever.retrieve_with_metadata()`에서 workspace 레벨 필터링 확인 필요
- **판단**: 취약
- **개선 방안**:
  1. ChromaDB 컬렉션을 workspace_id별로 분리
  2. RAG 검색 시 `workspace_id` 메타데이터 필터 적용
  3. 인덱싱 시 workspace_id를 chunk 메타데이터에 포함

### F-08: 미디어 생성 파일 경로 주입 잠재 위험 [보통]

- **검증항목**: 3.1.2
- **심각도**: 보통
- **파일 및 위치**:
  - `packages/agents/yaa_agents/media_editor/video_editor.py:21-27` (`_validate_path`)
  - `packages/agents/yaa_agents/orchestrator/supervisor.py:257-258`
- **설명**: 파이프라인 상태의 `output_dir`과 `channel_id`로 출력 경로가 구성됩니다:
  ```python
  f"{state.get('output_dir', './output')}/{state['channel_id']}/final.mp4"
  ```
  `channel_id`는 파이프라인 진입 시점에서 `CreateChannelRequest`처럼 패턴 검증을 받지 않습니다. `_validate_path()`는 빈 문자열만 검사하고 경로 순회(`../`)를 차단하지 않습니다.
- **판단**: 취약
- **개선 방안**:
  1. `_validate_path()`에 경로 순회 검사 추가 (`..` 포함 여부 확인)
  2. 파이프라인 초기 상태 생성 시 `channel_id` 패턴 검증 추가
  3. 출력 경로를 `resolve()` 후 허용된 디렉토리 내에 있는지 확인

### F-09: 데이터 파기 정책 부재 [보통]

- **검증항목**: 6.1.2
- **심각도**: 보통
- **파일 및 위치**: 프로젝트 전반
- **설명**: 다음 데이터에 대한 보존/삭제 정책이 수립되어 있지 않습니다:
  - 생성된 음성 파일 (ElevenLabs TTS 결과물)
  - 생성된 영상 파일 (FFmpeg 편집 결과물)
  - 파이프라인 실행 기록 (RunModel)
  - LLM 사용량 기록 (UsageModel)
  - 감사 로그 (AuditLogModel)
  - 워크스페이스 삭제 시 관련 데이터 연쇄 삭제 미구현
- **판단**: 취약
- **개선 방안**:
  1. 데이터 보존/삭제 정책 문서화 (미디어 파일: 30일, 실행 기록: 1년, 감사 로그: 3년 등)
  2. 스케줄된 클린업 작업 구현 (Arq cron job)
  3. 워크스페이스 삭제 시 CASCADE 삭제 또는 소프트 삭제 + 유예기간 후 영구 삭제

### F-10: 워크스페이스 API 키 평문 저장 폴백 [보통]

- **검증항목**: 2.1.3
- **심각도**: 보통
- **파일 및 위치**:
  - `packages/core/yaa_core/shared/encryption.py:42-47` (`decrypt_value`)
- **설명**: `decrypt_value()` 함수에서 `enc:` 접두사가 없는 값은 레거시 평문으로 간주하여 그대로 반환합니다. `ENCRYPTION_KEY`가 설정되지 않은 환경에서 새로 저장되는 API 키는 `encrypt_value()`에서 `RuntimeError`를 발생시키지만, 기존 평문 데이터는 계속 동작합니다.
  - `WorkspaceRepository._ENCRYPTED_FIELDS`에 암호화 대상 필드가 정의되어 있으나, 마이그레이션 없이 기존 평문 데이터가 존재할 수 있음
- **판단**: 부분이행
- **개선 방안**:
  1. 기존 평문 API 키를 암호화로 마이그레이션하는 원타임 스크립트 작성
  2. `ENCRYPTION_KEY` 미설정 시 서버 시작을 차단하거나 경고 로그 출력
  3. 평문 폴백을 제거하고, 레거시 데이터 접근 시 마이그레이션을 강제

### F-11: disable_auth 설정의 위험성 [높음]

- **검증항목**: 4.2.3
- **심각도**: 높음
- **파일 및 위치**:
  - `packages/api/yaa_app/api/auth.py:214-215`, `packages/api/yaa_app/api/auth.py:237-239`
  - `packages/core/yaa_core/shared/config.py:67`
- **설명**: `AppSettings.disable_auth: bool = False` 설정으로 전체 인증을 비활성화할 수 있습니다. 개발 편의를 위한 기능이나, 프로덕션에서 실수로 활성화될 경우:
  - 모든 API 엔드포인트가 인증 없이 접근 가능
  - `get_auth_context()`가 `AuthContext(auth_method="none", workspace_id=None)` 반환
  - 멀티테넌트 격리가 완전히 무력화 (workspace_id=None)
- **판단**: 취약
- **개선 방안**:
  1. 프로덕션 환경에서 `disable_auth=True` 설정 시 서버 시작을 차단
  2. `DISABLE_AUTH` 환경변수 사용 시 경고 로그 + 배너 출력
  3. 프로덕션 감지 로직 추가 (예: `DATABASE_URL`이 PostgreSQL이면 프로덕션으로 간주)

---

## 양호 사항 요약

1. **API 키 보안**: SHA-256 해싱, Fernet 대칭 암호화, `yaa_` 접두사 + `secrets.token_urlsafe` 생성
2. **멀티테넌트 격리**: workspace_id 기반 데이터 격리, 경로 순회 방지 (`_validate_workspace_id`, `_validate_channel_id`)
3. **인증 계층화**: API Key + JWT Bearer 이중 인증, scope 기반 권한 분리
4. **Rate Limiting**: slowapi 기반 요청 속도 제한 (분당 60회 기본)
5. **감사 로그**: 모든 API 요청에 대한 감사 로그 DB 저장 (IP, 메서드, 경로, 응답 코드, 소요 시간)
6. **비용 추적**: UsageCollector + UsageTrackingCallback으로 에이전트별 LLM 토큰/비용 실시간 추적
7. **요금제 제어**: PLAN_QUOTAS 기반 파이프라인 실행 횟수 제한 + 기능 접근 제어
8. **프로덕션 보안**: OpenAPI 문서 비활성화, CORS origin 제한, YouTube 토큰 파일 권한 600
9. **컨테이너 격리**: Docker Compose 기반 서비스 분리
10. **JSON 로깅**: 구조화 JSON 로그 포맷으로 로그 분석 용이

---

## 우선 조치 로드맵

| 순서 | 조치 | 발견 ID | 심각도 | 예상 공수 |
|:---:|:---|:---:|:---:|:---:|
| 1 | LLM 입력 필터링 + 프롬프트 인젝션 방어 | F-01 | 긴급 | 3일 |
| 2 | LLM 출력 콘텐츠 필터링/검증 레이어 추가 | F-02 | 긴급 | 3일 |
| 3 | PipelineRunRequest 입력 검증 강화 | F-03 | 높음 | 0.5일 |
| 4 | JWT admin 권한 세분화 | F-05 | 높음 | 1일 |
| 5 | disable_auth 프로덕션 안전장치 | F-11 | 높음 | 0.5일 |
| 6 | 워크스페이스별 LLM 토큰 한도 설정 | F-04 | 높음 | 2일 |
| 7 | LLM 입출력 요약 로깅 + 이상 탐지 | F-06 | 높음 | 2일 |
| 8 | RAG 워크스페이스 격리 | F-07 | 보통 | 1일 |
| 9 | 미디어 파일 경로 검증 강화 | F-08 | 보통 | 0.5일 |
| 10 | 데이터 보존/파기 정책 수립 + 구현 | F-09 | 보통 | 2일 |
| 11 | 레거시 평문 API 키 마이그레이션 | F-10 | 보통 | 1일 |

---

## 참고문헌

- 과학기술정보통신부/한국인터넷진흥원, 「인공지능(AI) 보안 안내서」
- OWASP Top 10 for LLM Applications (2025)
- NIST AI Risk Management Framework (AI RMF)
- EU AI Act - High-Risk AI Systems Requirements
