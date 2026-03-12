# Logging Configuration Guide

YouTube AI Agent Agency의 로깅 설정 가이드입니다.

## 로그 포맷

환경변수 `LOG_FORMAT`으로 로그 출력 형식을 제어합니다.

| 값 | 용도 | 설명 |
|----|------|------|
| `text` (기본값) | 개발 환경 | 사람이 읽기 쉬운 텍스트 포맷 |
| `json` | 프로덕션 환경 | Loki/ELK 등 로그 수집기에 적합한 구조화 JSON |

### 설정 방법

```bash
# .env 파일 또는 환경변수
LOG_FORMAT=json   # 프로덕션: JSON 포맷
LOG_FORMAT=text   # 개발: 텍스트 포맷 (기본값)
LOG_LEVEL=INFO    # 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
```

## 출력 예시

### 텍스트 포맷 (LOG_FORMAT=text)

```
2025-01-15 14:30:00 [INFO] yaa_app.api.main: 데이터베이스 초기화 완료
2025-01-15 14:30:01 [WARNING] yaa_app.api.middleware: 감사 로그 저장 실패
```

### JSON 포맷 (LOG_FORMAT=json)

```json
{
  "timestamp": "2025-01-15T14:30:00.123456+00:00",
  "level": "INFO",
  "logger": "yaa_app.api.main",
  "message": "데이터베이스 초기화 완료",
  "module": "main",
  "function": "lifespan",
  "line": 28
}
```

## 구조화 로깅 활용

### extra 필드 추가

```python
import logging

logger = logging.getLogger(__name__)

# extra 필드가 JSON 출력에 포함됩니다
logger.info(
    "파이프라인 실행 완료",
    extra={"channel_id": "tech-channel", "duration_ms": 1234.5}
)
```

JSON 출력:
```json
{
  "timestamp": "2025-01-15T14:30:00+00:00",
  "level": "INFO",
  "logger": "yaa_agents.orchestrator.supervisor",
  "message": "파이프라인 실행 완료",
  "channel_id": "tech-channel",
  "duration_ms": 1234.5
}
```

## Loki 연동

JSON 포맷 로그는 Docker 로그 드라이버를 통해 Loki로 전송됩니다.

### Grafana에서 로그 조회

1. Grafana (http://localhost:3001) 접속
2. Explore > Loki 데이터소스 선택
3. LogQL 쿼리 사용:

```logql
# 에러 로그만 조회
{job="yaa-api"} |= "ERROR"

# JSON 파싱 후 필터
{job="yaa-api"} | json | level="ERROR"

# 특정 채널 로그
{job="yaa-api"} | json | channel_id="tech-channel"
```

## 파일 구조

```
packages/core/yaa_core/shared/
└── logging_config.py     # JSONFormatter + setup_logging()
```
