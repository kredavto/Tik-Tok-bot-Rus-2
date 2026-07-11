# Glossary and Naming Conventions

## Glossary

| Term | Definition |
| --- | --- |
| Upload Job | Task for processing and publishing one video |
| Subscription | Active or historical user tariff assignment |
| Daily Usage | Daily publication limit accounting |
| Webhook Event | Inbound event from an external service or internal callback |
| Worker | Background process that handles queued tasks |
| Request ID | Unique identifier for one HTTP request |
| Correlation ID | Identifier for a chain of related operations |
| Plan | Tariff definition: FREE, PRO, or BUSINESS |
| Payment | Robokassa payment record |
| Admin Action | Immutable administrative audit event |
| System Setting | Mutable non-secret runtime configuration value |

## Naming Conventions

- Database tables use `snake_case` and plural names.
- Python modules use `snake_case`.
- Python classes use `PascalCase`.
- Variables and functions use `snake_case`.
- REST endpoints use the existing project style and kebab-case only when it improves readability.
- Environment variables use uppercase `SNAKE_CASE`.
- Plan names are written as `FREE`, `PRO`, and `BUSINESS` in product and technical documentation.

## Entity Names

Use these canonical names:

| Canonical Name | Database Table |
| --- | --- |
| User | `users` |
| TikTok Account | `tiktok_accounts` |
| Plan | `plans` |
| Subscription | `subscriptions` |
| Payment | `payments` |
| Upload Job | `upload_jobs` |
| Upload Job Event | `upload_job_events` |
| Daily Usage | `daily_usage` |
| Webhook Event | `webhook_events` |
| Admin Action | `admin_actions` |
| System Setting | `system_settings` |

## Consistency Rule

Code, documentation, database schema, tests, API responses, and user-facing text should use the same terminology unless an external provider requires a different term.

When a current implementation uses a different internal field name, document the mapping in the relevant entity specification and change it only through Alembic migration and compatibility review.
