.PHONY: help install test test-cov lint format run server clean docker-build docker-up docker-down docker-logs dev-setup db-migrate db-upgrade db-downgrade db-history rag-index worker redis-up redis-down monitoring-up monitoring-down

CORE_DIR = packages/core
AGENTS_DIR = packages/agents
API_DIR = packages/api

help: ## 사용 가능한 명령어 표시
	@echo "YouTube AI Agent Agency"
	@echo ""
	@echo "사용 가능한 명령어:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## 의존성 설치
	uv sync --all-packages --all-extras

test: ## 전체 테스트 실행
	cd $(API_DIR) && uv run pytest tests/ -v

test-cov: ## 커버리지 포함 테스트
	cd $(API_DIR) && uv run pytest tests/ --cov=yaa_app --cov=yaa_agents --cov=yaa_core --cov-report=html --cov-report=term

lint: ## 린트 검사
	uv run ruff check packages/

format: ## 코드 포맷팅
	uv run ruff format packages/

run: ## CLI 채널 목록 조회
	uv run youtube-agent channels list

server: ## FastAPI 서버 실행
	cd $(API_DIR) && uv run uvicorn yaa_app.api.main:app --reload --host 0.0.0.0 --port 8000

clean: ## 생성된 파일 정리
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf $(API_DIR)/htmlcov/
	rm -rf output/

docker-build: ## Docker 이미지 빌드
	docker compose build

docker-up: ## Docker Compose 시작
	docker compose up -d

docker-down: ## Docker Compose 종료
	docker compose down

docker-logs: ## Docker 로그 확인
	docker compose logs -f agents

db-migrate: ## 새 Alembic 마이그레이션 생성 (msg= 필수)
	cd $(API_DIR) && uv run alembic revision --autogenerate -m "$(msg)"

db-upgrade: ## DB 최신 스키마로 업그레이드
	cd $(API_DIR) && uv run alembic upgrade head

db-downgrade: ## DB 한 단계 롤백
	cd $(API_DIR) && uv run alembic downgrade -1

db-history: ## 마이그레이션 이력 확인
	cd $(API_DIR) && uv run alembic history

dev-setup: install ## 개발 환경 초기화
	@test -f .env || cp .env.example .env
	@echo "개발 환경 설정 완료"
	@echo "  1. .env 파일에 API 키를 입력하세요"
	@echo "  2. make test 로 테스트를 실행하세요"

# ============================================
# RAG (P7-2)
# ============================================

rag-index: ## 채널 브랜드 자료 RAG 인덱싱 (channel_id= 필수)
	uv run --package yaa-app youtube-agent rag-index --channel-id $(channel_id)

# ============================================
# Worker / Redis (P7-1)
# ============================================

worker: ## Arq 워커 실행 (로컬)
	cd $(API_DIR) && uv run python -m arq yaa_app.worker.tasks.WorkerConfig

redis-up: ## Redis 컨테이너 시작
	docker compose up -d redis

redis-down: ## Redis 컨테이너 종료
	docker compose stop redis

# ============================================
# Monitoring (P8-1+P8-2)
# ============================================

monitoring-up: ## 모니터링 스택 시작 (Prometheus + Grafana + Loki)
	docker compose -f docker-compose.yml -f infra/docker-compose.monitoring.yml up -d prometheus grafana loki

monitoring-down: ## 모니터링 스택 종료
	docker compose -f docker-compose.yml -f infra/docker-compose.monitoring.yml stop prometheus grafana loki
