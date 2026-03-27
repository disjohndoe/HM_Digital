#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Pulling latest code ==="
git pull origin main

echo "=== Building and restarting containers ==="
docker compose build
docker compose up -d

echo "=== Running database migrations ==="
docker compose exec -T backend alembic upgrade head

echo "=== Cleaning up old images ==="
docker image prune -f

echo "=== Deployment complete ==="
docker compose ps
