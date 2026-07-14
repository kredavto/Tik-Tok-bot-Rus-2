# Changelog

All notable changes to Tik_Tok_Loader are documented here.

The project follows Semantic Versioning.

## [Unreleased]

### Added

- Responsive administrative console for users, tariffs, payments, publication queue, runtime
  settings, analytics, and audit history.
- Versioned `/api/v1/admin` endpoints for user details, FREE fallback, publication error review,
  eligible task retry, typed settings, and audit search.
- Alembic `0006_admin_console` migration for administrative request IP and typed setting metadata.
- Runtime system-setting seeds and database-backed retention policy values.
- Admin console security and retry-classification regression tests.
- Production Telegram webhook dispatch through FastAPI with Redis-backed aiogram FSM.
- TikTok creator-info flow with manual privacy, interaction, and commercial-content choices.
- Official TikTok Content Posting status polling and final webhook handling.
- Chunked TikTok file upload for videos larger than 64 MB.
- PostgreSQL migrations for Robokassa invoice sequencing, active-subscription integrity, and
  TikTok post options.
- Regression tests for TikTok signatures, replay protection, chunk planning, creator info,
  webhook configuration, localization, and bot keyboards.
- Redis-leased scheduler with a heartbeat healthcheck.
- Automatic paid-subscription expiry, FREE fallback, and retryable Telegram notification state.
- Proactive TikTok token refresh with permanent OAuth error blocking.
- Alembic maintenance-state migration and scheduler lease regression tests.

### Changed

- Daily limits now use `Europe/Moscow` by default.
- Runtime plan prices, limits, activation flags, and durations are read from PostgreSQL without
  being overwritten at startup.
- Paid subscription activation expires the previous active subscription transactionally.
- TikTok webhook verification now follows the official `TikTok-Signature` timestamped HMAC format.
- Added the explicit SQLAlchemy `greenlet` runtime dependency.
- TikTok OAuth start now accepts only a short-lived state created by the Telegram bot.
- Full upload jobs are no longer retried after an ambiguous failure; deterministic byte-range
  chunk uploads retry server errors with bounded exponential backoff.
- Docker images now include Alembic configuration and migration files required by API startup.

### Security

- Admin UI credentials remain in page memory and are not written to browser storage.
- Administrative static responses use CSP, frame denial, no-sniff, and no-store headers.
- User detail endpoints expose TikTok account metadata without OAuth token fields.
- Local Word files containing Telegram API tokens are excluded from Git.
- Production webhook mode fails startup without HTTPS and a Telegram webhook secret.
- Public requests can no longer choose a Telegram user identifier during TikTok OAuth linking.

## [0.1.0] - 2026-07-12

### Added

