#!/bin/bash
set -e

echo "Starting Arq worker..."
exec uv run arq yaa_app.worker.tasks.WorkerSettings
