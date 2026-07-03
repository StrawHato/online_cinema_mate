#!/bin/sh

set -e

python scripts/wait_for_db.py

exec gunicorn src.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
