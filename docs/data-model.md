# Logical Data Model

Canonical entity names are defined in [Glossary and Naming Conventions](glossary-naming.md).

## Core Entities

| Entity | Purpose |
| --- | --- |
| `users` | Telegram users and account-level settings |
| `tiktok_accounts` | Connected TikTok accounts and encrypted OAuth tokens |
| `plans` | FREE, PRO, BUSINESS, and UNLIMIT tariffs |
| `subscriptions` | Active and historical subscriptions |
| `payments` | Provider-neutral payment history for Stars and approved external channels |
| `upload_jobs` | Publication tasks and status |
| `upload_job_events` | Upload lifecycle audit trail |
| `daily_usage` | Daily upload limit counters |
| `webhook_events` | Received Telegram, TikTok, and Robokassa webhook events |
| `admin_actions` | Administrator audit log |
| `system_settings` | Runtime non-secret settings |

## Main Relationships

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

## Integrity Rules

- Internal entities use UUID primary keys unless the domain requires a stable string identifier, such as `plans.id`.
- Foreign keys enforce core relationships.
- User deletion or anonymization must not break payment, subscription, publication, or audit history.
- TikTok OAuth tokens are encrypted before storage.
- Payment history is retained for accounting and audit.
- Daily usage counters are updated transactionally.
- Schema changes are applied only through Alembic migrations.
- All timestamps are UTC and timezone-aware.

## Business Rules

- New users receive the FREE plan automatically.
- Paid subscriptions have a finite `ends_at` value.
- Expired paid subscriptions return users to FREE.
- Payments are activated only after Robokassa ResultURL validation.
- Daily usage is consumed only after official TikTok API acceptance.
- Upload lifecycle transitions are recorded in `upload_job_events`.

## Development Requirement

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
