# Administrator Guide

## Access

The web console is served by FastAPI at `/admin-ui/`. In production, open it only through the
configured HTTPS domain. The console keeps credentials in browser memory for the current page
only; it does not use local or session storage.

Admin API access requires:

- `ADMIN_API_TOKEN`
- `ADMIN_CSRF_TOKEN` for mutating requests
- Telegram ID listed in `ADMIN_TELEGRAM_IDS`

Required headers:

```text
Authorization: Bearer <ADMIN_API_TOKEN>
X-Admin-Telegram-Id: <telegram_id>
X-CSRF-Token: <ADMIN_CSRF_TOKEN>
```

Do not expose secrets, TikTok tokens, Robokassa passwords, or raw OAuth credentials in the UI.

## Roles

RBAC is enforced on the server. Client-side checks are only UI hints.

| Role | Access |
| --- | --- |
| USER | Telegram bot features for own account |
| SUPPORT | Statistics, users, payments, upload jobs, and error logs |
| ADMIN | SUPPORT permissions plus user blocking and tariff management |
| SUPER_ADMIN | Full access, including system settings and role management |

The permission matrix is defined in `app.security.rbac`, so new roles and permissions can be added without changing business handlers.

## Sections

- Dashboard and analytics: `/api/v1/admin/dashboard`, `/api/v1/admin/analytics`
- Users and user details: `/api/v1/admin/users`
- Plans: `/api/v1/admin/plans`
- Payments: `/api/v1/admin/payments`
- Upload queue and publication errors: `/api/v1/admin/upload-jobs`, `/api/v1/admin/errors`
- System settings: `/api/v1/admin/settings`
- Audit journal: `/api/v1/admin/audit-actions`
- User role management: `/api/v1/admin/users/{user_id}/role`

Legacy `/admin/*` routes remain available for compatibility but are excluded from OpenAPI. New
clients must use `/api/v1/admin/*`.

Dashboard and analytics KPI are defined in [Metrics and KPI](metrics-and-kpi.md).

Administrative REST endpoint requirements are documented in [Administrative REST API](admin-rest-api.md).

## Plan Management

PRO and BUSINESS price, daily limit, duration, and sale availability are stored in PostgreSQL and can be changed without code edits.

Every plan update is written to `admin_actions`.

## User Management

Admins can:

- Search users by Telegram ID or username.
- Block or unblock users.
- Inspect connected TikTok account metadata without access to OAuth tokens.
- Inspect publication and payment history.
- Return a user to FREE without deleting subscription history.
- Review payment and subscription state.

SUPER_ADMIN can assign roles. Every mutating operation requires the CSRF token and is recorded
with the request source IP when available.

Queue inspection and safe retry rules are documented in [Queue and Retry Policy](queue-retry-policy.md).

Only failed jobs with a classified temporary network or queue error, no TikTok publish ID, and an
existing local video file can be restarted from the console. Authorization, permissions, platform
restrictions, invalid media, and ambiguous accepted publications are never retried automatically.

## Runtime Settings

The application seeds editable, non-secret settings for intake and retention. Retention workers
read these values from PostgreSQL on every cleanup cycle and use `.env` values only as fallback.
Invalid typed values are rejected before persistence.

Secrets remain in `.env`; secret-like keys are excluded from the settings API and configuration
export.

## Audit

Administrative actions are recorded in `admin_actions`. Payment and webhook processing are recorded in `webhook_events`.

Admin audit storage rules are documented in [Admin Actions Entity](admin-actions-entity.md).

System setting edit rules are documented in [System Settings Entity](system-settings-entity.md).
