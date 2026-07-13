# Tik_Tok_Loader. Единая техническая спецификация

**Unified Technical Specification**

- **Версия:** 0.2.0
- **Репозиторий:** `kredavto/Tik-Tok-bot-Rus-2`
- **Дата сборки:** 2026-07-13
- **Статус:** проектная спецификация для реализации

> Публикация TikTok в проекте проектируется только через официальный TikTok Content Posting API и OAuth 2.0. Неофициальные API, автоматизация интерфейса и методы обхода ограничений не входят в допустимую архитектуру.

## Оглавление

- [1. Compliance Notes](#1-compliance-notes)
- [2. Architecture Summary](#2-architecture-summary)
- [3. Project Component Map](#3-project-component-map)
- [4. Sequence Flows](#4-sequence-flows)
- [5. Implementation Roadmap](#5-implementation-roadmap)
- [6. Non-Functional Requirements](#6-non-functional-requirements)
- [7. Logical Data Model](#7-logical-data-model)
- [8. Users Entity](#8-users-entity)
- [9. TikTok Accounts Entity](#9-tiktok-accounts-entity)
- [10. Subscriptions Entity](#10-subscriptions-entity)
- [11. Payments Entity](#11-payments-entity)
- [12. Upload Jobs Entity](#12-upload-jobs-entity)
- [13. Daily Usage Entity](#13-daily-usage-entity)
- [14. Webhook Events Entity](#14-webhook-events-entity)
- [15. Admin Actions Entity](#15-admin-actions-entity)
- [16. System Settings Entity](#16-system-settings-entity)
- [17. User Guide](#17-user-guide)
- [18. Video Publication Lifecycle](#18-video-publication-lifecycle)
- [19. TikTok Developer Configuration](#19-tiktok-developer-configuration)
- [20. Robokassa Setup](#20-robokassa-setup)
- [21. API Documentation](#21-api-documentation)
- [22. REST API Standards](#22-rest-api-standards)
- [23. API Versioning and Client Compatibility](#23-api-versioning-and-client-compatibility)
- [24. Public REST API](#24-public-rest-api)
- [25. Administrative REST API](#25-administrative-rest-api)
- [26. OpenAPI and Contract Documentation](#26-openapi-and-contract-documentation)
- [27. Error Codes and Exception Handling](#27-error-codes-and-exception-handling)
- [28. Security, Backup, and Monitoring](#28-security-backup-and-monitoring)
- [29. Security Logging and Audit](#29-security-logging-and-audit)
- [30. Confidential Data Policy](#30-confidential-data-policy)
- [31. Environment Configuration and Secrets Control](#31-environment-configuration-and-secrets-control)
- [32. Configuration](#32-configuration)
- [33. Configuration Management](#33-configuration-management)
- [34. Deployment](#34-deployment)
- [35. Containerization](#35-containerization)
- [36. Production Launch Plan](#36-production-launch-plan)
- [37. Operations Runbook](#37-operations-runbook)
- [38. SOP Checklists](#38-sop-checklists)
- [39. Maintenance Guide](#39-maintenance-guide)
- [40. Post-Launch Maintenance and Versioning](#40-post-launch-maintenance-and-versioning)
- [41. Incident Response and Disaster Recovery](#41-incident-response-and-disaster-recovery)
- [42. Incident Management](#42-incident-management)
- [43. Backup and Restore Policy](#43-backup-and-restore-policy)
- [44. Service Continuity Plan](#44-service-continuity-plan)
- [45. Data Retention](#45-data-retention)
- [46. File Storage Policy](#46-file-storage-policy)
- [47. Queue and Retry Policy](#47-queue-and-retry-policy)
- [48. Performance and Scaling](#48-performance-and-scaling)
- [49. Capacity and Performance Management](#49-capacity-and-performance-management)
- [50. Metrics and KPI](#50-metrics-and-kpi)
- [51. Observability and Diagnostics](#51-observability-and-diagnostics)
- [52. Development Standards](#52-development-standards)
- [53. GitHub Workflow](#53-github-workflow)
- [54. Feature Development Plan](#54-feature-development-plan)
- [55. Technical Debt Management](#55-technical-debt-management)
- [56. Dependencies and Third-Party Services](#56-dependencies-and-third-party-services)
- [57. Infrastructure Dependency Management](#57-infrastructure-dependency-management)
- [58. License and Third-Party Component Management](#58-license-and-third-party-component-management)
- [59. Migration and Version Compatibility Plan](#59-migration-and-version-compatibility-plan)
- [60. Release Management](#60-release-management)
- [61. Change Acceptance Policy](#61-change-acceptance-policy)
- [62. QA Test Data and Acceptance Scenarios](#62-qa-test-data-and-acceptance-scenarios)
- [63. Acceptance Checklist](#63-acceptance-checklist)
- [64. Requirements Traceability Matrix](#64-requirements-traceability-matrix)
- [65. Glossary and Naming Conventions](#65-glossary-and-naming-conventions)
- [66. Specification Index](#66-specification-index)
- [67. Risk Management](#67-risk-management)

## Список сокращений и терминов

| Сокращение / термин | Описание |
| --- | --- |
| API | Application Programming Interface, программный интерфейс приложения |
| CI/CD | Continuous Integration / Continuous Delivery |
| CSRF | Cross-Site Request Forgery |
| FSM | Finite State Machine, конечный автомат сценариев Telegram-бота |
| JSON | JavaScript Object Notation |
| KPI | Key Performance Indicator |
| NFR | Non-Functional Requirements, нефункциональные требования |
| OAuth 2.0 | Протокол авторизации для подключения аккаунта TikTok |
| RBAC | Role-Based Access Control, ролевая модель доступа |
| REST | Representational State Transfer |
| SOP | Standard Operating Procedure, стандартная операционная процедура |
| TLS/SSL | Криптографическая защита транспортного соединения |
| UTC | Coordinated Universal Time |


# 1. Compliance Notes

Группа спецификации: Общие положения


The compliance boundary is summarized in [Architecture Summary](architecture-summary.md).

## 1.1. Regional Restrictions

TikTok suspended live streaming and new uploads in Russia in March 2022 while it reviewed the legal implications of Russia's "fake news" law. Public reporting has also described Russia-specific content availability differences after that decision.

This project must not include:

- VPN or proxy automation.
- Geolocation spoofing.
- Device fingerprint spoofing.
- Captcha or anti-bot bypasses.
- Shared account pools.
- Credential collection for direct TikTok password login.
- Attempts to evade TikTok account, API, or regional policies.

## 1.2. Supported Publishing Model

The supported model is the official TikTok Content Posting API:

- A TikTok developer app is registered.
- The app requests and receives approval for `video.publish`.
- Each creator authorizes the app through OAuth.
- The app follows TikTok review and audit requirements.
- The bot respects API errors, account restrictions, privacy settings, and rate limits.

If the official API is unavailable for a specific user or region, the bot should keep the upload as a queued draft and tell the user that publication cannot be completed automatically.

TikTok Developer Portal setup must follow [TikTok Developer Configuration](tiktok-developer-configuration.md).

# 2. Architecture Summary

Группа спецификации: Архитектура


Terminology and naming rules are defined in [Glossary and Naming Conventions](glossary-naming.md).

The consolidated component overview is maintained in [Project Component Map](component-map.md).

Non-functional requirements are defined in [Non-Functional Requirements](non-functional-requirements.md).

## 2.1. Core Principles

- Use only the official TikTok Content Posting API.
- Use OAuth 2.0 for TikTok account authorization.
- Keep the backend asynchronous with FastAPI and aiogram 3.x.
- Preserve the modular repository structure.
- Use Docker and Docker Compose as the primary deployment mechanism.
- Store runtime configuration in `.env` and database-backed system settings.
- Keep secrets out of Git.
- Use strict typing, automated tests, and CI checks.
- Treat all previous specification sections as mandatory project requirements.

## 2.2. Key Subsystems

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

## 2.3. Functional Commitments

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

## 2.4. Compliance Boundary

The project must not implement:

- VPN or proxy automation.
- Geolocation masking.
- Browser automation for TikTok publishing.
- Unofficial TikTok APIs.
- Credential scraping or password-based TikTok login.
- Attempts to bypass TikTok account, API, or regional restrictions.

If TikTok returns an authorization, permission, regional, account, or policy restriction, the system must report the issue to the user and stop automatic publication attempts for that job.

## 2.5. Quality Requirements

- Non-functional requirements must be checked before production release.
- Database changes use Alembic migrations.
- New features include tests and documentation.
- CI runs linting, typing, tests, migration checks, Docker build, and secret scanning.
- Production releases require staging verification and rollback readiness.
- Monitoring, logs, and KPI must support operational decisions.
- Observability must follow [Observability and Diagnostics](observability-diagnostics.md).
- Data quality controls must follow [Data Quality and Integrity](data-quality-integrity.md).

## 2.6. Final Rule

Future development must preserve architectural integrity, security, scalability, and maintainability while staying within the official TikTok API model.

Future change acceptance must follow [Change Acceptance Policy](change-acceptance-policy.md).

# 3. Project Component Map

Группа спецификации: Архитектура


This document is the high-level navigation map for Tik_Tok_Loader components. It gives developers a single overview of the system boundaries, data flows, and final architecture principles.

## 3.1. Main Components

| Component | Purpose |
| --- | --- |
| Telegram Bot | User interface, registration, FSM flows, uploads, tariffs, settings, and notifications. |
| FastAPI | REST API, TikTok OAuth, webhooks, Robokassa callbacks, business services, health checks, and metrics. |
| PostgreSQL | Primary data store for users, TikTok accounts, subscriptions, payments, upload jobs, usage counters, webhook events, audit logs, and settings. |
| Redis | Queue coordination, cache, rate limiting, OAuth state storage, and distributed locks. |
| Worker | Background processing for video validation, preparation, publication, status checks, cleanup, subscription expiry, and retries. |
| TikTok API | Official OAuth 2.0 authorization and Content Posting API video publication. |
| Robokassa | Payment acceptance for PRO and BUSINESS subscriptions through the existing merchant account. |
| Admin Panel | Administrative management, analytics, audit review, settings, users, payments, and upload queues. |

## 3.2. Interaction Flows

```mermaid
flowchart LR
    User["User"] --> Bot["Telegram Bot"]
    Bot --> API["FastAPI"]
    API --> DB["PostgreSQL"]
    API --> Redis["Redis"]
    Redis --> Worker["Worker"]
    Worker --> TikTok["TikTok Content Posting API"]
    Robokassa["Robokassa"] --> ResultURL["ResultURL"]
    ResultURL --> API
    API --> Bot
    Bot --> User
```

Canonical service flows are:

- User -> Telegram Bot -> FastAPI.
- FastAPI -> PostgreSQL / Redis.
- Worker -> official TikTok Content Posting API.
- Robokassa -> ResultURL -> FastAPI.
- FastAPI -> Telegram Bot -> User.

Detailed publication and payment sequences are documented in [Sequence Flows](sequence-flows.md).

## 3.3. Architecture Principles

- Modularity.
- Asynchronous processing.
- Security by default.
- Idempotent critical operations.
- Scalable API and worker boundaries.
- Complete and current documentation.
- Official TikTok APIs only.
- Automated tests for release readiness.

## 3.4. Final Guidance

All specification sections form one technical requirement set for Tik_Tok_Loader. Future changes must preserve the architecture described in [Architecture Summary](architecture-summary.md), remain inside the official TikTok API model, include relevant automated tests, and update documentation together with implementation changes.

# 4. Sequence Flows

Группа спецификации: Архитектура


The high-level component map is documented in [Project Component Map](component-map.md).

## 4.1. Video Publication Flow

```mermaid
sequenceDiagram
    participant User
    participant Bot as Telegram Bot
    participant API as FastAPI Backend
    participant DB as PostgreSQL
    participant Queue as Redis Queue
    participant Worker
    participant TikTok as Official TikTok API

    User->>Bot: Send video
    Bot->>API: Check subscription and daily limit
    API->>DB: Read user, subscription, daily_usage
    API-->>Bot: Limit check result
    Bot->>API: Create upload job
    API->>DB: Store upload_jobs and upload_job_events
    API->>Queue: Enqueue processing task
    Queue-->>Worker: Deliver task
    Worker->>DB: Mark VALIDATING/PREPARING
    Worker->>TikTok: Submit through official Content Posting API
    TikTok-->>Worker: Accepted/status/error
    Worker->>DB: Store status and lifecycle event
    Worker->>Bot: Notify user
    Bot-->>User: Publication result
```

Rules:

- Use Request ID and Correlation ID across bot, API, worker, and logs.
- Create `upload_jobs` before enqueueing processing.
- Record every status transition.
- Retry only temporary failures.
- Consume daily usage only after official TikTok API acceptance.
- Do not retry automatically for authorization, permission, platform, or regional restrictions.

## 4.2. Payment Flow

```mermaid
sequenceDiagram
    participant User
    participant Bot as Telegram Bot
    participant API as FastAPI Backend
    participant DB as PostgreSQL
    participant Robo as Robokassa

    User->>Bot: Select PRO or BUSINESS
    Bot->>API: Create payment order
    API->>DB: Store payment with InvId
    API-->>Bot: Return payment URL
    Bot-->>User: Send payment URL
    User->>Robo: Pay invoice
    Robo->>API: ResultURL notification
    API->>API: Verify signature, amount, currency, InvId
    API->>DB: Mark payment paid and activate subscription
    API-->>Robo: OK{InvId}
    API->>Bot: Notify subscription activated
    Bot-->>User: Payment success message
```

Rules:

- FREE does not create a payment.
- Only ResultURL activates subscriptions.
- SuccessURL is informational.
- Repeated ResultURL events are idempotent.
- Payment status and subscription activation must be transactional.
- Never log Robokassa secrets.

## 4.3. Cross-Cutting Requirements

- All service-to-service operations must be logged with sanitized context.
- Use UTC timestamps in logs and database events.
- Use correlation IDs for linked operations.
- Persist webhook events before processing.
- Keep retries idempotent.
- Follow [Queue and Retry Policy](queue-retry-policy.md), [Observability and Diagnostics](observability-diagnostics.md), and [Error Codes and Exception Handling](error-handling.md).

# 5. Implementation Roadmap

Группа спецификации: Управление реализацией


This document is the final implementation roadmap for Tik_Tok_Loader. It can be used as a development checklist from initial setup to production launch.

## 5.1. Roadmap Stages

| Stage | Goal | Completion Check |
| --- | --- | --- |
| 1. Infrastructure and repository preparation | Prepare repository, Docker layout, environment templates, CI skeleton, and deployment structure. | Repository structure, Docker Compose, `.env.example`, CI, and documentation entry points are present. |
| 2. Core architecture and database | Implement modular application layout, PostgreSQL schema, SQLAlchemy models, Alembic migrations, settings, logging, and Redis connectivity. | Migrations apply, database entities match documentation, health/readiness checks work. |
| 3. Telegram bot | Implement aiogram bot, FSM flows, menu, localization, keyboards, user registration, FREE assignment, plan display, and upload intake. | Bot scenarios pass tests and match FSM documentation. |
| 4. TikTok Content Posting API | Implement official OAuth 2.0 flow, encrypted token storage, token refresh, official publication client, webhook handling, and error reporting. | OAuth and mocked TikTok API tests pass; no unofficial API or bypass behavior exists. |
| 5. Robokassa integration | Implement payment creation, signature verification, ResultURL processing, idempotency, subscription activation, and payment audit. | PRO/BUSINESS payment scenarios pass, SuccessURL does not activate subscriptions. |
| 6. Workers and video processing | Implement queueing, FFprobe validation, safe FFmpeg preparation, TikTok submission jobs, cleanup, retries, and daily-limit accounting. | Upload lifecycle and queue recovery scenarios pass. |
| 7. Admin panel and analytics | Implement administrative API/panel, RBAC, settings, users, payments, upload queue, audit logs, and metrics views. | Admin operations are authenticated, audited, tested, and documented. |
| 8. CI/CD and deployment automation | Complete CI checks, Docker builds, migration checks, secret scanning, deployment guides, backup scripts, and Nginx/HTTPS setup. | CI passes and staging deployment is reproducible. |
| 9. Comprehensive testing | Run unit, integration, FSM, Robokassa, TikTok mock, queue, migration, security, and acceptance checks. | Required tests pass and QA scenarios are documented as complete. |
| 10. Production preparation and launch | Prepare production `.env`, domain, HTTPS, webhooks, TikTok app settings, Robokassa URLs, backups, monitoring, and launch smoke tests. | Production launch checklist passes and project is ready for operation. |

## 5.2. Control Points

Before declaring the project ready:

- All mandatory tests pass.
- Documentation is current.
- Configuration is verified.
- Security checks are complete.
- Secrets are protected.
- Backups and restore procedure are tested.
- OpenAPI and API compatibility are current.
- Technical debt and dependency/license registers are reviewed.
- Production readiness is confirmed.

## 5.3. Final Rule

All previous specification sections are used together as one requirements base for implementation and maintenance. Any roadmap stage may be split into smaller tasks, but each task must preserve the architecture, security, official TikTok API boundary, tests, and documentation rules defined in the specification.

# 6. Non-Functional Requirements

Группа спецификации: Нефункциональные требования


This document defines the non-functional requirements for Tik_Tok_Loader. These requirements apply to every component described in [Project Component Map](component-map.md) and must be checked together with functional acceptance criteria before release.

## 6.1. Performance

| Requirement | Implementation Direction |
| --- | --- |
| Asynchronous processing | Keep FastAPI, aiogram handlers, database access, Redis operations, and external integrations asynchronous where supported. |
| Queues for long-running tasks | Process video validation, preparation, TikTok publication, cleanup, token refresh, payment reconciliation, and subscription expiry in workers. |
| API response time control | Monitor API response time through metrics and logs, and investigate threshold breaches during operations. |
| Minimal blocking | Avoid blocking I/O in request handlers and bot handlers; move heavy work to background jobs. |

Performance controls are detailed in [Performance and Scaling](performance.md), [Capacity and Performance Management](capacity-management.md), and [Metrics and KPI](metrics-and-kpi.md).

## 6.2. Reliability

| Requirement | Implementation Direction |
| --- | --- |
| Idempotency | Keep webhook handling, payment confirmation, upload-job processing, retries, and daily-limit accounting safe for repeated execution. |
| Health checks | Expose and monitor liveness, readiness, and metrics endpoints. |
| Backups | Back up PostgreSQL, production configuration, deployment files, and critical documentation according to the retention policy. |
| Safe recovery | Validate restore procedures in staging and preserve payment, subscription, user, and upload history during recovery. |

Reliability controls are detailed in [Queue and Retry Policy](queue-retry-policy.md), [Backup and Restore Policy](backup-restore-policy.md), [Service Continuity Plan](service-continuity-plan.md), and [Incident Management](incident-management.md).

## 6.3. Security

| Requirement | Implementation Direction |
| --- | --- |
| Secrets only in `.env` | Keep Telegram, TikTok, Robokassa, database, Redis, and encryption secrets out of Git and application code. |
| Token encryption | Encrypt TikTok OAuth access and refresh tokens before storing them in PostgreSQL. |
| Webhook verification | Verify TikTok and Robokassa webhook signatures before changing business state. |
| RBAC | Enforce server-side roles and permissions for administrative operations. |

Security controls are detailed in [Security, Backup, and Monitoring](security.md), [TikTok Accounts Entity](tiktok-accounts-entity.md), [Webhook Events Entity](webhook-events-entity.md), and [Administrative REST API](admin-rest-api.md).

Security logging and audit controls are detailed in [Security Logging and Audit](security-logging-audit.md).

Confidential data controls are detailed in [Confidential Data Policy](confidential-data-policy.md).

## 6.4. Maintainability

| Requirement | Implementation Direction |
| --- | --- |
| Modular architecture | Keep bot, API, services, database, workers, security, and deployment code separated by responsibility. |
| Documentation | Update documentation together with code, API, schema, configuration, and operational changes. |
| Tests | Cover new behavior with unit, integration, FSM, Robokassa, TikTok mock, and queue-related tests where relevant. |
| Alembic | Apply all schema changes through Alembic migrations. |

Maintainability controls are detailed in [Development Standards](development.md), [Migration and Version Compatibility Plan](migration-compatibility-plan.md), [OpenAPI and Contract Documentation](openapi-contracts.md), and [Requirements Traceability Matrix](requirements-traceability.md).

## 6.5. Scalability

| Requirement | Implementation Direction |
| --- | --- |
| Horizontal API scaling | Support multiple FastAPI instances behind Nginx or another load balancer. |
| Horizontal worker scaling | Support multiple worker processes with Redis-backed coordination and idempotent task handling. |
| Extensible functionality | Add features through existing service boundaries, documented APIs, migrations, tests, and documentation updates. |

Scalability controls are detailed in [Performance and Scaling](performance.md), [Capacity and Performance Management](capacity-management.md), and [Feature Development Plan](feature-development-plan.md).

## 6.6. Acceptance Rule

A release is not production-ready until non-functional requirements are checked together with functional flows, security controls, operational readiness, and traceability coverage.

# 7. Logical Data Model

Группа спецификации: Данные


Canonical entity names are defined in [Glossary and Naming Conventions](glossary-naming.md).

## 7.1. Core Entities

| Entity | Purpose |
| --- | --- |
| `users` | Telegram users and account-level settings |
| `tiktok_accounts` | Connected TikTok accounts and encrypted OAuth tokens |
| `plans` | FREE, PRO, and BUSINESS tariffs |
| `subscriptions` | Active and historical subscriptions |
| `payments` | Robokassa payment history |
| `upload_jobs` | Publication tasks and status |
| `upload_job_events` | Upload lifecycle audit trail |
| `daily_usage` | Daily upload limit counters |
| `webhook_events` | Received Telegram, TikTok, and Robokassa webhook events |
| `admin_actions` | Administrator audit log |
| `system_settings` | Runtime non-secret settings |

## 7.2. Main Relationships

| Relationship | Cardinality |
| --- | --- |
| `users` -> `subscriptions` | 1:N |
| `users` -> `payments` | 1:N |
| `users` -> `upload_jobs` | 1:N |
| `users` -> `tiktok_accounts` | 1:N |
| `users` -> `daily_usage` | 1:N |
| `plans` -> `subscriptions` | 1:N |
| `plans` -> `payments` | 1:N |
| `subscriptions` -> `payments` | 1:N |
| `upload_jobs` -> `upload_job_events` | 1:N |

`webhook_events` can reference external IDs from Telegram, TikTok, or Robokassa and should be correlated with payments, upload jobs, or users through payload metadata and diagnostic identifiers when applicable.

## 7.3. Integrity Rules

- Internal entities use UUID primary keys unless the domain requires a stable string identifier, such as `plans.id`.
- Foreign keys enforce core relationships.
- User deletion or anonymization must not break payment, subscription, publication, or audit history.
- TikTok OAuth tokens are encrypted before storage.
- Payment history is retained for accounting and audit.
- Daily usage counters are updated transactionally.
- Schema changes are applied only through Alembic migrations.
- All timestamps are UTC and timezone-aware.

## 7.4. Business Rules

- New users receive the FREE plan automatically.
- Paid subscriptions have a finite `ends_at` value.
- Expired paid subscriptions return users to FREE.
- Payments are activated only after Robokassa ResultURL validation.
- Daily usage is consumed only after official TikTok API acceptance.
- Upload lifecycle transitions are recorded in `upload_job_events`.

## 7.5. Development Requirement

Any new persistent entity must update this model, add an Alembic migration, include tests, and follow [Data Quality and Integrity](data-quality-integrity.md).

The user entity is specified in [Users Entity](users-entity.md).

The TikTok account entity is specified in [TikTok Accounts Entity](tiktok-accounts-entity.md).

The subscription entity is specified in [Subscriptions Entity](subscriptions-entity.md).

The payment entity is specified in [Payments Entity](payments-entity.md).

The upload job entity is specified in [Upload Jobs Entity](upload-jobs-entity.md).

The daily usage entity is specified in [Daily Usage Entity](daily-usage-entity.md).

The webhook event entity is specified in [Webhook Events Entity](webhook-events-entity.md).

The admin action entity is specified in [Admin Actions Entity](admin-actions-entity.md).

The system setting entity is specified in [System Settings Entity](system-settings-entity.md).

# 8. Users Entity

Группа спецификации: Данные


## 8.1. Purpose

`users` stores Telegram users, account-level settings, access status, and links to subscriptions, payments, publication jobs, TikTok accounts, and daily usage counters.

## 8.2. Recommended Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Internal user identifier |
| `telegram_user_id` | BIGINT | Unique Telegram user identifier |
| `username` | VARCHAR | Telegram username when available |
| `language_code` | VARCHAR | Preferred interface language |
| `current_plan_id` | UUID or plan identifier | Current user tariff reference |
| `is_active` | BOOLEAN | User active state |
| `created_at` | TIMESTAMP WITH TIME ZONE | Record creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | Last update time |

The current implementation may use internal column names such as `telegram_id` while preserving the same domain meaning. Any schema rename or added field must be delivered through Alembic migration and compatibility checks.

## 8.3. Relationships

| Relationship | Cardinality |
| --- | --- |
| `users` -> `subscriptions` | 1:N |
| `users` -> `payments` | 1:N |
| `users` -> `upload_jobs` | 1:N |
| `users` -> `tiktok_accounts` | 1:N |
| `users` -> `daily_usage` | 1:N |

## 8.4. Integrity Requirements

- Use UUID as the primary key.
- Telegram user ID must be unique.
- User changes must be transactional.
- Users must not be physically deleted without a documented deletion or anonymization procedure.
- Payment, subscription, publication, and audit history must remain consistent after user anonymization.
- User changes that affect access, roles, plans, or blocking state must be auditable.

## 8.5. Audit Requirements

Audit:

- New user registration.
- Terms acceptance.
- Plan changes.
- User blocking or unblocking.
- TikTok disconnect.
- Anonymization or deletion workflow.
- Administrator-initiated profile changes.

## 8.6. Development Requirement

Changes to the `users` entity require updated SQLAlchemy models, Alembic migrations, tests, documentation, and data quality checks.

# 9. TikTok Accounts Entity

Группа спецификации: Данные


## 9.1. Purpose

`tiktok_accounts` stores connected TikTok accounts and OAuth integration metadata for official TikTok API access.

## 9.2. Recommended Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Internal record identifier |
| `user_id` | UUID | Reference to `users.id` |
| `tiktok_open_id` | VARCHAR | TikTok account identifier |
| `display_name` | VARCHAR | TikTok display name |
| `access_token` | TEXT encrypted | OAuth access token |
| `refresh_token` | TEXT encrypted | OAuth refresh token |
| `token_expires_at` | TIMESTAMP WITH TIME ZONE | Access token expiration time |
| `created_at` | TIMESTAMP WITH TIME ZONE | Connection creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | Last update time |

The current implementation may use internal column names such as `open_id`, `access_token_encrypted`, and `refresh_token_encrypted` while preserving the same domain meaning. Any schema rename or added field must be delivered through Alembic migration and compatibility checks.

## 9.3. Relationships

| Relationship | Cardinality |
| --- | --- |
| `users` -> `tiktok_accounts` | 1:N |
| `tiktok_accounts` -> `upload_jobs` | 1:N |

## 9.4. Security Requirements

- Store OAuth access tokens only in encrypted form.
- Store OAuth refresh tokens only in encrypted form.
- Never log tokens, decrypted token values, or raw OAuth responses containing tokens.
- Delete encrypted tokens when the user disconnects the TikTok account.
- Check access token expiration before each TikTok API call.
- Refresh access tokens safely through the official OAuth refresh flow.
- Do not collect TikTok passwords.

## 9.5. Integrity Requirements

- `user_id` is required.
- TikTok account identifier must be unique within the system unless a documented multi-tenant reason requires a different constraint.
- Token updates must be transactional.
- Account disconnect must be transactional and auditable.
- Upload jobs should reference the TikTok account used for publication when available.

## 9.6. Audit Requirements

Audit:

- TikTok OAuth connection.
- Token refresh success or sanitized failure.
- TikTok account disconnect.
- Permission or scope errors.
- Administrator support actions related to TikTok accounts.

## 9.7. Development Requirement

Changes to `tiktok_accounts` require updated SQLAlchemy models, Alembic migrations, tests, documentation, and security review.

# 10. Subscriptions Entity

Группа спецификации: Данные


## 10.1. Purpose

`subscriptions` stores active and historical user subscriptions for FREE, PRO, and BUSINESS plans.

## 10.2. Recommended Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Subscription identifier |
| `user_id` | UUID | Reference to `users.id` |
| `plan_id` | UUID or plan identifier | Reference to `plans.id` |
| `status` | VARCHAR | `active`, `expired`, or `cancelled` |
| `starts_at` | TIMESTAMP WITH TIME ZONE | Subscription start time |
| `expires_at` | TIMESTAMP WITH TIME ZONE | End time, `NULL` for FREE |
| `daily_limit` | INTEGER | Daily publication limit captured for the subscription |
| `created_at` | TIMESTAMP WITH TIME ZONE | Record creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | Last update time |

The current implementation may use `ends_at` for the same domain meaning as `expires_at`. Any schema rename or added field must be delivered through Alembic migration and compatibility checks.

## 10.3. Relationships

| Relationship | Cardinality |
| --- | --- |
| `users` -> `subscriptions` | 1:N |
| `plans` -> `subscriptions` | 1:N |
| `subscriptions` -> `payments` | 1:N |

## 10.4. Business Rules

- New users automatically receive the FREE plan.
- FREE subscriptions have no expiration time.
- PRO and BUSINESS subscriptions expire after the configured paid period.
- After PRO or BUSINESS expires, the user returns to FREE automatically.
- Only one subscription should be active for a user at the same time.
- Switching to a paid plan must not delete historical subscription records.
- Subscription status changes must be transactional.

## 10.5. Audit Requirements

Audit:

- FREE assignment.
- Paid subscription activation.
- Subscription renewal.
- Subscription expiration.
- Cancellation.
- Manual administrator changes.
- Automatic return to FREE.

## 10.6. Integrity Requirements

- `user_id` is required.
- `plan_id` is required.
- Historical subscription records must not be deleted.
- Payments linked to subscriptions must remain available for accounting and audit.
- Subscription state changes must not partially update payments, daily limits, or user state.

## 10.7. Development Requirement

Changes to `subscriptions` require updated SQLAlchemy models, Alembic migrations, tests, documentation, and data quality checks.

# 11. Payments Entity

Группа спецификации: Данные


## 11.1. Purpose

`payments` stores payment records for PRO and BUSINESS subscriptions paid through the existing Robokassa merchant account.

## 11.2. Recommended Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Internal payment identifier |
| `user_id` | UUID | Reference to `users.id` |
| `subscription_id` | UUID | Related subscription |
| `inv_id` | VARCHAR | Robokassa invoice identifier |
| `amount` | DECIMAL | Payment amount |
| `currency` | VARCHAR | Currency, `RUB` |
| `status` | VARCHAR | `created`, `pending`, `paid`, `failed`, `cancelled`, `refunded` |
| `paid_at` | TIMESTAMP WITH TIME ZONE | Payment confirmation time |
| `created_at` | TIMESTAMP WITH TIME ZONE | Record creation time |

The current implementation may use internal names such as `provider_invoice_id` for `inv_id` and `amount_rub` for `amount`. Any schema rename or added field must be delivered through Alembic migration and compatibility checks.

## 11.3. Relationships

| Relationship | Cardinality |
| --- | --- |
| `users` -> `payments` | 1:N |
| `subscriptions` -> `payments` | 1:N |

## 11.4. Business Rules

- FREE does not create a payment record.
- Only PRO and BUSINESS purchases create payment records.
- Subscription activation happens only after verified Robokassa ResultURL.
- SuccessURL is informational and must not activate a subscription.
- Repeated ResultURL notifications must be idempotent and must not activate the same subscription twice.
- Every payment status change must be auditable.

## 11.5. Security Requirements

- Do not store Robokassa secrets in `payments`.
- Verify digital signature before changing payment status.
- Verify amount before changing payment status.
- Verify currency when Robokassa provides it.
- Verify `InvId` before changing payment status.
- Do not log Robokassa passwords or raw secrets.
- Execute payment and subscription changes in a single transaction.

## 11.6. Development Requirement

Changes to `payments` require updated SQLAlchemy models, Alembic migrations, tests, documentation, Robokassa idempotency checks, and security review.

# 12. Upload Jobs Entity

Группа спецификации: Данные


## 12.1. Purpose

`upload_jobs` tracks the lifecycle of each video publication request from Telegram intake through official TikTok API submission and final status.

## 12.2. Recommended Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Upload job identifier |
| `user_id` | UUID | Reference to `users.id` |
| `tiktok_account_id` | UUID | Reference to `tiktok_accounts.id` |
| `status` | VARCHAR | `NEW`, `QUEUED`, `UPLOADING`, `PROCESSING`, `PUBLISHED`, `FAILED`, `CANCELLED` |
| `video_path` | TEXT | Temporary local file path |
| `caption` | TEXT | Video description |
| `hashtags` | TEXT | Hashtags |
| `error_code` | VARCHAR | Error code when available |
| `created_at` | TIMESTAMP WITH TIME ZONE | Record creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | Last update time |

The current implementation may use internal names such as `local_path` for `video_path` and may store hashtags as part of `caption` until a separate field is introduced through migration.

## 12.3. Lifecycle

1. Create upload job.
2. Validate video.
3. Queue processing.
4. Upload through the official TikTok Content Posting API.
5. Receive or poll publication status.
6. Mark as published, failed, or cancelled.

The detailed lifecycle is documented in [Video Publication Lifecycle](video-lifecycle.md).

## 12.4. Status Rules

- Every job uses a unique UUID.
- Status changes must follow allowed transitions.
- Every status change must be recorded in `upload_job_events`.
- Retry is allowed only for temporary errors.
- Terminal states must not be overwritten by stale retries.
- User daily limit is consumed only after official TikTok API acceptance.

Daily counter rules are documented in [Daily Usage Entity](daily-usage-entity.md).

## 12.5. Relationships

| Relationship | Cardinality |
| --- | --- |
| `users` -> `upload_jobs` | 1:N |
| `tiktok_accounts` -> `upload_jobs` | 1:N |
| `upload_jobs` -> `upload_job_events` | 1:N |

## 12.6. Development Requirement

Changes to `upload_jobs` require updated SQLAlchemy models, Alembic migrations, tests, queue/retry review, documentation, and data quality checks.

# 13. Daily Usage Entity

Группа спецификации: Данные


## 13.1. Purpose

`daily_usage` tracks daily publication limit consumption for FREE, PRO, and BUSINESS users.

## 13.2. Recommended Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Usage record identifier |
| `user_id` | UUID | Reference to `users.id` |
| `usage_date` | DATE | Accounting date |
| `plan_id` | UUID or plan identifier | Plan at the time of accounting |
| `daily_limit` | INTEGER | Daily publication limit |
| `used_count` | INTEGER | Successfully accepted publications |
| `remaining_count` | INTEGER | Remaining daily limit |
| `updated_at` | TIMESTAMP WITH TIME ZONE | Last update time |

The current implementation may use `upload_count` for the same domain meaning as `used_count`. `remaining_count` may be calculated from the active plan limit and used count until a persisted field is introduced through migration.

## 13.3. Business Rules

- Create a record automatically on the first accepted publication of the day.
- The business day resets at 00:00 Europe/Moscow.
- Increment usage only after the official TikTok API accepts the publication.
- Do not increment usage for validation, preparation, authorization, or platform-restriction failures.
- If a user changes plan during the day, recalculate remaining allowance without resetting already used publications.
- Reprocessing the same upload job must not increment the counter twice.

## 13.4. Integrity Requirements

- `user_id` and `usage_date` must be unique together.
- Counter updates must be transactional.
- Use locking or equivalent concurrency protection before incrementing counters.
- Counter updates must be idempotent for repeated worker attempts.
- Usage changes must be auditable.

## 13.5. Relationships

| Relationship | Cardinality |
| --- | --- |
| `users` -> `daily_usage` | 1:N |
| `plans` -> `daily_usage` | 1:N logical reference when plan is captured |

## 13.6. Development Requirement

Changes to `daily_usage` require updated SQLAlchemy models, Alembic migrations, tests for concurrent updates, queue/retry review, and data quality checks.

# 14. Webhook Events Entity

Группа спецификации: Данные


## 14.1. Purpose

`webhook_events` stores inbound webhook events from TikTok, Robokassa, Telegram, and internal service callbacks before processing.

## 14.2. Recommended Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Event identifier |
| `source` | VARCHAR | Event source: `tiktok`, `robokassa`, `telegram`, or internal source |
| `event_type` | VARCHAR | Event type |
| `external_event_id` | VARCHAR | External service event identifier |
| `payload` | JSONB | Original webhook payload |
| `processed` | BOOLEAN | Successful processing marker |
| `processed_at` | TIMESTAMP WITH TIME ZONE | Processing time |
| `created_at` | TIMESTAMP WITH TIME ZONE | Receive time |

The current implementation may use `provider` for `source`, `external_id` for `external_event_id`, and `status` for processing state. Any schema rename or added field must be delivered through Alembic migration and compatibility checks.

## 14.3. Business Rules

- Save every inbound event before processing begins.
- Identify repeated events by `source` and `external_event_id` when the external service provides an ID.
- Processing must be idempotent.
- Processing errors must be logged with sanitized reason and correlation context.
- Mark successful processing with `processed=true` or equivalent terminal processed status.
- Repeated processed events must not duplicate payments, subscription activation, upload status changes, or notifications.

## 14.4. Security Requirements

- Verify webhook signatures before trusting payload contents.
- Validate payload structure before processing.
- Do not store secret keys in `payload`.
- Mask tokens, passwords, signatures, and secrets in logs.
- Limit webhook event access to authorized administrators and support roles.

## 14.5. Sources

Supported sources:

- `telegram`
- `tiktok`
- `robokassa`
- Internal service callbacks when needed

## 14.6. Development Requirement

Changes to `webhook_events` require updated SQLAlchemy models, Alembic migrations, tests for idempotency and invalid signatures, documentation, and security review.

# 15. Admin Actions Entity

Группа спецификации: Данные


## 15.1. Purpose

`admin_actions` stores immutable audit records for administrative operations.

## 15.2. Recommended Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Audit record identifier |
| `admin_user_id` | UUID | Administrator who performed the action |
| `action` | VARCHAR | Administrative action type |
| `target_type` | VARCHAR | Changed entity type |
| `target_id` | UUID or VARCHAR | Changed entity identifier |
| `details` | JSONB | Additional change details |
| `created_at` | TIMESTAMP WITH TIME ZONE | Action time |
| `ip_address` | VARCHAR | Administrative request source when available |

The current implementation may use `metadata_json` for `details`. Any schema rename or added field, including `ip_address`, must be delivered through Alembic migration and compatibility checks.

## 15.3. Recorded Actions

Record:

- Plan changes.
- User blocking and unblocking.
- Manual subscription activation or cancellation.
- System settings changes.
- Safe task restart.
- Project configuration changes.
- Role or permission changes.
- User anonymization or TikTok disconnect initiated by support.

## 15.4. Integrity Requirements

- Audit records must not be modified by users.
- Audit records must not be changed after creation except by a documented retention or archival process.
- Deletion is allowed only according to approved retention policy.
- Every administrative operation must write an audit record before confirming success to the administrator.
- Search must be supported by administrator, action type, target, and time range.

Administrative REST requirements are documented in [Administrative REST API](admin-rest-api.md).

Security logging requirements are documented in [Security Logging and Audit](security-logging-audit.md).

## 15.5. Security Requirements

- Do not store secrets, raw tokens, passwords, or Robokassa credentials in `details`.
- Mask sensitive values before writing audit metadata.
- Restrict access to authorized administrator roles.

## 15.6. Development Requirement

Changes to `admin_actions` require updated SQLAlchemy models, Alembic migrations, tests, documentation, retention review, and security review.

# 16. System Settings Entity

Группа спецификации: Данные


## 16.1. Purpose

`system_settings` stores mutable non-secret project settings that can be changed without modifying source code.

## 16.2. Recommended Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Setting record identifier |
| `setting_key` | VARCHAR | Unique setting key |
| `setting_value` | TEXT or JSONB | Setting value |
| `value_type` | VARCHAR | `string`, `int`, `bool`, or `json` |
| `description` | TEXT | Setting description |
| `is_editable` | BOOLEAN | Whether admins may edit through admin UI |
| `updated_by` | UUID | Last administrator who changed the setting |
| `updated_at` | TIMESTAMP WITH TIME ZONE | Last update time |

The current implementation may use `key` for `setting_key` and `value` for `setting_value`. Any schema rename or added field must be delivered through Alembic migration and compatibility checks.

## 16.3. Example Settings

- PRO and BUSINESS prices.
- Daily publication limits.
- Temporary file retention.
- Maintenance mode.
- Logging levels and retention periods.
- Intake enabled or disabled.
- Feature flags for controlled rollout.

## 16.4. Integrity Requirements

- Every `setting_key` must be unique.
- Validate value type before saving.
- Validate allowed ranges and enum values before saving.
- Setting updates must be transactional.
- Setting updates must be written to `admin_actions`.
- Configuration export must exclude secret-like settings.

## 16.5. Security Requirements

- Critical secrets must not be stored in `system_settings`.
- Secrets remain only in `.env` or a managed secret store.
- Do not store Telegram bot tokens, TikTok client secrets, Robokassa passwords, encryption keys, API tokens, or webhook secrets in this table.
- Restrict editing to authorized administrator roles.

## 16.6. Development Requirement

Changes to `system_settings` require updated SQLAlchemy models, Alembic migrations, tests, documentation, configuration validation, and security review.

# 17. User Guide

Группа спецификации: Пользовательские сценарии


User-facing errors must follow [Error Codes and Exception Handling](error-handling.md).

## 17.1. Start

1. Open the Telegram bot.
2. Send `/start`.
3. Accept the user agreement.
4. Connect TikTok through official OAuth 2.0.

## 17.2. Upload Video

1. Tap `📤 Загрузить видео`.
2. Send MP4, MOV, or WEBM.
3. Enter a description.
4. Enter hashtags.
5. Confirm publication.

The bot validates and prepares the video, then sends it to TikTok only through the official Content Posting API.

## 17.3. Tariffs

- FREE: 2 videos per day.
- PRO: 5 videos per day.
- BUSINESS: 10 videos per day.

Paid plans are activated only after Robokassa ResultURL confirmation.

## 17.4. TikTok Disconnect

Open settings and tap `Отключить TikTok`. Stored OAuth tokens are deleted.

## 17.5. Errors

The bot shows a short user-safe message. Internal details, tokens, and provider secrets are never shown.

# 18. Video Publication Lifecycle

Группа спецификации: Пользовательские сценарии


Upload job storage rules are documented in [Upload Jobs Entity](upload-jobs-entity.md).

End-to-end publication sequence is documented in [Sequence Flows](sequence-flows.md).

## 18.1. Statuses

- `NEW`
- `VALIDATING`
- `PREPARING`
- `QUEUED`
- `UPLOADING`
- `PROCESSING`
- `PUBLISHED`
- `FAILED`
- `CANCELLED`

## 18.2. Flow

1. User starts upload.
2. Bot checks TikTok connection and daily limit.
3. Bot receives the video.
4. Worker validates container, signature, size, duration, and FFprobe metadata.
5. Worker transcodes WEBM to MP4 when needed.
6. User description and hashtags are stored with the upload job.
7. Worker sends the video through the official TikTok API.
8. Current status is stored on `upload_jobs`.
9. Each lifecycle transition is recorded in `upload_job_events`.
10. User receives a Telegram notification.

## 18.3. Error Rules

- No daily limit is consumed when validation or preparation fails.
- Daily limit is consumed only after official TikTok API acceptance.
- Authorization and platform restriction errors are not retried automatically.
- Temporary failures can be retried by the queue system.

Queue retry and duplicate-prevention rules are defined in [Queue and Retry Policy](queue-retry-policy.md).

Temporary file handling is defined in [File Storage Policy](file-storage-policy.md).

# 19. TikTok Developer Configuration

Группа спецификации: Интеграции


## 19.1. Application Configuration

- Store `TIKTOK_CLIENT_KEY` and `TIKTOK_CLIENT_SECRET` only in `.env` or a managed secret store.
- Do not commit TikTok credentials.
- Use separate TikTok developer applications for development, staging, and production when needed.
- Keep `TIKTOK_REDIRECT_URI` synchronized with the production HTTPS callback URL.
- Document every TikTok Developer Portal setting change in the operations journal or admin audit log.

## 19.2. OAuth Settings

Before release, verify:

- Redirect URI exactly matches `TIKTOK_REDIRECT_URI`.
- Required scopes are approved in TikTok Developer Portal.
- `video.publish` is approved before production publication is enabled.
- OAuth `state` validation works.
- Access token expiration is handled.
- Refresh token renewal flow works.
- Token refresh errors do not expose tokens in logs.

## 19.3. Webhook Settings

TikTok webhook configuration must:

- Use HTTPS.
- Match the production public domain.
- Signatures use the TikTok app `TIKTOK_CLIENT_SECRET`; no separate webhook secret is accepted by
  the official verification algorithm.
- Verify the `TikTok-Signature` timestamp and HMAC against the unmodified request body.
- Reject webhook timestamps older than five minutes to limit replay attacks.
- Process events idempotently.
- Log delivery, validation, and processing errors without exposing secrets.

## 19.4. Production Pre-Release Check

Before every production release:

1. Confirm TikTok Developer Portal app status.
2. Confirm production Redirect URI.
3. Confirm approved scopes.
4. Confirm webhook URL and `TIKTOK_CLIENT_SECRET` signature verification.
5. Run a test OAuth authorization with a test TikTok account.
6. Confirm encrypted token storage.
7. Confirm refresh flow behavior.
8. Confirm official Content Posting API behavior in staging or controlled production test.
9. Confirm no bypass, browser automation, or unofficial API behavior exists.

## 19.5. Required Direct Post UX

Before every publication the bot must query `/v2/post/publish/creator_info/query/` and:

1. Display the TikTok creator nickname.
2. Require a manual choice from the returned privacy options, with no default.
3. Enforce the creator-specific maximum video duration.
4. Let the user explicitly enable Comment, Duet, and Stitch only when TikTok allows them.
5. Collect commercial-content disclosure and prevent branded content with `SELF_ONLY` visibility.
6. Obtain explicit publication consent before any media is transferred.
7. Poll `/v2/post/publish/status/fetch/` or process final Content Posting webhooks.

Unaudited TikTok clients remain restricted to private posts and other platform limits. The system
must report those restrictions and must not attempt to bypass them.

TikTok account persistence rules are documented in [TikTok Accounts Entity](tiktok-accounts-entity.md).

## 19.6. Change Control

Changes to TikTok Developer settings must include:

- Date and owner.
- Environment.
- Changed setting.
- Reason for change.
- Expected impact.
- Verification result.
- Rollback plan when applicable.

## 19.7. Compliance Rule

If TikTok rejects authorization, scope, publication, region, account, policy, or webhook processing, the application must report the restriction and must not attempt circumvention.

# 20. Robokassa Setup

Группа спецификации: Интеграции


End-to-end payment sequence is documented in [Sequence Flows](sequence-flows.md).

## 20.1. Tariff Mapping

| Plan | Amount | Period |
| --- | ---: | --- |
| PRO | 499 RUB | 30 days |
| Business | 999 RUB | 30 days |

FREE does not use Robokassa.

## 20.2. Signature Rules

Payment link signature:

```text
MerchantLogin:OutSum:InvId:Password1
```

Result URL signature:

```text
OutSum:InvId:Password2
```

The bot contains helpers for both operations in `app.services.robokassa`.

## 20.3. Activation Rules

Only Result URL activates a subscription. Success URL is informational and never changes payment or subscription status.

Subscription state and history rules are documented in [Subscriptions Entity](subscriptions-entity.md).

Payment storage and idempotency rules are documented in [Payments Entity](payments-entity.md).

The backend validates:

- Result URL signature.
- `InvId`.
- Amount.
- Currency when Robokassa sends it.
- Repeated notifications idempotently.

Robokassa merchant credentials must stay only in `.env`.

# 21. API Documentation

Группа спецификации: API


OpenAPI and Swagger UI are available at:

- `/openapi.json`
- `/docs`
- `/redoc`

OpenAPI contract maintenance rules are documented in [OpenAPI and Contract Documentation](openapi-contracts.md).

REST response envelopes, compatibility rules, and tracing requirements are defined in [REST API Standards](rest-api-standards.md).

Public endpoint requirements are documented in [Public REST API](public-rest-api.md).

## 21.1. Public and Service Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | Liveness check |
| GET | `/api/v1/ready` | PostgreSQL and Redis readiness |
| GET | `/api/v1/metrics` | Prometheus-compatible counters |
| GET | `/api/v1/oauth/tiktok/start` | Start TikTok OAuth |
| GET | `/api/v1/oauth/tiktok/callback` | TikTok OAuth callback |
| POST | `/api/v1/webhooks/telegram` | Telegram webhook receiver |
| POST | `/api/v1/webhooks/tiktok` | TikTok webhook receiver |
| POST | `/api/v1/payments/robokassa/result` | Robokassa server notification |
| GET | `/api/v1/payments/robokassa/success` | Informational success response |
| GET | `/api/v1/payments/robokassa/fail` | Informational failure response |

## 21.2. TikTok OAuth Start

```http
GET /api/v1/oauth/tiktok/start?state=<one-time-state-created-by-bot>
```

The Telegram bot creates the short-lived state and sends this URL to the user. The endpoint
rejects missing, unknown, and expired states, then redirects to official TikTok OAuth. It never
accepts a Telegram user identifier from the public request.

## 21.3. Robokassa Result

Robokassa must call:

```http
POST /api/v1/payments/robokassa/result
```

Required form fields:

- `OutSum`
- `InvId`
- `SignatureValue`

Only this endpoint can activate a paid subscription.

Robokassa requires a plain text `OK{InvId}` response. Other API responses use JSON.

## 21.4. Error Format

```json
{
  "success": false,
  "error": {
    "code": "VAL-001",
    "message": "Invalid request"
  },
  "request_id": "uuid",
  "correlation_id": "uuid"
}
```

API validation and data integrity rules are documented in [Data Quality and Integrity](data-quality-integrity.md).

Error code catalog and exception handling rules are documented in [Error Codes and Exception Handling](error-handling.md).

## 21.5. Authorization

Admin endpoints require:

```text
Authorization: Bearer <ADMIN_API_TOKEN>
X-Admin-Telegram-Id: <telegram_id>
```

Mutating admin requests also require:

```text
X-CSRF-Token: <ADMIN_CSRF_TOKEN>
```

Telegram webhook requests can use:

```text
X-Telegram-Bot-Api-Secret-Token: <TELEGRAM_WEBHOOK_SECRET>
```

TikTok webhook requests must include `TikTok-Signature` in the official `t=<timestamp>,s=<hmac>`
format. The API validates HMAC-SHA256 over `<timestamp>.<raw_body>` with
`TIKTOK_CLIENT_SECRET` and rejects timestamps outside the five-minute replay window.

TikTok OAuth, webhook, and developer portal checks are documented in [TikTok Developer Configuration](tiktok-developer-configuration.md).

## 21.6. Examples

Start TikTok OAuth:

```bash
curl "https://your-domain.example/api/v1/oauth/tiktok/start?state=$OAUTH_STATE"
```

List upload jobs:

```bash
curl "https://your-domain.example/admin/upload-jobs?limit=50&offset=0" \
  -H "Authorization: Bearer $ADMIN_API_TOKEN" \
  -H "X-Admin-Telegram-Id: $ADMIN_TELEGRAM_ID"
```

## 21.7. Admin API

See [Administrator Guide](admin.md) and [Administrative REST API](admin-rest-api.md).

# 22. REST API Standards

Группа спецификации: API


## 22.1. General Rules

- Public REST methods use the `/api/v1` prefix.
- JSON is the default exchange format.
- Use correct HTTP status codes.
- Use a consistent response envelope.
- Include Request ID in every response.
- Include Correlation ID when the operation belongs to a broader workflow.
- Document API changes in OpenAPI and `CHANGELOG.md`.

OpenAPI contract rules are documented in [OpenAPI and Contract Documentation](openapi-contracts.md).

API version lifecycle and client compatibility rules are documented in [API Versioning and Client Compatibility](api-versioning-compatibility.md).

Robokassa ResultURL is the only intentional exception when a plain text `OK{InvId}` response is required by Robokassa.

Administrative endpoints follow [Administrative REST API](admin-rest-api.md).

Public endpoints follow [Public REST API](public-rest-api.md).

## 22.2. Successful Response

```json
{
  "success": true,
  "data": {},
  "request_id": "uuid"
}
```

When available, include:

```json
{
  "success": true,
  "data": {},
  "request_id": "uuid",
  "correlation_id": "uuid"
}
```

## 22.3. Error Response

```json
{
  "success": false,
  "error": {
    "code": "TT-001",
    "message": "Operation cannot be completed"
  },
  "request_id": "uuid",
  "correlation_id": "uuid"
}
```

Error codes are defined in [Error Codes and Exception Handling](error-handling.md).

## 22.4. Compatibility

- Do not remove existing response fields within the same major API version.
- Add new fields as optional.
- Keep public `/api/v1` behavior backward compatible.
- Introduce a new API version for incompatible changes.
- Document request, response, and error changes in OpenAPI.
- Update `CHANGELOG.md` for behavior changes.

## 22.5. Request Tracing

Each request should have:

- Request ID for the specific inbound request.
- Correlation ID for related operations across API, bot, worker, webhooks, payments, and logs.

Tracing rules are documented in [Observability and Diagnostics](observability-diagnostics.md).

# 23. API Versioning and Client Compatibility

Группа спецификации: API


This document defines the public API versioning strategy, client compatibility rules, and deprecation process for Tik_Tok_Loader.

## 23.1. Versioning Strategy

- Current public REST API methods use the `/api/v1` prefix.
- Backward-incompatible changes must be released only under a new major API prefix, such as `/api/v2`.
- Minor changes must not break existing clients.
- Each active API version must have current documentation and OpenAPI coverage.
- Robokassa ResultURL response format exceptions must remain documented because Robokassa may require plain text responses.

## 23.2. Compatible Changes

The following changes are allowed within the same major version when documented:

- Adding optional response fields.
- Adding optional request fields.
- Adding new endpoints.
- Adding new error codes without changing existing error semantics.
- Improving validation messages without exposing internal details.
- Extending enum-like values only when existing clients can safely ignore new values.

## 23.3. Breaking Changes

The following require a new major version or an approved migration path:

- Removing or renaming response fields.
- Changing field types or meanings.
- Changing required request fields.
- Removing endpoints.
- Changing authentication requirements for existing endpoints.
- Changing status codes or error response shape in a way that breaks existing clients.
- Changing idempotency behavior for webhooks, payments, or upload jobs.

## 23.4. Version Lifecycle

| Stage | Description |
| --- | --- |
| Development | Version is designed, implemented, tested, and documented. |
| Staging publication | Version is deployed to staging for integration and acceptance testing. |
| Production release | Version is available for production clients. |
| Support period | Version receives fixes and compatible additions. |
| Deprecation | Clients are warned about planned retirement and migration path. |
| Retirement | Version is removed only after the transition period and release approval. |

## 23.5. Deprecation Policy

- Announce deprecation before retirement.
- Document the replacement endpoint, field, or behavior.
- Avoid removing critical endpoints without a transition period.
- Keep OpenAPI and user-facing API documentation updated during deprecation.
- Log and monitor usage of deprecated endpoints when practical.
- Include deprecation and retirement dates in release notes when known.

## 23.6. Compatibility Criteria

New versions should preserve, where possible:

- Response envelope shape.
- Error code semantics.
- Request ID and Correlation ID behavior.
- Authentication model.
- Idempotency guarantees.
- Payment and webhook processing behavior.
- Existing endpoint behavior until an explicit migration path exists.

All exceptions must be described in documentation, OpenAPI, `CHANGELOG.md`, and release notes.

## 23.7. Release Requirements

Before releasing an API change:

- Update [OpenAPI and Contract Documentation](openapi-contracts.md).
- Update [REST API Standards](rest-api-standards.md) when shared rules change.
- Update public or administrative API documentation.
- Add or update tests for compatibility and error behavior.
- Document deprecation or migration steps when needed.
- Review impact through [Change Acceptance Policy](change-acceptance-policy.md).

# 24. Public REST API

Группа спецификации: API


## 24.1. General Requirements

- Public endpoints use the `/api/v1` prefix.
- JSON is the default exchange format.
- Standard HTTP status codes are used.
- Every request receives a Request ID.
- Related operations should include a Correlation ID.
- Responses follow [REST API Standards](rest-api-standards.md).
- Errors follow [Error Codes and Exception Handling](error-handling.md).

Robokassa ResultURL may return plain text `OK{InvId}` when required by Robokassa.

## 24.2. Core Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | Service liveness check |
| GET | `/api/v1/ready` | Application readiness check |
| GET | `/api/v1/oauth/tiktok/start` | Start TikTok OAuth authorization |
| GET | `/api/v1/oauth/tiktok/callback` | Complete TikTok OAuth |
| POST | `/api/v1/webhooks/tiktok` | Receive TikTok webhook |
| POST | `/api/v1/payments/robokassa/result` | Process Robokassa ResultURL |

Additional service endpoints, such as Telegram webhook and metrics, are documented in [API Documentation](api.md).

The OAuth start endpoint accepts only a short-lived random `state` previously created by the
Telegram bot. Public callers cannot select a Telegram user identifier or create an account link.

## 24.3. Compatibility Requirements

- Do not remove existing response fields without a new API version.
- Add new response fields as optional.
- Keep backward compatibility within `/api/v1`.
- Document changes in OpenAPI.
- Update `CHANGELOG.md` for behavior changes.

Detailed API lifecycle and deprecation rules are documented in [API Versioning and Client Compatibility](api-versioning-compatibility.md).

## 24.4. Error Handling

Errors use the shared response envelope:

```json
{
  "success": false,
  "error": {
    "code": "TT-001",
    "message": "Operation cannot be completed"
  },
  "request_id": "uuid"
}
```

Internal implementation details, stack traces, tokens, secrets, SQL errors, and raw external service responses must not be exposed to users.

# 25. Administrative REST API

Группа спецификации: API


## 25.1. Access Requirements

- All administrative endpoints require authentication.
- Role and permission checks are enforced on the server.
- Mutating requests require CSRF protection where applicable.
- Every administrative request should have a Request ID.
- Related operations should include a Correlation ID.
- Administrative changes must be recorded in `admin_actions`.
- Responses use JSON and follow [REST API Standards](rest-api-standards.md).
- Errors use [Error Codes and Exception Handling](error-handling.md).

API version lifecycle and compatibility rules are documented in [API Versioning and Client Compatibility](api-versioning-compatibility.md).

## 25.2. Recommended Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/v1/admin/users` | User list |
| GET | `/api/v1/admin/users/{id}` | User profile |
| POST | `/api/v1/admin/users/{id}/block` | Block user |
| POST | `/api/v1/admin/users/{id}/unblock` | Unblock user |
| GET | `/api/v1/admin/payments` | Payment list |
| GET | `/api/v1/admin/upload-jobs` | Publication queue |
| GET | `/api/v1/admin/settings` | System settings |
| PUT | `/api/v1/admin/settings` | Update system settings |

Additional administrative endpoints may be added when they follow the same authentication, RBAC, audit, and response-format rules.

## 25.3. Transaction Rules

Mutating operations must be transactional:

- User blocking and unblocking.
- Plan updates.
- System setting updates.
- Manual subscription changes.
- Safe task restart.
- Configuration import.

The audit record must be created in the same transaction as the change when possible.

## 25.4. Audit Requirements

Log in `admin_actions`:

- Administrator ID.
- Action type.
- Target type.
- Target ID.
- Sanitized details.
- UTC timestamp.
- Request source when available.

Do not write secrets, raw tokens, passwords, or Robokassa credentials to audit details.

## 25.5. Compatibility

- Keep `/api/v1/admin` backward compatible within the same major API version.
- Add new response fields as optional.
- Document endpoint changes in OpenAPI and `CHANGELOG.md`.
- Follow [Change Acceptance Policy](change-acceptance-policy.md) before release.

# 26. OpenAPI and Contract Documentation

Группа спецификации: API


## 26.1. Required OpenAPI Contents

OpenAPI must include:

- All REST endpoints.
- Request schemas.
- Response schemas.
- Error response schemas.
- Error code descriptions.
- Authorization requirements.
- Successful request examples.
- Error request examples.
- API versioning details.

## 26.2. Contract Requirements

- Any API change must update OpenAPI in the same change set.
- Changes must be checked for backward compatibility.
- New required request fields are allowed only in a new major API version.
- New response fields should be optional within the same major version.
- API contracts are the source for generated documentation.
- `CHANGELOG.md` must describe behavior or contract changes.

API versioning and deprecation rules are documented in [API Versioning and Client Compatibility](api-versioning-compatibility.md).

## 26.3. Availability

Developers can use:

- `/openapi.json`
- `/docs`
- `/redoc`

Swagger UI or equivalent interactive documentation is recommended for internal administrator and developer use only.

## 26.4. Release Quality Criteria

Before release:

- OpenAPI matches implemented endpoints.
- Request and response schemas validate.
- Error examples use documented error codes.
- Authorization requirements are current.
- Examples remain accurate.
- Compatibility impact is documented.

## 26.5. Development Requirement

Any endpoint, schema, status code, error code, authentication requirement, or response envelope change must update this contract documentation and related tests.

# 27. Error Codes and Exception Handling

Группа спецификации: API


## 27.1. Error Code Prefixes

| Prefix | Area |
| --- | --- |
| `AUTH` | Authorization and authentication |
| `PAY` | Robokassa payments |
| `TT` | TikTok API |
| `VAL` | Validation |
| `SYS` | System errors |
| `NET` | Network errors |

## 27.2. Code Format

Use stable unique codes:

```text
PREFIX-NNN
```

Examples:

| Code | Meaning | Retry |
| --- | --- | --- |
| `AUTH-001` | Missing or invalid admin token | No |
| `AUTH-002` | TikTok OAuth state mismatch | No |
| `PAY-001` | Invalid Robokassa signature | No |
| `PAY-002` | Robokassa payment amount mismatch | No |
| `PAY-003` | Duplicate Robokassa notification | Idempotent handling |
| `TT-001` | TikTok authorization failed | No |
| `TT-002` | TikTok permission or scope is missing | No |
| `TT-003` | TikTok platform or regional restriction | No |
| `TT-004` | Temporary TikTok service error | Yes |
| `VAL-001` | Invalid request payload | No |
| `VAL-002` | Invalid video format | No |
| `VAL-003` | Video exceeds configured limits | No |
| `SYS-001` | Unexpected internal error | Investigate |
| `SYS-002` | Configuration error | No |
| `NET-001` | Temporary network failure | Yes |
| `NET-002` | External service timeout | Yes |

## 27.3. REST Error Format

REST APIs return a consistent JSON structure:

```json
{
  "success": false,
  "error": {
    "code": "VAL-001",
    "message": "Invalid request"
  },
  "request_id": "uuid",
  "correlation_id": "uuid"
}
```

REST response envelope rules are documented in [REST API Standards](rest-api-standards.md).

Public API error behavior is documented in [Public REST API](public-rest-api.md).

The public `message` must be safe for users and must not expose tokens, secrets, stack traces, internal paths, SQL errors, or raw external API responses.

## 27.4. Logging Rules

Technical details belong in structured JSON logs, not in user-facing messages.

Logs should include:

- Error code.
- Request ID.
- Correlation ID.
- User ID when available.
- Upload job ID when available.
- Payment ID or Robokassa `InvId` when available.
- External service name.
- Retry classification.
- Sanitized technical reason.

Logs must mask secrets and tokens.

## 27.5. User Messages

User messages should:

- Be short and understandable.
- Explain the next safe action when possible.
- Avoid internal details.
- Distinguish temporary failures from required user/admin action.

## 27.6. Retry Strategy

Retry only:

- Temporary network errors.
- Temporary external service errors.
- Worker interruption before a terminal state is saved.

Do not retry automatically:

- Authorization failures.
- Missing permissions.
- TikTok regional, account, policy, or platform restrictions.
- Invalid Robokassa configuration or signature.
- Invalid user input.
- Invalid video files.

## 27.7. Development Requirement

Every new failure path must define:

- Stable error code.
- Public message.
- Log details.
- Retry classification.
- Test coverage for expected handling.

# 28. Security, Backup, and Monitoring

Группа спецификации: Безопасность


Security and reliability non-functional requirements are summarized in [Non-Functional Requirements](non-functional-requirements.md).

Security logging and audit requirements are defined in [Security Logging and Audit](security-logging-audit.md).

Confidential data handling rules are defined in [Confidential Data Policy](confidential-data-policy.md).

## 28.1. Application Security

- External callbacks must use HTTPS.
- Secrets stay only in `.env` or a managed secret store.
- TikTok OAuth tokens are encrypted before database storage.
- Internal business IDs use UUID where the domain does not require a stable public code.
- Robokassa ResultURL signatures are verified before activation.
- TikTok webhook signatures are always checked with `TIKTOK_CLIENT_SECRET`, the raw request body,
  and a five-minute timestamp tolerance.
- API rate limiting uses Redis.
- Logs are JSON and must not include tokens, passwords, or Robokassa secrets.
- Uploaded files must follow [File Storage Policy](file-storage-policy.md).

TikTok account token storage rules are documented in [TikTok Accounts Entity](tiktok-accounts-entity.md).

Webhook storage and validation rules are documented in [Webhook Events Entity](webhook-events-entity.md).

## 28.2. Server Baseline

Ubuntu 24.04 LTS:

```bash
sudo adduser deploy
sudo usermod -aG docker deploy
sudo sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

Use SSH keys in Termius. Do not enable password login.

## 28.3. Backups

Run before every update:

```bash
bash deploy/backup_postgres.sh
tar -czf backups/config_$(date -u +%Y%m%dT%H%M%SZ).tgz .env deploy docker-compose.yml
```

Restore drill:

```bash
docker compose cp backups/tiktok_loader_YYYYMMDDTHHMMSSZ.dump postgres:/tmp/restore.dump
docker compose exec postgres pg_restore --clean --if-exists --username tiktok --dbname tiktok_loader /tmp/restore.dump
```

Test restore on a staging server before relying on backups.

Full backup and recovery rules are documented in [Backup and Restore Policy](backup-restore-policy.md).

Infrastructure update controls are documented in [Infrastructure Dependency Management](infrastructure-dependency-management.md).

## 28.4. Update and Rollback

1. Create a PostgreSQL and config backup.
2. Pull the new release.
3. Run `docker compose build`.
4. Run `docker compose run --rm api alembic upgrade head`.
5. Start services.
6. If health/readiness fail, restore the previous image and database backup.

## 28.5. Monitoring

- `GET /health` for liveness.
- `GET /ready` for PostgreSQL and Redis readiness.
- `GET /metrics` for Prometheus-compatible counters.
- JSON logs can be collected by Docker logging drivers or an external collector.

# 29. Security Logging and Audit

Группа спецификации: Безопасность


This document defines logging, security audit, and incident investigation requirements for Tik_Tok_Loader.

Confidential data masking and secret-handling rules are defined in [Confidential Data Policy](confidential-data-policy.md).

## 29.1. Log Categories

The system must maintain structured logs for:

- Application services.
- Telegram bot handlers and FSM flows.
- REST API requests, responses, webhook processing, and errors.
- Background worker tasks.
- Security events.
- Administrative audit actions.

## 29.2. Required Events

The following events must be logged or audited with sanitized context:

| Event | Required Record |
| --- | --- |
| Administrator login | Security log and, where applicable, `admin_actions` entry. |
| System setting change | `admin_actions` entry with changed key, old/new non-secret values where safe, administrator, timestamp, and request context. |
| TikTok connection | Diagnostic log and persisted account state update. |
| TikTok disconnection | Diagnostic log, token deletion event, and audit entry when initiated by support or administrator. |
| Payment creation | Payment record, diagnostic log, and correlation context. |
| Payment confirmation | Robokassa webhook event, payment status update, subscription update, and diagnostic log. |
| Upload status change | Upload job event and diagnostic log with job, user, and status identifiers. |
| Authorization failure | Security log with error code, request context, and masked identity details. |
| Access denial | Security log with role, permission, endpoint/action, and request context. |

## 29.3. Storage Requirements

Logs and audit records must:

- Use structured JSON format.
- Use UTC timestamps.
- Include `request_id` and `correlation_id` when available.
- Mask confidential data before persistence or transport.
- Exclude raw TikTok OAuth tokens, Robokassa passwords, Telegram bot token, encryption keys, private keys, and `.env` values.
- Support search by Request ID, Correlation ID, user, upload job, payment, webhook event, and administrator.
- Follow configured retention periods for logs, audit records, webhook events, and backups.

Retention rules are defined in [Data Retention](data-retention.md).

## 29.4. Investigation Use

Logs are used for:

- Operational diagnostics.
- Security incident investigation.
- Administrative operation proof.
- External integration troubleshooting.
- Payment and publication status reconciliation.

Incident response must use logs together with database audit records, webhook history, payment history, and upload lifecycle events. Procedures are documented in [Incident Response and Disaster Recovery](incident-response.md) and [Incident Management](incident-management.md).

## 29.5. Access Control

- Security logs and administrative audit logs are available only to authorized administrator roles.
- Sensitive log exports must be protected like production data.
- Audit records must not be changed after creation except through approved retention or archival procedures.

Administrative audit storage is documented in [Admin Actions Entity](admin-actions-entity.md).

## 29.6. Acceptance Rule

A release is not production-ready unless security logging, masking, searchable request context, audit storage, and retention behavior are verified for critical user, payment, publication, OAuth, and administrative flows.

# 30. Confidential Data Policy

Группа спецификации: Безопасность


This document defines how Tik_Tok_Loader handles, stores, protects, audits, and rotates confidential data.

Environment-specific secret control rules are defined in [Environment Configuration and Secrets Control](environment-configuration-secrets.md).

## 30.1. Confidential Data Categories

| Category | Examples |
| --- | --- |
| TikTok OAuth tokens | Access tokens, refresh tokens, token expiry metadata |
| Robokassa secrets | Merchant login, Password #1, Password #2 |
| Telegram secrets | Telegram bot token, webhook secret |
| Encryption keys | Token encryption key, administrative API or CSRF secrets |
| Backups with personal data | PostgreSQL dumps, configuration backups, audit exports |
| Production configuration | `.env`, Nginx production configuration with sensitive paths or headers |

## 30.2. Storage Rules

- Store secrets only in `.env` files on the server or in an approved secret store.
- Store TikTok OAuth tokens only in encrypted form in PostgreSQL.
- Do not commit `.env`, private keys, raw tokens, production backups, or secret exports to Git.
- Do not include secrets in repository backups.
- Minimize the number of services and operators with access to secrets.
- Keep critical secrets out of `system_settings`; database settings are for non-secret runtime configuration only.
- Protect backups that may contain personal data or encrypted tokens with access controls and retention limits.

## 30.3. Access Control

- Apply least-privilege access for administrators, operators, service accounts, containers, and CI jobs.
- Restrict administrative access to authorized roles.
- Review access rights regularly and after personnel, infrastructure, or ownership changes.
- Log administrative operations involving confidential data with masked values.
- Do not display raw secrets in dashboards, admin panels, logs, error messages, or support exports.

## 30.4. Runtime Handling

- Load secrets from environment variables during service startup.
- Validate required secrets at startup and fail safely when configuration is incomplete.
- Mask secrets before logging request bodies, headers, webhook payloads, exceptions, configuration dumps, or audit metadata.
- Do not store sensitive values in Telegram FSM state, Redis cache, or task payloads unless required and protected by expiration and masking.
- Avoid passing raw tokens between services when an internal identifier can be used instead.

## 30.5. Rotation

The system must support planned replacement of:

- TikTok OAuth tokens through the official refresh and disconnect/reconnect flows.
- Robokassa passwords through environment configuration updates.
- Telegram bot token through environment configuration updates and webhook reconfiguration when applicable.
- Encryption keys through a documented key-rotation procedure.
- Administrative tokens and CSRF secrets through environment configuration updates.

Rotation should be possible without changing application architecture and with minimal downtime.

## 30.6. Backup and Recovery

- Treat PostgreSQL backups, configuration backups, and audit exports as confidential data.
- Store production `.env` outside Git and restore it only from a protected source.
- Do not copy production backups into development environments unless data is anonymized or access is approved.
- Verify retention and deletion of old backups according to [Data Retention](data-retention.md).

## 30.7. Audit and Incident Handling

- Log access changes, administrative secret-related operations, token disconnects, and configuration changes with masked details.
- Investigate suspected secret exposure through [Security Logging and Audit](security-logging-audit.md) and [Incident Response and Disaster Recovery](incident-response.md).
- Rotate affected secrets after confirmed or suspected exposure.
- Document incident scope, affected data, actions taken, and preventive measures.

## 30.8. Related Documents

- [Configuration](configuration.md)
- [Security, Backup, and Monitoring](security.md)
- [Security Logging and Audit](security-logging-audit.md)
- [Backup and Restore Policy](backup-restore-policy.md)
- [TikTok Accounts Entity](tiktok-accounts-entity.md)
- [Data Retention](data-retention.md)

# 31. Environment Configuration and Secrets Control

Группа спецификации: Безопасность


This document defines how Tik_Tok_Loader manages configuration across environments and protects secrets used by the application.

## 31.1. Environments

| Environment | Purpose |
| --- | --- |
| Development | Local development and debugging. |
| Staging | Integration, pre-release, and acceptance testing. |
| Production | User-facing runtime operation. |

## 31.2. Configuration Requirements

- Use a separate `.env` file for every environment.
- Do not copy production secrets into development or staging.
- Keep real `.env` files outside Git.
- Keep only `.env.example` and non-secret environment templates in the repository.
- Record configuration changes in `CHANGELOG.md`, the operations journal, or `admin_actions`, depending on the change type.
- Validate required configuration values at startup.
- Fail startup safely when required parameters are missing or invalid.
- Keep environment configuration aligned with [Configuration](configuration.md) and `.env.example`.

## 31.3. Secrets Management

- Store secrets outside the repository.
- Limit access by least privilege.
- Rotate secrets regularly.
- Rotate secrets immediately after suspected compromise.
- Keep production secret ownership documented.
- Do not expose secrets through logs, admin UI, support exports, metrics, OpenAPI examples, or error messages.
- Do not store sensitive values in Telegram FSM state or long-lived Redis records.

Secret categories and rotation rules are defined in [Confidential Data Policy](confidential-data-policy.md).

## 31.4. Environment Separation

Development, staging, and production must have separate values for:

- Telegram bot token and webhook secret.
- TikTok client key, client secret, redirect URI, and webhook secret.
- Robokassa credentials and callback URLs.
- PostgreSQL and Redis credentials.
- Token encryption keys.
- Administrative API and CSRF secrets.
- Public base URL.

## 31.5. Release Compliance Check

Before every release, verify:

- Environment variables match the current documentation.
- `.env.example` is current and contains no real secrets.
- Production secrets are current, protected, and not reused in non-production environments.
- Required settings pass startup validation.
- Callback URLs match the target environment.
- Any configuration changes are documented.

## 31.6. Incident Rule

If a secret may be compromised, treat it as a security incident, rotate the affected secret, review logs and audit records, and document the response through [Security Logging and Audit](security-logging-audit.md) and [Incident Response and Disaster Recovery](incident-response.md).

# 32. Configuration

Группа спецификации: Конфигурация


Only `.env.example` is stored in Git. Real `.env` files are environment-specific and must not be committed.

Confidential data handling and secret rotation rules are defined in [Confidential Data Policy](confidential-data-policy.md).

Environment-specific configuration and secret control rules are defined in [Environment Configuration and Secrets Control](environment-configuration-secrets.md).

Use separate files for development, staging, and production, then copy the selected file to `.env` on the server.

Application: `APP_ENV`, `APP_VERSION`, `APP_HOST`, `APP_PORT`, `PUBLIC_BASE_URL`, `TIMEZONE`.

Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_ADMIN_IDS`.

Database: `DATABASE_URL`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.

Redis: `REDIS_URL`.

TikTok API: `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REDIRECT_URI`.

Telegram delivery: `TELEGRAM_DELIVERY_MODE` is `polling` for local development and `webhook` for
production. Webhook mode also requires `TELEGRAM_WEBHOOK_SECRET`,
`TELEGRAM_WEBHOOK_PATH`, and an HTTPS `PUBLIC_BASE_URL`.

`TIKTOK_WEBHOOK_SECRET` is retained only as a deprecated compatibility variable. Official TikTok
webhook verification uses `TIKTOK_CLIENT_SECRET`.

TikTok Developer Portal setup and pre-release checks are described in [TikTok Developer Configuration](tiktok-developer-configuration.md).

Robokassa: `ROBOKASSA_MERCHANT_LOGIN`, `ROBOKASSA_PASSWORD_1`, `ROBOKASSA_PASSWORD_2`, `ROBOKASSA_RESULT_URL`, `ROBOKASSA_SUCCESS_URL`, `ROBOKASSA_FAIL_URL`.

Security: `TOKEN_ENCRYPTION_KEY`, `ADMIN_API_TOKEN`, `ADMIN_CSRF_TOKEN`.

Generate Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

After `.env` is filled, local deployment starts with:

```bash
docker compose up -d
```

Runtime non-secret settings and tariffs can be exported/imported through the admin API. See [Configuration Management](configuration-management.md).

# 33. Configuration Management

Группа спецификации: Конфигурация


## 33.1. Sources

- Secrets are stored only in `.env` or a managed secret store.
- Runtime non-secret settings are stored in PostgreSQL `system_settings`.
- Tariffs are stored in PostgreSQL `plans`.

System setting storage rules are documented in [System Settings Entity](system-settings-entity.md).

Environment-specific `.env` and secret management rules are documented in [Environment Configuration and Secrets Control](environment-configuration-secrets.md).

## 33.2. Export

```bash
curl https://your-domain.example/admin/configuration/export \
  -H "Authorization: Bearer $ADMIN_API_TOKEN" \
  -H "X-Admin-Telegram-Id: $ADMIN_TELEGRAM_ID"
```

The export contains no secret-like keys such as passwords, tokens, keys, or secrets.

## 33.3. Import

```bash
curl -X POST https://your-domain.example/admin/configuration/import \
  -H "Authorization: Bearer $ADMIN_API_TOKEN" \
  -H "X-Admin-Telegram-Id: $ADMIN_TELEGRAM_ID" \
  -H "X-CSRF-Token: $ADMIN_CSRF_TOKEN" \
  -H "Content-Type: application/json" \
  -d @runtime-config.json
```

Before import, the current runtime configuration is recorded in `admin_actions` as an audit backup.

## 33.4. Audit

The following are recorded:

- Tariff updates.
- System setting updates.
- Configuration export.
- Configuration import.
- Administrative actions.

## 33.5. Startup Validation

Required settings are validated during startup. Missing required parameters cause safe startup failure without logging secrets.

## 33.6. Documentation Rule

Any configuration change that affects behavior must update this guide, `.env.example`, and related tests where applicable.

# 34. Deployment

Группа спецификации: Эксплуатация


Target: VPS in the Netherlands, managed through Termius or any SSH client.

## 34.1. Server Checklist

1. Create an Ubuntu 24.04 VPS in the Netherlands.
2. Point a domain or subdomain to the server.
3. Connect through Termius with SSH keys.
4. Update the system and install Docker.
5. Clone `kredavto/Tik-Tok-bot-Rus-2`.
6. Create production `.env`.
7. Start Docker Compose.
8. Configure Nginx and HTTPS.
9. Configure Telegram, TikTok, and Robokassa webhooks.
10. Check service health.

For first go-live, follow [Production Launch Plan](production-launch.md).

Infrastructure runtime updates must follow [Infrastructure Dependency Management](infrastructure-dependency-management.md).

## 34.2. Commands

```bash
git clone https://github.com/kredavto/Tik-Tok-bot-Rus-2.git
cd Tik-Tok-bot-Rus-2
cp .env.example .env
nano .env
docker compose up -d --build
docker compose logs -f api bot worker
```

Run migrations explicitly before first start or during deploy:

```bash
docker compose run --rm api alembic upgrade head
```

Migration safety, compatibility, and rollback rules are documented in [Migration and Version Compatibility Plan](migration-compatibility-plan.md).

Health checks:

```bash
curl https://your-domain.example/health
curl https://your-domain.example/ready
curl https://your-domain.example/metrics
```

## 34.3. Systemd Alternative

Use Docker Compose for the first deployment. If systemd is required, copy
`deploy/tiktok-loader-bot.service` to `/etc/systemd/system/` and adjust paths.

## 34.4. Robokassa URLs

Configure these in the Robokassa dashboard after the HTTP webhook service is added:

- Result URL: `https://your-domain.example/payments/robokassa/result`
- Success URL: `https://your-domain.example/payments/robokassa/success`
- Fail URL: `https://your-domain.example/payments/robokassa/fail`

The FastAPI service exposes Robokassa result, success, and fail endpoints.

## 34.5. Telegram Webhook

Development can use `TELEGRAM_DELIVERY_MODE=polling`. Production uses
`TELEGRAM_DELIVERY_MODE=webhook`; the bot service registers
`https://<domain>/api/v1/webhooks/telegram`, while FastAPI verifies
`X-Telegram-Bot-Api-Secret-Token` and dispatches the update through aiogram. FSM data is stored in
Redis so multiple API instances share state.

Never configure a bot token that has appeared in chat, logs, source files, or Git. Revoke it in
BotFather and place the replacement only in the server-side `.env`.

## 34.6. Environments

Use separate files outside Git for each environment:

- `.env.development`
- `.env.staging`
- `.env.production`

Copy the selected file to `.env` on the server. Never commit real `.env` files.

# 35. Containerization

Группа спецификации: Эксплуатация


## 35.1. Services

- `bot`: Telegram bot on aiogram.
- `api`: FastAPI backend.
- `worker`: Dramatiq background workers.
- `postgres`: PostgreSQL 16.
- `redis`: Redis cache, locks, and queue backend.
- `nginx`: reverse proxy for public HTTP/HTTPS traffic.

## 35.2. Startup

```bash
cp .env.example .env
docker compose up -d
```

## 35.3. Networking

PostgreSQL and Redis are not published to the host. Application services communicate over the dedicated `internal` Docker network. Nginx is attached to both `internal` and `public` networks and is the only public entrypoint.

## 35.4. Volumes

- `postgres_data`: persistent PostgreSQL data.
- `redis_data`: Redis persistence.
- `./data`: uploaded video workspace.
- `./backups`: database and configuration backups.

## 35.5. Healthchecks

Compose includes healthchecks for:

- PostgreSQL via `pg_isready`.
- Redis via `redis-cli ping`.
- API via `/health`.
- Nginx via `/health` proxy.

Service continuity requirements are documented in [Service Continuity Plan](service-continuity-plan.md).

## 35.6. Production Notes

- Keep secrets only in `.env`.
- Do not expose PostgreSQL or Redis ports.
- Put TLS certificates under `deploy/nginx/certs` or terminate HTTPS at a managed load balancer.
- Update base images regularly.

# 36. Production Launch Plan

Группа спецификации: Эксплуатация


End-to-end implementation stages are documented in [Implementation Roadmap](implementation-roadmap.md).

## 36.1. Preparation

- Domain name points to the production server.
- HTTPS certificate is issued and valid.
- Production `.env` is filled and stored outside Git.
- Production secrets are not reused in development or staging.
- PostgreSQL connection works.
- Redis connection works.
- Telegram webhook or polling mode is configured intentionally.
- TikTok OAuth Redirect URI matches the production callback URL.
- Existing Robokassa merchant settings are verified.
- Robokassa ResultURL, SuccessURL, and FailURL use the production HTTPS domain.
- Backup procedure is tested.

Environment and secret readiness must follow [Environment Configuration and Secrets Control](environment-configuration-secrets.md).

## 36.2. First Startup

```bash
docker compose up -d
docker compose ps
curl https://your-domain.example/health
curl https://your-domain.example/ready
curl https://your-domain.example/metrics
```

## 36.3. Smoke Test

1. Register a new Telegram user with `/start`.
2. Accept the user agreement.
3. Confirm FREE plan is assigned.
4. Start TikTok OAuth connection.
5. Confirm TikTok OAuth callback succeeds.
6. Generate a PRO payment link.
7. Complete a Robokassa test payment.
8. Confirm ResultURL activates PRO.
9. Upload one test video.
10. Confirm validation, preparation, queueing, worker processing, and TikTok API submission.
11. Confirm admin metrics and logs are visible.

## 36.4. Success Criteria

- All containers are running.
- Healthchecks are green.
- Telegram, TikTok, and Robokassa callbacks work.
- FREE, PRO, and BUSINESS limits match the specification.
- No critical errors appear in logs.
- Metrics are available to administrators.
- Backups are present and restorable.

## 36.5. Handover

Save and hand over:

- Production `.env` location and owner.
- Backup location and restore instructions.
- Domain and certificate details.
- Robokassa merchant settings.
- TikTok developer app settings.
- Telegram bot settings.
- Operations runbook and incident process.
- Current Git commit and release version.

# 37. Operations Runbook

Группа спецификации: Эксплуатация


## 37.1. Daily Operations

- Check Telegram bot availability.
- Check FastAPI `/health` and `/ready`.
- Review `/metrics` for queue size and error counters.
- Confirm the latest PostgreSQL backup exists.
- Confirm backup verification follows [Backup and Restore Policy](backup-restore-policy.md).
- Review critical JSON logs for `api`, `bot`, `worker`, `postgres`, `redis`, and `nginx`.
- Use Request ID and Correlation ID when investigating related API, worker, payment, and publication events.
- Check Robokassa ResultURL events in `webhook_events`.

## 37.2. Weekly Operations

- Check disk usage for Docker volumes, `./data`, and `./backups`.
- Check storage directories and cleanup health according to [File Storage Policy](file-storage-policy.md).
- Review PostgreSQL slow queries and run `EXPLAIN ANALYZE` for suspicious queries.
- Check dependency updates and base image updates.
- Verify SSL certificate expiration date.
- Review worker throughput and retry patterns.
- Review capacity thresholds according to [Capacity and Performance Management](capacity-management.md).
- Review operational KPI from [Metrics and KPI](metrics-and-kpi.md).

## 37.3. Monthly Operations

- Perform a restore drill from the latest backup on staging.
- Record restore drill results according to [Backup and Restore Policy](backup-restore-policy.md).
- Verify retention cleanup for temporary videos, webhook logs, audit logs, and backups.
- Review performance bottlenecks and queue latency.
- Review resource headroom and scaling needs.
- Review business and quality KPI trends.
- Review data quality checks according to [Data Quality and Integrity](data-quality-integrity.md).
- Confirm scheduled maintenance tasks still run.
- Review admin audit log for unexpected changes.

## 37.4. Update Checklist

Before update:

1. Set `intake_enabled=false` if the update affects upload processing.
2. Create a PostgreSQL backup.
3. Record the current Git tag and `APP_VERSION`.
4. Confirm `CHANGELOG.md` is updated.

During update:

1. Pull the release tag.
2. Rebuild containers.
3. Apply Alembic migrations.
4. Restart services.

After update:

1. Check `/health`, `/ready`, and `/metrics`.
2. Test `/start`, TikTok OAuth start, tariff display, Robokassa payment link generation, and upload queue creation.
3. Watch logs for at least 15 minutes.
4. Re-enable intake with `intake_enabled=true`.

## 37.5. Goal

Maintenance should keep the service stable, secure, predictable, and recoverable while preserving user data integrity.

Service continuity requirements are documented in [Service Continuity Plan](service-continuity-plan.md).

## 37.6. Incidents

Use [Incident Management](incident-management.md) to classify P1-P4 incidents, record impact, manage escalation, and run post-incident reviews.

Standard preflight, post-update, and diagnostic checklists are in [SOP Checklists](sop-checklists.md).

Tracing, event correlation, and log search requirements are described in [Observability and Diagnostics](observability-diagnostics.md).

# 38. SOP Checklists

Группа спецификации: Эксплуатация


## 38.1. Daily Administrator Checklist

- Check Telegram bot availability.
- Check FastAPI `/health` and `/ready`.
- Check worker container status.
- Confirm a PostgreSQL backup completed during the last 24 hours.
- Review critical JSON logs for `api`, `bot`, and `worker`.
- Check publication queue size and failed job count.

## 38.2. Weekly Checklist

- Check disk usage for Docker volumes, temporary video storage, and backups.
- Check PostgreSQL health and connection count.
- Check Redis health and memory usage.
- Review dependency and base image security updates.
- Verify TLS/SSL certificate expiration date.

Infrastructure update rules are documented in [Infrastructure Dependency Management](infrastructure-dependency-management.md).

## 38.3. Production Preflight

- Production `.env` is filled and not committed.
- PostgreSQL is reachable from application containers.
- Redis is reachable from application containers.
- HTTPS and certificates are valid.
- Telegram webhook or polling mode is configured intentionally.
- TikTok OAuth redirect URI matches the developer console.
- TikTok callback URL is public HTTPS.
- TikTok Developer Portal scopes, webhook, and test OAuth authorization are verified.
- Robokassa ResultURL, SuccessURL, and FailURL match production domain.
- `TOKEN_ENCRYPTION_KEY` is generated and stored securely.
- Backups are configured and tested.

## 38.4. Configuration Change Checklist

Before changing production configuration:

1. Create a PostgreSQL backup.
2. Export or save the current application configuration.
3. Record the planned change, owner, and expected impact.
4. Apply the configuration change.
5. Restart only the services affected by the change.
6. Check `/health`, `/ready`, and `/metrics`.
7. Verify the affected user or admin scenario.
8. Record the final result in the admin audit log or operations journal.

## 38.5. Post-Update Checklist

- All containers are running.
- PostgreSQL, Redis, API, and Nginx healthchecks pass.
- Alembic migrations applied successfully.
- `/health`, `/ready`, and `/metrics` respond.
- User `/start` flow works.
- TikTok OAuth start URL works.
- Robokassa test payment link is generated.
- Upload job can be queued.
- Worker processes queued jobs.
- Logs show no new critical errors.

## 38.6. Diagnostics

Logs:

```bash
docker compose logs --tail=200 api bot worker
```

Queue and Redis:

```bash
docker compose exec redis redis-cli ping
docker compose exec redis redis-cli llen dramatiq:default
```

Database:

```bash
docker compose exec postgres pg_isready -U tiktok -d tiktok_loader
```

Disk:

```bash
df -h
docker system df
```

External services:

- Check Telegram bot API status.
- Check TikTok developer app status.
- Check Robokassa merchant dashboard.

## 38.7. Incident Documentation

For significant incidents, record:

- Date and time.
- Problem description.
- User impact.
- Actions taken.
- Final resolution.
- Preventive recommendations.

Use [Incident Management](incident-management.md) for priority classification and post-incident review.

## 38.8. Emergency Procedure

For a critical incident:

1. Stop risky operations, such as new upload intake, if continued processing can increase impact.
2. Classify the incident priority and affected services.
3. Estimate user impact for publishing, payments, OAuth, and admin access.
4. Restore service using the approved runbook, rollback, or backup restore procedure.
5. Verify `/health`, `/ready`, queues, payments, and publication status integrity.
6. Document root cause, actions taken, final status, and prevention steps.

# 39. Maintenance Guide

Группа спецификации: Эксплуатация


## 39.1. Source of Truth

GitHub repository `kredavto/Tik-Tok-bot-Rus-2` is the single source of code.

All changes should go through pull requests. Direct production edits are not allowed.

## 39.2. Versioning

Use Semantic Versioning:

- `MAJOR` for incompatible API or data model changes.
- `MINOR` for backward-compatible features.
- `PATCH` for fixes.

Every release updates `CHANGELOG.md`.

## 39.3. Production Update Procedure

1. Create PostgreSQL and configuration backups.
2. Pull the latest approved release from GitHub.
3. Build Docker images.
4. Apply Alembic migrations.
5. Start services.
6. Check `/health`, `/ready`, `/metrics`.
7. Watch JSON logs for errors.

## 39.4. Rollback Procedure

1. Stop application services.
2. Restore the previous Docker image or Git tag.
3. Restore PostgreSQL from the pre-update backup when the migration is not backward compatible.
4. Start services.
5. Validate health and readiness.

## 39.5. Support Operations

Administrators can use the admin API to inspect:

- User profile and block state.
- Active subscription.
- Payment history.
- Upload jobs and publication errors.
- Audit log entries.

Users can disconnect TikTok from the bot settings. This deletes stored TikTok OAuth tokens.

## 39.6. Routine Maintenance

Use [Operations Runbook](operations-runbook.md) for daily, weekly, and monthly checks.

After the first production launch, use [Post-Launch Maintenance and Versioning](post-launch-maintenance.md) for release planning, change control, quality gates, and post-release monitoring.

Dependency updates and third-party integration checks are described in [Dependencies and Third-Party Services](dependencies-and-integrations.md).

## 39.7. Feature Development

Before adding a feature, assess:

- API compatibility.
- Database schema changes and Alembic migration needs.
- Telegram bot user journeys.
- Security and privacy impact.
- Test coverage and documentation updates.
- Dependency and third-party service compatibility.

# 40. Post-Launch Maintenance and Versioning

Группа спецификации: Эксплуатация


## 40.1. Release Cycle

Every production change follows the same controlled cycle:

1. Plan the change and document expected impact.
2. Develop in a dedicated feature branch.
3. Complete code review.
4. Run CI checks.
5. Verify the change in staging.
6. Deploy to production from an approved release.
7. Monitor service health, logs, metrics, payments, and publication flow after release.

## 40.2. Maintenance Schedule

### 40.2.1. Daily

- Check Telegram bot availability.
- Check API health and readiness.
- Check PostgreSQL and Redis availability.
- Review publication queue size.
- Confirm backup job completion.

### 40.2.2. Weekly

- Review error logs.
- Review failed TikTok publication jobs.
- Review failed Robokassa payments.
- Check disk usage and container health.
- Check for security updates in dependencies and base images.

### 40.2.3. Monthly

- Analyze PostgreSQL query performance.
- Review worker throughput and queue latency.
- Test backup restore in a non-production environment.
- Review retention cleanup for temporary videos, logs, and backups.
- Review release notes and pending technical debt.

Technical debt review rules are documented in [Technical Debt Management](technical-debt-management.md).

## 40.3. Change Management

Each change must include:

- Updated documentation when behavior, operations, or configuration changes.
- Alembic migration when the database schema changes.
- Tests for new or changed behavior.
- `CHANGELOG.md` entry for user-visible, operational, or security-relevant changes.
- Security and privacy impact review when user data, tokens, payments, or admin functions are affected.

Configuration changes should be made through `.env` or system settings, audited, and backed up before critical updates.

## 40.4. Release Quality Gates

A release can proceed only when:

- All required tests pass.
- CI has no blocking failures.
- No critical security finding remains open.
- Documentation matches the implemented version.
- Existing user scenarios remain compatible.
- Staging verification is complete.
- Rollback path is known and current backup exists.

## 40.5. Post-Release Monitoring

After each production deployment, monitor:

- `/health`, `/ready`, and `/metrics`.
- Telegram bot command response time.
- TikTok OAuth callback errors.
- TikTok publication failures.
- Robokassa ResultURL processing.
- Active subscription activation and expiration.
- Worker queue size and retry count.
- Critical application logs.

## 40.6. Stability Goal

The maintenance process must keep development predictable, reduce release risk, and preserve stable service operation while the project evolves.

# 41. Incident Response and Disaster Recovery

Группа спецификации: Эксплуатация


Incident classification and postmortem process are described in [Incident Management](incident-management.md).

Backup selection and restore verification must follow [Backup and Restore Policy](backup-restore-policy.md).

Continuity measures and planned maintenance rules are documented in [Service Continuity Plan](service-continuity-plan.md).

Security investigation logging requirements are defined in [Security Logging and Audit](security-logging-audit.md).

## 41.1. Critical Failure Procedure

1. Stop intake of new uploads by setting `intake_enabled=false` through the admin settings API.
2. Check `/health`, `/ready`, and `/metrics`.
3. Inspect JSON logs for `web`, `bot`, `worker`, `postgres`, `redis`, and `nginx`.
4. Create a backup before repair with `bash deploy/backup_postgres.sh`.
5. Restart services with `docker compose restart web bot worker`.
6. Restore PostgreSQL from backup if data or migrations are corrupted.
7. Verify queue integrity before resuming workers.
8. Set `intake_enabled=true` after recovery.

## 41.2. Queue Recovery

- `NEW`, `VALIDATING`, `PREPARING`, `QUEUED`, and `UPLOADING` jobs can be retried.
- `PROCESSING` jobs must be checked against TikTok status before retry.
- Daily usage is consumed only after official TikTok acceptance, so failed video preparation does not consume quota.

## 41.3. Monitoring Checklist

- Telegram bot process is running.
- FastAPI `/ready` returns `ready`.
- PostgreSQL accepts connections.
- Redis responds to ping.
- Worker logs show task processing.
- Nginx serves HTTPS.
- `/metrics` contains queue size, publication counts, payment counts, and subscription counts.

## 41.4. Audit

Critical operations are recorded in:

- `admin_actions` for administrator changes.
- `webhook_events` for Telegram, TikTok, and Robokassa events.
- Structured JSON logs for service-level diagnostics.

# 42. Incident Management

Группа спецификации: Эксплуатация


## 42.1. Priorities

| Priority | Example | Target Response |
| --- | --- | --- |
| P1 | Telegram bot or API is fully unavailable | Immediate response |
| P2 | Video publication or Robokassa payments are unavailable | Same business day |
| P3 | Partial errors in isolated functions | Planned fix |
| P4 | Cosmetic UI or documentation issue | Backlog |

## 42.2. Response Flow

1. Record the incident.
2. Assign priority.
3. Estimate user impact.
4. Apply temporary mitigation when needed.
5. Fix the root cause.
6. Verify service health and key user flows.
7. Document results and follow-up actions.

## 42.3. Incident Record Template

```text
Incident ID:
Priority:
Started at:
Detected by:
Affected services:
User impact:
Current status:
Mitigation:
Root cause:
Resolution:
Follow-up actions:
Closed at:
```

## 42.4. Availability Checks

- Telegram bot responds to `/start`.
- FastAPI `/health` and `/ready` return success.
- Nginx HTTPS endpoint is reachable.
- PostgreSQL and Redis healthchecks are green.
- Worker queue size is not growing unexpectedly.
- Latest backup exists and is readable.
- Robokassa ResultURL events are received.
- TikTok API errors are not above baseline.
- SSL certificate is valid and not close to expiration.

## 42.5. Escalation

- P1: stop intake if uploads or payments may be corrupted, notify project owner, keep checking every 15 minutes.
- P2: notify project owner, isolate failing integration, keep existing queue data intact.
- P3: open a tracked issue and schedule a fix.
- P4: add to documentation or UI backlog.

## 42.6. Post-Incident Review

After every P1/P2 incident:

1. Write a short postmortem.
2. Identify the root cause and contributing factors.
3. Add tests or monitoring where useful.
4. Update runbooks and deployment checks.
5. Track follow-up actions to completion.

Risk controls are summarized in [Risk Management](risk-management.md).

# 43. Backup and Restore Policy

Группа спецификации: Надежность


## 43.1. Backup Objects

Back up:

- PostgreSQL database.
- Production `.env` stored only on the server or in a managed secret store.
- Project documentation.
- Nginx configuration.
- Docker Compose configuration.
- Deployment scripts.
- Audit logs when required by the retention policy.

Do not commit production backups or real `.env` files to Git.

Backups containing personal or secret-related data must follow [Confidential Data Policy](confidential-data-policy.md).

## 43.2. Backup Policy

- Run PostgreSQL backups regularly.
- Keep multiple backup generations.
- Verify every backup job completed successfully.
- Store backups outside the running database container.
- Protect backups with access controls.
- Periodically test restore on staging or an isolated recovery host.
- Apply `BACKUP_RETENTION_DAYS` for backup retention.

## 43.3. Backup Verification

For each backup, record:

- UTC timestamp.
- Environment.
- Backup file name.
- Database revision.
- Application version or Git commit.
- File size.
- Exit status.
- Verification result.

Failed backup jobs must be treated as operational incidents.

## 43.4. Restore Procedure

1. Identify the failure cause and affected components.
2. Stop risky operations, including new upload intake if needed.
3. Prepare infrastructure: Docker, volumes, network, `.env`, Nginx, and HTTPS.
4. Restore PostgreSQL from the latest valid backup when data recovery is required.
5. Restore configuration files from the protected source.
6. Start PostgreSQL, Redis, API, bot, worker, and Nginx.
7. Apply required Alembic migrations only after confirming version compatibility.
8. Check `/health`, `/ready`, and `/metrics`.
9. Verify key user scenarios.
10. Document the incident and recovery actions.

## 43.5. Recovery Success Criteria

After recovery, these must work correctly:

- Telegram user authorization and `/start`.
- TikTok OAuth connection.
- Video upload queueing and worker processing.
- Robokassa ResultURL payment processing.
- Subscription state and tariff limits.
- Admin API and audit log access.
- Queue state without duplicate publication or duplicate quota consumption.
- User, subscription, payment, and publication history.

Continuity planning and planned maintenance rules are documented in [Service Continuity Plan](service-continuity-plan.md).

## 43.6. Restore Drill

At least periodically:

1. Restore the latest backup to staging.
2. Apply migrations for the target version.
3. Run smoke tests.
4. Verify payments, subscriptions, and upload job integrity.
5. Record restore duration and issues found.

## 43.7. Documentation Requirement

Every significant recovery must record:

- Incident date and priority.
- Root cause.
- Backup selected.
- Data loss assessment.
- Recovery steps.
- Validation result.
- Preventive actions.

# 44. Service Continuity Plan

Группа спецификации: Надежность


## 44.1. Critical Services

The service depends on:

- Telegram bot.
- FastAPI.
- PostgreSQL.
- Redis.
- Publication worker.
- Nginx.

Each critical service must have a health check, logs, and a documented recovery path.

## 44.2. Continuity Measures

- Use Docker restart policies for application services.
- Monitor service state through health checks.
- Keep PostgreSQL backups current and verified.
- Keep recovery instructions current.
- Verify rollback readiness before production updates.
- Keep `.env`, Nginx, and Docker Compose configuration recoverable from protected storage.
- Use idempotent queue, webhook, and payment processing to support safe restarts.

## 44.3. Planned Maintenance

When possible:

1. Schedule maintenance during low-activity periods.
2. Announce maintenance to administrators and support staff.
3. Create PostgreSQL and configuration backups.
4. Stop risky operations such as new upload intake if needed.
5. Apply changes.
6. Check `/health`, `/ready`, and `/metrics`.
7. Verify registration, TikTok OAuth, upload queueing, Robokassa payment flow, and admin functions.
8. Document the result and any follow-up actions.

## 44.4. External Service Degradation

If Telegram, TikTok, Robokassa, or another external dependency is degraded:

- Keep internal state consistent.
- Retry only temporary failures.
- Do not retry authorization, regional, policy, or invalid payment errors automatically.
- Notify users with a clear message when a user-facing action cannot be completed.
- Record external errors in logs and webhook history.

## 44.5. Recovery Readiness

Operations must keep these ready:

- Current backup and restore instructions.
- Recent tested backup.
- Current production `.env` location and owner.
- Current deployment commit or release tag.
- Rollback path.
- Incident response contacts and procedure.

## 44.6. Success Criteria

The service is operating successfully when:

- Bot and API respond predictably.
- PostgreSQL and Redis are healthy.
- Workers process queues without uncontrolled backlog.
- Nginx serves HTTPS endpoints.
- User, subscription, publication, and payment history remain intact.
- Recovery from component failures is safe and documented.

# 45. Data Retention

Группа спецификации: Надежность


## 45.1. Configuration

```env
VIDEO_RETENTION_HOURS=24
LOG_RETENTION_DAYS=90
BACKUP_RETENTION_DAYS=14
AUDIT_LOG_RETENTION_DAYS=365
```

## 45.2. Policy

- Temporary videos are removed after processing or retention expiry.
- TikTok OAuth tokens are encrypted and deleted when the user disconnects TikTok.
- Robokassa payment history is retained for accounting and audit.
- Webhook and upload lifecycle logs follow `LOG_RETENTION_DAYS`.
- Admin audit logs follow `AUDIT_LOG_RETENTION_DAYS`.
- Backups follow `BACKUP_RETENTION_DAYS`.

Temporary video storage rules are defined in [File Storage Policy](file-storage-policy.md).

## 45.3. User Data Deletion

Admin endpoint:

```http
POST /admin/users/{user_id}/anonymize
```

This removes TikTok tokens and anonymizes personal Telegram profile data while preserving records required for financial and legal audit.

# 46. File Storage Policy

Группа спецификации: Надежность


## 46.1. Storage Principles

- Store user videos only for the time required to process them.
- Separate temporary, processing, completed, and failed data.
- Use unique identifiers for directories and files.
- Do not expose internal file paths to users.
- Do not keep user files longer than the configured retention policy.
- Store file paths in PostgreSQL only for internal processing and audit.

## 46.2. Directory Structure

Recommended production layout:

```text
storage/
├── uploads/
├── processing/
├── completed/
├── failed/
└── temp/
```

Directory purpose:

| Directory | Purpose |
| --- | --- |
| `uploads/` | Newly received Telegram video files |
| `processing/` | Files currently being validated or transcoded |
| `completed/` | Files kept briefly after successful processing when needed for diagnostics |
| `failed/` | Files kept briefly after failed validation or processing when allowed by retention policy |
| `temp/` | Short-lived intermediate files |

## 46.3. Cleanup Policy

- Delete temporary files after successful or failed processing.
- Delete expired files on a scheduled cleanup task.
- Log cleanup actions with UTC timestamps.
- Monitor free disk space daily.
- Alert administrators before disk usage becomes critical.
- Follow `VIDEO_RETENTION_HOURS` for video retention.

## 46.4. Security Requirements

- Never execute uploaded files.
- Validate MIME type, extension, container signature, size, duration, and FFprobe metadata.
- Use generated internal filenames instead of user-provided names.
- Normalize and validate paths to prevent path traversal.
- Restrict storage permissions to application service users and containers.
- Do not expose internal storage paths in Telegram messages, API responses, or admin UI.
- Keep PostgreSQL and Redis separate from file storage volumes.

## 46.5. Operational Checks

Administrators should monitor:

- Free disk space.
- Number and size of files in each storage directory.
- Cleanup task success.
- Failed cleanup operations.
- Upload jobs pointing to missing files.
- Unexpected files outside the allowed directory structure.

## 46.6. Recovery Notes

If disk space is exhausted:

1. Stop new upload intake.
2. Check queue state and currently processing jobs.
3. Run scheduled cleanup or manually remove expired temporary files.
4. Confirm PostgreSQL still has consistent upload job statuses.
5. Restart affected workers.
6. Re-enable upload intake after health checks pass.

# 47. Queue and Retry Policy

Группа спецификации: Надежность


## 47.1. Background Task Types

The worker layer handles:

- Video preparation.
- Publication through the official TikTok Content Posting API.
- Publication status checks.
- OAuth token refresh.
- Temporary file cleanup.
- Subscription expiration checks.
- Return to FREE plan after paid subscription expiration.

## 47.2. Queue Rules

- Every queued task must have a unique identifier.
- Tasks must be idempotent.
- Upload status must be updated after each processing stage.
- Retries are allowed only for temporary failures.
- The same upload job must not be processed concurrently.
- Redis locks are used to prevent duplicate processing.
- PostgreSQL stores the durable task state.
- Redis may cache short-lived status and coordination data.

## 47.3. Retryable Errors

Automatic retry is allowed for:

- Deterministic byte-range chunk uploads rejected with a temporary TikTok 5xx response.
- Publication status checks that have not yet reached a terminal TikTok status.
- Temporary Telegram notification failures.
- Temporary Redis or database connectivity issues when retrying is safe.

The complete publication actor is not automatically replayed after an ambiguous failure because
the official API may already have accepted the publication. Such jobs are marked failed for
operator review. A full retry requires evidence that TikTok did not accept the earlier request.

Retry classification must follow [Error Codes and Exception Handling](error-handling.md).

## 47.4. Non-Retryable Errors

Do not retry automatically for:

- Missing or insufficient TikTok OAuth permissions.
- TikTok regional, account, or platform restrictions.
- Invalid Robokassa configuration.
- Invalid Robokassa signature, amount, currency, or `InvId`.
- Invalid user video format, unsupported container, or corrupted file.
- User cancellation.
- Policy or authorization rejection from an official external API.

## 47.5. Status Updates

Upload jobs use the lifecycle statuses documented in [Video Publication Lifecycle](video-lifecycle.md).

Upload job persistence rules are documented in [Upload Jobs Entity](upload-jobs-entity.md).

Each transition should include:

- Upload job ID.
- User ID.
- Previous status.
- New status.
- UTC timestamp.
- Human-readable reason.
- Correlation ID when available.

## 47.6. Duplicate Prevention

To prevent duplicate publication and duplicate quota consumption:

- Worker processing must acquire a per-upload lock.
- Daily limits are consumed transactionally.
- Daily usage counters follow [Daily Usage Entity](daily-usage-entity.md).
- Payments are activated only through Robokassa ResultURL after signature validation.
- Webhook handling must be idempotent.
- Terminal states must not be overwritten by stale retries.

## 47.7. Administrative Control

Administrators should be able to inspect:

- Queue size.
- Waiting task count.
- Processing task count.
- Failed task count.
- Retry count.
- Last error reason.
- Correlation ID.
- Related user, payment, or upload job.

Administrators may safely restart individual failed tasks only when the failure is retryable and the task has no active processing lock.

## 47.8. Operational Goal

Queue processing must preserve data integrity, avoid duplicate publication attempts, avoid duplicate payment activation, and keep enough diagnostic data for safe recovery.

# 48. Performance and Scaling

Группа спецификации: Производительность


Performance-related non-functional requirements are summarized in [Non-Functional Requirements](non-functional-requirements.md).

## 48.1. Goals

- Fast Telegram command responses.
- Long-running work is handled by workers.
- Redis is used for cache, locks, OAuth state, rate limiting, and queue coordination.
- PostgreSQL queries use indexes for common filters and ordering.

Operational KPI for performance and reliability are defined in [Metrics and KPI](metrics-and-kpi.md).

Capacity thresholds and scaling actions are documented in [Capacity and Performance Management](capacity-management.md).

## 48.2. Scaling API

Set:

```env
API_WORKERS=2
```

Run multiple `web` containers behind Nginx or another load balancer when needed.

## 48.3. Scaling Workers

Set:

```env
DRAMATIQ_PROCESSES=2
DRAMATIQ_THREADS=8
```

Worker operations use Redis locks for upload-job idempotency and daily-limit safety.

Queue retry behavior and safe task restart rules are documented in [Queue and Retry Policy](queue-retry-policy.md).

## 48.4. Database

Admin lists use pagination:

```http
GET /admin/users?limit=50&offset=0
GET /admin/payments?limit=50&offset=0
GET /admin/upload-jobs?status=FAILED&limit=50&offset=0
```

Use PostgreSQL `EXPLAIN ANALYZE` during performance reviews.

## 48.5. Safe Restarts

- Upload state is persisted in PostgreSQL.
- Queue state is coordinated through Redis and Dramatiq.
- Daily quota is consumed only after official TikTok API acceptance.

# 49. Capacity and Performance Management

Группа спецификации: Производительность


## 49.1. Controlled Resources

Monitor:

- CPU usage.
- Memory usage.
- Free disk space.
- PostgreSQL CPU, memory, connections, locks, slow queries, and storage.
- Redis memory, latency, connected clients, and key growth.
- Active worker task count.
- Publication queue length.
- API response time.
- Upload processing duration.
- External API error rates.

## 49.2. Threshold Events

Investigate when any of these trends appear:

- API response time grows above the expected baseline.
- Publication queue length increases continuously.
- Worker retries increase.
- Free disk space becomes low.
- PostgreSQL slow queries or lock waits increase.
- Redis memory usage approaches configured limits.
- TikTok publication errors increase.
- Robokassa webhook failures increase.
- Background task processing time increases.

## 49.3. Scaling Actions

Use the least risky action that addresses the bottleneck:

- Increase worker processes or threads for queue backlog.
- Add more FastAPI instances behind Nginx or a load balancer for API pressure.
- Optimize PostgreSQL queries and add indexes for slow queries.
- Increase PostgreSQL resources when query optimization is not enough.
- Increase disk capacity before storage reaches critical usage.
- Tune Redis memory and persistence settings when queue/cache pressure grows.
- Move heavy processing to additional worker hosts when a single server is saturated.

## 49.4. Review Cadence

Daily:

- Check service availability, queue size, and disk space.

Weekly:

- Review worker throughput, API latency, PostgreSQL slow queries, and Redis health.

Monthly:

- Review growth trends, resource headroom, queue latency, publication success rate, and payment reliability.
- Plan capacity increases before thresholds become incidents.
- Update operational documentation when scaling rules change.

## 49.5. Capacity Planning Inputs

Use:

- Metrics from `/metrics`.
- Admin dashboard KPI.
- Docker resource usage.
- PostgreSQL query analysis.
- Redis diagnostics.
- Worker queue metrics.
- Incident history.
- Growth in users, uploads, subscriptions, and payments.

## 49.6. Operational Goal

Capacity management must keep user-facing flows responsive, avoid uncontrolled queue growth, protect data integrity, and give administrators enough lead time to scale infrastructure safely.

# 50. Metrics and KPI

Группа спецификации: Производительность


## 50.1. Technical KPI

Track these indicators for operational stability:

| Metric | Purpose |
| --- | --- |
| Telegram bot availability | Confirms users can interact with the bot |
| FastAPI availability | Confirms callbacks, health checks, and internal API are reachable |
| Average publication processing time | Measures upload lifecycle performance |
| Successful publication rate | Tracks reliability of video publication flow |
| Average API response time | Tracks backend responsiveness |
| Worker queue size | Shows publication backlog and scaling pressure |
| Worker retry count | Shows temporary failures and external service instability |

## 50.2. Business Metrics

Track these indicators for project growth:

| Metric | Purpose |
| --- | --- |
| New users | Measures registration growth |
| Active FREE users | Shows free-tier usage |
| Active PRO users | Shows paid PRO adoption |
| Active BUSINESS users | Shows paid BUSINESS adoption |
| FREE to PRO conversion | Measures PRO monetization |
| FREE to BUSINESS conversion | Measures BUSINESS monetization |
| Successful payments | Measures Robokassa revenue flow |
| Revenue by plan | Supports pricing and growth analysis |

## 50.3. Quality Metrics

Track these indicators for release and support quality:

| Metric | Purpose |
| --- | --- |
| Critical error count | Shows production stability |
| Repeated failure count | Shows recurring defects or external instability |
| Incident recovery time | Measures time to restore normal service |
| Pre-release test pass rate | Shows release readiness |
| Failed webhook count | Tracks Telegram, TikTok, and Robokassa callback issues |
| Failed publication count by reason | Helps prioritize reliability work |

## 50.4. Administrative Dashboard

The admin dashboard should expose:

- Current service availability.
- User counts by tariff.
- New registrations by period.
- Publication volume and success rate.
- Robokassa successful payments and revenue by period.
- Conversion FREE to PRO and FREE to BUSINESS.
- Queue size, processing latency, and failed jobs.
- Critical errors and repeated failures.

## 50.5. Operational Use

Use metrics to:

- Detect incidents.
- Plan worker and API scaling.
- Evaluate release quality.
- Identify bottlenecks in publication processing.
- Review monetization and tariff performance.
- Prioritize technical debt and reliability work.

Capacity planning and threshold handling are described in [Capacity and Performance Management](capacity-management.md).

Metrics must never include TikTok OAuth tokens, Robokassa secrets, Telegram bot tokens, or raw user video contents.

Diagnostic event and log correlation requirements are described in [Observability and Diagnostics](observability-diagnostics.md).

# 51. Observability and Diagnostics

Группа спецификации: Наблюдаемость


Security logging and audit requirements are defined in [Security Logging and Audit](security-logging-audit.md).

## 51.1. Unified Tracing

- Assign a Request ID to every incoming HTTP request.
- Use a Correlation ID for related operations across API, bot, worker, database events, and external callbacks.
- Propagate diagnostic identifiers from FastAPI handlers to worker jobs and logs.
- Store timestamps in UTC with timezone-aware values.
- Include user, upload job, payment, webhook event, and admin action identifiers when available.

## 51.2. Diagnostic Events

Record structured events for:

- User authorization and registration.
- TikTok OAuth connection and disconnection.
- Upload job creation.
- Upload status changes.
- Video validation and preparation failures.
- TikTok API authorization, permission, regional, rate limit, and service errors.
- Robokassa payment creation, ResultURL processing, and payment confirmation.
- Telegram webhook processing.
- Administrative actions.
- Configuration changes.
- Background job retries and terminal failures.

Queue retry policy and duplicate-prevention rules are documented in [Queue and Retry Policy](queue-retry-policy.md).

Webhook event persistence rules are documented in [Webhook Events Entity](webhook-events-entity.md).

## 51.3. Log Requirements

Logs must:

- Use structured JSON format.
- Use UTC timestamps.
- Include stable error codes for handled failures.
- Include `request_id` and `correlation_id` when available.
- Be searchable by Telegram user ID, internal user ID, upload job ID, payment ID, and webhook event ID.
- Mask TikTok OAuth tokens, Robokassa secrets, Telegram bot tokens, API tokens, passwords, and encryption keys.
- Avoid storing raw user video contents.
- Follow configurable retention periods.

Error code and exception handling rules are documented in [Error Codes and Exception Handling](error-handling.md).

## 51.4. Cross-Service Diagnostics

For a publication flow, the same correlation context should connect:

1. Telegram upload intake.
2. Upload job record.
3. Queue enqueue event.
4. Worker validation and preparation.
5. TikTok API submission and status handling.
6. User notification.
7. Admin dashboard status and logs.

See [Sequence Flows](sequence-flows.md) for component interaction order.

For a payment flow, the same correlation context should connect:

1. Payment order creation.
2. Robokassa payment link generation.
3. ResultURL callback.
4. Signature and amount validation.
5. Subscription activation.
6. User notification.
7. Audit and webhook history.

## 51.5. Operational Diagnostics

Administrators should be able to search diagnostics by:

- Telegram ID.
- Internal user UUID.
- TikTok account UUID.
- Upload job UUID.
- Payment UUID and Robokassa `InvId`.
- Webhook event UUID.
- Request ID.
- Correlation ID.

Administrative audit storage rules are documented in [Admin Actions Entity](admin-actions-entity.md).

## 51.6. Goal

Diagnostic data must make it possible to identify failure causes quickly, analyze performance, verify external integration behavior, and simplify long-term maintenance without exposing confidential data.

# 52. Development Standards

Группа спецификации: Разработка


All development must preserve the requirements in [Architecture Summary](architecture-summary.md) and the subsystem boundaries in [Project Component Map](component-map.md).

The full documentation entry point is [Specification Index](specification-index.md).

## 52.1. Repository Structure

```text
Tik-Tok-bot-Rus-2/
├── app/
├── tests/
├── docs/
├── deploy/
├── alembic/
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

## 52.2. Coding Standards

- Python 3.12.
- Type hints for public functions, methods, and data structures.
- Ruff for linting and formatting checks.
- Public functions and classes should include docstrings when their behavior is not obvious from the name and type signature.
- Business logic, API handlers, data access, security, worker code, and infrastructure code stay in separate modules.

Project terminology and naming rules are documented in [Glossary and Naming Conventions](glossary-naming.md).

## 52.3. Git Workflow

1. Create a feature branch from the latest `main`.
2. Make focused commits.
3. Add or update tests.
4. Add Alembic migrations for schema changes.
5. Update documentation and `CHANGELOG.md`.
6. Open a pull request.
7. Pass CI.
8. Complete code review before merge.

Do not commit:

- `.env`
- secrets
- private keys
- production backups
- raw OAuth tokens

Repository workflow details and branch protection recommendations are documented in [GitHub Workflow](github-workflow.md).

Feature expansion rules are documented in [Feature Development Plan](feature-development-plan.md).

Database validation, constraints, transactions, and data consistency rules are documented in [Data Quality and Integrity](data-quality-integrity.md).

Entity relationships are documented in [Logical Data Model](data-model.md).

Post-launch change acceptance rules are documented in [Change Acceptance Policy](change-acceptance-policy.md).

Technical debt tracking and review rules are documented in [Technical Debt Management](technical-debt-management.md).

## 52.4. Quality Gates

Before merge:

```bash
ruff format --check .
ruff check .
mypy app
pytest
docker compose run --rm api alembic upgrade head
docker compose build
detect-secrets scan --all-files --exclude-files '\.git/.*|\.env\.example'
```

## 52.5. Compatibility

Public REST methods use `/api/v1`. New API versions must be introduced without breaking existing clients.

REST response format and API compatibility rules are documented in [REST API Standards](rest-api-standards.md).

# 53. GitHub Workflow

Группа спецификации: Разработка


## 53.1. Repository

The source of truth is `kredavto/Tik-Tok-bot-Rus-2`.

GitHub stores source code, documentation, CI history, pull requests, issues, and release tags.

## 53.2. Development Flow

1. Create a feature branch from `main`.
2. Keep the branch synchronized with `main`.
3. Implement focused changes.
4. Add or update tests.
5. Update documentation and `CHANGELOG.md` when behavior changes.
6. Open a pull request.
7. Wait for CI.
8. Complete code review.
9. Merge only after checks pass.

## 53.3. Branch Protection Recommendations

Enable these settings for `main`:

- Require pull request before merge.
- Require status checks to pass.
- Require branches to be up to date before merge.
- Require code review.
- Block force pushes.
- Block direct pushes.
- Run secret scanning.

## 53.4. Task Description Standard

Each change should document:

- Goal.
- Expected result.
- Affected components.
- Specification reference.
- Acceptance criteria.

For new product functionality, follow [Feature Development Plan](feature-development-plan.md).

## 53.5. Completion Criteria

A task is complete when:

- Code is implemented.
- Tests pass.
- Documentation is current.
- CI is green.
- Changes are ready for a release.

## 53.6. Release Tags

Release tags should follow SemVer, for example:

```text
v0.1.0
```

Sign releases when project policy requires it.

# 54. Feature Development Plan

Группа спецификации: Разработка


## 54.1. Principles

- Preserve the modular architecture.
- Keep public `/api/v1` behavior backward compatible.
- Add tests and documentation for every new feature.
- Apply database changes only through Alembic migrations.
- Reuse existing service layers instead of duplicating business logic.
- Use existing authorization, logging, configuration, audit, and error-handling mechanisms.

## 54.2. Feature Delivery Flow

1. Prepare a technical description.
2. Define affected modules, API methods, data model, background tasks, and user scenarios.
3. Assess security, privacy, performance, and operational impact.
4. Create a dedicated Git feature branch.
5. Implement the feature in the correct module boundaries.
6. Add or update unit, integration, FSM, and service tests as needed.
7. Add Alembic migrations for schema changes.
8. Update documentation and `CHANGELOG.md`.
9. Verify the feature in staging.
10. Release a new SemVer version.

## 54.3. Compatibility Requirements

New features must:

- Integrate through existing service, repository, API, bot, and worker layers.
- Avoid duplicating tariff, payment, upload, OAuth, and RBAC logic.
- Preserve existing Telegram user flows unless a migration path is documented.
- Keep existing API fields stable within the same major version.
- Use existing request ID, correlation ID, JSON logging, and audit logging.
- Keep configuration in `.env` or database-backed system settings.

## 54.4. Quality Control

Before merging a feature:

- Code review is complete.
- CI/CD passes.
- Tests cover the changed behavior.
- Alembic migrations apply and downgrade strategy is understood.
- Performance impact is checked for queues, database queries, and API endpoints.
- Security review is complete for user data, OAuth tokens, payments, admin actions, and webhooks.
- Documentation and `CHANGELOG.md` are current.
- Any introduced or removed technical debt is recorded according to [Technical Debt Management](technical-debt-management.md).

## 54.5. Release Readiness

A feature is release-ready only after staging verification confirms:

- Main user scenarios still work.
- Admin workflows still work.
- Robokassa payment behavior remains idempotent.
- TikTok OAuth and official API behavior remain compliant.
- Daily limits and subscription expiration still behave correctly.
- Monitoring, logs, and audit events include the new behavior.

# 55. Technical Debt Management

Группа спецификации: Разработка


This document defines how Tik_Tok_Loader records, prioritizes, reviews, and resolves technical debt during project evolution.

## 55.1. Sources of Technical Debt

Technical debt may come from:

- Temporary architecture compromises.
- Outdated dependencies or infrastructure components.
- Insufficient test coverage.
- Duplicated business logic.
- Code review findings.
- Performance bottlenecks found during operations.
- Documentation gaps discovered during release or incident review.

## 55.2. Debt Record Format

Every technical debt item must have:

| Field | Purpose |
| --- | --- |
| `id` | Unique identifier in `TD-###` format |
| `title` | Short description |
| `source` | Origin: code review, incident, release, dependency update, architecture review, or QA |
| `reason` | Why the debt exists |
| `priority` | `High`, `Medium`, or `Low` |
| `owner` | Responsible person or team |
| `affected_area` | Component, module, API, test suite, deployment area, or documentation section |
| `remediation_plan` | Planned fix or mitigation |
| `target_release` | Planned release or review date |
| `status` | `Open`, `In Progress`, `Deferred`, `Resolved`, or `Accepted Risk` |

## 55.3. Prioritization

- Critical security issues are resolved first and must not be deferred without explicit risk acceptance.
- Stability, data integrity, payment, OAuth, publication, and recovery issues are planned for the nearest practical release.
- Medium-priority maintainability and test coverage issues are scheduled into the roadmap.
- Low-priority improvements are grouped and reviewed during regular planning.

## 55.4. Review Rules

- Review technical debt before every release.
- Update status, owner, priority, and target release during review.
- Assess the impact of unresolved debt on release quality.
- Convert repeated incidents or recurring review comments into debt records.
- Close a debt item only after implementation, tests, and documentation are updated where relevant.

## 55.5. Release Control

A release may proceed with open technical debt only when:

- No unresolved critical security debt remains.
- Stability and data integrity risks are understood.
- Remaining items have owners and target releases.
- Risk acceptance is documented for deferred high-priority items.

## 55.6. Documentation

Technical debt decisions that affect architecture, testing, deployment, operations, or user behavior must update the corresponding documentation and `CHANGELOG.md` when resolved.

# 56. Dependencies and Third-Party Services

Группа спецификации: Зависимости


## 56.1. Core Dependencies

The project depends on:

- Python 3.12.
- FastAPI.
- aiogram 3.x.
- SQLAlchemy 2.x.
- Alembic.
- Redis.
- PostgreSQL 16.
- FFmpeg and FFprobe.
- Docker and Docker Compose.

Python dependency versions are constrained in `pyproject.toml`. Runtime service versions are controlled by Docker images and production deployment configuration.

Infrastructure runtime update rules are documented in [Infrastructure Dependency Management](infrastructure-dependency-management.md).

License and third-party component registry rules are documented in [License and Third-Party Component Management](license-third-party-management.md).

## 56.2. External Integrations

Supported production integrations are:

- Telegram Bot API.
- Official TikTok Content Posting API.
- Existing Robokassa merchant account.

The project must not use unofficial TikTok APIs, browser automation, credential scraping, or methods that bypass TikTok platform restrictions.

## 56.3. Update Policy

- Check dependency and base image updates regularly.
- Prioritize security updates for Python libraries, Docker images, PostgreSQL, Redis, Nginx, and FFmpeg.
- Test updates in staging before production.
- Do not update critical libraries directly in production.
- Keep version constraints explicit.
- Document relevant dependency and integration changes in `CHANGELOG.md`.
- Keep license and source metadata current for third-party components.

## 56.4. Compatibility Checks

Before releasing dependency updates, verify:

- Telegram bot FSM flows still work.
- FastAPI endpoints remain compatible.
- Alembic migrations still apply cleanly.
- SQLAlchemy async database access is stable.
- Redis queue and cache behavior is unchanged.
- FFmpeg and FFprobe validation still accepts supported video formats.
- Robokassa signature validation and ResultURL idempotency still work.
- TikTok OAuth and Content Posting API clients still match official API behavior.

## 56.5. Third-Party Service Control

For each external service, maintain:

- Current dashboard owner and access process.
- Production callback URLs.
- Test mode procedure where supported.
- Incident contact or status page.
- Last successful integration test date.

## 56.6. Release Rule

A release that changes dependencies or third-party integration behavior can proceed only after CI passes, staging verification is complete, documentation is updated, and rollback steps are known.

# 57. Infrastructure Dependency Management

Группа спецификации: Зависимости


This document defines how Tik_Tok_Loader controls infrastructure component versions, operating system updates, container updates, and runtime dependency compatibility.

## 57.1. Controlled Components

| Component | Control Area |
| --- | --- |
| Ubuntu Server 24.04 LTS | OS packages, kernel security updates, SSH, firewall, and system libraries |
| Docker Engine and Docker Compose | Container runtime, Compose plugin, networking, and volumes |
| Nginx | Reverse proxy, TLS termination, headers, and upstream routing |
| PostgreSQL | Database engine version, backup compatibility, migrations, and extensions |
| Redis | Queue/cache runtime version, memory behavior, and persistence settings |
| Python and project libraries | Python runtime, application dependencies, and version constraints |
| Docker base images | Security patches, Python image compatibility, and OS package updates |

## 57.2. Update Policy

- Check OS, Docker, Docker Compose, Nginx, PostgreSQL, Redis, Python library, and base image updates regularly.
- Test updates in staging before production rollout.
- Create a production backup before updating production infrastructure.
- Document performed updates in `CHANGELOG.md` or the operations journal, depending on release scope.
- Verify compatibility after every update.
- Avoid direct critical infrastructure changes in production without a rollback plan.

## 57.3. Security Control

- Install critical security updates in a timely manner.
- Review Docker base image vulnerabilities before release.
- Remove unused OS packages, Python libraries, containers, images, and volumes when safe.
- Keep TLS/SSL certificate expiration under regular control.
- Confirm PostgreSQL and Redis remain inaccessible from the public internet.
- Keep secrets in `.env` or an approved secret store only.

## 57.4. Production Update Procedure

1. Review the change scope and affected services.
2. Create a PostgreSQL backup and save current production configuration.
3. Apply the update in staging.
4. Run migrations and acceptance checks in staging when applicable.
5. Schedule production work in a low-activity window.
6. Apply the update to production.
7. Restart only affected services when possible.
8. Check `/health`, `/ready`, and `/metrics`.
9. Verify key user scenarios.
10. Review logs for new critical errors.
11. Document the update result.

## 57.5. Compatibility Checks

After infrastructure updates, verify:

- Telegram bot responds to `/start`.
- FastAPI health, readiness, and metrics endpoints respond.
- PostgreSQL accepts connections and Alembic state is correct.
- Redis accepts connections and queues operate normally.
- Worker processes jobs without duplicate processing.
- Nginx serves HTTPS and proxies callbacks correctly.
- Robokassa ResultURL processing still verifies signatures.
- TikTok OAuth start and callback URLs still match public HTTPS configuration.
- Video validation and FFmpeg/FFprobe behavior remain compatible.

## 57.6. Successful Update Criteria

An infrastructure update is successful only when:

- All services pass health checks.
- Key user flows work correctly.
- Logs contain no new critical errors.
- Backup and rollback paths are known.
- Update actions and outcomes are documented.

## 57.7. Related Documents

- [Dependencies and Third-Party Services](dependencies-and-integrations.md)
- [License and Third-Party Component Management](license-third-party-management.md)
- [Deployment](deployment.md)
- [Release Management](release.md)
- [Security, Backup, and Monitoring](security.md)
- [SOP Checklists](sop-checklists.md)
- [Capacity and Performance Management](capacity-management.md)

# 58. License and Third-Party Component Management

Группа спецификации: Зависимости


This document defines how Tik_Tok_Loader tracks third-party components, validates licenses, and controls dependency security.

## 58.1. Component Registry

The dependency registry must cover:

- Python runtime and project packages from `pyproject.toml`.
- FastAPI and aiogram.
- SQLAlchemy and Alembic.
- Redis and PostgreSQL.
- FFmpeg and FFprobe.
- Docker, Docker Compose, and Nginx.
- Docker base images.
- CI tools, linters, type checkers, test tools, and secret scanners.

Each registry entry should include:

| Field | Purpose |
| --- | --- |
| Component | Package, image, binary, or service name |
| Version | Current allowed or deployed version |
| Source | Package index, official image, vendor site, OS package, or repository |
| License | License name and link when available |
| Usage | Runtime, development, CI, deployment, or operations |
| Owner | Person or team responsible for review |
| Notes | Exceptions, constraints, or special usage conditions |

## 58.2. License Checks

- Record licenses for all external libraries and runtime components.
- Check license compatibility before adding a dependency.
- Document exceptions and special conditions before release approval.
- Recheck license metadata when dependencies are upgraded.
- Avoid dependencies with unclear origin or incompatible licensing.

## 58.3. Security Control

- Regularly check known vulnerabilities for Python packages, Docker base images, OS packages, PostgreSQL, Redis, Nginx, FFmpeg, and CI tools.
- Update dependencies only after staging verification.
- Remove unused libraries, binaries, images, and tooling when safe.
- Keep versions constrained in dependency files and deployment configuration.
- Document dependency and component changes in `CHANGELOG.md` when they affect runtime, security, operations, or compatibility.

## 58.4. Review Before Adding a Dependency

Before adding a third-party component:

1. Confirm the component is necessary and not already covered by an existing dependency.
2. Confirm the source is trustworthy.
3. Confirm the license is acceptable for the project.
4. Confirm maintenance activity and security posture.
5. Confirm staging compatibility.
6. Update dependency files, documentation, tests, and `CHANGELOG.md` where relevant.

## 58.5. Release Requirements

Before release:

- Dependency versions are documented.
- License exceptions are reviewed.
- Known critical vulnerabilities are resolved or explicitly risk-accepted.
- Unused dependencies are reviewed for removal.
- Staging verification passes after dependency changes.

## 58.6. Related Documents

- [Dependencies and Third-Party Services](dependencies-and-integrations.md)
- [Infrastructure Dependency Management](infrastructure-dependency-management.md)
- [Release Management](release.md)
- [Technical Debt Management](technical-debt-management.md)

# 59. Migration and Version Compatibility Plan

Группа спецификации: Релизы


## 59.1. Migration Rules

- Apply all database schema changes only through Alembic.
- Review and test every migration before production.
- Avoid irreversible schema or data changes without a separate rollback plan.
- Keep migrations safe to re-run where the operation can reasonably be idempotent.
- Keep schema migrations and application code compatible during rolling or staged deployment when possible.
- Never edit an already-applied production migration; create a new migration instead.

## 59.2. Migration Preflight

Before applying migrations:

1. Confirm CI has passed.
2. Review Alembic migration scripts.
3. Apply migrations in staging.
4. Run automated tests.
5. Run acceptance checks for registration, TikTok OAuth, upload queue, Robokassa payment, and admin flows.
6. Create a production PostgreSQL backup.
7. Record current Git tag, `APP_VERSION`, and database revision.

## 59.3. Version Compatibility

- New application versions must preserve existing user data.
- Public `/api/v1` changes should remain backward compatible.
- Tariff changes that affect stored records must include data migration logic.
- Documentation and `CHANGELOG.md` must be updated with the release.
- Workers and API must agree on upload status values, payment status values, and queue payload formats.
- New columns should prefer nullable or defaulted rollout paths when zero-downtime compatibility is required.

## 59.4. Production Update Procedure

1. Create PostgreSQL and configuration backups.
2. Deploy the approved application version.
3. Apply Alembic migrations.
4. Check `/health`, `/ready`, and `/metrics`.
5. Verify key user scenarios.
6. Monitor errors, queues, payments, publication success, and external callbacks.

## 59.5. Rollback Procedure

If the update fails:

1. Stop new upload intake when needed.
2. Revert to the previous stable application version.
3. Restore the database backup if the failed migration changed data incompatibly.
4. Restart services.
5. Check health, readiness, queue state, payment processing, and publication state.
6. Document the incident and corrective action.

## 59.6. Post-Update Control

After every update, monitor:

- API and bot error logs.
- Worker queue size and retries.
- Failed upload jobs.
- Robokassa ResultURL processing.
- TikTok OAuth and publication errors.
- Database consistency checks.
- User support reports.
- Overall system stability.

## 59.7. Development Requirement

Any new database entity or schema change must include an Alembic migration, data quality rules, tests, documentation, and a compatibility assessment before release.

# 60. Release Management

Группа спецификации: Релизы


## 60.1. Environments

| Environment | Purpose |
| --- | --- |
| Development | Local development and debugging |
| Staging | Pre-release acceptance testing |
| Production | User-facing runtime |

Environment templates live in `deploy/env.*.example`. Real `.env.*` files are not committed.

## 60.2. Release Requirements

- CI passes.
- Alembic migrations are tested.
- Docker images build.
- `CHANGELOG.md` is updated.
- OpenAPI contract is current when REST API behavior changes.
- QA acceptance scenarios pass in staging.
- Requirements traceability matrix is current.
- `APP_VERSION`, `app.__version__`, and `pyproject.toml` follow SemVer.
- Production backup is created before deployment.
- Risk impact is reviewed before production deployment.

## 60.3. Release Flow

1. Create a release branch.
2. Update version and changelog.
3. Run CI checks.
4. Deploy to staging.
5. Run acceptance tests.
6. Approve release.
7. Back up production.
8. Deploy to production.
9. Check `/health`, `/ready`, `/metrics`.
10. Monitor logs and core scenarios after release.

Post-launch release planning, routine checks, and quality gates are described in [Post-Launch Maintenance and Versioning](post-launch-maintenance.md).

Dependency and third-party service updates must follow [Dependencies and Third-Party Services](dependencies-and-integrations.md).

Infrastructure runtime updates must follow [Infrastructure Dependency Management](infrastructure-dependency-management.md).

New functionality must satisfy [Feature Development Plan](feature-development-plan.md) before release approval.

Database migration and version compatibility rules are documented in [Migration and Version Compatibility Plan](migration-compatibility-plan.md).

Every release candidate must satisfy [Change Acceptance Policy](change-acceptance-policy.md).

Acceptance testing must follow [QA Test Data and Acceptance Scenarios](qa-acceptance-scenarios.md).

Requirement coverage must follow [Requirements Traceability Matrix](requirements-traceability.md).

Documentation completeness must follow [Specification Index](specification-index.md).

Environment configuration and secret readiness must follow [Environment Configuration and Secrets Control](environment-configuration-secrets.md).

Technical debt must be reviewed according to [Technical Debt Management](technical-debt-management.md).

License and third-party component checks must follow [License and Third-Party Component Management](license-third-party-management.md).

API versioning, compatibility, and deprecation checks must follow [API Versioning and Client Compatibility](api-versioning-compatibility.md).

Implementation stage readiness must follow [Implementation Roadmap](implementation-roadmap.md).

## 60.4. Production Update

```bash
bash deploy/backup_postgres.sh
git fetch --tags
git checkout vX.Y.Z
docker compose build
docker compose run --rm api alembic upgrade head
docker compose up -d
curl https://your-domain.example/health
curl https://your-domain.example/ready
```

## 60.5. Rollback

1. Stop intake with `intake_enabled=false`.
2. Check out the previous stable tag.
3. Rebuild and restart containers.
4. Restore the database backup if the failed release changed data incompatibly.
5. Check health and readiness.
6. Re-enable intake.

## 60.6. API Compatibility

Public REST methods use `/api/v1`. Backward-compatible fields can be added. Removing or changing fields requires a new major API version.

# 61. Change Acceptance Policy

Группа спецификации: Релизы


## 61.1. Architectural Principles

All future changes must:

- Preserve the modular project structure.
- Keep business logic, API handlers, data access, workers, security, and infrastructure separated.
- Use documented extension points and existing service layers.
- Avoid duplicating tariff, payment, upload, OAuth, queue, or RBAC logic.
- Include tests and documentation for new behavior.
- Stay within the official TikTok API model.

## 61.2. Change Acceptance Flow

Before accepting a change:

1. Confirm the change matches the technical specification.
2. Confirm architecture impact has been reviewed.
3. Confirm CI/CD passes.
4. Confirm no regression in key user scenarios.
5. Confirm migrations and configuration changes are tested.
6. Confirm security review is complete when user data, payments, OAuth, webhooks, admin functions, or secrets are affected.
7. Update documentation.
8. Update `CHANGELOG.md`.
9. Confirm release readiness.

Requirement links must be updated in [Requirements Traceability Matrix](requirements-traceability.md).

API changes must also satisfy [OpenAPI and Contract Documentation](openapi-contracts.md).

API version compatibility must satisfy [API Versioning and Client Compatibility](api-versioning-compatibility.md).

Technical debt introduced, changed, or resolved by a change must follow [Technical Debt Management](technical-debt-management.md).

New dependencies or third-party components must follow [License and Third-Party Component Management](license-third-party-management.md).

## 61.3. Minimum Quality Criteria

A change can be accepted only when:

- Static analysis passes.
- Required automated tests pass.
- No critical security issue remains open.
- Configuration changes are documented.
- Alembic migrations are reviewed and tested when schema changes exist.
- Backward compatibility is preserved or a migration path is documented.
- Operational impact is understood.
- Rollback or recovery path is known.
- Technical debt impact is reviewed.
- License and third-party component impact is reviewed when dependencies change.

## 61.4. Regression Checks

Key scenarios to protect:

- New user registration and FREE assignment.
- TikTok OAuth connection and disconnect.
- Video upload FSM and queue creation.
- Worker processing and status transitions.
- Robokassa payment creation and ResultURL activation.
- Subscription expiration and return to FREE.
- Admin dashboard and audit logging.
- Health, readiness, metrics, and logs.

QA data and detailed acceptance scenarios are documented in [QA Test Data and Acceptance Scenarios](qa-acceptance-scenarios.md).

## 61.5. Final Requirement

All specification parts form one requirement set for Tik_Tok_Loader. Future changes must respect the architecture, security rules, testing process, deployment process, and operational procedures documented in this repository.

The complete documentation entry point is [Specification Index](specification-index.md).

# 62. QA Test Data and Acceptance Scenarios

Группа спецификации: Качество


Requirement-to-test mapping is maintained in [Requirements Traceability Matrix](requirements-traceability.md).

## 62.1. Test Users

Prepare these accounts in staging:

| Test User | Purpose |
| --- | --- |
| FREE user | Validate free daily limit and default plan assignment |
| PRO user | Validate paid plan behavior and daily limit |
| BUSINESS user | Validate higher paid limit |
| Administrator | Validate admin API and audit log |
| User without TikTok | Validate TikTok connection requirement |

Use test credentials and staging-only data. Do not use production secrets in QA environments.

## 62.2. Acceptance Scenarios

### 62.2.1. New User Registration

Expected result:

- User is created.
- Terms flow works.
- FREE plan is assigned.
- Audit and diagnostic logs contain expected entries.

### 62.2.2. TikTok OAuth Connection

Expected result:

- OAuth starts through official TikTok authorization.
- Callback validates `state`.
- Tokens are encrypted before storage.
- User receives a successful connection notification.

### 62.2.3. Successful Video Publication

Expected result:

- Upload job is created.
- Video is validated.
- Job is queued and processed.
- Official TikTok API acceptance is recorded.
- User daily usage is incremented only after acceptance.
- User receives final notification.

### 62.2.4. Daily Limit Exceeded

Expected result:

- User cannot exceed the plan limit.
- No extra upload is accepted.
- User receives a clear limit notification.
- Logs include user and correlation context.

### 62.2.5. PRO Purchase Through Robokassa

Expected result:

- Payment order and `InvId` are created.
- Robokassa ResultURL signature, amount, currency, and `InvId` are verified.
- Subscription activates only after ResultURL.
- SuccessURL does not activate subscription.
- User receives payment success notification.

### 62.2.6. Automatic Return to FREE

Expected result:

- Expired PRO or BUSINESS subscription is marked expired.
- FREE becomes active.
- User history remains intact.
- User receives expiration or plan-change notification when applicable.

### 62.2.7. Repeated Webhook

Expected result:

- Duplicate webhook is detected.
- Processing is idempotent.
- Payment or subscription is not activated twice.
- Webhook event history contains enough diagnostic detail.

### 62.2.8. Temporary Queue Failure Recovery

Expected result:

- Temporary failure is retried safely.
- Non-retryable failures are not retried automatically.
- Job status remains consistent.
- Daily usage is not double-counted.

## 62.3. Success Criteria

All acceptance scenarios must:

- Finish with the expected result.
- Produce no unhandled exceptions.
- Preserve database integrity.
- Produce required logs, audit records, and diagnostic identifiers.
- Send correct user notifications.
- Leave queues and counters in a consistent state.

## 62.4. Release Rule

A release candidate is not ready until required QA scenarios pass in staging or an equivalent controlled environment.

# 63. Acceptance Checklist

Группа спецификации: Качество


Final implementation must satisfy [Architecture Summary](architecture-summary.md).

Non-functional requirements must be validated according to [Non-Functional Requirements](non-functional-requirements.md).

Documentation completeness must be checked against [Specification Index](specification-index.md).

Implementation progress must be checked against [Implementation Roadmap](implementation-roadmap.md).

## 63.1. Functional Readiness

- New Telegram user registration works.
- FREE plan is assigned automatically.
- User agreement flow works.
- TikTok OAuth 2.0 connection uses the official TikTok authorization flow.
- TikTok OAuth tokens are encrypted in storage.
- Video upload FSM works: video, description, hashtags, confirmation.
- Video validation and preparation work for MP4, MOV, and WEBM.
- Upload lifecycle events are recorded.
- FREE, PRO, and BUSINESS limits match the specification.
- Robokassa payment link generation works for PRO and BUSINESS.
- Robokassa ResultURL activates paid subscriptions.
- SuccessURL does not activate subscriptions.
- User can disconnect TikTok.

## 63.2. Technical Readiness

- `docker compose up -d` starts all services.
- PostgreSQL and Redis are not exposed publicly.
- API, PostgreSQL, Redis, and Nginx healthchecks pass.
- Alembic migrations apply cleanly.
- Migration compatibility checks are complete.
- CI passes Ruff format, Ruff lint, MyPy, tests, Alembic, Docker build, and secret scan.
- `.env` files are not committed.
- `.env.example` is complete and current.
- Confidential data handling and secret rotation policy is documented.
- Environment configuration and secret readiness are verified.
- OpenAPI is available at `/docs` and `/openapi.json`.
- API version compatibility and deprecation impact have been reviewed.
- Requirements traceability matrix is current.
- Specification index is current.
- Technical debt register has been reviewed.
- License and third-party component register has been reviewed.
- Non-functional requirements have been checked.

## 63.3. Operational Readiness

- Production `.env` is prepared.
- HTTPS is configured.
- Telegram, TikTok, and Robokassa callbacks are configured.
- PostgreSQL backup works.
- Restore drill has been tested on staging.
- Backup and restore policy is documented and current.
- `/health`, `/ready`, and `/metrics` are monitored.
- Security logging and audit requirements are verified.
- Capacity thresholds and scaling actions are documented.
- Service continuity plan is documented and current.
- Infrastructure dependency update policy is documented and current.
- Incident management process is documented.
- Operations runbook is current.
- Release and rollback procedures are documented.

## 63.4. Final Sign-Off

Project is ready for production only after functional, integration, security, and operational checks pass successfully.

Required QA scenarios are documented in [QA Test Data and Acceptance Scenarios](qa-acceptance-scenarios.md).

Requirement coverage is tracked in [Requirements Traceability Matrix](requirements-traceability.md).

The first production run should follow [Production Launch Plan](production-launch.md).

Post-launch support should follow [Post-Launch Maintenance and Versioning](post-launch-maintenance.md).

Future changes should be accepted through [Change Acceptance Policy](change-acceptance-policy.md).

# 64. Requirements Traceability Matrix

Группа спецификации: Приложения


## 64.1. Purpose

Each functional requirement must have a stable identifier and a visible link to implementation, tests, and documentation.

## 64.2. Initial Matrix

| ID | Requirement | Component | Test | Documentation | Status |
| --- | --- | --- | --- | --- | --- |
| `REQ-001` | User registration | Telegram Bot | `QA-REG-001` | [Users Entity](users-entity.md), [QA Scenarios](qa-acceptance-scenarios.md) | Planned |
| `REQ-002` | TikTok OAuth | FastAPI / OAuth | `QA-OAUTH-001` | [TikTok Developer Configuration](tiktok-developer-configuration.md), [Public REST API](public-rest-api.md) | Planned |
| `REQ-003` | PRO/BUSINESS payment | Robokassa | `QA-PAY-001` | [Payments Entity](payments-entity.md), [Robokassa Setup](robokassa.md) | Planned |
| `REQ-004` | Video publication | Worker / TikTok API | `QA-UPL-001` | [Upload Jobs Entity](upload-jobs-entity.md), [Video Lifecycle](video-lifecycle.md) | Planned |
| `REQ-005` | Daily limits | `daily_usage` | `QA-LIMIT-001` | [Daily Usage Entity](daily-usage-entity.md) | Planned |
| `NFR-001` | Performance, reliability, security, maintainability, and scalability controls | Cross-cutting | Release readiness checks | [Non-Functional Requirements](non-functional-requirements.md) | Planned |
| `NFR-002` | Security logging and audit | Observability / Audit | Release readiness checks | [Security Logging and Audit](security-logging-audit.md) | Planned |
| `NFR-003` | Infrastructure dependency management | Deployment / Operations | Post-update checks | [Infrastructure Dependency Management](infrastructure-dependency-management.md) | Planned |
| `NFR-004` | Confidential data management | Security / Configuration | Release readiness checks | [Confidential Data Policy](confidential-data-policy.md) | Planned |
| `DOC-001` | Specification index and documentation maintenance | Documentation | Release readiness checks | [Specification Index](specification-index.md) | Planned |
| `CFG-001` | Environment configuration and secrets control | Configuration / Security | Release readiness checks | [Environment Configuration and Secrets Control](environment-configuration-secrets.md) | Planned |
| `TD-001` | Technical debt management | Development / Maintenance | Release readiness checks | [Technical Debt Management](technical-debt-management.md) | Planned |
| `DEP-001` | License and third-party component management | Dependencies / Release | Release readiness checks | [License and Third-Party Component Management](license-third-party-management.md) | Planned |
| `API-001` | API versioning and client compatibility | REST API / OpenAPI | Compatibility checks | [API Versioning and Client Compatibility](api-versioning-compatibility.md) | Planned |
| `ROAD-001` | Final implementation roadmap | Delivery / Release | Roadmap control points | [Implementation Roadmap](implementation-roadmap.md) | Planned |

## 64.3. Maintenance Rules

- Every new requirement receives a unique `REQ-###` identifier.
- Every new acceptance scenario receives a unique `QA-...` identifier.
- Requirement changes must update implementation, tests, and documentation links.
- Removing a requirement must be documented in `CHANGELOG.md`.
- The matrix must be reviewed before every release.
- A requirement is complete only when implementation, automated or manual QA coverage, and documentation are all present.

## 64.4. Completion Criterion

The project is release-ready only when every approved requirement has traceability to implementation, tests, and documentation.

# 65. Glossary and Naming Conventions

Группа спецификации: Приложения


## 65.1. Glossary

| Term | Definition |
| --- | --- |
| Upload Job | Task for processing and publishing one video |
| Subscription | Active or historical user tariff assignment |
| Daily Usage | Daily publication limit accounting |
| Webhook Event | Inbound event from an external service or internal callback |
| Worker | Background process that handles queued tasks |
| Request ID | Unique identifier for one HTTP request |
| Correlation ID | Identifier for a chain of related operations |
| Plan | Tariff definition: FREE, PRO, or BUSINESS |
| Payment | Robokassa payment record |
| Admin Action | Immutable administrative audit event |
| System Setting | Mutable non-secret runtime configuration value |

## 65.2. Naming Conventions

- Database tables use `snake_case` and plural names.
- Python modules use `snake_case`.
- Python classes use `PascalCase`.
- Variables and functions use `snake_case`.
- REST endpoints use the existing project style and kebab-case only when it improves readability.
- Environment variables use uppercase `SNAKE_CASE`.
- Plan names are written as `FREE`, `PRO`, and `BUSINESS` in product and technical documentation.

## 65.3. Entity Names

Use these canonical names:

| Canonical Name | Database Table |
| --- | --- |
| User | `users` |
| TikTok Account | `tiktok_accounts` |
| Plan | `plans` |
| Subscription | `subscriptions` |
| Payment | `payments` |
| Upload Job | `upload_jobs` |
| Upload Job Event | `upload_job_events` |
| Daily Usage | `daily_usage` |
| Webhook Event | `webhook_events` |
| Admin Action | `admin_actions` |
| System Setting | `system_settings` |

## 65.4. Consistency Rule

Code, documentation, database schema, tests, API responses, and user-facing text should use the same terminology unless an external provider requires a different term.

When a current implementation uses a different internal field name, document the mapping in the relevant entity specification and change it only through Alembic migration and compatibility review.

# 66. Specification Index

Группа спецификации: Приложения


This document is the final index for the Tik_Tok_Loader technical specification. All specification parts are treated as one requirement set for development, testing, deployment, operations, and maintenance.

## 66.1. Purpose

The current documentation set is the authoritative project specification. It is used as:

- Technical assignment.
- Architecture specification.
- Development guide.
- QA and acceptance reference.
- Deployment and operations guide.
- Maintenance and change-control reference.

## 66.2. Core Specification Groups

| Group | Documents |
| --- | --- |
| Architecture | [Architecture Summary](architecture-summary.md), [Project Component Map](component-map.md), [Sequence Flows](sequence-flows.md), [Glossary and Naming Conventions](glossary-naming.md) |
| Functional behavior | [User Guide](user-guide.md), [Video Lifecycle](video-lifecycle.md), [Robokassa Setup](robokassa.md), [TikTok Developer Configuration](tiktok-developer-configuration.md) |
| Data model | [Logical Data Model](data-model.md), entity specifications for users, TikTok accounts, subscriptions, payments, upload jobs, usage, webhooks, admin actions, and settings |
| API contracts | [REST API Standards](rest-api-standards.md), [API Versioning and Client Compatibility](api-versioning-compatibility.md), [Public REST API](public-rest-api.md), [Administrative REST API](admin-rest-api.md), [OpenAPI and Contract Documentation](openapi-contracts.md), [Error Codes and Exception Handling](error-handling.md) |
| Security and compliance | [Compliance Notes](compliance.md), [Security, Backup, and Monitoring](security.md), [Security Logging and Audit](security-logging-audit.md), [Confidential Data Policy](confidential-data-policy.md), [Environment Configuration and Secrets Control](environment-configuration-secrets.md), [RBAC-related admin documentation](admin-rest-api.md) |
| Operations | [Deployment](deployment.md), [Production Launch Plan](production-launch.md), [Operations Runbook](operations-runbook.md), [SOP Checklists](sop-checklists.md), [Incident Response and Disaster Recovery](incident-response.md), [Incident Management](incident-management.md) |
| Reliability and scale | [Non-Functional Requirements](non-functional-requirements.md), [Performance and Scaling](performance.md), [Capacity and Performance Management](capacity-management.md), [Queue and Retry Policy](queue-retry-policy.md), [Service Continuity Plan](service-continuity-plan.md) |
| Data protection and retention | [Data Retention](data-retention.md), [File Storage Policy](file-storage-policy.md), [Backup and Restore Policy](backup-restore-policy.md) |
| Release and change control | [Release Management](release.md), [Post-Launch Maintenance and Versioning](post-launch-maintenance.md), [Change Acceptance Policy](change-acceptance-policy.md), [Migration and Version Compatibility Plan](migration-compatibility-plan.md), [Infrastructure Dependency Management](infrastructure-dependency-management.md), [License and Third-Party Component Management](license-third-party-management.md), [Technical Debt Management](technical-debt-management.md) |
| Quality control | [Implementation Roadmap](implementation-roadmap.md), [QA Test Data and Acceptance Scenarios](qa-acceptance-scenarios.md), [Acceptance Checklist](acceptance-checklist.md), [Requirements Traceability Matrix](requirements-traceability.md), [Development Standards](development.md) |

## 66.3. Documentation Maintenance Rules

- Every functionality change must update the relevant documentation section in the same change set.
- Architecture changes must be documented before release approval.
- New entities, API endpoints, background jobs, configuration keys, scenarios, and external integration behavior must be documented together with implementation.
- Documentation version must match the application version and release notes.
- `CHANGELOG.md` must describe user-facing, operational, security, dependency, and documentation changes relevant to the release.
- Requirement links must be kept current in [Requirements Traceability Matrix](requirements-traceability.md).
- Technical debt must be reviewed before release according to [Technical Debt Management](technical-debt-management.md).

## 66.4. Completeness Control

Before release, verify:

- Documentation matches implemented code.
- Documentation matches automated and manual tests.
- Documentation matches environment variables and configuration templates.
- OpenAPI matches implemented REST endpoints.
- Alembic migrations match the documented data model.
- Operational runbooks match the deployed infrastructure.
- Security, confidential data, logging, backup, and retention policies are current.
- Specification version is fixed for the release.
- Technical debt status is reviewed and documented.
- License and third-party component status is reviewed and documented.
- Implementation roadmap status is reviewed.

## 66.5. Release Rule

The documentation set must be reviewed before every production release. A release is not ready if code, tests, configuration, deployment procedures, OpenAPI contracts, or operational runbooks contradict the current specification.

## 66.6. Final Statement

The specification parts form the project documentation foundation for Tik_Tok_Loader. The set must be used as the technical assignment, architecture specification, and maintenance guide for future development.

# 67. Risk Management

Группа спецификации: Приложения


## 67.1. Operational Constraints

- Use only official TikTok interfaces.
- Do not perform actions outside granted OAuth permissions.
- Do not store secrets in Git.
- External integrations must handle temporary unavailability.
- Do not retry TikTok authorization errors or platform restriction errors automatically.

## 67.2. Risk Register

| Risk | Controls |
| --- | --- |
| External API unavailable | Retry temporary failures only, log errors, keep queue state durable |
| Robokassa payment errors | Validate ResultURL signature, amount, currency, and InvId; process idempotently; audit all status changes |
| Load growth | Scale API workers and Dramatiq workers horizontally; paginate admin lists; monitor queue size |
| PostgreSQL failure | Back up regularly and test restores on staging |
| Redis failure | Keep canonical upload/payment/subscription state in PostgreSQL; restart services safely |
| Bad release | Back up before deploy, test on staging, deploy step-by-step, monitor after release |
| Secret leakage | Keep secrets in `.env` or secret storage only; CI secret scan; never export secret-like settings |
| Video processing failure | Validate files before publishing; do not consume daily quota until official TikTok API accepts publication |

## 67.3. Change Control

Before production changes:

1. Assess API, database, security, and user-flow impact.
2. Add or update tests.
3. Update documentation.
4. Test in staging.
5. Create a production backup.
6. Deploy step-by-step.
7. Monitor `/health`, `/ready`, `/metrics`, queues, payments, and TikTok API errors.

## 67.4. Resilience Criteria

The system must preserve user history, payment records, subscriptions, upload metadata, and audit trails during temporary external failures and controlled restarts.

