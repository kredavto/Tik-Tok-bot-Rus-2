#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=deploy/lib/common.sh
source "$(dirname "$0")/lib/common.sh"

ENVIRONMENT="${1:-}"
GIT_REF="${2:-}"
CONFIRM="${3:-}"
[[ "$ENVIRONMENT" == "staging" || "$ENVIRONMENT" == "production" ]] \
  || die "usage: deploy/rollback.sh <staging|production> <git-ref> --confirm"
[[ -n "$GIT_REF" && "$CONFIRM" == "--confirm" ]] \
  || die "rollback requires a target ref and explicit --confirm"

require_command docker
require_command git
validate_deploy_environment "$ENVIRONMENT"
validate_tls_files
require_clean_tracked_worktree

log "creating a database backup before application rollback"
bash deploy/backup_postgres.sh >/dev/null

git fetch --prune --tags origin
TARGET_SHA="$(git rev-parse --verify "${GIT_REF}^{commit}")"
git checkout --detach "$TARGET_SHA"

log "building and starting the selected application revision"
compose build
compose up -d --remove-orphans
bash deploy/smoke_test.sh

log "application rollback complete: $TARGET_SHA"
log "no Alembic downgrade was performed; use restore_postgres.sh only after compatibility review"
