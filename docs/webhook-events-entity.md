# Webhook Events Entity

## Purpose

`webhook_events` stores inbound webhook events from TikTok, Robokassa, Telegram, and internal service callbacks before processing.

## Recommended Fields

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

## Business Rules

- Save every inbound event before processing begins.
- Identify repeated events by `source` and `external_event_id` when the external service provides an ID.
- Processing must be idempotent.
- Processing errors must be logged with sanitized reason and correlation context.
- Mark successful processing with `processed=true` or equivalent terminal processed status.
- Repeated processed events must not duplicate payments, subscription activation, upload status changes, or notifications.

## Security Requirements

- Verify webhook signatures before trusting payload contents.
- Validate payload structure before processing.
- Do not store secret keys in `payload`.
- Mask tokens, passwords, signatures, and secrets in logs.
- Limit webhook event access to authorized administrators and support roles.

## Sources

Supported sources:

- `telegram`
- `tiktok`
- `robokassa`
- Internal service callbacks when needed

## Development Requirement

Changes to `webhook_events` require updated SQLAlchemy models, Alembic migrations, tests for idempotency and invalid signatures, documentation, and security review.
