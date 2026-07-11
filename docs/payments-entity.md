# Payments Entity

## Purpose

`payments` stores payment records for PRO and BUSINESS subscriptions paid through the existing Robokassa merchant account.

## Recommended Fields

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

## Relationships

| Relationship | Cardinality |
| --- | --- |
| `users` -> `payments` | 1:N |
| `subscriptions` -> `payments` | 1:N |

## Business Rules

- FREE does not create a payment record.
- Only PRO and BUSINESS purchases create payment records.
- Subscription activation happens only after verified Robokassa ResultURL.
- SuccessURL is informational and must not activate a subscription.
- Repeated ResultURL notifications must be idempotent and must not activate the same subscription twice.
- Every payment status change must be auditable.

## Security Requirements

- Do not store Robokassa secrets in `payments`.
- Verify digital signature before changing payment status.
- Verify amount before changing payment status.
- Verify currency when Robokassa provides it.
- Verify `InvId` before changing payment status.
- Do not log Robokassa passwords or raw secrets.
- Execute payment and subscription changes in a single transaction.

## Development Requirement

Changes to `payments` require updated SQLAlchemy models, Alembic migrations, tests, documentation, Robokassa idempotency checks, and security review.
