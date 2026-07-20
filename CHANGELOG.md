# Changelog

All notable changes to Tik_Tok_Loader are documented here.

The project follows Semantic Versioning.

## [Unreleased]

### Added

- `/connect` Telegram command as an accessible alternative to the TikTok OAuth menu button.
- Review-ready TikTok publication preview and literal Music Usage Confirmation / Branded Content
  Policy declarations before the final publish action.
- User-safe handling for TikTok creator posting caps and posting bans returned by creator-info.

### Changed

- Record successful TikTok Sandbox OAuth acceptance, encrypted token persistence, replay
  protection, Telegram notification, and official Creator Info verification on 2026-07-20.
- Align commercial-content disclosure with TikTok Direct Post UX: the control is off by default,
  enabled explicitly, supports own-brand and branded-content multi-selection, and displays the
  resulting `Promotional content` or `Paid partnership` label.

## [0.2.0] - 2026-07-17

### Added

- Public Tik_Tok_Loader service page, Terms of Service, Privacy Policy, hardened response headers,
  and an original 1024 x 1024 application icon for TikTok Developer review.
- Production TikTok Developer Portal values and a Sandbox demo/review evidence checklist.

- Telegram Stars (`XTR`) invoice flow with pre-checkout validation, transactional subscription
  activation, unique charge tracking, duplicate-delivery protection, `/paysupport`, configurable
  plan prices, and separate Stars analytics.
- Alembic `0008_telegram_stars_payments` migration and focused Stars concurrency/security tests.
- Alembic `0009_set_stars_plan_prices` migration setting PRO to `199 XTR` and BUSINESS to
  `499 XTR`.
- Audited admin operations for external-channel Robokassa checkout creation and official Telegram
  Stars refunds.
- A Cloudflare Tunnel Compose override that exposes only the API on a configurable loopback port and
  leaves the bundled Nginx service disabled unless explicitly selected.
- An audited Stars refund reconciliation endpoint for unresolved provider outcomes.

### Changed

- Record the successful 2026-07-17 production Telegram Stars acceptance: an audited temporary
  `10 XTR` PRO price, one confirmed payment and subscription, official refund, automatic FREE
  restoration, and restoration of the approved `199 XTR` price.
- Update the unified specification to revision `0.9.4`; decouple Telegram Stars checkout from RUB
  pricing, use single-chat invoices, persist definitive invoice rejection, keep `/terms` available,
  register the supported Telegram command menu, and surface pending refunds in the administrator
  payment view.
- Update the unified specification to revision `0.9.2` with completed Robokassa provider
  acceptance, production infrastructure status, remaining TikTok/Stars gates, and corrected
  in-bot versus external-channel payment flows.
- Generate the unified PDF specification with a multi-level table of contents, page numbers, and
  clickable document outline entries.
- In-bot paid-plan checkout now follows Telegram's digital-goods requirement and no longer exposes
  Robokassa links as an alternative to Stars.
- Payment records and administrator views now distinguish provider, currency, RUB amount, Stars
  amount, and provider charge identifier.
- SBP was removed from the approved project scope; supported payment integrations are Robokassa
  and Telegram Stars only.

### Fixed

- Prevent Robokassa callback signatures and other credentials from reaching application, Uvicorn,
  or Nginx access logs; sanitize persisted callback payloads and scrub historical JSONB records.
- Make Telegram Stars refunds recoverable across network and database failures with a committed
  `refund_pending` claim, duplicate-send suppression, and `refunded_payment` reconciliation.
- Reject unapproved tracked DOCX/PDF files in the secret gate and exclude binary documents from
  Docker build contexts.
- Add behavioral RBAC, CSRF, audit, idempotency, and ambiguous-failure tests for payment admin
  operations.
- Support the Robokassa shop's configured MD5, SHA-256, or SHA-512 algorithm with constant-time
  signature comparison, and restrict ResultURL activation by provider, currency, and payment state.
- Ignore the local Robokassa credential document and preserve administrator-customized Stars prices
  when downgrading the default-price migration.
