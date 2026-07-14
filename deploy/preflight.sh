#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=deploy/lib/common.sh
source "$(dirname "$0")/lib/common.sh"

ENVIRONMENT="${1:-}"
[[ "$ENVIRONMENT" == "staging" || "$ENVIRONMENT" == "production" ]] \
  || die "usage: deploy/preflight.sh <staging|production>"

require_command docker
require_command git
require_command python3
validate_deploy_environment "$ENVIRONMENT"
validate_tls_certificate
require_clean_tracked_worktree

log "checking Docker daemon and Compose model"
docker info >/dev/null 2>&1 || die "Docker daemon is not available"
compose config --quiet

minimum_free_mb="${MIN_FREE_DISK_MB:-2048}"
[[ "$minimum_free_mb" =~ ^[0-9]+$ ]] || die "MIN_FREE_DISK_MB must be a non-negative integer"
available_mb="$(df -Pk "$PROJECT_ROOT" | awk 'NR == 2 {print int($4 / 1024)}')"
[[ "$available_mb" =~ ^[0-9]+$ ]] || die "could not determine available disk space"
((available_mb >= minimum_free_mb)) \
  || die "available disk space is below ${minimum_free_mb} MB"

log "preflight passed for $ENVIRONMENT (free disk: ${available_mb} MB)"
