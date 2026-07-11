# Admin Actions Entity

## Purpose

`admin_actions` stores immutable audit records for administrative operations.

## Recommended Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Audit record identifier |
| `admin_user_id` | UUID | Administrator who performed the action |
| `action` | VARCHAR | Administrative action type |
| `target_type` | VARCHAR | Changed entity type |
| `target_id` | UUID or VARCHAR | Changed entity identifier |
| `details` | JSONB | Additional change details |
| `created_at` | TIMESTAMP WITH TIME ZONE | Action time |
| `ip_address` | VARCHAR | Administrative request source when available |

The current implementation may use `metadata_json` for `details`. Any schema rename or added field, including `ip_address`, must be delivered through Alembic migration and compatibility checks.

## Recorded Actions

Record:

- Plan changes.
- User blocking and unblocking.
- Manual subscription activation or cancellation.
- System settings changes.
- Safe task restart.
- Project configuration changes.
- Role or permission changes.
- User anonymization or TikTok disconnect initiated by support.

## Integrity Requirements

- Audit records must not be modified by users.
- Audit records must not be changed after creation except by a documented retention or archival process.
- Deletion is allowed only according to approved retention policy.
- Every administrative operation must write an audit record before confirming success to the administrator.
- Search must be supported by administrator, action type, target, and time range.

Administrative REST requirements are documented in [Administrative REST API](admin-rest-api.md).

Security logging requirements are documented in [Security Logging and Audit](security-logging-audit.md).

## Security Requirements

- Do not store secrets, raw tokens, passwords, or Robokassa credentials in `details`.
- Mask sensitive values before writing audit metadata.
- Restrict access to authorized administrator roles.

## Development Requirement

Changes to `admin_actions` require updated SQLAlchemy models, Alembic migrations, tests, documentation, retention review, and security review.
