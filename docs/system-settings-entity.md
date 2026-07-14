# System Settings Entity

## Purpose

`system_settings` stores mutable non-secret project settings that can be changed without modifying source code.

## Recommended Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Setting record identifier |
| `setting_key` | VARCHAR | Unique setting key |
| `setting_value` | TEXT or JSONB | Setting value |
| `value_type` | VARCHAR | `string`, `int`, `bool`, or `json` |
| `description` | TEXT | Setting description |
| `is_editable` | BOOLEAN | Whether admins may edit through admin UI |
| `updated_by` | UUID | Last administrator who changed the setting |
| `updated_at` | TIMESTAMP WITH TIME ZONE | Last update time |

The current implementation may use `key` for `setting_key` and `value` for `setting_value`. Any schema rename or added field must be delivered through Alembic migration and compatibility checks.

## Example Settings

- `intake_enabled`.
- `video_retention_hours`.
- `log_retention_days`.
- `backup_retention_days`.
- `audit_log_retention_days`.

Plan prices, daily limits, duration, and sale availability are stored in `plans`, not duplicated in
`system_settings`.

## Integrity Requirements

- Every `setting_key` must be unique.
- Validate value type before saving.
- Validate allowed ranges and enum values before saving.
- Setting updates must be transactional.
- Setting updates must be written to `admin_actions`.
- Configuration export must exclude secret-like settings.
- Seed defaults only when a key is absent; never overwrite an administrator change at startup.
- Retention workers read database values for each cleanup cycle and use `.env` as fallback.

## Security Requirements

- Critical secrets must not be stored in `system_settings`.
- Secrets remain only in `.env` or a managed secret store.
- Do not store Telegram bot tokens, TikTok client secrets, Robokassa passwords, encryption keys, API tokens, or webhook secrets in this table.
- Restrict editing to authorized administrator roles.

## Development Requirement

Changes to `system_settings` require updated SQLAlchemy models, Alembic migrations, tests, documentation, configuration validation, and security review.
