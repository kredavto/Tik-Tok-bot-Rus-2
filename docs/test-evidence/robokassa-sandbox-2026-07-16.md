# Robokassa sandbox acceptance evidence

Date: 2026-07-16 (UTC)  
Environment: staging  
Application revision: `3a04e6ebf4352cf9c55b071d3247fa27341de5d3`

## Scope

The acceptance run covered checkout signature validation with test Password #1,
ResultURL validation with test Password #2, payment idempotency, subscription
activation, durable Telegram notification recovery, deployment health checks,
and rejection of invalid callback signatures. No real funds were charged.

## Results

| Check | Result | Evidence |
| --- | --- | --- |
| Robokassa sandbox checkout opens | PASS | Test checkout displayed the expected merchant and PRO amount of 499 RUB. |
| Sandbox card operation | PASS | Robokassa test UI completed the operation with the successful test outcome. |
| Automatic provider ResultURL | BLOCKED | The provider did not call the configured public endpoint. The merchant test profile must be updated in Robokassa. |
| Direct HTTPS ResultURL, first delivery | PASS | Fresh staging invoice `1003` returned HTTP 200 and `OK1003`. |
| Direct HTTPS ResultURL, duplicate delivery | PASS | Duplicate delivery returned HTTP 200 and `OK1003` without a second activation. |
| Invalid ResultURL signature | PASS | Callback returned HTTP 400 with public error code `PAY_400`. |
| Payment status | PASS | Invoice `1003` is `paid`. |
| Subscription integrity | PASS | Exactly one active subscription remained after processing. |
| Webhook idempotency | PASS | Exactly one claimed `payment_result` event exists for invoice `1003`. |
| Notification recovery | PASS | A durable `payment_success_notification` outbox event remained `pending` while the Telegram token was invalid. |
| Automated tests and migrations | PASS | GitHub Actions CI run #47 completed successfully. |
| Independent code review | PASS | No P0-P2 findings remained for revision `3a04e6e`. |
| Concurrent worker runtime | PASS | 24 idempotent DB maintenance actors completed on four Dramatiq threads without asyncpg or cross-event-loop errors. |

## Deployment verification

The deployment created a PostgreSQL backup, built the application image,
applied Alembic migrations, and started the API, bot, worker, scheduler,
PostgreSQL, and Redis containers. Public health, readiness, metrics, OpenAPI,
and Content-Security-Policy checks passed at `https://loader.invest-lend.ru`.
The worker was then exercised with 24 concurrent maintenance actors; all database
operations ran through the persistent worker event loop without pool contention.
The pre-existing `tiktokbot` stack and its Cloudflare tunnel remained active and
were not modified.

## Remaining gates

1. Enter the Robokassa cabinet PIN and configure the test merchant profile:
   - Result URL: `https://loader.invest-lend.ru/api/v1/payments/robokassa/result`
   - Result method: `POST`
   - Success URL: `https://loader.invest-lend.ru/api/v1/payments/robokassa/success`
   - Fail URL: `https://loader.invest-lend.ru/api/v1/payments/robokassa/fail`
2. Repeat a new sandbox checkout and confirm that Robokassa itself delivers the
   first ResultURL notification.
3. Replace the revoked Telegram token in the new stack, configure the webhook,
   and verify that the pending outbox notification is delivered.
4. Only after all sandbox gates pass, replace test Robokassa credentials with
   production credentials and set `ROBOKASSA_TEST_MODE=false`.

Robokassa documents that the merchant receives payment confirmation through
ResultURL and that duplicate deliveries must be handled by the merchant:
[payment interface](https://docs.robokassa.ru/ru/pay-interface.html) and
[notifications and redirects](https://docs.robokassa.ru/ru/notifications-and-redirects).

## Secret handling

Passwords, Telegram tokens, signatures, checkout URLs, user identifiers, and
raw callback payloads are intentionally excluded from this evidence file.
