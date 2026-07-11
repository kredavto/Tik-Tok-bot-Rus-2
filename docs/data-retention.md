# Data Retention

## Configuration

```env
VIDEO_RETENTION_HOURS=24
LOG_RETENTION_DAYS=90
BACKUP_RETENTION_DAYS=14
AUDIT_LOG_RETENTION_DAYS=365
```

## Policy

- Temporary videos are removed after processing or retention expiry.
- TikTok OAuth tokens are encrypted and deleted when the user disconnects TikTok.
- Robokassa payment history is retained for accounting and audit.
- Webhook and upload lifecycle logs follow `LOG_RETENTION_DAYS`.
- Admin audit logs follow `AUDIT_LOG_RETENTION_DAYS`.
- Backups follow `BACKUP_RETENTION_DAYS`.

Temporary video storage rules are defined in [File Storage Policy](file-storage-policy.md).

## User Data Deletion

Admin endpoint:

```http
POST /admin/users/{user_id}/anonymize
```

This removes TikTok tokens and anonymizes personal Telegram profile data while preserving records required for financial and legal audit.
