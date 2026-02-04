# YouTube AI Agent Agency - 사용방법 매뉴얼

## 목차

1. [빠른 시작](#1-빠른-시작)
2. [CLI 사용법](#2-cli-사용법)
3. [API 서버](#3-api-서버)
4. [인증 및 권한](#4-인증-및-권한)
5. [채널 관리](#5-채널-관리)
6. [데이터베이스 및 마이그레이션](#6-데이터베이스-및-마이그레이션)
7. [Docker 실행](#7-docker-실행)
8. [Makefile 명령어 레퍼런스](#8-makefile-명령어-레퍼런스)
9. [프로젝트 구조](#9-프로젝트-구조)
10. [환경변수 레퍼런스](#10-환경변수-레퍼런스)
11. [에이전트 아키텍처 상세](#11-에이전트-아키텍처-상세)
12. [트러블슈팅](#12-트러블슈팅)
13. [FAQ](#13-faq)

---

## 1. 빠른 시작

### 필수 요구사항

- **Python** 3.11 이상
- **uv** (Python 패키지 매니저)
- **FFmpeg** (영상/오디오 처리)

### 설치

```bash
# 1. 저장소 클론
git clone <repository-url>
cd Youtube-AI-Agent-Agency

# 2. 개발 환경 초기화 (의존성 설치 + .env 생성)
make dev-setup

# 3. .env 파일에 API 키 입력
# 아래 "환경변수 레퍼런스" 섹션 참고
vi .env

# 4. 테스트 실행으로 설치 확인
make test
```

### 수동 설치 (uv 직접 사용)

```bash
cd packages/agents
uv pip install -e ".[all]"
```

---

## 2. CLI 사용법

설치 후 `youtube-agent` 명령어를 사용할 수 있습니다.

### 도움말

```bash
youtube-agent --help
```

### 파이프라인 실행

전체 콘텐츠 파이프라인(브랜드 리서치 → 원고 → SEO → 미디어 생성 → 편집 → 업로드)을 실행합니다.

```bash
youtube-agent run --channel <채널ID> --topic <주제> [--dry-run]
```

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--channel` | O | 채널 ID (channels/ 디렉토리명) |
| `--topic` | O | 콘텐츠 주제 |
| `--dry-run` | X | 실제 YouTube 업로드를 건너뜀 |

**예시:**

```bash
# 실제 업로드
youtube-agent run --channel deepure-cattery --topic "고양이 건강 관리 팁 5가지"

# dry-run (업로드 없이 파이프라인만 실행)
youtube-agent run --channel deepure-cattery --topic "고양이 건강 관리" --dry-run
```

### 채널 목록 조회

등록된 모든 채널을 확인합니다.

```bash
youtube-agent channels list
```

**출력 예시:**

```
등록된 채널 (1개):
  [✓] deepure-cattery - 딥퓨어캐터리
```

- `✓`: 브랜드 가이드(`brand_guide.yaml`) 있음
- `✗`: 브랜드 가이드 없음

### 새 채널 생성

템플릿을 기반으로 새 채널을 생성합니다.

```bash
youtube-agent channels create <채널ID>
```

**예시:**

```bash
youtube-agent channels create tax-accounting
```

생성 후 `channels/tax-accounting/config.yaml` 파일을 편집하여 채널 정보를 입력합니다.

### 브랜드 리서치

특정 채널에 대한 브랜드 리서치를 수행하고 `brand_guide.yaml`을 생성합니다.

```bash
youtube-agent brand-research --channel <채널ID> --brand <브랜드명>
```

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--channel` | O | 채널 ID |
| `--brand` | O | 브랜드명 |

**예시:**

```bash
youtube-agent brand-research --channel deepure-cattery --brand "딥퓨어캐터리"
```

---

## 3. API 서버

FastAPI 기반 REST API 서버를 통해 프로그래밍 방식으로 시스템을 제어할 수 있습니다.

### 서버 실행

```bash
# Makefile 사용
make server

# 또는 직접 실행
cd packages/agents
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 시작되면 `http://localhost:8000`에서 접근 가능합니다.
Swagger UI 문서: `http://localhost:8000/docs`

### 인증

API 서버는 API 키 기반 인증을 지원합니다. 개발 환경에서는 `DISABLE_AUTH=true`로 비활성화할 수 있습니다.

```bash
# API 키를 헤더로 전달
curl -H "X-API-Key: yaa_xxxxx..." http://localhost:8000/api/v1/channels/

# 또는 쿼리 파라미터로 전달
curl http://localhost:8000/api/v1/channels/?api_key=yaa_xxxxx...
```

자세한 인증 설정은 [인증 및 권한](#4-인증-및-권한) 섹션을 참고하세요.

### 엔드포인트

#### GET /api/v1/health

헬스체크 엔드포인트입니다.

```bash
curl http://localhost:8000/api/v1/health
```

**응답:**

```json
{
  "status": "healthy"
}
```

#### GET /api/v1/channels/

등록된 채널 목록을 조회합니다.

```bash
curl http://localhost:8000/api/v1/channels/
```

**응답:**

```json
{
  "channels": [
    {
      "channel_id": "deepure-cattery",
      "name": "딥퓨어캐터리",
      "category": "pets",
      "has_brand_guide": true
    }
  ],
  "total": 1
}
```

#### GET /api/v1/channels/{channel_id}

특정 채널의 상세 정보를 조회합니다.

```bash
curl http://localhost:8000/api/v1/channels/deepure-cattery
```

**응답:**

```json
{
  "channel_id": "deepure-cattery",
  "name": "딥퓨어캐터리",
  "category": "pets",
  "has_brand_guide": true
}
```

**에러 (404):** 존재하지 않는 채널 ID로 요청한 경우

```json
{
  "detail": "채널을 찾을 수 없습니다: nonexistent"
}
```

#### POST /api/v1/pipeline/run

콘텐츠 파이프라인을 백그라운드에서 실행합니다.

```bash
curl -X POST http://localhost:8000/api/v1/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "deepure-cattery",
    "topic": "고양이 건강 관리 팁",
    "brand_name": "딥퓨어캐터리",
    "dry_run": true
  }'
```

**요청 본문:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `channel_id` | string | O | 채널 ID |
| `topic` | string | O | 콘텐츠 주제 |
| `brand_name` | string | X | 브랜드명 (기본값: `""`) |
| `dry_run` | boolean | X | 업로드 건너뜀 (기본값: `false`) |

**응답:**

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "channel_id": "deepure-cattery",
  "topic": "고양이 건강 관리 팁"
}
```

#### GET /api/v1/status/{run_id}

파이프라인 실행 상태를 조회합니다.

```bash
curl http://localhost:8000/api/v1/status/550e8400-e29b-41d4-a716-446655440000
```

**응답:**

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "current_agent": "script_writer",
  "errors": [],
  "result": null
}
```

**상태 값:**

| 상태 | 설명 |
|------|------|
| `pending` | 실행 대기 중 |
| `running` | 파이프라인 실행 중 |
| `completed` | 성공적으로 완료 |
| `failed` | 에러로 실패 |

#### GET /api/v1/pipeline/runs

파이프라인 실행 이력을 조회합니다. 필터링 및 페이지네이션을 지원합니다.

```bash
# 전체 조회
curl http://localhost:8000/api/v1/pipeline/runs

# 채널별 필터링
curl "http://localhost:8000/api/v1/pipeline/runs?channel_id=deepure-cattery"

# 상태 필터링 + 페이지네이션
curl "http://localhost:8000/api/v1/pipeline/runs?status=completed&limit=10&offset=0"
```

**쿼리 파라미터:**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `channel_id` | string | - | 채널 ID 필터 |
| `status` | string | - | 상태 필터 (pending/running/completed/failed) |
| `limit` | int | 20 | 페이지당 결과 수 (1~100) |
| `offset` | int | 0 | 건너뛸 결과 수 |

**응답:**

```json
{
  "runs": [
    {
      "run_id": "550e8400-...",
      "channel_id": "deepure-cattery",
      "topic": "고양이 건강 관리",
      "status": "completed",
      "dry_run": true,
      "created_at": "2025-01-15T10:30:00",
      "completed_at": "2025-01-15T10:35:00"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### POST /api/v1/channels/

새 채널을 생성합니다. **admin 스코프 필요.**

```bash
curl -X POST http://localhost:8000/api/v1/channels/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: yaa_xxxxx..." \
  -d '{
    "channel_id": "new-channel",
    "name": "새 채널",
    "category": "tech"
  }'
```

**요청 본문:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `channel_id` | string | O | 채널 ID (영문, 숫자, 하이픈, 언더스코어) |
| `name` | string | O | 채널명 |
| `category` | string | X | 카테고리 (기본값: `"general"`) |
| `description` | string | X | 설명 (기본값: `""`) |

**응답 (201):**

```json
{
  "channel_id": "new-channel",
  "name": "새 채널",
  "category": "tech",
  "has_brand_guide": false
}
```

**에러:** 이미 존재하는 채널 ID (409), 잘못된 ID 형식 (422)

#### PATCH /api/v1/channels/{channel_id}

채널 설정을 수정합니다. **admin 스코프 필요.**

```bash
curl -X PATCH http://localhost:8000/api/v1/channels/deepure-cattery \
  -H "Content-Type: application/json" \
  -H "X-API-Key: yaa_xxxxx..." \
  -d '{"name": "수정된 채널명", "category": "pets"}'
```

**요청 본문:** `name`, `category`, `description` 중 최소 하나 필요

#### DELETE /api/v1/channels/{channel_id}

채널을 삭제합니다. **admin 스코프 필요.**

```bash
curl -X DELETE http://localhost:8000/api/v1/channels/old-channel \
  -H "X-API-Key: yaa_xxxxx..."
```

#### POST /api/v1/admin/api-keys

새 API 키를 생성합니다. **admin 스코프 필요.**

```bash
curl -X POST http://localhost:8000/api/v1/admin/api-keys \
  -H "Content-Type: application/json" \
  -H "X-API-Key: yaa_xxxxx..." \
  -d '{"name": "프론트엔드 키", "scopes": ["read", "write"]}'
```

**요청 본문:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `name` | string | O | 키 이름 |
| `scopes` | string[] | X | 권한 (기본값: `["read", "write"]`) |
| `expires_days` | int | X | 만료일 (1~365일) |

**응답 (201):**

```json
{
  "api_key": "yaa_xxxxxxxxxxxxxxxx",
  "key_id": "key-uuid-...",
  "name": "프론트엔드 키",
  "scopes": ["read", "write"],
  "created_at": "2025-01-15T10:00:00",
  "expires_at": null
}
```

> **주의:** `api_key` 값은 생성 시에만 반환됩니다. 분실 시 재발급해야 합니다.

#### GET /api/v1/admin/api-keys

API 키 목록을 조회합니다. **admin 스코프 필요.**

```bash
# 활성 키만 조회
curl http://localhost:8000/api/v1/admin/api-keys \
  -H "X-API-Key: yaa_xxxxx..."

# 비활성 키 포함
curl "http://localhost:8000/api/v1/admin/api-keys?include_inactive=true" \
  -H "X-API-Key: yaa_xxxxx..."
```

#### DELETE /api/v1/admin/api-keys/{key_id}

API 키를 비활성화합니다. **admin 스코프 필요.**

```bash
curl -X DELETE http://localhost:8000/api/v1/admin/api-keys/{key_id} \
  -H "X-API-Key: yaa_xxxxx..."
```

#### GET /api/v1/admin/audit-logs

감사 로그를 조회합니다. **admin 스코프 필요.**

```bash
# 전체 조회
curl http://localhost:8000/api/v1/admin/audit-logs \
  -H "X-API-Key: yaa_xxxxx..."

# 필터링
curl "http://localhost:8000/api/v1/admin/audit-logs?method=POST&limit=50" \
  -H "X-API-Key: yaa_xxxxx..."
```

**쿼리 파라미터:**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `api_key_id` | string | - | API 키 ID 필터 |
| `method` | string | - | HTTP 메서드 필터 (GET/POST/...) |
| `limit` | int | 100 | 페이지당 결과 수 (1~1000) |
| `offset` | int | 0 | 건너뛸 결과 수 |

---

## 4. 인증 및 권한

### API 키 인증

시스템은 SHA-256 해싱 기반 API 키 인증을 사용합니다. API 키는 `yaa_` 접두사로 시작합니다.

### 인증 방법

API 키는 두 가지 방법으로 전달할 수 있습니다:

1. **HTTP 헤더** (권장):
   ```bash
   curl -H "X-API-Key: yaa_xxxxx..." http://localhost:8000/api/v1/channels/
   ```

2. **쿼리 파라미터**:
   ```bash
   curl "http://localhost:8000/api/v1/channels/?api_key=yaa_xxxxx..."
   ```

### 권한 스코프

| 스코프 | 설명 | 접근 가능 엔드포인트 |
|--------|------|---------------------|
| `read` | 읽기 전용 | GET 엔드포인트 |
| `write` | 읽기/쓰기 | GET, POST 엔드포인트 |
| `admin` | 관리자 | 모든 엔드포인트 (API 키 관리, 감사 로그 포함) |

### 개발 모드

개발 환경에서는 인증을 비활성화할 수 있습니다:

```bash
# .env 파일에서
DISABLE_AUTH=true
```

### 첫 API 키 생성

인증이 비활성화된 상태에서 첫 admin 키를 생성합니다:

```bash
# 1. DISABLE_AUTH=true 상태에서 서버 실행
make server

# 2. admin 키 생성
curl -X POST http://localhost:8000/api/v1/admin/api-keys \
  -H "Content-Type: application/json" \
  -d '{"name": "관리자 키", "scopes": ["read", "write", "admin"]}'

# 3. 응답의 api_key 값을 안전하게 저장

# 4. .env에서 DISABLE_AUTH=false로 변경
```

---

## 5. 채널 관리

### 채널 디렉토리 구조

각 채널은 `channels/` 하위에 독립된 디렉토리로 관리됩니다.

```
channels/
├── _template/              # 템플릿 (새 채널 생성 시 복사됨)
│   ├── config.yaml
│   └── brand_guide.yaml
├── deepure-cattery/        # 실제 채널 예시
│   ├── config.yaml
│   └── brand_guide.yaml
└── tax-accounting/         # 추가 채널
    └── config.yaml
```

### config.yaml 설정

채널의 기본 설정 파일입니다.

```yaml
channel:
  name: "딥퓨어캐터리"             # 채널명
  youtube_channel_id: "UC..."      # YouTube 채널 ID
  category: "pets"                  # 카테고리
  language: "ko"                    # 언어

seo:
  primary_keywords:                 # 주요 키워드
    - "고양이 브리더"
    - "고양이 분양"
  secondary_keywords:               # 보조 키워드
    - "고양이 건강"
    - "고양이 묘종"

editing:
  intro_template: ""                # 인트로 템플릿 경로
  outro_template: ""                # 아웃트로 템플릿 경로
  subtitle_style: "soft"           # 자막 스타일 (default/soft/bold)
  bgm_volume: 0.12                 # BGM 볼륨 (0.0~1.0)
```

### brand_guide.yaml 설정

브랜드 가이드 파일입니다. `brand-research` 명령어로 자동 생성하거나 수동으로 작성할 수 있습니다.

```yaml
brand:
  name: "딥퓨어캐터리"                      # 브랜드명
  tagline: "건강한 혈통, 따뜻한 가족"        # 슬로건
  positioning: "프리미엄 고양이 브리더"       # 포지셔닝
  values:                                    # 핵심 가치
    - "책임감 있는 브리딩"
    - "고양이 건강 최우선"

target_audience:
  primary: "고양이를 처음 분양받으려는 20-40대" # 주요 타겟
  pain_points:                                  # 고객 고충
    - "건강한 고양이를 어디서 분양받을지 모름"
  content_needs:                                # 콘텐츠 니즈
    - "고양이 품종별 특성 이해"

tone_and_manner:
  personality: "따뜻하지만 전문적인 수의사 친구"  # 성격
  formality: "semi-formal"       # formal / semi-formal / casual
  emotion: "warm"                # warm / neutral / energetic
  humor_level: "light"           # none / light / moderate / heavy
  writing_style:
    sentence_length: "medium"    # short / medium / long
    vocabulary: "전문용어를 쉽게 풀어서 설명"
    call_to_action: "부드러운 권유형"
  do:                            # 지켜야 할 것
    - "고양이 건강과 행복을 최우선으로 언급"
  dont:                          # 하지 말아야 할 것
    - "과도한 판매 압박"

voice_design:
  narration_style: "차분하고 신뢰감 있는 여성 목소리"
  elevenlabs_voice_id: ""        # ElevenLabs 음성 ID
  speech_rate: "moderate"        # slow / moderate / fast
  pitch: "medium"                # low / medium / high
  language: "ko"
  reference_samples: []          # 참고 음성 샘플 경로

visual_identity:
  color_palette:                 # 브랜드 컬러 (HEX)
    - "#F5E6D3"
    - "#8B7355"
  thumbnail_style: "따뜻한 톤, 고양이 클로즈업 중심"
  font_preference: "둥근 산세리프"

competitors:                     # 경쟁사 분석
  - channel: "캣맘TV"
    strengths:
      - "친근한 일상 콘텐츠"
    differentiation: "전문 브리딩 지식 기반 신뢰성"
```

### 새 채널 추가 워크플로우

1. 채널 생성:
   ```bash
   youtube-agent channels create my-new-channel
   ```

2. `channels/my-new-channel/config.yaml` 편집

3. 브랜드 리서치 실행 (자동으로 `brand_guide.yaml` 생성):
   ```bash
   youtube-agent brand-research --channel my-new-channel --brand "브랜드명"
   ```

4. 생성된 `brand_guide.yaml` 검토 및 수정

5. 파이프라인 테스트:
   ```bash
   youtube-agent run --channel my-new-channel --topic "첫 번째 주제" --dry-run
   ```

### API를 통한 채널 관리

CLI 외에 REST API로도 채널을 관리할 수 있습니다:

```bash
# 채널 목록 조회
curl http://localhost:8000/api/v1/channels/

# 채널 생성 (admin 권한 필요)
curl -X POST http://localhost:8000/api/v1/channels/ \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "new-channel", "name": "새 채널", "category": "tech"}'

# 채널 수정
curl -X PATCH http://localhost:8000/api/v1/channels/new-channel \
  -H "Content-Type: application/json" \
  -d '{"name": "수정된 이름"}'

# 채널 삭제
curl -X DELETE http://localhost:8000/api/v1/channels/new-channel
```

---

## 6. 데이터베이스 및 마이그레이션

### 데이터베이스

시스템은 SQLAlchemy 2.0 async를 사용합니다.

| 환경 | 데이터베이스 | URL 형식 |
|------|------------|----------|
| 개발 | SQLite | `sqlite+aiosqlite:///./data/agency.db` |
| Docker | PostgreSQL 16 | `postgresql+asyncpg://agency:password@db:5432/youtube_agency` |

### Alembic 마이그레이션

DB 스키마 변경 시 Alembic 마이그레이션을 사용합니다.

```bash
# 현재 스키마로 DB 업그레이드
make db-upgrade

# 새 마이그레이션 생성 (모델 변경 후)
make db-migrate msg="Add new column"

# 한 단계 롤백
make db-downgrade

# 마이그레이션 이력 확인
make db-history
```

### 테이블 구조

| 테이블 | 설명 |
|--------|------|
| `pipeline_runs` | 파이프라인 실행 이력 (상태, 결과, 에러) |
| `api_keys` | API 키 (해시, 스코프, 활성 상태) |
| `audit_logs` | 감사 로그 (요청 메서드, 경로, 응답 코드, 소요 시간) |

---

## 7. Docker 실행

### 이미지 빌드

```bash
make docker-build
```

### 컨테이너 시작

```bash
# 백그라운드 실행
make docker-up

# 로그 확인
make docker-logs
```

### 컨테이너 종료

```bash
make docker-down
```

### Docker Compose 구성

`docker-compose.yml`에서 다음을 설정합니다:

| 항목 | 값 | 설명 |
|------|-----|------|
| 포트 | `8000:8000` | API 서버 포트 |
| 소스 마운트 | `./packages/agents/src:/app/packages/agents/src:ro` | 소스 코드 (읽기 전용) |
| 채널 마운트 | `./channels:/app/channels` | 채널 설정 |
| 출력 마운트 | `./output:/app/output` | 생성된 콘텐츠 |
| 환경변수 | `.env` | API 키 등 |

### 헬스체크

Docker 컨테이너는 30초 간격으로 `/api/v1/health` 엔드포인트를 확인합니다.

---

## 8. Makefile 명령어 레퍼런스

```bash
make help    # 사용 가능한 명령어 목록
```

| 명령어 | 설명 |
|--------|------|
| `make help` | 사용 가능한 명령어 표시 |
| `make install` | 의존성 설치 |
| `make dev-setup` | 개발 환경 초기화 (install + .env 생성) |
| `make test` | 전체 테스트 실행 |
| `make test-cov` | 커버리지 포함 테스트 |
| `make lint` | 린트 검사 (ruff check) |
| `make format` | 코드 포맷팅 (ruff format) |
| `make run` | CLI 채널 목록 조회 |
| `make server` | FastAPI 서버 실행 (reload 모드) |
| `make clean` | 캐시, 빌드 파일 정리 |
| `make docker-build` | Docker 이미지 빌드 |
| `make docker-up` | Docker Compose 시작 |
| `make docker-down` | Docker Compose 종료 |
| `make docker-logs` | Docker 로그 확인 |
| `make db-migrate msg="설명"` | 새 Alembic 마이그레이션 생성 |
| `make db-upgrade` | DB 최신 스키마로 업그레이드 |
| `make db-downgrade` | DB 한 단계 롤백 |
| `make db-history` | 마이그레이션 이력 확인 |

---

## 9. 프로젝트 구조

```
Youtube-AI-Agent-Agency/
├── packages/agents/                    # Python 에이전트 패키지
│   ├── pyproject.toml                  # 프로젝트 설정, 의존성
│   ├── src/
│   │   ├── cli.py                      # CLI 엔트리포인트
│   │   ├── __main__.py                 # python -m src 지원
│   │   ├── shared/                     # 공유 모듈
│   │   │   ├── config.py              # AppSettings, ChannelRegistry
│   │   │   ├── models.py             # Pydantic 데이터 모델
│   │   │   ├── llm_clients.py        # LLM 클라이언트 팩토리
│   │   │   └── llm_utils.py          # JSON 파싱 유틸리티
│   │   ├── orchestrator/              # LangGraph Supervisor
│   │   │   ├── supervisor.py          # 파이프라인 그래프 빌드
│   │   │   ├── state.py              # PipelineState 정의
│   │   │   └── workflows/            # 워크플로우 (향후 확장)
│   │   ├── brand_researcher/          # 브랜드 리서치 에이전트
│   │   │   ├── agent.py
│   │   │   ├── collector.py          # 웹/SNS 수집기
│   │   │   ├── analyzer.py           # 포지셔닝 분석
│   │   │   └── voice_designer.py     # 톤앤매너 설계
│   │   ├── script_writer/             # 원고 생성 에이전트 (Claude)
│   │   │   └── agent.py
│   │   ├── media_generator/           # 미디어 생성 에이전트
│   │   │   ├── agent.py
│   │   │   ├── voice_gen.py          # ElevenLabs TTS
│   │   │   └── image_gen.py          # 이미지 생성
│   │   ├── media_editor/              # 미디어 편집 에이전트
│   │   │   ├── agent.py
│   │   │   ├── video_editor.py       # FFmpeg 영상 편집
│   │   │   ├── subtitle.py           # 자막 처리
│   │   │   └── audio_mixer.py        # 오디오 믹싱
│   │   ├── seo_optimizer/             # SEO 최적화 에이전트 (GPT)
│   │   │   ├── agent.py
│   │   │   ├── keyword_research.py   # 키워드 리서치
│   │   │   └── metadata_gen.py       # 메타데이터 생성
│   │   ├── publisher/                 # YouTube 업로드 에이전트
│   │   │   ├── agent.py
│   │   │   └── youtube_api.py        # YouTube Data API v3
│   │   ├── analyzer/                  # 성과 분석 에이전트
│   │   │   ├── agent.py
│   │   │   ├── analytics.py          # YouTube Analytics API
│   │   │   └── report_gen.py         # 리포트 생성
│   │   ├── database/                  # 데이터 영속화
│   │   │   ├── engine.py             # 비동기 세션 팩토리
│   │   │   ├── models.py            # SQLAlchemy ORM 모델
│   │   │   └── repositories.py      # Repository 패턴 (CRUD)
│   │   └── api/                       # FastAPI REST API
│   │       ├── main.py               # 앱 팩토리
│   │       ├── auth.py               # API 키 인증 + 스코프 검증
│   │       ├── middleware.py          # 감사 로그 + Rate Limiting
│   │       ├── schemas.py            # Pydantic 스키마
│   │       ├── dependencies.py       # 의존성 주입
│   │       └── routes/               # 엔드포인트
│   │           ├── admin.py          # API 키 관리 + 감사 로그
│   │           ├── pipeline.py       # 파이프라인 실행 + 이력
│   │           ├── channels.py       # 채널 CRUD
│   │           └── status.py         # 상태 조회 + 헬스체크
│   ├── alembic/                       # DB 마이그레이션
│   │   ├── env.py                    # 마이그레이션 환경
│   │   └── versions/                 # 마이그레이션 파일
│   └── tests/                         # 테스트
├── channels/                           # 채널별 YAML 설정
├── docs/                               # 프로젝트 문서
├── .env.example                        # 환경변수 템플릿
├── Makefile                            # 빌드/실행 명령어
├── Dockerfile                          # 컨테이너 이미지
└── docker-compose.yml                  # 서비스 구성
```

### 파이프라인 흐름

```
Brand Research → Script Writing → SEO Optimization → Media Generation → Media Editing → Publishing
```

각 단계는 LangGraph Supervisor가 StateGraph의 조건부 엣지로 제어합니다.

---

## 10. 환경변수 레퍼런스

`.env.example` 파일을 `.env`로 복사한 후 실제 값을 입력합니다.

```bash
cp .env.example .env
```

### 필수 환경변수

| 변수 | 설명 | 예시 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI API 키 (GPT-4o) | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API 키 (Claude) | `sk-ant-...` |

### 선택 환경변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `ELEVENLABS_API_KEY` | ElevenLabs 음성 합성 API 키 | - |
| `TAVILY_API_KEY` | Tavily 웹 검색 API 키 | - |
| `YOUTUBE_CLIENT_ID` | YouTube API OAuth 클라이언트 ID | - |
| `YOUTUBE_CLIENT_SECRET` | YouTube API OAuth 시크릿 | - |
| `CHANNELS_DIR` | 채널 설정 디렉토리 경로 | `./channels` |
| `LOG_LEVEL` | 로깅 레벨 | `INFO` |
| `DATABASE_URL` | 데이터베이스 URL | `sqlite+aiosqlite:///./data/agency.db` |
| `DISABLE_AUTH` | 인증 비활성화 (개발용) | `true` |
| `RATE_LIMIT_PER_MINUTE` | 일반 Rate Limit | `60` |
| `RATE_LIMIT_PIPELINE_PER_MINUTE` | 파이프라인 Rate Limit | `10` |
| `CORS_ORIGINS` | CORS 허용 origin (쉼표 구분) | `http://localhost:3000` |
| `DB_PASSWORD` | Docker PostgreSQL 비밀번호 | `localdevpassword` |

### API 키 발급 안내

| 서비스 | 발급 URL |
|--------|---------|
| OpenAI | https://platform.openai.com/api-keys |
| Anthropic | https://console.anthropic.com/ |
| ElevenLabs | https://elevenlabs.io/ |
| Tavily | https://tavily.com/ |
| YouTube API | https://console.cloud.google.com/ |

---

## 11. 에이전트 아키텍처 상세

### 파이프라인 아키텍처

시스템은 LangGraph StateGraph 기반의 6단계 파이프라인으로 구성됩니다. 각 단계는 독립적인 에이전트가 담당하며, 조건부 엣지(conditional edge)로 실행 흐름을 제어합니다.

```
┌─────────────────┐
│  Brand Research  │  ← 브랜드 리서치 (Tavily 웹 검색 + LLM 분석)
└────────┬────────┘
         ▼
┌─────────────────┐
│  Script Writing  │  ← 원고 생성 (Claude)
└────────┬────────┘
         ▼
┌─────────────────┐
│ SEO Optimization │  ← SEO/AEO/GEO 최적화 (GPT-4o)
└────────┬────────┘
         ▼
┌─────────────────┐
│ Media Generation │  ← 음성 합성 (ElevenLabs TTS) + 이미지 생성
└────────┬────────┘
         ▼
┌─────────────────┐
│  Media Editing   │  ← 영상 편집 (FFmpeg) + 자막 + 오디오 믹싱
└────────┬────────┘
         ▼
┌─────────────────┐
│   Publishing     │  ← YouTube 업로드 (Data API v3)
└─────────────────┘
```

### 에이전트별 상세

#### Brand Researcher

웹에서 브랜드 정보를 수집하고 분석하여 `brand_guide.yaml`을 생성합니다.

| 구성 요소 | 역할 |
|-----------|------|
| `collector.py` | Tavily/BeautifulSoup으로 웹/SNS 정보 수집 |
| `analyzer.py` | 수집된 데이터를 LLM으로 포지셔닝 분석 |
| `voice_designer.py` | 톤앤매너, 음성 스타일 설계 |

**출력:** `BrandGuide` (브랜드 정보, 타겟 오디언스, 톤앤매너, 음성 디자인, 비주얼 아이덴티티, 경쟁사 분석)

#### Script Writer

브랜드 가이드에 맞춰 구조화된 영상 원고를 생성합니다.

- **사용 LLM:** Claude (Anthropic)
- **입력:** `ContentPlan` + `BrandGuide`
- **출력:** `Script` (제목, 섹션별 본문/비주얼 노트, 예상 재생 시간)

#### SEO Optimizer

검색 최적화를 위한 키워드 리서치와 메타데이터를 생성합니다.

| 구성 요소 | 역할 |
|-----------|------|
| `keyword_research.py` | 주제 기반 키워드 분석 (검색량, 경쟁도) |
| `metadata_gen.py` | 제목, 설명, 태그 등 YouTube 메타데이터 생성 |

- **사용 LLM:** GPT-4o (OpenAI)
- **출력:** `SEOAnalysis` + `VideoMetadata`

#### Media Generator

텍스트를 음성과 이미지로 변환합니다.

| 구성 요소 | 역할 |
|-----------|------|
| `voice_gen.py` | ElevenLabs API로 TTS 음성 합성 |
| `image_gen.py` | AI 이미지 생성 (썸네일, 삽입 이미지) |

- **출력:** `VoiceGenerationResult` + `ImageGenerationResult[]`

#### Media Editor

생성된 소스를 조합하여 최종 영상을 편집합니다.

| 구성 요소 | 역할 |
|-----------|------|
| `video_editor.py` | FFmpeg 기반 영상 편집, 트랜지션 |
| `subtitle.py` | 자막 생성 및 스타일링 |
| `audio_mixer.py` | BGM 믹싱, 볼륨 조절 |

- **출력:** `EditResult` (최종 MP4 파일 경로, 해상도, 파일 크기)

#### Publisher

편집된 영상을 YouTube에 업로드합니다.

- **API:** YouTube Data API v3 (OAuth 2.0)
- **기본 공개 설정:** `private` (비공개)
- **`--dry-run` 모드:** 실제 업로드를 건너뛰고 파이프라인만 검증
- **출력:** `PublishResult` (video_id, URL, 상태)

### 상태 관리

파이프라인 전체에서 공유되는 `PipelineState`로 데이터가 전달됩니다.

| 상태 키 | 타입 | 생성 에이전트 |
|---------|------|---------------|
| `brand_guide` | `BrandGuide` | Brand Researcher |
| `script` | `Script` | Script Writer |
| `seo_analysis` | `SEOAnalysis` | SEO Optimizer |
| `metadata` | `VideoMetadata` | SEO Optimizer |
| `voice_result` | `VoiceGenerationResult` | Media Generator |
| `image_results` | `ImageGenerationResult[]` | Media Generator |
| `edit_result` | `EditResult` | Media Editor |
| `publish_result` | `PublishResult` | Publisher |

### 에러 처리 및 라우팅

- 각 노드에서 예외 발생 시 `errors` 리스트에 에러 메시지가 누적됩니다.
- `status`가 `FAILED`로 변경되면 파이프라인이 즉시 종료됩니다(`END`로 라우팅).
- 에러가 없으면 다음 단계로 자동 진행됩니다.

### 콘텐츠 생명주기

```
DRAFT → REVIEW → APPROVED → PUBLISHED
                          ↘ FAILED
```

| 상태 | 설명 |
|------|------|
| `DRAFT` | 초기 상태, 파이프라인 시작 |
| `REVIEW` | Human-in-the-loop 검토 대기 |
| `APPROVED` | 검토 통과 (dry-run 완료 시에도 이 상태) |
| `PUBLISHED` | YouTube 업로드 완료 |
| `FAILED` | 에러로 파이프라인 중단 |

---

## 12. 트러블슈팅

### 설치 관련

#### `uv` 명령어를 찾을 수 없음

```
command not found: uv
```

**해결:** uv를 설치합니다.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### FFmpeg가 설치되지 않음

```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```

**해결:**

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Docker 사용 시 이미지에 포함되어 있음
```

#### 의존성 설치 실패

```bash
# 캐시 정리 후 재설치
make clean && make install
```

### API 키 관련

#### API 키 미설정 에러

```
OPENAI_API_KEY가 설정되지 않았습니다
```

**해결:** `.env` 파일에 API 키가 정확히 입력되었는지 확인합니다.

```bash
# .env 파일 확인
cat .env | grep -v "^#" | grep -v "^$"

# .env.example과 비교
diff .env .env.example
```

#### ElevenLabs API 할당량 초과

```
elevenlabs.api_error: 429 Too Many Requests
```

**해결:** ElevenLabs 대시보드에서 할당량을 확인하고, 필요 시 플랜을 업그레이드합니다. 테스트 시에는 `--dry-run` 모드를 사용하여 API 호출을 최소화합니다.

### 채널 관련

#### 채널을 찾을 수 없음

```
채널을 찾을 수 없습니다: my-channel
```

**해결:** `channels/` 디렉토리에 해당 채널 폴더가 있는지 확인합니다.

```bash
youtube-agent channels list
ls channels/
```

#### brand_guide.yaml 파싱 에러

```
yaml.scanner.ScannerError: while parsing a block mapping
```

**해결:** YAML 문법 오류를 수정합니다. 들여쓰기(스페이스 2칸)와 콜론 뒤 공백에 주의합니다.

```bash
# YAML 유효성 검사
python -c "import yaml; yaml.safe_load(open('channels/my-channel/brand_guide.yaml'))"
```

### Docker 관련

#### 포트 충돌

```
Bind for 0.0.0.0:8000 failed: port is already allocated
```

**해결:** 이미 8000 포트를 사용하는 프로세스를 종료하거나, `docker-compose.yml`에서 포트를 변경합니다.

```bash
# 포트 사용 프로세스 확인
lsof -i :8000

# docker-compose.yml에서 포트 변경
# ports: "8001:8000"
```

#### 컨테이너 헬스체크 실패

**해결:** 로그를 확인하여 원인을 파악합니다.

```bash
make docker-logs
docker inspect --format='{{.State.Health.Status}}' youtube-agent
```

### 파이프라인 실행 관련

#### 파이프라인이 특정 단계에서 멈춤

**해결:** 로그 레벨을 `DEBUG`로 변경하여 상세 로그를 확인합니다.

```bash
# .env 파일 수정
LOG_LEVEL=DEBUG

# 또는 환경변수로 직접 설정
LOG_LEVEL=DEBUG youtube-agent run --channel my-channel --topic "주제" --dry-run
```

#### YouTube 업로드 인증 실패

```
google.auth.exceptions.RefreshError
```

**해결:** OAuth 토큰이 만료되었습니다. `token.json` 파일을 삭제하고 다시 인증합니다.

```bash
rm token.json
youtube-agent run --channel my-channel --topic "주제"
# 브라우저에서 OAuth 인증 수행
```

---

## 13. FAQ

### 일반

**Q: 무료로 사용할 수 있나요?**

A: 이 프로젝트 자체는 MIT 라이선스로 무료입니다. 다만 외부 API(OpenAI, Anthropic, ElevenLabs, YouTube API)는 각 서비스의 요금 정책에 따라 비용이 발생할 수 있습니다.

**Q: 어떤 언어의 콘텐츠를 생성할 수 있나요?**

A: 기본 설정은 한국어(`ko`)이지만, `config.yaml`의 `language` 필드를 변경하면 다른 언어도 지원합니다. LLM과 ElevenLabs가 지원하는 언어라면 사용 가능합니다.

**Q: 한 번에 여러 채널의 콘텐츠를 생성할 수 있나요?**

A: 현재는 채널별로 개별 실행해야 합니다. 멀티 채널 배치 처리는 향후 업데이트에서 지원 예정입니다.

### 파이프라인

**Q: `--dry-run` 모드에서는 어떤 API가 호출되나요?**

A: dry-run 모드에서는 YouTube 업로드만 건너뜁니다. 브랜드 리서치, 원고 생성, SEO 최적화, 미디어 생성, 영상 편집은 정상적으로 실행되므로 해당 API 비용이 발생합니다.

**Q: 파이프라인 도중 실패하면 처음부터 다시 실행해야 하나요?**

A: 네, 현재는 재시도 시 전체 파이프라인을 다시 실행해야 합니다. 다만, 이미 생성된 `brand_guide.yaml`은 자동으로 재사용됩니다.

**Q: 업로드된 영상의 공개 설정은 어떻게 되나요?**

A: 기본값은 `private`(비공개)입니다. 업로드 후 YouTube Studio에서 직접 공개 상태를 변경하거나, 코드에서 `privacy_status`를 `public` 또는 `unlisted`로 수정할 수 있습니다.

### 채널 설정

**Q: brand_guide.yaml을 수동으로 작성해도 되나요?**

A: 네. `brand-research` 명령어로 자동 생성하거나, `channels/_template/brand_guide.yaml`을 참고하여 직접 작성할 수 있습니다.

**Q: 여러 채널에 같은 브랜드 가이드를 사용할 수 있나요?**

A: 가능하지만 권장하지 않습니다. 각 채널의 특성에 맞는 독립적인 브랜드 가이드를 유지하는 것이 콘텐츠 품질에 도움됩니다.

### API 서버

**Q: API 서버에 인증이 있나요?**

A: 네. SHA-256 기반 API 키 인증이 구현되어 있습니다. `X-API-Key` 헤더 또는 `api_key` 쿼리 파라미터로 인증합니다. 개발 환경에서는 `DISABLE_AUTH=true`로 비활성화할 수 있습니다. 자세한 내용은 [인증 및 권한](#4-인증-및-권한) 섹션을 참고하세요.

**Q: API로 파이프라인 실행 결과를 실시간으로 받을 수 있나요?**

A: `GET /api/v1/status/{run_id}` 엔드포인트로 폴링(polling)하여 상태를 확인할 수 있습니다. WebSocket 기반 실시간 알림은 향후 지원 예정입니다.
