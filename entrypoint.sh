#!/bin/bash
set -e

echo "Running database migrations..."
cd /app/packages/api && python -m alembic upgrade head

echo "Starting FastAPI server..."
exec uvicorn yaa_app.api.main:app --host 0.0.0.0 --port 8000
