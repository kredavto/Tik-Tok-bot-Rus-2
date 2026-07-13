# Security, Backup, and Monitoring

Security and reliability non-functional requirements are summarized in [Non-Functional Requirements](non-functional-requirements.md).

Security logging and audit requirements are defined in [Security Logging and Audit](security-logging-audit.md).

Confidential data handling rules are defined in [Confidential Data Policy](confidential-data-policy.md).

## Application Security

- External callbacks must use HTTPS.
- Secrets stay only in `.env` or a managed secret store.
- TikTok OAuth tokens are encrypted before database storage.
- Internal business IDs use UUID where the domain does not require a stable public code.
- Robokassa ResultURL signatures are verified before activation.
- TikTok webhook signatures are always checked with `TIKTOK_CLIENT_SECRET`, the raw request body,
  and a five-minute timestamp tolerance.
- API rate limiting uses Redis.
- Logs are JSON and must not include tokens, passwords, or Robokassa secrets.
- Uploaded files must follow [File Storage Policy](file-storage-policy.md).

TikTok account token storage rules are documented in [TikTok Accounts Entity](tiktok-accounts-entity.md).

Webhook storage and validation rules are documented in [Webhook Events Entity](webhook-events-entity.md).

## Server Baseline

Ubuntu 24.04 LTS:

```bash
sudo adduser deploy
sudo usermod -aG docker deploy
sudo sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

Use SSH keys in Termius. Do not enable password login.

## Backups

Run before every update:

```bash
bash deploy/backup_postgres.sh
tar -czf backups/config_$(date -u +%Y%m%dT%H%M%SZ).tgz .env deploy docker-compose.yml
```

Restore drill:

```bash
docker compose cp backups/tiktok_loader_YYYYMMDDTHHMMSSZ.dump postgres:/tmp/restore.dump
docker compose exec postgres pg_restore --clean --if-exists --username tiktok --dbname tiktok_loader /tmp/restore.dump
```

Test restore on a staging server before relying on backups.

Full backup and recovery rules are documented in [Backup and Restore Policy](backup-restore-policy.md).

Infrastructure update controls are documented in [Infrastructure Dependency Management](infrastructure-dependency-management.md).

## Update and Rollback

1. Create a PostgreSQL and config backup.
2. Pull the new release.
3. Run `docker compose build`.
4. Run `docker compose run --rm api alembic upgrade head`.
5. Start services.
6. If health/readiness fail, restore the previous image and database backup.

## Monitoring

- `GET /health` for liveness.
- `GET /ready` for PostgreSQL and Redis readiness.
- `GET /metrics` for Prometheus-compatible counters.
- JSON logs can be collected by Docker logging drivers or an external collector.
