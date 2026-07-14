# TikTok Accounts Entity

## Purpose

`tiktok_accounts` stores connected TikTok accounts and OAuth integration metadata for official TikTok API access.

## Recommended Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Internal record identifier |
| `user_id` | UUID | Reference to `users.id` |
| `tiktok_open_id` | VARCHAR | TikTok account identifier |
| `display_name` | VARCHAR | TikTok display name |
| `access_token` | TEXT encrypted | OAuth access token |
| `refresh_token` | TEXT encrypted | OAuth refresh token |
| `token_expires_at` | TIMESTAMP WITH TIME ZONE | Access token expiration time |
| `refresh_blocked_at` | TIMESTAMP WITH TIME ZONE | Time automatic refresh was stopped after a non-retryable error |
| `refresh_error_code` | VARCHAR | Sanitized non-retryable refresh error code |
| `created_at` | TIMESTAMP WITH TIME ZONE | Connection creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | Last update time |

The current implementation may use internal column names such as `open_id`, `access_token_encrypted`, and `refresh_token_encrypted` while preserving the same domain meaning. Any schema rename or added field must be delivered through Alembic migration and compatibility checks.

## Relationships

| Relationship | Cardinality |
| --- | --- |
| `users` -> `tiktok_accounts` | 1:N |
| `tiktok_accounts` -> `upload_jobs` | 1:N |

## Security Requirements

- Store OAuth access tokens only in encrypted form.
- Store OAuth refresh tokens only in encrypted form.
- Never log tokens, decrypted token values, or raw OAuth responses containing tokens.
- Delete encrypted tokens when the user disconnects the TikTok account.
- Check access token expiration before each TikTok API call.
- Refresh access tokens safely through the official OAuth refresh flow.
- Retry only network, rate-limit, and server failures. A permanent OAuth response blocks further
  scheduled refresh attempts until the user reconnects the account.
- Do not collect TikTok passwords.

## Integrity Requirements

- `user_id` is required.
- TikTok account identifier must be unique within the system unless a documented multi-tenant reason requires a different constraint.
- Token updates must be transactional.
- Account disconnect must be transactional and auditable.
- Upload jobs should reference the TikTok account used for publication when available.

## Audit Requirements

Audit:

- TikTok OAuth connection.
- Token refresh success or sanitized failure.
- TikTok account disconnect.
- Permission or scope errors.
- Administrator support actions related to TikTok accounts.

## Development Requirement

Changes to `tiktok_accounts` require updated SQLAlchemy models, Alembic migrations, tests, documentation, and security review.
