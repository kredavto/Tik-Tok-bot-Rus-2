# Project Component Map

This document is the high-level navigation map for Tik_Tok_Loader components. It gives developers a single overview of the system boundaries, data flows, and final architecture principles.

## Main Components

| Component | Purpose |
| --- | --- |
| Telegram Bot | User interface, registration, FSM flows, uploads, tariffs, settings, and notifications. |
| FastAPI | REST API, TikTok OAuth, webhooks, Robokassa callbacks, business services, health checks, and metrics. |
| PostgreSQL | Primary data store for users, TikTok accounts, subscriptions, payments, upload jobs, usage counters, webhook events, audit logs, and settings. |
| Redis | Queue coordination, cache, rate limiting, OAuth state storage, and distributed locks. |
| Worker | Background processing for video validation, preparation, publication, status checks, cleanup, subscription expiry, and retries. |
| Scheduler | Redis-leased dispatch of subscription expiry, OAuth refresh, and retention tasks. |
| TikTok API | Official OAuth 2.0 authorization and Content Posting API video publication. |
| Telegram Stars | In-bot payment acceptance for PRO and BUSINESS digital subscriptions. |
| Robokassa | Existing callback integration reserved for a separately approved sales channel. |
| SBP C2B | Future official merchant QR/API integration issued by an acquiring bank. |
| Admin Panel | Administrative management, analytics, audit review, settings, users, payments, and upload queues. |

## Interaction Flows

```mermaid
flowchart LR
    User["User"] --> Bot["Telegram Bot"]
    Bot --> API["FastAPI"]
    API --> DB["PostgreSQL"]
    API --> Redis["Redis"]
    Scheduler["Scheduler"] --> Redis
    Redis --> Worker["Worker"]
    Worker --> TikTok["TikTok Content Posting API"]
    Stars["Telegram Stars"] --> Bot
    Robokassa["Robokassa"] --> ResultURL["ResultURL"]
    SBP["SBP acquiring bank"] --> PaymentCallback["Verified callback/status"]
    PaymentCallback --> API
    ResultURL --> API
    API --> Bot
    Bot --> User
```

Canonical service flows are:

- User -> Telegram Bot -> FastAPI.
- FastAPI -> PostgreSQL / Redis.
- Worker -> official TikTok Content Posting API.
- Telegram Stars -> Bot API update -> PostgreSQL subscription transaction.
- Approved external channel: Robokassa -> ResultURL -> FastAPI.
- Future approved channel: SBP acquiring bank -> verified callback/status -> FastAPI.
- FastAPI -> Telegram Bot -> User.

Detailed publication and payment sequences are documented in [Sequence Flows](sequence-flows.md).

## Architecture Principles

- Modularity.
- Asynchronous processing.
- Security by default.
- Idempotent critical operations.
- Scalable API and worker boundaries.
- Complete and current documentation.
- Official TikTok APIs only.
- Automated tests for release readiness.

## Final Guidance

All specification sections form one technical requirement set for Tik_Tok_Loader. Future changes must preserve the architecture described in [Architecture Summary](architecture-summary.md), remain inside the official TikTok API model, include relevant automated tests, and update documentation together with implementation changes.
