# Public REST API

## General Requirements

- Public endpoints use the `/api/v1` prefix.
- JSON is the default exchange format.
- Standard HTTP status codes are used.
- Every request receives a Request ID.
- Related operations should include a Correlation ID.
- Responses follow [REST API Standards](rest-api-standards.md).
- Errors follow [Error Codes and Exception Handling](error-handling.md).

Robokassa ResultURL may return plain text `OK{InvId}` when required by Robokassa.

## Core Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | Service liveness check |
| GET | `/api/v1/ready` | Application readiness check |
| GET | `/api/v1/oauth/tiktok/start` | Start TikTok OAuth authorization |
| GET | `/api/v1/oauth/tiktok/callback` | Complete TikTok OAuth |
| POST | `/api/v1/webhooks/tiktok` | Receive TikTok webhook |
| POST | `/api/v1/payments/robokassa/result` | Process Robokassa ResultURL |

Additional service endpoints, such as Telegram webhook and metrics, are documented in [API Documentation](api.md).

## Compatibility Requirements

- Do not remove existing response fields without a new API version.
- Add new response fields as optional.
- Keep backward compatibility within `/api/v1`.
- Document changes in OpenAPI.
- Update `CHANGELOG.md` for behavior changes.

Detailed API lifecycle and deprecation rules are documented in [API Versioning and Client Compatibility](api-versioning-compatibility.md).

## Error Handling

Errors use the shared response envelope:

```json
{
  "success": false,
  "error": {
    "code": "TT-001",
    "message": "Operation cannot be completed"
  },
  "request_id": "uuid"
}
```

Internal implementation details, stack traces, tokens, secrets, SQL errors, and raw external service responses must not be exposed to users.
