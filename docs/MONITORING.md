# Monitoring Setup Guide

YouTube AI Agent Agency의 모니터링 시스템 설정 가이드입니다.

## 아키텍처

```
FastAPI (/metrics) ──> Prometheus ──> Grafana
         │
         └──> stdout (JSON logs) ──> Loki ──> Grafana
```

## 빠른 시작

### 1. 모니터링 스택 시작

```bash
# 모니터링 서비스 (Prometheus + Grafana + Loki) 시작
make monitoring-up

# 전체 스택 (API + DB + 모니터링) 시작
docker compose -f docker-compose.yml -f infra/docker-compose.monitoring.yml up -d
```

### 2. 접속 URL

| 서비스 | URL | 설명 |
|--------|-----|------|
| Prometheus | http://localhost:9090 | 메트릭 쿼리 |
| Grafana | http://localhost:3001 | 대시보드 (로그인 불필요) |
| Loki | http://localhost:3100 | 로그 수집 |

### 3. 모니터링 종료

```bash
make monitoring-down
```

## Prometheus 메트릭

FastAPI 앱은 `/metrics` 엔드포인트에서 Prometheus 형식의 메트릭을 노출합니다.

### 사용 가능한 메트릭

| 메트릭 | 타입 | 레이블 | 설명 |
|--------|------|--------|------|
| `yaa_http_requests_total` | Counter | method, path, status | HTTP 요청 총 수 |
| `yaa_http_request_duration_seconds` | Histogram | method, path | HTTP 요청 처리 시간 |
| `yaa_pipeline_runs_total` | Counter | status | 파이프라인 실행 수 |
| `yaa_pipeline_duration_seconds` | Histogram | channel_id | 파이프라인 실행 시간 |

### 선택적 의존성

`prometheus-client`는 선택적 의존성입니다. 설치하지 않아도 앱이 정상 동작합니다.

```bash
# prometheus-client 설치
cd packages/api && uv sync --extra monitoring
```

## Grafana 대시보드

### 프로비저닝된 대시보드

- **YAA Overview**: HTTP 요청률, 지연시간 (p50/p95/p99), 파이프라인 실행 수, 에러율

### 데이터소스

Prometheus와 Loki가 자동으로 프로비저닝됩니다.

## PromQL 쿼리 예시

```promql
# 5분간 초당 요청 수
sum(rate(yaa_http_requests_total[5m]))

# 95퍼센타일 지연시간
histogram_quantile(0.95, sum(rate(yaa_http_request_duration_seconds_bucket[5m])) by (le))

# 5xx 에러율
sum(rate(yaa_http_requests_total{status=~"5.."}[5m])) / sum(rate(yaa_http_requests_total[5m])) * 100

# 파이프라인 성공/실패 비율
sum(rate(yaa_pipeline_runs_total[5m])) by (status)
```

## 파일 구조

```
infra/
├── docker-compose.monitoring.yml   # 모니터링 Docker Compose 오버레이
├── prometheus/
│   └── prometheus.yml              # Prometheus 스크래핑 설정
├── grafana/
│   ├── dashboards/
│   │   └── yaa-overview.json       # 대시보드 JSON
│   └── provisioning/
│       ├── dashboards/
│       │   └── dashboards.yml      # 대시보드 프로비저닝
│       └── datasources/
│           └── datasources.yml     # 데이터소스 프로비저닝
└── loki/
    └── loki-config.yml             # Loki 로컬 설정
```
