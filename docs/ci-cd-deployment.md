# CI/CD and Deployment Automation

This document defines the automated quality gates and the supported staging and production
deployment procedure for Tik_Tok_Loader.

## CI Pipeline

GitHub Actions runs three jobs:

- `Quality and security`: Ruff formatting and linting, MyPy, Bash syntax, ShellCheck, and secret
   scanning.
- `Migrations and tests`: PostgreSQL 16 and Redis integration services, Alembic upgrade/check,
   downgrade-to-base/upgrade verification on a disposable database, and the full test suite.
- `Container build`: Docker Compose model validation, application image build, and verification
   that the runtime image uses the unprivileged `appuser` account.

The container job starts only after the quality and integration jobs pass. The workflow has
read-only repository permissions and cancels superseded runs for the same branch or pull request.

## Secret Gate

`python tools/check_secrets.py` compares the current scan with `.secrets.baseline`. New findings
fail CI and report only the file, line, and detector type. A second non-baselined check always
rejects Telegram bot token patterns and private-key blocks.

Baseline changes require code review. A finding must never be added to the baseline to conceal a
real credential. Rotate any credential that has appeared in chat, source, a pull request, logs, or
CI output before using the project in staging or production.

## Server Prerequisites

- Ubuntu 24.04 LTS.
- Docker Engine with the Compose plugin.
- Git, Python 3, curl, and SSH key access.
- A domain pointing to the server.
- A real environment file at `.env`, readable only by the deployment operator.
- TLS files at `${TLS_CERT_DIR}/fullchain.pem` and `${TLS_CERT_DIR}/privkey.pem`.

Run the configuration gate before a release:

```bash
python3 tools/validate_deploy_env.py --env-file .env --environment staging
python3 tools/validate_deploy_env.py --env-file .env --environment production
```

The gate validates environment identity, HTTPS callbacks, domain consistency, webhook mode,
secret length and uniqueness, Fernet key format, Robokassa mode, and required TikTok credentials
when publication is enabled. It never prints secret values.

## TLS Bootstrap

For the first certificate, temporarily start the HTTP Nginx template and use Certbot webroot:

```bash
NGINX_TEMPLATE=http.conf.template docker compose up -d api nginx
sudo certbot certonly --webroot \
  --webroot-path "$(pwd)/deploy/nginx/acme" \
  --domain loader.example.net
sudo install -m 0644 /etc/letsencrypt/live/loader.example.net/fullchain.pem \
  deploy/nginx/certs/fullchain.pem
sudo install -m 0600 /etc/letsencrypt/live/loader.example.net/privkey.pem \
  deploy/nginx/certs/privkey.pem
docker compose restart nginx
```

Replace the example domain. Keep `NGINX_TEMPLATE=https.conf.template` in staging and production.
Automate certificate renewal with a root-owned Certbot deploy hook that refreshes the two copied
files and runs `docker compose exec -T nginx nginx -s reload`.

## Automated Deployment

Deploy an immutable tag or reviewed commit:

```bash
ENV_FILE=.env bash deploy/deploy.sh staging v0.2.0
ENV_FILE=.env bash deploy/deploy.sh production v0.2.0
```

The script:

- validates `.env` and TLS files;
- rejects tracked local changes;
- creates and verifies a PostgreSQL backup;
- records the previous Git revision under ignored `.deploy/`;
- fetches and checks out the requested commit in detached mode;
- builds images with refreshed base layers;
- applies Alembic migrations;
- requires the one-shot `migrate` service to complete before application services start;
- starts Compose services; and
- checks `/health`, `/ready`, and `/metrics` through the public URL.

The deployment operator must still configure Telegram, TikTok, and Robokassa dashboards and run
the acceptance scenarios. Termius is an SSH client for these server-side commands; it does not
change the deployment procedure.

## Backup and Restore

Create a verified custom-format PostgreSQL archive:

```bash
ENV_FILE=.env bash deploy/backup_postgres.sh
```

The command uses the database container's configured user and database, verifies the archive with
`pg_restore --list`, writes a SHA-256 sidecar and metadata, applies mode `0600`, and removes files
older than `BACKUP_RETENTION_DAYS`.

Restore is destructive and requires explicit confirmation:

```bash
ENV_FILE=.env bash deploy/restore_postgres.sh \
  backups/tiktok_loader_YYYYMMDDTHHMMSSZ.dump --confirm
```

The restore verifies the checksum and archive, creates a pre-restore safety backup, stops public
and background application services, recreates the database, restores data, applies migrations,
starts services, and runs smoke tests. On failure, application services remain stopped for
investigation. Use `--skip-pre-backup` only in a documented disaster-recovery case.

## Application Rollback

```bash
ENV_FILE=.env bash deploy/rollback.sh production <previous-tag-or-commit> --confirm
```

Rollback creates a fresh backup and changes application code only. It never runs `alembic
downgrade`. The target application must be schema-compatible. Restore an older database backup
only after impact review and according to the recovery plan.
