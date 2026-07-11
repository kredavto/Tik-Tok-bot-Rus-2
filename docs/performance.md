# Performance and Scaling

Performance-related non-functional requirements are summarized in [Non-Functional Requirements](non-functional-requirements.md).

## Goals

- Fast Telegram command responses.
- Long-running work is handled by workers.
- Redis is used for cache, locks, OAuth state, rate limiting, and queue coordination.
- PostgreSQL queries use indexes for common filters and ordering.

Operational KPI for performance and reliability are defined in [Metrics and KPI](metrics-and-kpi.md).

Capacity thresholds and scaling actions are documented in [Capacity and Performance Management](capacity-management.md).

## Scaling API

Set:

```env
API_WORKERS=2
```

Run multiple `web` containers behind Nginx or another load balancer when needed.

## Scaling Workers

Set:

```env
DRAMATIQ_PROCESSES=2
DRAMATIQ_THREADS=8
```

Worker operations use Redis locks for upload-job idempotency and daily-limit safety.

Queue retry behavior and safe task restart rules are documented in [Queue and Retry Policy](queue-retry-policy.md).

## Database

Admin lists use pagination:

```http
GET /admin/users?limit=50&offset=0
GET /admin/payments?limit=50&offset=0
GET /admin/upload-jobs?status=FAILED&limit=50&offset=0
```

Use PostgreSQL `EXPLAIN ANALYZE` during performance reviews.

## Safe Restarts

- Upload state is persisted in PostgreSQL.
- Queue state is coordinated through Redis and Dramatiq.
- Daily quota is consumed only after official TikTok API acceptance.
