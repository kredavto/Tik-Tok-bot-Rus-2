# Queue and Retry Policy

## Background Task Types

The worker layer handles:

- Video preparation.
- Publication through the official TikTok Content Posting API.
- Publication status checks.
- OAuth token refresh.
- Temporary file cleanup.
- Subscription expiration checks.
- Return to FREE plan after paid subscription expiration.
- Delivery of durable payment-success notifications.

## Queue Rules

- Every queued task must have a unique identifier.
- Tasks must be idempotent.
- Upload status must be updated after each processing stage.
- Retries are allowed only for temporary failures.
- The same upload job must not be processed concurrently.
- Redis locks are used to prevent duplicate processing.
- PostgreSQL stores the durable task state.
- Redis may cache short-lived status and coordination data.
- All actor coroutines in one Dramatiq process run on one persistent asyncio event loop. Worker
  threads submit coroutines to that loop so the shared SQLAlchemy async pool is never reused across
  incompatible event loops.

## Periodic Maintenance

The dedicated `scheduler` service dispatches maintenance actors through Dramatiq. A Redis lease
is acquired for each periodic task before dispatch, which allows multiple scheduler instances to
run without intentionally enqueueing the same interval twice. If broker dispatch fails, the lease
is released so the next scheduler tick can retry.

The current periodic tasks are:

- Expire due PRO and BUSINESS subscriptions and create the replacement FREE subscription.
- Refresh TikTok access tokens before their expiry.
- Remove temporary files and expired operational records according to the retention policy.
- Redispatch pending payment-success notification outbox events.

Subscription selection uses PostgreSQL `FOR UPDATE SKIP LOCKED`. Expiration notifications use a
per-subscription Redis lock and a durable `expiration_notified_at` marker.

Robokassa activation creates a `payment_success_notification` outbox event in the same PostgreSQL
transaction as the paid subscription. A per-event Redis lock prevents concurrent delivery. The
event becomes `processed` only after Telegram accepts the message. Pending payment outbox events
are excluded from retention cleanup and remain recoverable after broker, worker, or Telegram
outages.

## Retryable Errors

Automatic retry is allowed for:

- Deterministic byte-range chunk uploads rejected with a temporary TikTok 5xx response.
- Publication status checks that have not yet reached a terminal TikTok status.
- Temporary Telegram notification failures.
- Temporary Redis or database connectivity issues when retrying is safe.
- TikTok token refresh requests that fail because of network errors, HTTP 429, or HTTP 5xx.

The complete publication actor is not automatically replayed after an ambiguous failure because
the official API may already have accepted the publication. Such jobs are marked failed for
operator review. A full retry requires evidence that TikTok did not accept the earlier request.

Retry classification must follow [Error Codes and Exception Handling](error-handling.md).

## Non-Retryable Errors

Do not retry automatically for:

- Missing or insufficient TikTok OAuth permissions.
- TikTok regional, account, or platform restrictions.
- Invalid Robokassa configuration.
- Invalid Robokassa signature, amount, currency, or `InvId`.
- Invalid user video format, unsupported container, or corrupted file.
- User cancellation.
- Policy or authorization rejection from an official external API.
- TikTok refresh-token rejection or another permanent OAuth error. The account is marked as
  refresh-blocked until the user reconnects it through the official OAuth flow.
- Telegram `Forbidden`, `Bad Request`, or `Not Found` responses for a payment recipient. The
  affected outbox event becomes `rejected` so it cannot starve newer notifications.

## Status Updates

Upload jobs use the lifecycle statuses documented in [Video Publication Lifecycle](video-lifecycle.md).

Upload job persistence rules are documented in [Upload Jobs Entity](upload-jobs-entity.md).

Each transition should include:

- Upload job ID.
- User ID.
- Previous status.
- New status.
- UTC timestamp.
- Human-readable reason.
- Correlation ID when available.

## Duplicate Prevention

To prevent duplicate publication and duplicate quota consumption:

- Worker processing must acquire a per-upload lock.
- Daily limits are consumed transactionally.
- Daily usage counters follow [Daily Usage Entity](daily-usage-entity.md).
- Payments are activated only through Robokassa ResultURL after signature validation.
- Webhook handling must be idempotent.
- Terminal states must not be overwritten by stale retries.

## Administrative Control

Administrators should be able to inspect:

- Queue size.
- Waiting task count.
- Processing task count.
- Failed task count.
- Retry count.
- Last error reason.
- Correlation ID.
- Related user, payment, or upload job.

Administrators may safely restart individual failed tasks only when the failure is retryable and the task has no active processing lock.

## Operational Goal

Queue processing must preserve data integrity, avoid duplicate publication attempts, avoid duplicate payment activation, and keep enough diagnostic data for safe recovery.
