# Error Codes and Exception Handling

## Error Code Prefixes

| Prefix | Area |
| --- | --- |
| `AUTH` | Authorization and authentication |
| `PAY` | Robokassa payments |
| `TT` | TikTok API |
| `VAL` | Validation |
| `SYS` | System errors |
| `NET` | Network errors |

## Code Format

Use stable unique codes:

```text
PREFIX-NNN
```

Examples:

| Code | Meaning | Retry |
| --- | --- | --- |
| `AUTH-001` | Missing or invalid admin token | No |
| `AUTH-002` | TikTok OAuth state mismatch | No |
| `PAY-001` | Invalid Robokassa signature | No |
| `PAY-002` | Robokassa payment amount mismatch | No |
| `PAY-003` | Duplicate Robokassa notification | Idempotent handling |
| `TT-001` | TikTok authorization failed | No |
| `TT-002` | TikTok permission or scope is missing | No |
| `TT-003` | TikTok platform or regional restriction | No |
| `TT-004` | Temporary TikTok service error | Yes |
| `VAL-001` | Invalid request payload | No |
| `VAL-002` | Invalid video format | No |
| `VAL-003` | Video exceeds configured limits | No |
| `SYS-001` | Unexpected internal error | Investigate |
| `SYS-002` | Configuration error | No |
| `NET-001` | Temporary network failure | Yes |
| `NET-002` | External service timeout | Yes |

## REST Error Format

REST APIs return a consistent JSON structure:

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

REST response envelope rules are documented in [REST API Standards](rest-api-standards.md).

Public API error behavior is documented in [Public REST API](public-rest-api.md).

The public `message` must be safe for users and must not expose tokens, secrets, stack traces, internal paths, SQL errors, or raw external API responses.

## Logging Rules

Technical details belong in structured JSON logs, not in user-facing messages.

Logs should include:

- Error code.
- Request ID.
- Correlation ID.
- User ID when available.
- Upload job ID when available.
- Payment ID or Robokassa `InvId` when available.
- External service name.
- Retry classification.
- Sanitized technical reason.

Logs must mask secrets and tokens.

## User Messages

User messages should:

- Be short and understandable.
- Explain the next safe action when possible.
- Avoid internal details.
- Distinguish temporary failures from required user/admin action.

## Retry Strategy

Retry only:

- Temporary network errors.
- Temporary external service errors.
- Worker interruption before a terminal state is saved.

Do not retry automatically:

- Authorization failures.
- Missing permissions.
- TikTok regional, account, policy, or platform restrictions.
- Invalid Robokassa configuration or signature.
- Invalid user input.
- Invalid video files.

## Development Requirement

Every new failure path must define:

- Stable error code.
- Public message.
- Log details.
- Retry classification.
- Test coverage for expected handling.
