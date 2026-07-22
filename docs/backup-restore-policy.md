# Backup and Restore Policy

## Backup Objects

Back up:

- PostgreSQL database.
- Production `.env` stored only on the server or in a managed secret store.
- Project documentation.
- Nginx configuration.
- Docker Compose configuration.
- Deployment scripts.
- Audit logs when required by the retention policy.

Do not commit production backups or real `.env` files to Git.

Backups containing personal or secret-related data must follow [Confidential Data Policy](confidential-data-policy.md).

## Backup Policy

- Run PostgreSQL backups regularly.
- Keep multiple backup generations.
- Verify every backup job completed successfully.
- Store backups outside the running database container.
- Protect backups with access controls.
- Periodically test restore on staging or an isolated recovery host.
- Apply `BACKUP_RETENTION_DAYS` for backup retention.

## Backup Verification

For each backup, record:

- UTC timestamp.
- Environment.
- Backup file name.
- Database revision.
- Application version or Git commit.
- File size.
- Exit status.
- Verification result.

Failed backup jobs must be treated as operational incidents.

The supported command is `ENV_FILE=.env bash deploy/backup_postgres.sh`. It creates a PostgreSQL
custom archive, verifies it with `pg_restore --list`, and writes `.sha256` and `.meta` sidecars.

## Restore Procedure

1. Identify the failure cause and affected components.
2. Stop risky operations, including new upload intake if needed.
3. Prepare infrastructure: Docker, volumes, network, `.env`, Nginx, and HTTPS.
4. Restore PostgreSQL from the latest valid backup when data recovery is required.
5. Restore configuration files from the protected source.
6. Start PostgreSQL, Redis, API, bot, worker, and Nginx.
7. Apply required Alembic migrations only after confirming version compatibility.
8. Check `/health`, `/ready`, and `/metrics`.
9. Verify key user scenarios.
10. Document the incident and recovery actions.

Use `ENV_FILE=.env bash deploy/restore_postgres.sh <archive> --confirm`. The script keeps
application services stopped if restoration fails. Full command behavior is documented in
[CI/CD and Deployment Automation](ci-cd-deployment.md).

## Recovery Success Criteria

After recovery, these must work correctly:

- Telegram user authorization and `/start`.
- TikTok OAuth connection.
- Video upload queueing and worker processing.
- Robokassa ResultURL payment processing.
- Subscription state and tariff limits.
- Admin API and audit log access.
- Queue state without duplicate publication or duplicate quota consumption.
- User, subscription, payment, and publication history.

Continuity planning and planned maintenance rules are documented in [Service Continuity Plan](service-continuity-plan.md).

## Restore Drill

At least periodically:

1. Restore the latest backup to staging.
2. Apply migrations for the target version.
3. Run smoke tests.
4. Verify payments, subscriptions, and upload job integrity.
5. Record restore duration and issues found.

## Documentation Requirement

Every significant recovery must record:

- Incident date and priority.
- Root cause.
- Backup selected.
- Data loss assessment.
- Recovery steps.
- Validation result.
- Preventive actions.
