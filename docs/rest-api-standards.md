# REST API Standards

## General Rules

- Public REST methods use the `/api/v1` prefix.
- JSON is the default exchange format.
- Use correct HTTP status codes.
- Use a consistent response envelope.
- Include Request ID in every response.
- Include Correlation ID when the operation belongs to a broader workflow.
- Document API changes in OpenAPI and `CHANGELOG.md`.

OpenAPI contract rules are documented in [OpenAPI and Contract Documentation](openapi-contracts.md).

API version lifecycle and client compatibility rules are documented in [API Versioning and Client Compatibility](api-versioning-compatibility.md).

Robokassa ResultURL is the only intentional exception when a plain text `OK{InvId}` response is required by Robokassa.

Administrative endpoints follow [Administrative REST API](admin-rest-api.md).

Public endpoints follow [Public REST API](public-rest-api.md).

## Successful Response

```json
{
  "success": true,
  "data": {},
  "request_id": "uuid"
}
```

When available, include:

```json
{
  "success": true,
  "data": {},
  "request_id": "uuid",
  "correlation_id": "uuid"
}
```

## Error Response

```json
{
  "success": false,
  "error": {
    "code": "TT-001",
    "message": "Operation cannot be completed"
  },
  "request_id": "uuid",
  "correlation_id": "uuid"
}
```

Error codes are defined in [Error Codes and Exception Handling](error-handling.md).

## Compatibility

- Do not remove existing response fields within the same major API version.
- Add new fields as optional.
- Keep public `/api/v1` behavior backward compatible.
- Introduce a new API version for incompatible changes.
- Document request, response, and error changes in OpenAPI.
- Update `CHANGELOG.md` for behavior changes.

## Request Tracing

Each request should have:

- Request ID for the specific inbound request.
- Correlation ID for related operations across API, bot, worker, webhooks, payments, and logs.

Tracing rules are documented in [Observability and Diagnostics](observability-diagnostics.md).
