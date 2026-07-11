# Administrative REST API

## Access Requirements

- All administrative endpoints require authentication.
- Role and permission checks are enforced on the server.
- Mutating requests require CSRF protection where applicable.
- Every administrative request should have a Request ID.
- Related operations should include a Correlation ID.
- Administrative changes must be recorded in `admin_actions`.
- Responses use JSON and follow [REST API Standards](rest-api-standards.md).
- Errors use [Error Codes and Exception Handling](error-handling.md).

API version lifecycle and compatibility rules are documented in [API Versioning and Client Compatibility](api-versioning-compatibility.md).

## Recommended Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/v1/admin/users` | User list |
| GET | `/api/v1/admin/users/{id}` | User profile |
| POST | `/api/v1/admin/users/{id}/block` | Block user |
| POST | `/api/v1/admin/users/{id}/unblock` | Unblock user |
| GET | `/api/v1/admin/payments` | Payment list |
| GET | `/api/v1/admin/upload-jobs` | Publication queue |
| GET | `/api/v1/admin/settings` | System settings |
| PUT | `/api/v1/admin/settings` | Update system settings |

Additional administrative endpoints may be added when they follow the same authentication, RBAC, audit, and response-format rules.

## Transaction Rules

Mutating operations must be transactional:

- User blocking and unblocking.
- Plan updates.
- System setting updates.
- Manual subscription changes.
- Safe task restart.
- Configuration import.

The audit record must be created in the same transaction as the change when possible.

## Audit Requirements

Log in `admin_actions`:

- Administrator ID.
- Action type.
- Target type.
- Target ID.
- Sanitized details.
- UTC timestamp.
- Request source when available.

Do not write secrets, raw tokens, passwords, or Robokassa credentials to audit details.

## Compatibility

- Keep `/api/v1/admin` backward compatible within the same major API version.
- Add new response fields as optional.
- Document endpoint changes in OpenAPI and `CHANGELOG.md`.
- Follow [Change Acceptance Policy](change-acceptance-policy.md) before release.
