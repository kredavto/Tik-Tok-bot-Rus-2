# Confidential Data Policy

This document defines how Tik_Tok_Loader handles, stores, protects, audits, and rotates confidential data.

Environment-specific secret control rules are defined in [Environment Configuration and Secrets Control](environment-configuration-secrets.md).

## Confidential Data Categories

| Category | Examples |
| --- | --- |
| TikTok OAuth tokens | Access tokens, refresh tokens, token expiry metadata |
| Robokassa secrets | Merchant login, Password #1, Password #2 |
| Telegram secrets | Telegram bot token, webhook secret |
| Encryption keys | Token encryption key, administrative API or CSRF secrets |
| Backups with personal data | PostgreSQL dumps, configuration backups, audit exports |
| Production configuration | `.env`, Nginx production configuration with sensitive paths or headers |

## Storage Rules

- Store secrets only in `.env` files on the server or in an approved secret store.
- Store TikTok OAuth tokens only in encrypted form in PostgreSQL.
- Do not commit `.env`, private keys, raw tokens, production backups, or secret exports to Git.
- Do not include secrets in repository backups.
- Minimize the number of services and operators with access to secrets.
- Keep critical secrets out of `system_settings`; database settings are for non-secret runtime configuration only.
- Protect backups that may contain personal data or encrypted tokens with access controls and retention limits.

## Access Control

- Apply least-privilege access for administrators, operators, service accounts, containers, and CI jobs.
- Restrict administrative access to authorized roles.
- Review access rights regularly and after personnel, infrastructure, or ownership changes.
- Log administrative operations involving confidential data with masked values.
- Do not display raw secrets in dashboards, admin panels, logs, error messages, or support exports.

## Runtime Handling

- Load secrets from environment variables during service startup.
- Validate required secrets at startup and fail safely when configuration is incomplete.
- Mask secrets before logging request bodies, headers, webhook payloads, exceptions, configuration dumps, or audit metadata.
- Do not store sensitive values in Telegram FSM state, Redis cache, or task payloads unless required and protected by expiration and masking.
- Avoid passing raw tokens between services when an internal identifier can be used instead.

## Rotation

The system must support planned replacement of:

- TikTok OAuth tokens through the official refresh and disconnect/reconnect flows.
- Robokassa passwords through environment configuration updates.
- Telegram bot token through environment configuration updates and webhook reconfiguration when applicable.
- Encryption keys through a documented key-rotation procedure.
- Administrative tokens and CSRF secrets through environment configuration updates.

Rotation should be possible without changing application architecture and with minimal downtime.

## Backup and Recovery

- Treat PostgreSQL backups, configuration backups, and audit exports as confidential data.
- Store production `.env` outside Git and restore it only from a protected source.
- Do not copy production backups into development environments unless data is anonymized or access is approved.
- Verify retention and deletion of old backups according to [Data Retention](data-retention.md).

## Audit and Incident Handling

- Log access changes, administrative secret-related operations, token disconnects, and configuration changes with masked details.
- Investigate suspected secret exposure through [Security Logging and Audit](security-logging-audit.md) and [Incident Response and Disaster Recovery](incident-response.md).
- Rotate affected secrets after confirmed or suspected exposure.
- Document incident scope, affected data, actions taken, and preventive measures.

## Related Documents

- [Configuration](configuration.md)
- [Security, Backup, and Monitoring](security.md)
- [Security Logging and Audit](security-logging-audit.md)
- [Backup and Restore Policy](backup-restore-policy.md)
- [TikTok Accounts Entity](tiktok-accounts-entity.md)
- [Data Retention](data-retention.md)
