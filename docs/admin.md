# Administrator Guide

## Access

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

- Dashboard: `/admin/dashboard`
- Analytics: `/admin/analytics`
- Users: `/admin/users`
- Plans: `/admin/plans`
- Payments: `/admin/payments`
- Upload queue: `/admin/upload-jobs`
- System settings: `/admin/settings`
- User role management: `/admin/users/{user_id}/role`

Dashboard and analytics KPI are defined in [Metrics and KPI](metrics-and-kpi.md).

Administrative REST endpoint requirements are documented in [Administrative REST API](admin-rest-api.md).

## Plan Management

PRO and BUSINESS price, daily limit, duration, and sale availability are stored in PostgreSQL and can be changed without code edits.

Every plan update is written to `admin_actions`.

## User Management

Admins can:

- Search users by Telegram ID or username.
- Block or unblock users.
- Inspect publication history through upload jobs.
- Review payment and subscription state.

Queue inspection and safe retry rules are documented in [Queue and Retry Policy](queue-retry-policy.md).

## Audit

Administrative actions are recorded in `admin_actions`. Payment and webhook processing are recorded in `webhook_events`.

Admin audit storage rules are documented in [Admin Actions Entity](admin-actions-entity.md).

System setting edit rules are documented in [System Settings Entity](system-settings-entity.md).
