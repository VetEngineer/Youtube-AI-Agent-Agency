# 비동기 작업 큐 아키텍처

> Phase 7-1: Redis + Arq 기반 비동기 파이프라인 실행

## 개요

파이프라인 실행을 FastAPI `BackgroundTasks`에서 Redis 기반 Arq 작업 큐로 전환합니다.
이를 통해 워커 프로세스를 독립적으로 스케일링하고, 작업 재시도/모니터링이 가능해집니다.

## 아키텍처

```
┌─────────────┐     ┌─────────┐     ┌──────────────┐     ┌────────┐
│  FastAPI API │────>│  Redis  │────>│  Arq Worker  │────>│   DB   │
│  (enqueue)   │     │  Queue  │     │  (execute)   │     │        │
└─────────────┘     └─────────┘     └──────────────┘     └────────┘
```

1. `POST /api/v1/pipeline/run` 요청이 들어오면 DB에 `pending` 상태로 저장
2. Redis가 사용 가능하면 Arq 큐에 작업 등록
3. Worker가 큐에서 작업을 가져와 파이프라인 실행
4. 실행 결과를 DB에 업데이트 (`completed` / `failed`)

## 폴백 전략

Redis가 사용 불가능하면 기존 `BackgroundTasks` 방식으로 자동 폴백됩니다.
이를 통해 개발 환경에서 Redis 없이도 정상 동작합니다.

```python
# pipeline.py 핵심 로직
enqueued = await enqueue_pipeline(run_id, ...)
if not enqueued:
    background_tasks.add_task(_execute_pipeline, ...)
```

## 설정

### 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `REDIS_HOST` | `localhost` | Redis 호스트 |
| `REDIS_PORT` | `6379` | Redis 포트 |
| `REDIS_DB` | `0` | Redis DB 번호 |
| `REDIS_PASSWORD` | `""` | Redis 비밀번호 |
| `WORKER_MAX_JOBS` | `5` | 동시 실행 최대 작업 수 |
| `WORKER_JOB_TIMEOUT` | `1800` | 작업 타임아웃 (초, 기본 30분) |
| `WORKER_QUEUE_NAME` | `yaa:pipeline` | 큐 이름 |

### .env 예시

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
WORKER_MAX_JOBS=3
```

## 실행 방법

### Docker Compose (권장)

```bash
# 전체 스택 (API + Worker + Redis + DB)
docker compose up -d

# 로그 확인
docker compose logs -f worker
```

### 로컬 개발

```bash
# 1. Redis 시작
make redis-up

# 2. 워커 실행 (별도 터미널)
make worker

# 3. API 서버 실행 (별도 터미널)
make server
```

## 파일 구조

```
packages/agents/src/worker/
├── __init__.py      # 모듈 초기화
├── config.py        # WorkerSettings (환경변수 기반)
├── enqueue.py       # enqueue_pipeline() 헬퍼
└── tasks.py         # Arq 작업 정의 + WorkerConfig
```

## 스케일링

Worker 인스턴스를 늘려 병렬 처리량을 증가시킬 수 있습니다:

```bash
docker compose up -d --scale worker=3
```

각 Worker는 `WORKER_MAX_JOBS`개의 작업을 동시에 처리합니다.
