# Architecture Summary

Terminology and naming rules are defined in [Glossary and Naming Conventions](glossary-naming.md).

The consolidated component overview is maintained in [Project Component Map](component-map.md).

Non-functional requirements are defined in [Non-Functional Requirements](non-functional-requirements.md).

## Core Principles

- Use only the official TikTok Content Posting API.
- Use OAuth 2.0 for TikTok account authorization.
- Keep the backend asynchronous with FastAPI and aiogram 3.x.
- Preserve the modular repository structure.
- Use Docker and Docker Compose as the primary deployment mechanism.
- Store runtime configuration in `.env` and database-backed system settings.
- Keep secrets out of Git.
- Use strict typing, automated tests, and CI checks.
- Treat all previous specification sections as mandatory project requirements.

## Key Subsystems

| Subsystem | Responsibility |
| --- | --- |
| Telegram bot | User registration, FSM flows, upload intake, tariff display, notifications |
| FastAPI backend | OAuth callbacks, webhooks, payments, admin API, health, readiness, metrics |
| PostgreSQL | Users, plans, subscriptions, payments, upload jobs, audit data, settings |
| Redis | Cache, locks, queue coordination, OAuth state, rate limiting |
| Worker | Video validation, preparation, publication workflow, cleanup, background jobs |
| Robokassa | Paid PRO and BUSINESS subscription payments |
| TikTok OAuth 2.0 | User authorization for official TikTok API access |
| TikTok Content Posting API | Official publication workflow |
| Admin API | Users, subscriptions, payments, plans, jobs, analytics, settings |
| Monitoring and logging | Health checks, readiness checks, metrics, JSON logs, audit trail |

Main component interaction flows are documented in [Sequence Flows](sequence-flows.md).

## Functional Commitments

- FREE, PRO, and BUSINESS tariffs are supported.
- FREE is assigned automatically to new users.
- Paid subscriptions expire automatically and return users to FREE.
- Daily upload limits are enforced transactionally.
- Video files are validated safely before publication processing.
- Payments are processed idempotently through Robokassa ResultURL.
- Background jobs are idempotent and safe to retry only for temporary failures.
- OAuth tokens are stored encrypted.
- User, payment, publication, webhook, and admin actions are logged.
- Public API compatibility is preserved within `/api/v1`.
- Data validation and persistence must follow [Data Quality and Integrity](data-quality-integrity.md).
- REST API format and compatibility must follow [REST API Standards](rest-api-standards.md).
- Entity relationships must follow [Logical Data Model](data-model.md).

## Compliance Boundary

The project must not implement:

- VPN or proxy automation.
- Geolocation masking.
- Browser automation for TikTok publishing.
- Unofficial TikTok APIs.
- Credential scraping or password-based TikTok login.
- Attempts to bypass TikTok account, API, or regional restrictions.

If TikTok returns an authorization, permission, regional, account, or policy restriction, the system must report the issue to the user and stop automatic publication attempts for that job.

## Quality Requirements

- Non-functional requirements must be checked before production release.
- Database changes use Alembic migrations.
- New features include tests and documentation.
- CI runs linting, typing, tests, migration checks, Docker build, and secret scanning.
- Production releases require staging verification and rollback readiness.
- Monitoring, logs, and KPI must support operational decisions.
- Observability must follow [Observability and Diagnostics](observability-diagnostics.md).
- Data quality controls must follow [Data Quality and Integrity](data-quality-integrity.md).

## Final Rule

Future development must preserve architectural integrity, security, scalability, and maintainability while staying within the official TikTok API model.

Future change acceptance must follow [Change Acceptance Policy](change-acceptance-policy.md).
