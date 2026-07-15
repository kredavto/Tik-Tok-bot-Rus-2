# Payments Entity

## Purpose

`payments` stores the immutable history of PRO and BUSINESS payment attempts. Telegram Stars is the
checkout provider for digital subscriptions purchased inside the bot. Robokassa and official SBP C2B
are retained only for separately approved channels that comply with provider and platform rules.

## Recommended Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Internal payment identifier |
| `user_id` | UUID | Reference to `users.id` |
| `subscription_id` | UUID | Related subscription |
| `provider` | VARCHAR | `telegram_stars`, `robokassa`, or approved `sbp` integration |
| `provider_invoice_id` | INTEGER | Internal/Robokassa invoice reference |
| `provider_charge_id` | VARCHAR | Unique provider confirmation ID |
| `amount_rub` | INTEGER | RUB amount snapshot where applicable |
| `amount_stars` | INTEGER | Telegram Stars amount where applicable |
| `currency` | VARCHAR | `XTR` or `RUB` |
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
- Telegram Stars activation happens only after validated `successful_payment`.
- Robokassa activation happens only after verified ResultURL in an approved channel.
- SBP activation requires a bank-confirmed callback or status response, never a QR scan or screenshot.
- SuccessURL is informational and must not activate a subscription.
- Repeated ResultURL notifications must be idempotent and must not activate the same subscription twice.
- Every payment status change must be auditable.

## Security Requirements

- Do not store provider secrets or personal banking data in `payments`.
- Validate the Telegram user, amount, `XTR` currency, invoice payload, and charge ID.
- Verify digital signature before changing payment status.
- Verify amount before changing payment status.
- Verify currency when Robokassa provides it.
- Verify `InvId` before changing payment status.
- Do not log Robokassa passwords or raw secrets.
- Execute payment and subscription changes in a single transaction.

## Development Requirement

Changes to `payments` require updated SQLAlchemy models, Alembic migrations, tests, documentation,
provider-specific idempotency checks, and security review.
