#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"

docker compose exec -T postgres pg_dump \
  --username tiktok \
  --dbname tiktok_loader \
  --format custom \
  --file "/tmp/tiktok_loader_${STAMP}.dump"

docker compose cp "postgres:/tmp/tiktok_loader_${STAMP}.dump" "$BACKUP_DIR/"
docker compose exec -T postgres rm "/tmp/tiktok_loader_${STAMP}.dump"

find "$BACKUP_DIR" -name "tiktok_loader_*.dump" -mtime +14 -delete

