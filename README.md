# Tik-Tok Bot Rus 2

Telegram bot for preparing and submitting videos to a user's TikTok account through the official TikTok Content Posting API after OAuth 2.0 authorization.

Important: this project does not implement VPN, proxy routing, device spoofing, account farming, geolocation masking, or any other mechanism intended to bypass TikTok regional restrictions. TikTok publishing is designed only through the official TikTok Content Posting API after app review, user OAuth authorization, and approval for the required scopes.

## Tariffs

| Plan | Price, RUB | Price, Telegram Stars | Daily video limit |
| --- | ---: | ---: | ---: |
| FREE | 0 | - | 2 |
| PRO | 499 | 199 XTR | 5 |
| BUSINESS | 999 | 499 XTR | 10 |

## What Is Included

- Telegram bot built with aiogram.
- FastAPI backend for provider webhooks and TikTok OAuth callbacks.
- User plans and daily upload limits.
- Telegram Stars invoices with transactional and idempotent subscription activation.
- Robokassa callback support reserved for separately approved external channels.
- PostgreSQL 16 database.
- Redis queues and cache.
- Dedicated scheduler for subscription expiry, OAuth refresh, and retention cleanup.
- One-shot Alembic migration gate before application services start.
- Responsive administrative console with RBAC, analytics, audit, and safe queue controls.
- Video intake from Telegram and local storage.
- Official TikTok Content Posting API client scaffold.
- Docker Compose setup for deployment on a VPS.
- Reproducible CI, verified backup/restore, release, rollback, and HTTPS automation.
- Systemd unit template and deployment checklist.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Open Telegram, start your bot, and use:

- `/start` to see the menu.
- `/tariffs` to view available plans.
- `/status` to check the current plan and daily limit.
- `/connect` to connect a TikTok account through official OAuth 2.0.
- `/upload` to start the video publication workflow.
- `/terms` to review the user agreement.
- `/paysupport` for payment support.
- `/help` to open the bot guide.

## Required Environment

See [.env.example](.env.example).

For production, configure:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `ROBOKASSA_MERCHANT_LOGIN`
- `ROBOKASSA_PASSWORD_1`
- `ROBOKASSA_PASSWORD_2`
- `PUBLIC_BASE_URL`
- TikTok developer credentials after app approval

Paid-plan prices are `199 XTR` for PRO and `499 XTR` for BUSINESS. They are stored in PostgreSQL and
remain manageable through the administrator panel.

## TikTok Publishing

TikTok publishing requires:

1. A registered TikTok developer app.
2. Content Posting API enabled.
3. Approved `video.publish` scope.
4. User OAuth authorization.
5. App audit before public visibility restrictions are lifted.

Before confirmation, the bot queries current creator information, requires a manual privacy
choice, lets the user configure the interaction options TikTok currently allows, and asks for
commercial-content disclosure. Production publication remains disabled until the TikTok app and
`video.publish` scope are approved.

Until those requirements are met, production publication remains disabled. A queued task stops
with a clear user-facing error and does not attempt an unofficial fallback or bypass.

## Scheduled Maintenance

The `scheduler` container uses Redis leases to enqueue periodic tasks exactly once per configured
window. It expires PRO/BUSINESS subscriptions and returns users to FREE, refreshes TikTok OAuth
tokens before expiration, and runs retention cleanup. Docker monitors its Redis heartbeat.

## Administrative Console

FastAPI serves the operational console at `/admin-ui/` and its versioned API at
`/api/v1/admin`. Access requires a configured administrator Telegram ID, API token, and CSRF
token. Credentials are held only in browser memory, and TikTok OAuth tokens are never returned to
the UI.

## Documentation

