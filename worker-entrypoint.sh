#!/bin/bash
set -e

echo "Starting Arq worker..."
exec python -m arq yaa_app.worker.tasks.WorkerConfig
