# Non-Functional Requirements

This document defines the non-functional requirements for Tik_Tok_Loader. These requirements apply to every component described in [Project Component Map](component-map.md) and must be checked together with functional acceptance criteria before release.

## Performance

| Requirement | Implementation Direction |
| --- | --- |
| Asynchronous processing | Keep FastAPI, aiogram handlers, database access, Redis operations, and external integrations asynchronous where supported. |
| Queues for long-running tasks | Process video validation, preparation, TikTok publication, cleanup, token refresh, payment reconciliation, and subscription expiry in workers. |
| API response time control | Monitor API response time through metrics and logs, and investigate threshold breaches during operations. |
| Minimal blocking | Avoid blocking I/O in request handlers and bot handlers; move heavy work to background jobs. |

Performance controls are detailed in [Performance and Scaling](performance.md), [Capacity and Performance Management](capacity-management.md), and [Metrics and KPI](metrics-and-kpi.md).

## Reliability

| Requirement | Implementation Direction |
| --- | --- |
| Idempotency | Keep webhook handling, payment confirmation, upload-job processing, retries, and daily-limit accounting safe for repeated execution. |
| Health checks | Expose and monitor liveness, readiness, and metrics endpoints. |
| Backups | Back up PostgreSQL, production configuration, deployment files, and critical documentation according to the retention policy. |
| Safe recovery | Validate restore procedures in staging and preserve payment, subscription, user, and upload history during recovery. |

Reliability controls are detailed in [Queue and Retry Policy](queue-retry-policy.md), [Backup and Restore Policy](backup-restore-policy.md), [Service Continuity Plan](service-continuity-plan.md), and [Incident Management](incident-management.md).

## Security

| Requirement | Implementation Direction |
| --- | --- |
| Secrets only in `.env` | Keep Telegram, TikTok, Robokassa, database, Redis, and encryption secrets out of Git and application code. |
| Token encryption | Encrypt TikTok OAuth access and refresh tokens before storing them in PostgreSQL. |
| Webhook verification | Verify TikTok and Robokassa webhook signatures before changing business state. |
| RBAC | Enforce server-side roles and permissions for administrative operations. |

Security controls are detailed in [Security, Backup, and Monitoring](security.md), [TikTok Accounts Entity](tiktok-accounts-entity.md), [Webhook Events Entity](webhook-events-entity.md), and [Administrative REST API](admin-rest-api.md).

Security logging and audit controls are detailed in [Security Logging and Audit](security-logging-audit.md).

Confidential data controls are detailed in [Confidential Data Policy](confidential-data-policy.md).

## Maintainability

| Requirement | Implementation Direction |
| --- | --- |
| Modular architecture | Keep bot, API, services, database, workers, security, and deployment code separated by responsibility. |
| Documentation | Update documentation together with code, API, schema, configuration, and operational changes. |
| Tests | Cover new behavior with unit, integration, FSM, Robokassa, TikTok mock, and queue-related tests where relevant. |
| Alembic | Apply all schema changes through Alembic migrations. |

Maintainability controls are detailed in [Development Standards](development.md), [Migration and Version Compatibility Plan](migration-compatibility-plan.md), [OpenAPI and Contract Documentation](openapi-contracts.md), and [Requirements Traceability Matrix](requirements-traceability.md).

## Scalability

| Requirement | Implementation Direction |
| --- | --- |
| Horizontal API scaling | Support multiple FastAPI instances behind Nginx or another load balancer. |
| Horizontal worker scaling | Support multiple worker processes with Redis-backed coordination and idempotent task handling. |
| Extensible functionality | Add features through existing service boundaries, documented APIs, migrations, tests, and documentation updates. |

Scalability controls are detailed in [Performance and Scaling](performance.md), [Capacity and Performance Management](capacity-management.md), and [Feature Development Plan](feature-development-plan.md).

## Acceptance Rule

A release is not production-ready until non-functional requirements are checked together with functional flows, security controls, operational readiness, and traceability coverage.
