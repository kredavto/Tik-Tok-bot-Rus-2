#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=deploy/lib/common.sh
source "$(dirname "$0")/lib/common.sh"

require_command docker
require_file "$ENV_FILE"

BACKUP_DIR="${BACKUP_DIR:-$(env_value BACKUP_DIR)}"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
if [[ "$BACKUP_DIR" != /* ]]; then
  BACKUP_DIR="$PROJECT_ROOT/${BACKUP_DIR#./}"
fi
[[ "$BACKUP_DIR" != "/" ]] || die "BACKUP_DIR cannot be the filesystem root"

RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-$(env_value BACKUP_RETENTION_DAYS)}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
[[ "$RETENTION_DAYS" =~ ^[0-9]+$ ]] || die "BACKUP_RETENTION_DAYS must be an integer"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FINAL_PATH="$BACKUP_DIR/tiktok_loader_${STAMP}.dump"
TEMP_PATH="${FINAL_PATH}.partial"
META_PATH="${FINAL_PATH}.meta"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
trap 'rm -f "$TEMP_PATH"' EXIT

log "creating PostgreSQL backup"
compose up -d postgres >/dev/null
compose exec -T postgres sh -ec \
  'exec pg_dump --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --format=custom' \
  >"$TEMP_PATH"

[[ -s "$TEMP_PATH" ]] || die "database backup is empty"
compose exec -T postgres pg_restore --list <"$TEMP_PATH" >/dev/null

CHECKSUM="$(sha256_file "$TEMP_PATH")"
SIZE_BYTES="$(wc -c <"$TEMP_PATH" | tr -d ' ')"
GIT_SHA="$(git rev-parse HEAD 2>/dev/null || printf unknown)"
APP_VERSION="$(env_value APP_VERSION)"
DB_REVISION="$(compose run --rm --no-deps api alembic current 2>/dev/null | tail -n 1 || true)"
DB_REVISION="${DB_REVISION:-unknown}"

mv "$TEMP_PATH" "$FINAL_PATH"
chmod 600 "$FINAL_PATH"
printf '%s  %s\n' "$CHECKSUM" "$(basename "$FINAL_PATH")" >"${FINAL_PATH}.sha256"
printf 'created_at=%s\nenvironment=%s\ngit_sha=%s\napp_version=%s\nalembic_revision=%s\nsize_bytes=%s\nverified=true\n' \
  "$STAMP" "$(env_value APP_ENV)" "$GIT_SHA" "$APP_VERSION" "$DB_REVISION" "$SIZE_BYTES" \
  >"$META_PATH"
chmod 600 "${FINAL_PATH}.sha256" "$META_PATH"

find "$BACKUP_DIR" -type f \
  \( -name 'tiktok_loader_*.dump' -o -name 'tiktok_loader_*.dump.sha256' -o -name 'tiktok_loader_*.dump.meta' \) \
  -mtime "+$RETENTION_DAYS" -delete

log "backup verified: $FINAL_PATH ($SIZE_BYTES bytes)"
printf '%s\n' "$FINAL_PATH"
