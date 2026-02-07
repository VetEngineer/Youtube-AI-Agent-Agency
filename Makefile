.PHONY: help install test test-cov lint format run server clean docker-build docker-up docker-down docker-logs dev-setup db-migrate db-upgrade db-downgrade db-history rag-index

AGENTS_DIR = packages/agents

help: ## 사용 가능한 명령어 표시
	@echo "YouTube AI Agent Agency"
	@echo ""
	@echo "사용 가능한 명령어:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## 의존성 설치
	cd $(AGENTS_DIR) && uv pip install -e ".[all]"

test: ## 전체 테스트 실행
	cd $(AGENTS_DIR) && uv run pytest tests/ -v

test-cov: ## 커버리지 포함 테스트
	cd $(AGENTS_DIR) && uv run pytest tests/ --cov=src --cov-report=html --cov-report=term

lint: ## 린트 검사
	cd $(AGENTS_DIR) && uv run ruff check src/ tests/

format: ## 코드 포맷팅
	cd $(AGENTS_DIR) && uv run ruff format src/ tests/

run: ## CLI 채널 목록 조회
	cd $(AGENTS_DIR) && uv run youtube-agent channels list

server: ## FastAPI 서버 실행
	cd $(AGENTS_DIR) && uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

clean: ## 생성된 파일 정리
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf $(AGENTS_DIR)/htmlcov/
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
	cd $(AGENTS_DIR) && uv run alembic revision --autogenerate -m "$(msg)"

db-upgrade: ## DB 최신 스키마로 업그레이드
	cd $(AGENTS_DIR) && uv run alembic upgrade head

db-downgrade: ## DB 한 단계 롤백
	cd $(AGENTS_DIR) && uv run alembic downgrade -1

db-history: ## 마이그레이션 이력 확인
	cd $(AGENTS_DIR) && uv run alembic history

dev-setup: install ## 개발 환경 초기화
	@test -f .env || cp .env.example .env
	@echo "개발 환경 설정 완료"
	@echo "  1. .env 파일에 API 키를 입력하세요"
	@echo "  2. make test 로 테스트를 실행하세요"

# ============================================
# RAG (P7-2)
# ============================================

rag-index: ## 채널 브랜드 자료 RAG 인덱싱 (channel= 필수)
	cd $(AGENTS_DIR) && uv run python -c "from src.brand_researcher.rag import BrandIndexer, RAGConfig; idx = BrandIndexer(RAGConfig()); print(f'Indexed {idx.index_channel(\"$(channel)\", __import__(\"pathlib\").Path(\"../../channels/$(channel)\"))} chunks')"
