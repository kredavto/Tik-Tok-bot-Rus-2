# Staging Acceptance Runbook

This runbook is the mandatory rehearsal before the first production deployment. Use isolated
staging credentials, a staging domain, Robokassa test mode, and a TikTok test account approved for
the application's official scopes.

## Entry Criteria

- The release commit passed all GitHub Actions jobs.
- The CI run contains the `release-candidate-manifest` artifact for the same full Git SHA.
- DNS points the staging domain to the Netherlands VPS.
- A valid TLS certificate and matching private key are installed.
- The Telegram token has never appeared in chat, source, logs, or Git.
- TikTok Developer Portal contains the exact staging Redirect URI and webhook URL.
- Robokassa test settings contain the exact ResultURL, SuccessURL, and FailURL.
- A verified PostgreSQL backup can be created and restored on a disposable database.

## Automated Gate

Copy `deploy/env.staging.example` to the server-side `.env`, replace every placeholder, and run:

```bash
ENV_FILE=.env bash deploy/preflight.sh staging
ENV_FILE=.env bash deploy/deploy.sh staging <reviewed-tag-or-commit>
docker compose ps
```

The preflight validates the environment without printing secrets, checks certificate lifetime,
hostname and key matching, validates the Compose model, checks Docker, and enforces a free-disk
floor. Deployment creates a verified database backup, applies migrations, starts services,
configures the Telegram webhook, runs public smoke tests, and writes the server-side release
manifest before image construction.

The public smoke test verifies the versioned health, readiness and metrics endpoints, required
OpenAPI paths, admin security headers, and the webhook URL returned by Telegram. It does not send
messages, create payments, or publish a video.

## Manual Acceptance Scenarios

Record the UTC start/end time, release commit, operator, test account identifiers, and sanitized
result for every scenario. Never attach tokens, signatures, passwords, payment credentials, or raw
OAuth payloads.

| ID | Scenario | Expected result |
| --- | --- | --- |
| `QA-REG-001` | New user runs `/start` and accepts terms | User and active FREE subscription are created once |
| `QA-OAUTH-001` | User connects TikTok through OAuth 2.0 | Account metadata is stored and tokens are encrypted |
| `QA-LIMIT-001` | FREE user submits within and beyond the daily limit | Two accepted posts are allowed; the next request is rejected |
| `QA-PAY-001` | User pays for PRO through Robokassa test mode | ResultURL activates one 30-day subscription idempotently |
| `QA-PAY-002` | ResultURL is delivered twice | Payment and subscription are not duplicated |
| `QA-UPL-001` | User submits a supported test video | Job reaches TikTok through the official API and receives a final status |
| `QA-UPL-002` | Worker experiences a controlled temporary failure | Retry is bounded and the usage counter is not charged twice |
| `QA-EXP-001` | A paid subscription is expired in staging data | Scheduler returns the user to FREE and preserves history |
| `QA-ADM-001` | Administrator reviews users, payments, jobs, settings and audit | RBAC applies and changing actions appear in the audit log |
| `QA-DR-001` | Backup is restored into a disposable database | Schema and critical record counts match the source backup |

## Evidence Package

Store sanitized evidence in the release record or pull request:

- release tag and full Git SHA;
- release-candidate manifest filename and aggregate source-tree SHA-256;
- GitHub Actions run URL;
- preflight and smoke-test pass timestamps;
- Docker image tag and `docker compose ps` status;
- Alembic current revision;
- backup filename, checksum, and restore-test result;
- the table of manual scenario results;
- approved exceptions with owner and expiry date.

## Exit Decision

Staging is accepted only when all automated checks and critical manual scenarios pass, no P1/P2
defect remains open, and the rollback target is known. Production credentials must be separate,
Robokassa test mode must be disabled, and the production launch still requires an explicit owner
decision. The accepted prerelease must be promoted to a stable SemVer and pass CI again before
production deployment.