- Initial production scaffold.
- Telegram bot with aiogram 3.x and FSM flows.
- FastAPI backend for health checks, OAuth, webhooks, payments, admin API, and metrics.
- PostgreSQL 16 schema with SQLAlchemy async and Alembic migration.
- Redis cache, rate limiting, OAuth state storage, and Dramatiq queue.
- Robokassa payment flow for PRO and BUSINESS plans.
- Official TikTok Content Posting API integration scaffold with OAuth 2.0.
- Encrypted storage for TikTok OAuth tokens.
- Admin API, analytics, audit logging, and system settings.
- Docker Compose with bot, api, worker, postgres, redis, and nginx.
- Security, backup, deployment, API, and administrator documentation.
- CI pipeline for linting, typing, tests, Alembic, Docker build, and secret scan.
- RBAC roles and permission checks.
- Upload lifecycle audit events.
- Retention settings and cleanup tasks.
- Performance, scaling, data retention, and user documentation.
- Release management and environment templates.
- Operations runbook for routine maintenance.
- Incident management process for P1-P4 production issues.
- Runtime configuration export/import with audit trail.
- Final acceptance checklist.
- Risk management register and operational constraints.
- GitHub workflow, PR template, issue templates, and CODEOWNERS.
- SOP checklists for production preflight, post-update checks, diagnostics, and incident documentation.
- Production launch plan and handover checklist.
- Post-launch maintenance, versioning, release quality gates, and monitoring plan.
- Daily, weekly, configuration-change, and emergency SOP checklists.
- Dependency update policy and third-party service compatibility controls.
- Feature development plan for modular expansion, compatibility, tests, staging, and release quality.
- Operational metrics and KPI registry for admin analytics, scaling, and release quality.
- Final architecture summary with mandatory principles, subsystems, functional commitments, and compliance boundary.
- Observability and diagnostics strategy with Request ID, Correlation ID, JSON logs, diagnostic events, and retention rules.
- Queue and retry policy for background tasks, duplicate prevention, non-retryable errors, and administrative control.
- File storage policy for temporary videos, directory structure, cleanup, disk monitoring, and path security.
- TikTok Developer configuration policy for OAuth, scopes, webhook signatures, pre-release checks, and change control.
- Data quality and integrity policy for server validation, database constraints, transactions, periodic checks, and new entity requirements.
- Migration and version compatibility plan for Alembic safety, backups, rollout, rollback, and post-update control.
- Backup and restore policy for PostgreSQL, server configuration, documentation, audit logs, restore drills, and recovery criteria.
- Capacity and performance management plan for resource monitoring, thresholds, scaling actions, and periodic review.
- Service continuity plan for critical services, health checks, planned maintenance, external degradation, and recovery readiness.
- Final change acceptance policy for post-launch architecture, quality gates, regression checks, documentation, and release readiness.
- Error code catalog and exception handling strategy for REST errors, user messages, logging, and retry classification.
- REST API standards for JSON response envelopes, `/api/v1` compatibility, HTTP status codes, OpenAPI updates, and request tracing.
- Logical data model for core entities, relationships, UUID/FK integrity rules, and business persistence rules.
- Users entity specification for Telegram identity, current plan reference, active state, relationships, transactional updates, and audit requirements.
- TikTok accounts entity specification for encrypted OAuth tokens, TikTok open ID, upload links, token refresh, disconnect, and audit requirements.
- Subscriptions entity specification for FREE/PRO/BUSINESS lifecycle, active-subscription rules, history retention, payment links, and audit requirements.
- Payments entity specification for Robokassa invoices, ResultURL-only activation, idempotency, status audit, and transaction safety.
- Upload jobs entity specification for publication lifecycle, status transitions, retry rules, error codes, and quota consumption timing.
- Daily usage entity specification for per-day limits, Europe/Moscow reset, transactional counters, plan changes, and duplicate-processing protection.
- Webhook events entity specification for inbound event storage, idempotent processing, signature validation, payload safety, and admin-only access.
- Admin actions entity specification for immutable audit records, fixed administrative events, search requirements, retention, and sensitive data masking.
- System settings entity specification for mutable non-secret configuration, value typing, admin editability, audit trail, and secret exclusion.
- Administrative REST API specification for `/api/v1/admin` endpoints, authentication, RBAC, audit logging, transactions, and compatibility.
- Public REST API specification for `/api/v1` health, readiness, TikTok OAuth, webhooks, Robokassa ResultURL, compatibility, and error handling.
- OpenAPI and contract documentation policy for endpoint schemas, examples, authorization, error codes, versioning, compatibility, and release checks.
- Sequence flow documentation for video publication and Robokassa payment interactions across bot, API, queue, worker, database, and external services.
- Glossary and naming conventions for canonical project terms, database tables, Python code, REST endpoints, environment variables, and tariff names.
- QA test data and acceptance scenarios for users, TikTok OAuth, publication, limits, Robokassa, duplicate webhooks, queue recovery, and release criteria.
- Requirements traceability matrix linking functional requirements to components, QA cases, documentation, and release readiness.
- Final project component map covering core subsystems, interaction flows, architecture principles, and documentation navigation.
- Non-functional requirements covering performance, reliability, security, maintainability, scalability, and release acceptance.
- Security logging and audit requirements for JSON logs, required security events, masking, retention, search, and incident investigation.
- Infrastructure dependency management plan for Ubuntu, Docker, Nginx, PostgreSQL, Redis, Python libraries, base images, update policy, and compatibility checks.
- Confidential data policy for OAuth tokens, Robokassa secrets, Telegram tokens, encryption keys, backups, least privilege, audit, and rotation.
- Final specification index and documentation maintenance rules covering completeness checks, version alignment, and release readiness.
- Environment configuration and secrets control rules for development, staging, production, startup validation, rotation, and release compliance.
- Technical debt management plan with `TD-###` records, priorities, owners, remediation plans, review cadence, and release control.
- License and third-party component management policy covering component registry, license checks, vulnerability control, dependency additions, and release requirements.
- API versioning and client compatibility policy for `/api/v1`, breaking changes, lifecycle stages, deprecation, OpenAPI updates, and release checks.
- Final implementation roadmap covering infrastructure, database, bot, TikTok API, Robokassa, workers, admin, CI/CD, testing, and production launch.
- Unified project specification generated in Markdown, DOCX, and PDF formats with title page, table of contents, numbered sections, abbreviation list, appendices, and reusable build script.
