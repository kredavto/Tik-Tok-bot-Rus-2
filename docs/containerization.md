# Containerization

## Services

- `bot`: Telegram bot on aiogram.
- `api`: FastAPI backend.
- `worker`: Dramatiq background workers.
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

Service continuity requirements are documented in [Service Continuity Plan](service-continuity-plan.md).

## Production Notes

- Keep secrets only in `.env`.
- Do not expose PostgreSQL or Redis ports.
- Put TLS certificates under `deploy/nginx/certs` or terminate HTTPS at a managed load balancer.
- Update base images regularly.
