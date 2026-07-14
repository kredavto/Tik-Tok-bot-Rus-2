# Test Strategy and Quality Gates

This document defines the automated test layers, release evidence, and staging checks for
Tik_Tok_Loader. Detailed business scenarios are maintained in
[QA Test Data and Acceptance Scenarios](qa-acceptance-scenarios.md).

## Test Layers

| Layer | Scope | Primary Evidence |
| --- | --- | --- |
| Unit | Plans, RBAC, configuration, signatures, encryption, status transitions, localization | `tests/test_plans.py`, `tests/test_rbac.py`, `tests/test_configuration.py`, `tests/test_security_crypto.py` |
| Bot FSM | Description, hashtags, creator constraints, privacy, commercial content, cancellation | `tests/test_bot_fsm.py` |
| API and contracts | Health, tracing headers, safe errors, OAuth state validation, webhook rejection, OpenAPI paths | `tests/test_api_integration.py`, `tools/check_openapi.py` |
| Video and TikTok client | File signatures, duration, cleanup, chunk planning, retries, creator info, webhook HMAC | `tests/test_video_service.py`, `tests/test_tiktok_service.py` |
| Queue resilience | Distributed job lock and scheduler lease idempotency | `tests/test_worker_resilience.py`, `tests/test_scheduler.py` |
| PostgreSQL integration | Registration, plans, daily limits, payment confirmation, subscription expiry, upload event history | `tests/test_subscriptions.py`, `tests/test_robokassa.py`, `tests/test_upload_lifecycle_integration.py` |
| Migration | Upgrade, schema drift check, downgrade to base, and clean re-upgrade | GitHub Actions `Migrations and tests` job |
| Container | Compose model, image build, and non-root runtime | GitHub Actions `Container build` job |
| Staging acceptance | Real Telegram webhook, approved TikTok application, Robokassa test mode, HTTPS, backup and restore | Signed release checklist and staging run record |

## Local Quality Commands

Run static checks and infrastructure-free tests:

```bash
ruff format --check .
ruff check .
mypy app
python tools/check_openapi.py
python tools/check_secrets.py
pytest --cov=app --cov-report=term-missing --cov-fail-under=45
```

The full `pytest` command requires PostgreSQL and may require Redis. GitHub Actions provides
PostgreSQL 16, Redis, FFmpeg, an isolated encryption key, and a migrated disposable database.

## Coverage Policy

CI enforces a project-wide line coverage floor of 45%. The floor is a regression guard, not a
completion target. New or changed business logic must include focused tests, and critical payment,
quota, OAuth, webhook, and queue paths require behavioral assertions even when aggregate coverage
already passes.

Coverage XML is generated in CI for later publication or quality-platform integration.

## Concurrency and Idempotency

Automated PostgreSQL tests verify these invariants:

- Concurrent Telegram registration creates one user and one active FREE subscription.
- Concurrent first-use quota checks create one daily usage row.
- Duplicate Robokassa confirmation activates a paid subscription exactly once.
- A paid ResultURL with malformed or mismatched amount cannot activate a subscription.
- Upload status history contains every accepted transition and terminal jobs cannot be reopened.
- Redis leases prevent duplicate scheduler dispatch and upload worker execution.

## External-Service Boundary

Unit and integration tests mock TikTok HTTP responses and validate only the official OAuth 2.0 and
Content Posting API contract implemented by this project. They do not prove that a TikTok
application has been approved or that a specific account or region is eligible to publish.

Robokassa production activation requires a real ResultURL round trip against the configured store.
SuccessURL is informational and is never acceptance evidence.

## Release Evidence

A release candidate requires:

- Successful GitHub Actions quality, integration, migration, and container jobs.
- Current requirement-to-test links in the traceability matrix.
- Staging execution of scenarios that depend on Telegram, TikTok, Robokassa, HTTPS, or recovery.
- No unresolved critical security findings.
- A backup and restore record before production deployment.

Passing automated tests does not by itself authorize production launch.
