#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env}"
STATE_DIR="${STATE_DIR:-$PROJECT_ROOT/.deploy}"

cd "$PROJECT_ROOT"

log() {
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "required command is not available: $1"
}

require_file() {
  [[ -f "$1" ]] || die "required file does not exist: $1"
}

compose() {
  local ingress
  local compose_files=(-f docker-compose.yml)
  ingress="$(env_value DEPLOY_INGRESS)"
  if [[ "${ingress:-nginx}" == "cloudflared" ]]; then
    compose_files+=(-f deploy/docker-compose.cloudflared.yml)
  fi
  docker compose --env-file "$ENV_FILE" "${compose_files[@]}" "$@"
}

env_value() {
  python3 - "$ENV_FILE" "$1" <<'PY'
from pathlib import Path
import sys

from app.core.deploy_validation import parse_env_file

print(parse_env_file(Path(sys.argv[1])).get(sys.argv[2], ""))
PY
}

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    die "sha256sum or shasum is required"
  fi
}

validate_deploy_environment() {
  local environment="$1"
  require_command python3
  require_file "$ENV_FILE"
  python3 tools/validate_deploy_env.py --env-file "$ENV_FILE" --environment "$environment"
}

validate_tls_files() {
  local template cert_dir
  [[ "$(env_value DEPLOY_INGRESS)" != "cloudflared" ]] || return 0
  template="$(env_value NGINX_TEMPLATE)"
  [[ "$template" == "https.conf.template" ]] || return 0
  cert_dir="$(tls_cert_dir)"
  require_file "$cert_dir/fullchain.pem"
  require_file "$cert_dir/privkey.pem"
}

tls_cert_dir() {
  local cert_dir
  cert_dir="$(env_value TLS_CERT_DIR)"
  if [[ "$cert_dir" != /* ]]; then
    cert_dir="$PROJECT_ROOT/${cert_dir#./}"
  fi
  printf '%s\n' "$cert_dir"
}

validate_tls_certificate() {
  local template cert_dir cert_file key_file domain minimum_seconds cert_fingerprint key_fingerprint
  [[ "$(env_value DEPLOY_INGRESS)" != "cloudflared" ]] || return 0
  template="$(env_value NGINX_TEMPLATE)"
  [[ "$template" == "https.conf.template" ]] || return 0

  require_command openssl
  validate_tls_files
  cert_dir="$(tls_cert_dir)"
  cert_file="$cert_dir/fullchain.pem"
  key_file="$cert_dir/privkey.pem"
  domain="$(env_value DOMAIN)"
  minimum_seconds="${TLS_MIN_VALIDITY_SECONDS:-1209600}"
  [[ "$minimum_seconds" =~ ^[0-9]+$ ]] \
    || die "TLS_MIN_VALIDITY_SECONDS must be a non-negative integer"

  openssl x509 -in "$cert_file" -noout -checkend "$minimum_seconds" >/dev/null \
    || die "TLS certificate expires in less than $minimum_seconds seconds"
  openssl x509 -in "$cert_file" -noout -checkhost "$domain" >/dev/null \
    || die "TLS certificate does not cover DOMAIN"

  cert_fingerprint="$({ openssl x509 -in "$cert_file" -pubkey -noout \
    | openssl pkey -pubin -outform DER 2>/dev/null \
    | openssl dgst -sha256; } 2>/dev/null)"
  key_fingerprint="$({ openssl pkey -in "$key_file" -pubout -outform DER 2>/dev/null \
    | openssl dgst -sha256; } 2>/dev/null)"
  [[ -n "$cert_fingerprint" && "$cert_fingerprint" == "$key_fingerprint" ]] \
    || die "TLS certificate and private key do not match"
}

require_clean_tracked_worktree() {
  if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
    die "tracked files contain local changes; commit or stash them before deployment"
  fi
}
