#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=deploy/lib/common.sh
source "$(dirname "$0")/lib/common.sh"

BACKUP_PATH="${1:-}"
CONFIRM="${2:-}"
SKIP_PRE_BACKUP="${3:-}"
[[ -f "$BACKUP_PATH" ]] \
  || die "usage: deploy/restore_postgres.sh <backup.dump> --confirm [--skip-pre-backup]"
[[ "$CONFIRM" == "--confirm" ]] || die "restore requires explicit --confirm"

require_command docker
require_file "$ENV_FILE"
validate_tls_files

EXPECTED_FILE="${BACKUP_PATH}.sha256"
require_file "$EXPECTED_FILE"
EXPECTED="$(awk '{print $1}' "$EXPECTED_FILE")"
ACTUAL="$(sha256_file "$BACKUP_PATH")"
[[ "$EXPECTED" == "$ACTUAL" ]] || die "backup checksum verification failed"

compose up -d postgres redis >/dev/null
compose exec -T postgres pg_restore --list <"$BACKUP_PATH" >/dev/null

if [[ "$SKIP_PRE_BACKUP" != "--skip-pre-backup" ]]; then
  log "creating a safety backup before restore"
  bash deploy/backup_postgres.sh >/dev/null
fi

log "stopping application services"
compose stop api bot worker scheduler nginx

restore_failed() {
  log "restore failed; application services remain stopped for investigation"
}
trap restore_failed ERR

log "recreating target database"
# Variables expand inside the PostgreSQL container, not in the host shell.
# shellcheck disable=SC2016
compose exec -T postgres sh -ec \
  'dropdb --username="$POSTGRES_USER" --if-exists --force "$POSTGRES_DB" && createdb --username="$POSTGRES_USER" "$POSTGRES_DB"'
# shellcheck disable=SC2016
compose exec -T postgres sh -ec \
  'exec pg_restore --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --no-owner --no-privileges --exit-on-error' \
  <"$BACKUP_PATH"

compose up --no-deps migrate
compose up -d --remove-orphans
trap - ERR
bash deploy/smoke_test.sh
log "database restore and smoke test completed"
