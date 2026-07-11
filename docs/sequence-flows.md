# Sequence Flows

The high-level component map is documented in [Project Component Map](component-map.md).

## Video Publication Flow

```mermaid
sequenceDiagram
    participant User
    participant Bot as Telegram Bot
    participant API as FastAPI Backend
    participant DB as PostgreSQL
    participant Queue as Redis Queue
    participant Worker
    participant TikTok as Official TikTok API

    User->>Bot: Send video
    Bot->>API: Check subscription and daily limit
    API->>DB: Read user, subscription, daily_usage
    API-->>Bot: Limit check result
    Bot->>API: Create upload job
    API->>DB: Store upload_jobs and upload_job_events
    API->>Queue: Enqueue processing task
    Queue-->>Worker: Deliver task
    Worker->>DB: Mark VALIDATING/PREPARING
    Worker->>TikTok: Submit through official Content Posting API
    TikTok-->>Worker: Accepted/status/error
    Worker->>DB: Store status and lifecycle event
    Worker->>Bot: Notify user
    Bot-->>User: Publication result
```

Rules:

- Use Request ID and Correlation ID across bot, API, worker, and logs.
- Create `upload_jobs` before enqueueing processing.
- Record every status transition.
- Retry only temporary failures.
- Consume daily usage only after official TikTok API acceptance.
- Do not retry automatically for authorization, permission, platform, or regional restrictions.

## Payment Flow

```mermaid
sequenceDiagram
    participant User
    participant Bot as Telegram Bot
    participant API as FastAPI Backend
    participant DB as PostgreSQL
    participant Robo as Robokassa

    User->>Bot: Select PRO or BUSINESS
    Bot->>API: Create payment order
    API->>DB: Store payment with InvId
    API-->>Bot: Return payment URL
    Bot-->>User: Send payment URL
    User->>Robo: Pay invoice
    Robo->>API: ResultURL notification
    API->>API: Verify signature, amount, currency, InvId
    API->>DB: Mark payment paid and activate subscription
    API-->>Robo: OK{InvId}
    API->>Bot: Notify subscription activated
    Bot-->>User: Payment success message
```

Rules:

- FREE does not create a payment.
- Only ResultURL activates subscriptions.
- SuccessURL is informational.
- Repeated ResultURL events are idempotent.
- Payment status and subscription activation must be transactional.
- Never log Robokassa secrets.

## Cross-Cutting Requirements

- All service-to-service operations must be logged with sanitized context.
- Use UTC timestamps in logs and database events.
- Use correlation IDs for linked operations.
- Persist webhook events before processing.
- Keep retries idempotent.
- Follow [Queue and Retry Policy](queue-retry-policy.md), [Observability and Diagnostics](observability-diagnostics.md), and [Error Codes and Exception Handling](error-handling.md).
