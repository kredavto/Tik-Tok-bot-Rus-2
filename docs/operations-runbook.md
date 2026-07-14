# Operations Runbook

## Daily Operations

- Check Telegram bot availability.
- Check FastAPI `/health` and `/ready`.
- Review `/metrics` for queue size and error counters.
- Confirm the latest PostgreSQL backup exists.
- Confirm backup verification follows [Backup and Restore Policy](backup-restore-policy.md).
- Review critical JSON logs for `api`, `bot`, `worker`, `scheduler`, `postgres`, `redis`, and `nginx`.
- Confirm the `scheduler` container is healthy and its subscription sweep is running.
- Use Request ID and Correlation ID when investigating related API, worker, payment, and publication events.
- Check Robokassa ResultURL events in `webhook_events`.

## Weekly Operations

- Check disk usage for Docker volumes, `./data`, and `./backups`.
- Check storage directories and cleanup health according to [File Storage Policy](file-storage-policy.md).
- Review PostgreSQL slow queries and run `EXPLAIN ANALYZE` for suspicious queries.
- Check dependency updates and base image updates.
- Verify SSL certificate expiration date.
- Review worker throughput and retry patterns.
- Review capacity thresholds according to [Capacity and Performance Management](capacity-management.md).
- Review operational KPI from [Metrics and KPI](metrics-and-kpi.md).

## Monthly Operations

- Perform a restore drill from the latest backup on staging.
- Record restore drill results according to [Backup and Restore Policy](backup-restore-policy.md).
- Verify retention cleanup for temporary videos, webhook logs, audit logs, and backups.
- Review performance bottlenecks and queue latency.
- Review resource headroom and scaling needs.
- Review business and quality KPI trends.
- Review data quality checks according to [Data Quality and Integrity](data-quality-integrity.md).
- Confirm scheduled maintenance tasks still run.
- Review admin audit log for unexpected changes.

## Update Checklist

Before update:

1. Set `intake_enabled=false` if the update affects upload processing.
2. Create a PostgreSQL backup.
3. Record the current Git tag and `APP_VERSION`.
4. Confirm `CHANGELOG.md` is updated.

During update:

1. Pull the release tag.
2. Rebuild containers.
3. Apply Alembic migrations.
4. Restart services.

After update:

1. Check `/health`, `/ready`, and `/metrics`.
2. Test `/start`, TikTok OAuth start, tariff display, Robokassa payment link generation, and upload queue creation.
3. Watch logs for at least 15 minutes.
4. Re-enable intake with `intake_enabled=true`.

## Goal

Maintenance should keep the service stable, secure, predictable, and recoverable while preserving user data integrity.

Service continuity requirements are documented in [Service Continuity Plan](service-continuity-plan.md).

## Incidents

Use [Incident Management](incident-management.md) to classify P1-P4 incidents, record impact, manage escalation, and run post-incident reviews.

Standard preflight, post-update, and diagnostic checklists are in [SOP Checklists](sop-checklists.md).

Tracing, event correlation, and log search requirements are described in [Observability and Diagnostics](observability-diagnostics.md).
