FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml ./
COPY packages/core/pyproject.toml packages/core/
COPY packages/agents/pyproject.toml packages/agents/
COPY packages/api/pyproject.toml packages/api/

# Create minimal package dirs for editable install
RUN mkdir -p packages/core/yaa_core packages/agents/yaa_agents packages/api/yaa_app && \
    touch packages/core/yaa_core/__init__.py packages/agents/yaa_agents/__init__.py packages/api/yaa_app/__init__.py

RUN uv pip install --system \
    -e packages/core \
    -e "packages/agents[media,rag]" \
    -e "packages/api[all]"

COPY packages/ packages/
COPY channels channels

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "yaa_app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
