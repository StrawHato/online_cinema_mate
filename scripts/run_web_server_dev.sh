#!/bin/sh

set -e

python scripts/wait_for_db.py

exec uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload
