#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=deploy/lib/common.sh
source "$(dirname "$0")/lib/common.sh"

ENVIRONMENT="${1:-}"
GIT_REF="${2:-}"
[[ "$ENVIRONMENT" == "staging" || "$ENVIRONMENT" == "production" ]] \
  || die "usage: deploy/deploy.sh <staging|production> <git-ref>"
[[ -n "$GIT_REF" ]] || die "a release branch, tag, or commit is required"

bash deploy/preflight.sh "$ENVIRONMENT"

mkdir -p "$STATE_DIR"
PREVIOUS_SHA="$(git rev-parse HEAD)"
printf '%s\n' "$PREVIOUS_SHA" >"$STATE_DIR/previous_revision"

log "backing up the database before deployment"
bash deploy/backup_postgres.sh >/dev/null

log "fetching release reference"
git fetch --prune --tags origin
TARGET_SHA="$(git rev-parse --verify "${GIT_REF}^{commit}")"
git checkout --detach "$TARGET_SHA"

log "building application image"
compose build --pull
log "applying Alembic migrations"
compose up --no-deps migrate
log "starting services"
compose up -d --remove-orphans

log "configuring and verifying Telegram webhook"
compose run --rm --no-deps bot python -m app.bot.webhook configure
bash deploy/smoke_test.sh
printf '%s\n' "$TARGET_SHA" >"$STATE_DIR/current_revision"
log "deployment complete: $TARGET_SHA (previous: $PREVIOUS_SHA)"
