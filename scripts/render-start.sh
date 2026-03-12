#!/usr/bin/env bash
# scripts/render-start.sh

set -e

echo "→ Running database migrations..."
alembic upgrade head

echo "→ Seeding super admin..."
python scripts/seed_super_admin.py

echo "→ Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}"
