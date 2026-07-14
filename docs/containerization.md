# Containerization

## Services

- `bot`: Telegram bot on aiogram.
- `api`: FastAPI backend.
- `worker`: Dramatiq background workers.
- `scheduler`: recurring task dispatch with Redis leases and heartbeat.
- `migrate`: one-shot Alembic migration gate that must complete before application services start.
- `postgres`: PostgreSQL 16.
- `redis`: Redis cache, locks, and queue backend.
- `nginx`: reverse proxy for public HTTP/HTTPS traffic.

## Startup

```bash
cp .env.example .env
docker compose up -d
```

## Networking

PostgreSQL and Redis are not published to the host. Application services communicate over the dedicated `internal` Docker network. Nginx is attached to both `internal` and `public` networks and is the only public entrypoint.

## Volumes

- `postgres_data`: persistent PostgreSQL data.
- `redis_data`: Redis persistence.
- `./data`: uploaded video workspace.
- `./backups`: database and configuration backups.

## Healthchecks

Compose includes healthchecks for:

- PostgreSQL via `pg_isready`.
- Redis via `redis-cli ping`.
- API via `/health`.
- Nginx via `/health` proxy.
- Scheduler via its Redis heartbeat.

API, bot, worker, and scheduler wait for the one-shot `migrate` service. This prevents concurrent
schema upgrades when API or worker processes are scaled horizontally.

Service continuity requirements are documented in [Service Continuity Plan](service-continuity-plan.md).

## Production Notes

- Keep secrets only in `.env`.
- Do not expose PostgreSQL or Redis ports.
- Use `NGINX_TEMPLATE=https.conf.template` and put copied TLS certificate/key files under
  `TLS_CERT_DIR`, or terminate HTTPS at a managed load balancer with an approved Compose override.
- Application containers run as `appuser`, drop Linux capabilities, enable `no-new-privileges`,
  and use an isolated temporary filesystem.
- Update base images regularly.