- [Changelog](CHANGELOG.md)
- [Unified Specification - Markdown](docs/final/Tik_Tok_Loader_Unified_Specification.md)
- [Unified Specification - DOCX](docs/final/Tik_Tok_Loader_Unified_Specification.docx)
- [Unified Specification - PDF](docs/final/Tik_Tok_Loader_Unified_Specification.pdf)
- [Specification Index](docs/specification-index.md)
- [Implementation Roadmap](docs/implementation-roadmap.md)
- [Architecture Summary](docs/architecture-summary.md)
- [Project Component Map](docs/component-map.md)
- [Deployment](docs/deployment.md)
- [CI/CD and Deployment Automation](docs/ci-cd-deployment.md)
- [Compliance Notes](docs/compliance.md)
- [Robokassa Setup](docs/robokassa.md)
- [Telegram Stars](docs/telegram-stars.md)
- [Security, Backup, and Monitoring](docs/security.md)
- [Security Logging and Audit](docs/security-logging-audit.md)
- [Confidential Data Policy](docs/confidential-data-policy.md)
- [Administrator Guide](docs/admin.md)
- [API Documentation](docs/api.md)
- [User Guide](docs/user-guide.md)
- [Maintenance Guide](docs/maintenance.md)
- [Configuration](docs/configuration.md)
- [Environment Configuration and Secrets Control](docs/environment-configuration-secrets.md)
- [Incident Response](docs/incident-response.md)
- [Incident Management](docs/incident-management.md)
- [Development Standards](docs/development.md)
- [Technical Debt Management](docs/technical-debt-management.md)
- [Non-Functional Requirements](docs/non-functional-requirements.md)
- [Performance and Scaling](docs/performance.md)
- [Data Retention](docs/data-retention.md)
- [Video Lifecycle](docs/video-lifecycle.md)
- [Release Management](docs/release.md)
- [Release Candidate Manifest](docs/release-candidate.md)
- [Containerization](docs/containerization.md)
- [Operations Runbook](docs/operations-runbook.md)
- [Configuration Management](docs/configuration-management.md)
- [Acceptance Checklist](docs/acceptance-checklist.md)
- [Risk Management](docs/risk-management.md)
- [GitHub Workflow](docs/github-workflow.md)
- [SOP Checklists](docs/sop-checklists.md)
- [Production Launch](docs/production-launch.md)
- [Staging Acceptance Runbook](docs/staging-acceptance-runbook.md)
- [Post-Launch Maintenance and Versioning](docs/post-launch-maintenance.md)
- [Dependencies and Third-Party Services](docs/dependencies-and-integrations.md)
- [License and Third-Party Component Management](docs/license-third-party-management.md)
- [Infrastructure Dependency Management](docs/infrastructure-dependency-management.md)
- [Feature Development Plan](docs/feature-development-plan.md)
- [Metrics and KPI](docs/metrics-and-kpi.md)
- [Observability and Diagnostics](docs/observability-diagnostics.md)
- [Queue and Retry Policy](docs/queue-retry-policy.md)
- [File Storage Policy](docs/file-storage-policy.md)
- [TikTok Developer Configuration](docs/tiktok-developer-configuration.md)
- [Data Quality and Integrity](docs/data-quality-integrity.md)
- [Migration and Version Compatibility Plan](docs/migration-compatibility-plan.md)
- [Backup and Restore Policy](docs/backup-restore-policy.md)
- [Capacity and Performance Management](docs/capacity-management.md)
- [Service Continuity Plan](docs/service-continuity-plan.md)
- [Change Acceptance Policy](docs/change-acceptance-policy.md)
- [Error Codes and Exception Handling](docs/error-handling.md)
- [REST API Standards](docs/rest-api-standards.md)
- [API Versioning and Client Compatibility](docs/api-versioning-compatibility.md)
- [Logical Data Model](docs/data-model.md)
- [Users Entity](docs/users-entity.md)
- [TikTok Accounts Entity](docs/tiktok-accounts-entity.md)
- [Subscriptions Entity](docs/subscriptions-entity.md)
- [Payments Entity](docs/payments-entity.md)
- [Upload Jobs Entity](docs/upload-jobs-entity.md)
- [Daily Usage Entity](docs/daily-usage-entity.md)
- [Webhook Events Entity](docs/webhook-events-entity.md)
- [Admin Actions Entity](docs/admin-actions-entity.md)
- [System Settings Entity](docs/system-settings-entity.md)
- [Administrative REST API](docs/admin-rest-api.md)
- [Public REST API](docs/public-rest-api.md)
- [OpenAPI and Contract Documentation](docs/openapi-contracts.md)
- [Sequence Flows](docs/sequence-flows.md)
- [Glossary and Naming Conventions](docs/glossary-naming.md)
- [QA Test Data and Acceptance Scenarios](docs/qa-acceptance-scenarios.md)
- [Test Strategy and Quality Gates](docs/test-strategy.md)
- [Requirements Traceability Matrix](docs/requirements-traceability.md)
