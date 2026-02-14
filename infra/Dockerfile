FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY packages/ packages/

# Install dependencies (production only)
RUN uv sync --all-packages --extra auth --extra queue --extra monitoring --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "yaa_app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
