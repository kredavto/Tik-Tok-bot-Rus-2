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

## Implemented Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/v1/admin/session` | Current role and permissions |
| GET | `/api/v1/admin/dashboard` | Operational counters |
| GET | `/api/v1/admin/analytics` | Tariff, registration, upload, and revenue analytics |
| GET | `/api/v1/admin/users` | User list |
| GET | `/api/v1/admin/users/{id}` | User profile |
| POST | `/api/v1/admin/users/{id}/block` | Block user |
| POST | `/api/v1/admin/users/{id}/unblock` | Unblock user |
| POST | `/api/v1/admin/users/{id}/force-free` | Expire active plan and create FREE subscription |
| POST | `/api/v1/admin/users/{id}/anonymize` | Apply the approved anonymization procedure |
| PATCH | `/api/v1/admin/users/{id}/role` | Change role; SUPER_ADMIN only |
| GET | `/api/v1/admin/plans` | Tariff list |
| PATCH | `/api/v1/admin/plans/{id}` | Update tariff parameters |
| GET | `/api/v1/admin/payments` | Provider-neutral payment list with RUB/XTR amounts |
| GET | `/api/v1/admin/upload-jobs` | Publication queue |
| GET | `/api/v1/admin/errors` | Failed publications |
| POST | `/api/v1/admin/upload-jobs/{id}/retry` | Retry an eligible temporary failure |
| GET | `/api/v1/admin/settings` | System settings |
| PUT | `/api/v1/admin/settings/{key}` | Update one typed system setting |
| GET | `/api/v1/admin/audit-actions` | Filterable audit journal |
| GET | `/api/v1/admin/configuration/export` | Export non-secret runtime configuration |
| POST | `/api/v1/admin/configuration/import` | Validate and import runtime configuration |

Legacy `/admin/*` aliases are temporarily supported but omitted from OpenAPI.

## Transaction Rules

Mutating operations must be transactional:

- User blocking and unblocking.
- Plan updates.
- System setting updates.
- Manual subscription changes.
- Safe task restart.
- Configuration import.

The safe retry endpoint rejects jobs already accepted by TikTok and any error that is not explicitly
classified as temporary. It also verifies that the local source file still exists.

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
