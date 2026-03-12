#!/usr/bin/env bash
# scripts/export_db.sh
#
# Dumps your local rentbnb_demo database into docker/initdb/dump.sql
# so that the Docker Postgres container imports it automatically on first boot.
#
# Usage:
#   chmod +x scripts/export_db.sh
#   ./scripts/export_db.sh
#
# Prerequisites: pg_dump must be on your PATH (comes with PostgreSQL install)

set -euo pipefail

# ──────────── source config from .env ────────────────────────────────────────
DB_USER=${DB_USER:-admin}
DB_PASSWORD=${DB_PASSWORD:-admin}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-rentbnb_demo}

DUMP_DIR="$(cd "$(dirname "$0")/.." && pwd)/docker/initdb"
DUMP_FILE="${DUMP_DIR}/dump.sql"

mkdir -p "${DUMP_DIR}"

echo "→ Dumping '${DB_NAME}' from ${DB_HOST}:${DB_PORT} as user '${DB_USER}' ..."

PGPASSWORD="${DB_PASSWORD}" pg_dump \
  --host="${DB_HOST}" \
  --port="${DB_PORT}" \
  --username="${DB_USER}" \
  --dbname="${DB_NAME}" \
  --no-owner \
  --no-acl \
  --format=plain \
  --file="${DUMP_FILE}"

echo "✓ Dump written to: ${DUMP_FILE}"
echo ""
echo "Next steps:"
echo "  1. docker compose up --build"
echo "     Postgres will auto-import ${DUMP_FILE} on first boot."
echo "  2. The 'app' service will then run 'alembic upgrade head'."
