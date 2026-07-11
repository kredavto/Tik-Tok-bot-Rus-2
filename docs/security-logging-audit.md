# Security Logging and Audit

This document defines logging, security audit, and incident investigation requirements for Tik_Tok_Loader.

Confidential data masking and secret-handling rules are defined in [Confidential Data Policy](confidential-data-policy.md).

## Log Categories

The system must maintain structured logs for:

- Application services.
- Telegram bot handlers and FSM flows.
- REST API requests, responses, webhook processing, and errors.
- Background worker tasks.
- Security events.
- Administrative audit actions.

## Required Events

The following events must be logged or audited with sanitized context:

| Event | Required Record |
| --- | --- |
| Administrator login | Security log and, where applicable, `admin_actions` entry. |
| System setting change | `admin_actions` entry with changed key, old/new non-secret values where safe, administrator, timestamp, and request context. |
| TikTok connection | Diagnostic log and persisted account state update. |
| TikTok disconnection | Diagnostic log, token deletion event, and audit entry when initiated by support or administrator. |
| Payment creation | Payment record, diagnostic log, and correlation context. |
| Payment confirmation | Robokassa webhook event, payment status update, subscription update, and diagnostic log. |
| Upload status change | Upload job event and diagnostic log with job, user, and status identifiers. |
| Authorization failure | Security log with error code, request context, and masked identity details. |
| Access denial | Security log with role, permission, endpoint/action, and request context. |

## Storage Requirements

Logs and audit records must:

- Use structured JSON format.
- Use UTC timestamps.
- Include `request_id` and `correlation_id` when available.
- Mask confidential data before persistence or transport.
- Exclude raw TikTok OAuth tokens, Robokassa passwords, Telegram bot token, encryption keys, private keys, and `.env` values.
- Support search by Request ID, Correlation ID, user, upload job, payment, webhook event, and administrator.
- Follow configured retention periods for logs, audit records, webhook events, and backups.

Retention rules are defined in [Data Retention](data-retention.md).

## Investigation Use

Logs are used for:

- Operational diagnostics.
- Security incident investigation.
- Administrative operation proof.
- External integration troubleshooting.
- Payment and publication status reconciliation.

Incident response must use logs together with database audit records, webhook history, payment history, and upload lifecycle events. Procedures are documented in [Incident Response and Disaster Recovery](incident-response.md) and [Incident Management](incident-management.md).

## Access Control

- Security logs and administrative audit logs are available only to authorized administrator roles.
- Sensitive log exports must be protected like production data.
- Audit records must not be changed after creation except through approved retention or archival procedures.

Administrative audit storage is documented in [Admin Actions Entity](admin-actions-entity.md).

## Acceptance Rule

A release is not production-ready unless security logging, masking, searchable request context, audit storage, and retention behavior are verified for critical user, payment, publication, OAuth, and administrative flows.
