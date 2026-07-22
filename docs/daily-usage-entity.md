# Daily Usage Entity

## Purpose

`daily_usage` tracks publication reservations for FREE, PRO, BUSINESS, and UNLIMIT users.

## Recommended Fields

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

## Business Rules

- Create a record automatically on the first accepted publication of the day.
- The business day resets at 00:00 Europe/Moscow.
- Reserve usage only after the official TikTok API accepts the publication.
- Return the reserved attempt exactly once when TikTok reports final `FAILED`, including provider
  `internal` failures. The upload job stores the accounting date and refund timestamp.
- Do not increment usage for validation, preparation, authorization, or platform-restriction failures.
- `daily_limit=0` means unlimited. Usage is still counted for analytics but never blocks publishing.
- If a user changes plan during the day, recalculate remaining allowance without resetting already used publications.
- Reprocessing the same upload job must not increment the counter twice.

## Integrity Requirements

- `user_id` and `usage_date` must be unique together.
- Counter updates must be transactional.
- Use locking or equivalent concurrency protection before incrementing counters.
- Counter updates must be idempotent for repeated worker attempts.
- Webhook and polling races must not refund one upload more than once.
- Usage changes must be auditable.

## Relationships

| Relationship | Cardinality |
| --- | --- |
| `users` -> `daily_usage` | 1:N |
| `plans` -> `daily_usage` | 1:N logical reference when plan is captured |

## Development Requirement

Changes to `daily_usage` require updated SQLAlchemy models, Alembic migrations, tests for concurrent updates, queue/retry review, and data quality checks.