- Allow the scheduler heartbeat healthcheck enough time for Python startup on constrained hosts,
  preventing a working scheduler from being reported as unhealthy.
- Make inbound webhook claims atomic across API workers, separate reverse-proxied clients for
  rate limiting, accept Robokassa payment-method aliases, preserve accepted TikTok publications
  when quota state changes, and periodically reconcile posts still processing at TikTok.
- Persist TikTok acceptance, publication status, and daily quota before local cache,
  notification, queue, or file-cleanup side effects, preventing accepted posts from being
  reclassified as failed when infrastructure is temporarily unavailable.
- Bind each administrative API token to a server-configured Telegram principal, reject blocked or
  unprovisioned admins, and remove client-controlled RBAC identity headers.
- Reject delayed Stars success events after refund initiation or completion, classify definitive
  refund rejections, and provide an audited recovery path for ambiguous outcomes.
- Apply the Cloudflare Compose override automatically in checked preflight, deploy, and rollback
  flows when `DEPLOY_INGRESS=cloudflared`.
- Extract and scan text from the approved generated DOCX/PDF artifacts for high-risk secrets.
- Exercise Robokassa ResultURL end to end over HTTP, including signature, currency, duplicate
  delivery, subscription activation, and `OK{InvId}` response behavior.
- Persist Robokassa payment-success notifications in a transactional PostgreSQL outbox so callback
  acknowledgement is independent of Redis and Telegram availability.
- Protect pending payment notifications from retention cleanup and prevent permanently rejected
  Telegram recipients from starving newer outbox events.
- Run all Dramatiq actor coroutines on one persistent event loop per worker process, preventing
  asyncpg connection-pool races between Dramatiq threads.

## [0.2.0-rc.1] - 2026-07-14

### Added

- Deterministic release-candidate manifest with version, Git, source-tree, migration, and required
  quality-gate metadata, generated by CI and verified again during deployment.
- Production/staging preflight covering exact callback contracts, TLS lifetime and key matching,
  Docker/Compose readiness, clean tracked state, and minimum free disk space.
- Explicit Telegram webhook configure/verify/delete command, drift monitor, and deployment smoke
  verification that preserves pending updates.
- Staging acceptance runbook with provider-backed scenarios and sanitized release evidence.
- Comprehensive FSM, video-validation, API-contract, worker-lock, queue-lease, payment,
  subscription, quota-concurrency, and upload-lifecycle tests.
- CI coverage gate with XML output, OpenAPI contract validation, and application compile check.
- Test strategy defining automated layers, concurrency guarantees, staging boundaries, and release
  evidence.
- Four-job GitHub Actions pipeline for quality/security, database integration, container runtime,
  and deterministic release-candidate evidence.
- Target-aware deployment environment validator with secret-safe diagnostics.
- Verified PostgreSQL backup, confirmed restore, application rollback, and public smoke-test
  scripts.
- Nginx HTTP/HTTPS templates with TLS hardening, ACME bootstrap path, and production headers.
- CI/CD and deployment automation guide with Termius-compatible server commands.
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

- Public deployment smoke checks now cover versioned health, readiness and metrics endpoints,
  required OpenAPI callback paths, admin security headers, and Telegram webhook state.
- Environment templates now use canonical versioned callbacks and include webhook monitoring and
  TikTok webhook compatibility variables.
- Telegram user registration and daily usage initialization now use PostgreSQL upserts to preserve
  uniqueness under concurrent requests.
- Robokassa ResultURL processing now locks payment and user rows, rejects malformed amounts with a
  valid payment status, and suppresses duplicate subscription activation and notification.
- REST errors now follow the versioned error catalog with safe messages and request/correlation IDs.
- Application containers now run with dropped capabilities, `no-new-privileges`, init handling,
  and isolated temporary filesystems.
- Alembic startup now uses a one-shot Compose migration gate before API, bot, worker, and
  scheduler services, avoiding concurrent upgrades during horizontal scaling.
- Secret scanning now blocks new findings and always rejects Telegram tokens and private keys.
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
