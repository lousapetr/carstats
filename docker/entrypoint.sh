#!/bin/sh
set -e

mkdir -p /app/data/uploads

uv run alembic upgrade head
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
