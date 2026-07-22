# Upload Jobs Entity

## Purpose

`upload_jobs` tracks the lifecycle of each video publication request from Telegram intake through official TikTok API submission and final status.

## Recommended Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Upload job identifier |
| `user_id` | UUID | Reference to `users.id` |
| `tiktok_account_id` | UUID | Reference to `tiktok_accounts.id` |
| `status` | VARCHAR | `NEW`, `QUEUED`, `UPLOADING`, `PROCESSING`, `PUBLISHED`, `FAILED`, `CANCELLED` |
| `video_path` | TEXT | Temporary local file path |
| `caption` | TEXT | Video description |
| `hashtags` | TEXT | Hashtags |
| `error_code` | VARCHAR | Error code when available |
| `usage_date` | DATE | Business date on which the accepted attempt was reserved |
| `usage_refunded_at` | TIMESTAMP WITH TIME ZONE | Idempotency marker for a returned attempt |
| `created_at` | TIMESTAMP WITH TIME ZONE | Record creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | Last update time |

The current implementation may use internal names such as `local_path` for `video_path` and may store hashtags as part of `caption` until a separate field is introduced through migration.

## Lifecycle

1. Create upload job.
2. Validate video.
3. Queue processing.
4. Upload through the official TikTok Content Posting API.
5. Receive or poll publication status.
6. Mark as published, failed, or cancelled.

The detailed lifecycle is documented in [Video Publication Lifecycle](video-lifecycle.md).

## Status Rules

- Every job uses a unique UUID.
- Status changes must follow allowed transitions.
- Every status change must be recorded in `upload_job_events`.
- Retry is allowed only for temporary errors.
- Terminal states must not be overwritten by stale retries.
- User daily allowance is reserved only after official TikTok API acceptance.
- A final TikTok `FAILED` status returns the reservation exactly once. Repeated webhook delivery or
  polling cannot decrement the counter twice.

Daily counter rules are documented in [Daily Usage Entity](daily-usage-entity.md).

## Relationships

| Relationship | Cardinality |
| --- | --- |
| `users` -> `upload_jobs` | 1:N |
| `tiktok_accounts` -> `upload_jobs` | 1:N |
| `upload_jobs` -> `upload_job_events` | 1:N |

## Development Requirement

Changes to `upload_jobs` require updated SQLAlchemy models, Alembic migrations, tests, queue/retry review, documentation, and data quality checks.
