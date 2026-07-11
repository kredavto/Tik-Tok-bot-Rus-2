# Subscriptions Entity

## Purpose

`subscriptions` stores active and historical user subscriptions for FREE, PRO, and BUSINESS plans.

## Recommended Fields

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

## Relationships

| Relationship | Cardinality |
| --- | --- |
| `users` -> `subscriptions` | 1:N |
| `plans` -> `subscriptions` | 1:N |
| `subscriptions` -> `payments` | 1:N |

## Business Rules

- New users automatically receive the FREE plan.
- FREE subscriptions have no expiration time.
- PRO and BUSINESS subscriptions expire after the configured paid period.
- After PRO or BUSINESS expires, the user returns to FREE automatically.
- Only one subscription should be active for a user at the same time.
- Switching to a paid plan must not delete historical subscription records.
- Subscription status changes must be transactional.

## Audit Requirements

Audit:

- FREE assignment.
- Paid subscription activation.
- Subscription renewal.
- Subscription expiration.
- Cancellation.
- Manual administrator changes.
- Automatic return to FREE.

## Integrity Requirements

- `user_id` is required.
- `plan_id` is required.
- Historical subscription records must not be deleted.
- Payments linked to subscriptions must remain available for accounting and audit.
- Subscription state changes must not partially update payments, daily limits, or user state.

## Development Requirement

Changes to `subscriptions` require updated SQLAlchemy models, Alembic migrations, tests, documentation, and data quality checks.
