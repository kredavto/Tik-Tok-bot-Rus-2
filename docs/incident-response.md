# Incident Response and Disaster Recovery

Incident classification and postmortem process are described in [Incident Management](incident-management.md).

Backup selection and restore verification must follow [Backup and Restore Policy](backup-restore-policy.md).

Continuity measures and planned maintenance rules are documented in [Service Continuity Plan](service-continuity-plan.md).

Security investigation logging requirements are defined in [Security Logging and Audit](security-logging-audit.md).

## Critical Failure Procedure

1. Stop intake of new uploads by setting `intake_enabled=false` through the admin settings API.
2. Check `/health`, `/ready`, and `/metrics`.
3. Inspect JSON logs for `web`, `bot`, `worker`, `postgres`, `redis`, and `nginx`.
4. Create a backup before repair with `bash deploy/backup_postgres.sh`.
5. Restart services with `docker compose restart web bot worker`.
6. Restore PostgreSQL from backup if data or migrations are corrupted.
7. Verify queue integrity before resuming workers.
8. Set `intake_enabled=true` after recovery.

## Queue Recovery

- `NEW`, `VALIDATING`, `PREPARING`, `QUEUED`, and `UPLOADING` jobs can be retried.
- `PROCESSING` jobs must be checked against TikTok status before retry.
- Daily usage is consumed only after official TikTok acceptance, so failed video preparation does not consume quota.

## Monitoring Checklist

- Telegram bot process is running.
- FastAPI `/ready` returns `ready`.
- PostgreSQL accepts connections.
- Redis responds to ping.
- Worker logs show task processing.
- Nginx serves HTTPS.
- `/metrics` contains queue size, publication counts, payment counts, and subscription counts.

## Audit

Critical operations are recorded in:

- `admin_actions` for administrator changes.
- `webhook_events` for Telegram, TikTok, and Robokassa events.
- Structured JSON logs for service-level diagnostics.
