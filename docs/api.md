# API Documentation

OpenAPI and Swagger UI are available at:

- `/openapi.json`
- `/docs`
- `/redoc`

OpenAPI contract maintenance rules are documented in [OpenAPI and Contract Documentation](openapi-contracts.md).

REST response envelopes, compatibility rules, and tracing requirements are defined in [REST API Standards](rest-api-standards.md).

Public endpoint requirements are documented in [Public REST API](public-rest-api.md).

## Public and Service Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | Liveness check |
| GET | `/api/v1/ready` | PostgreSQL and Redis readiness |
| GET | `/api/v1/metrics` | Prometheus-compatible counters |
| GET | `/api/v1/oauth/tiktok/start` | Start TikTok OAuth |
| GET | `/api/v1/oauth/tiktok/callback` | TikTok OAuth callback |
| POST | `/api/v1/webhooks/telegram` | Telegram webhook receiver |
| POST | `/api/v1/webhooks/tiktok` | TikTok webhook receiver |
| POST | `/api/v1/payments/robokassa/result` | Robokassa server notification |
| GET | `/api/v1/payments/robokassa/success` | Informational success response |
| GET | `/api/v1/payments/robokassa/fail` | Informational failure response |

## TikTok OAuth Start

```http
GET /api/v1/oauth/tiktok/start?state=<one-time-state-created-by-bot>
```

The Telegram bot creates the short-lived state and sends this URL to the user. The endpoint
rejects missing, unknown, and expired states, then redirects to official TikTok OAuth. It never
accepts a Telegram user identifier from the public request.

## Robokassa Result

Robokassa must call:

```http
POST /api/v1/payments/robokassa/result
```

Required form fields:

- `OutSum`
- `InvId`
- `SignatureValue`

Only this endpoint can activate a paid subscription.

Robokassa requires a plain text `OK{InvId}` response. Other API responses use JSON.

## Error Format

```json
{
  "success": false,
  "error": {
    "code": "VAL-001",
    "message": "Invalid request"
  },
  "request_id": "uuid",
  "correlation_id": "uuid"
}
```

API validation and data integrity rules are documented in [Data Quality and Integrity](data-quality-integrity.md).

Error code catalog and exception handling rules are documented in [Error Codes and Exception Handling](error-handling.md).

## Authorization

Admin endpoints require:

```text
Authorization: Bearer <ADMIN_API_TOKEN>
```

The bearer token is bound server-side to `ADMIN_API_TELEGRAM_ID`. Client-controlled identity
headers are ignored and must not be used for authorization.

Mutating admin requests also require:

```text
X-CSRF-Token: <ADMIN_CSRF_TOKEN>
```

Payment administration adds:

- `POST /api/v1/admin/payments/robokassa/orders` to create an audited external-channel checkout.
- `POST /api/v1/admin/payments/{payment_id}/refund-stars` to refund a paid Stars transaction through
  Telegram. It returns `refund_pending` without a second provider call while an earlier ambiguous
  result awaits reconciliation, and persists `refunded` only after provider confirmation.
- `POST /api/v1/admin/payments/{payment_id}/reconcile-stars-refund` with outcome `refunded` or
  `not_refunded` after a provider-side check. This guarded operation finalizes or releases a pending
  refund and records the decision in `admin_actions`.

Telegram webhook requests can use:

```text
X-Telegram-Bot-Api-Secret-Token: <TELEGRAM_WEBHOOK_SECRET>
```

TikTok webhook requests must include `TikTok-Signature` in the official `t=<timestamp>,s=<hmac>`
format. The API validates HMAC-SHA256 over `<timestamp>.<raw_body>` with
`TIKTOK_CLIENT_SECRET` and rejects timestamps outside the five-minute replay window.

TikTok OAuth, webhook, and developer portal checks are documented in [TikTok Developer Configuration](tiktok-developer-configuration.md).

## Examples

Start TikTok OAuth:

```bash
curl "https://your-domain.example/api/v1/oauth/tiktok/start?state=$OAUTH_STATE"
```

List upload jobs:

```bash
curl "https://your-domain.example/api/v1/admin/upload-jobs?limit=50&offset=0" \
  -H "Authorization: Bearer $ADMIN_API_TOKEN"
```

## Admin API

The browser console is available at `/admin-ui/`. Its API is served under `/api/v1/admin`.

See [Administrator Guide](admin.md) and [Administrative REST API](admin-rest-api.md).
