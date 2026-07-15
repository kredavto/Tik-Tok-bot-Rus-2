# Data Quality and Integrity

## Server-Side Validation

- Validate all external input on the server.
- Use Pydantic schemas for API request and response validation.
- Validate required fields, types, enum values, ranges, identifiers, and timestamps.
- Reject invalid requests with a clear error response.
- Do not rely on Telegram, browser, or admin UI validation as the only protection.

## Database Integrity

- Use foreign keys for relationships between users, TikTok accounts, subscriptions, payments, upload jobs, events, and audit records.
- Use unique constraints for natural uniqueness, such as Telegram user ID, payment invoice ID, and OAuth account ownership where applicable.
- Use indexes for frequently queried identifiers and statuses.
- Use transactions for critical operations.
- Roll back the full transaction when a critical step fails.
- Do not allow partial persistence for payments, subscriptions, quota consumption, or upload state transitions.

Logical relationships are documented in [Logical Data Model](data-model.md).

## Critical Transaction Boundaries

Transactions are required for:

- New user registration and FREE plan assignment.
- Robokassa ResultURL verification and subscription activation.
- Daily upload quota consumption.
- Upload status transition and lifecycle event creation.
- TikTok account token update.
- Admin plan and system setting changes.
- User anonymization and TikTok disconnect.

User-specific integrity rules are documented in [Users Entity](users-entity.md).

TikTok account integrity and token storage rules are documented in [TikTok Accounts Entity](tiktok-accounts-entity.md).

Subscription integrity rules are documented in [Subscriptions Entity](subscriptions-entity.md).

Payment integrity rules are documented in [Payments Entity](payments-entity.md).

Upload job integrity rules are documented in [Upload Jobs Entity](upload-jobs-entity.md).

Daily usage integrity rules are documented in [Daily Usage Entity](daily-usage-entity.md).

Webhook event integrity rules are documented in [Webhook Events Entity](webhook-events-entity.md).

Admin action integrity rules are documented in [Admin Actions Entity](admin-actions-entity.md).

System setting integrity rules are documented in [System Settings Entity](system-settings-entity.md).

## Data Quality Checks

Run periodic checks for:

- Orphaned records without valid foreign-key parents.
- Upload jobs with invalid status transitions.
- Payments marked paid without a matching subscription activation.
- Active subscriptions with expired `ends_at`.
- Users without an active or fallback FREE plan.
- Upload jobs referencing missing local files before retention expiry.
- Webhook events processed more than once without idempotency markers.
- Admin actions missing actor, action type, or timestamp.

Detected inconsistencies must be logged with UTC timestamps, affected identifiers, severity, and remediation status.

## Status Consistency

Publication statuses must follow [Video Publication Lifecycle](video-lifecycle.md).

Payment statuses must remain within the documented provider states:

- `created`
- `pending`
- `paid`
- `refund_pending` (Telegram Stars only)
- `failed`
- `cancelled`
- `refunded`

Terminal statuses must not be overwritten by stale retries.

## Development Requirements

Every new persistent entity must include:

- SQLAlchemy model definition.
- Alembic migration.
- Pydantic validation schema when exposed through API or admin operations.
- Foreign keys, indexes, and unique constraints where appropriate.
- Unit or integration tests for valid and invalid data.
- Documentation updates.
- Changelog entry when behavior or operations change.

Migration compatibility and production rollout rules are documented in [Migration and Version Compatibility Plan](migration-compatibility-plan.md).

## Operational Goal

Data handling must preserve referential integrity, prevent silent corruption, and keep enough diagnostic context for safe repair when inconsistencies are detected.
