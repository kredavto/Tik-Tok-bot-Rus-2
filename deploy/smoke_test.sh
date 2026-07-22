#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=deploy/lib/common.sh
source "$(dirname "$0")/lib/common.sh"

require_command curl
require_file "$ENV_FILE"

BASE_URL="${1:-${SMOKE_BASE_URL:-$(env_value PUBLIC_BASE_URL)}}"
BASE_URL="${BASE_URL%/}"
[[ "$BASE_URL" == http://* || "$BASE_URL" == https://* ]] || die "a valid base URL is required"

RETRIES="${SMOKE_RETRIES:-20}"
DELAY="${SMOKE_RETRY_DELAY_SECONDS:-3}"
CURL_ARGS=(--fail --silent --show-error --connect-timeout 5 --max-time 15)

wait_for() {
  local path="$1"
  local expected="$2"
  local attempt response
  for ((attempt = 1; attempt <= RETRIES; attempt++)); do
    if response="$(curl "${CURL_ARGS[@]}" "$BASE_URL$path" 2>/dev/null)" \
      && grep -Fq "$expected" <<<"$response"; then
      log "smoke check passed: $path"
      return 0
    fi
    sleep "$DELAY"
  done
  die "smoke check failed after $RETRIES attempts: $path"
}

wait_for_header() {
  local path="$1"
  local expected="$2"
  local attempt headers
  for ((attempt = 1; attempt <= RETRIES; attempt++)); do
    if headers="$(curl "${CURL_ARGS[@]}" --dump-header - --output /dev/null "$BASE_URL$path" 2>/dev/null)" \
      && grep -Fiq "$expected" <<<"$headers"; then
      log "security header check passed: $path"
      return 0
    fi
    sleep "$DELAY"
  done
  die "security header check failed after $RETRIES attempts: $path"
}

wait_for /api/v1/health '"status":"ok"'
wait_for /api/v1/ready '"status":"ready"'
wait_for /api/v1/metrics 'tiktok_loader_http_requests_total'
wait_for /openapi.json '"/api/v1/webhooks/telegram"'
wait_for /openapi.json '"/api/v1/payments/robokassa/result"'
wait_for_header /admin-ui/ 'content-security-policy:'

if [[ "$(env_value TELEGRAM_DELIVERY_MODE)" == "webhook" \
  && "${SMOKE_VERIFY_TELEGRAM_WEBHOOK:-true}" == "true" ]]; then
  compose run --rm --no-deps bot python -m app.bot.webhook verify
  log "Telegram webhook verification passed"
fi

log "deployment smoke test passed"
