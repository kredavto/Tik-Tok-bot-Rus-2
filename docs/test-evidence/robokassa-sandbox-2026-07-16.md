# Robokassa sandbox acceptance evidence

- Date: 2026-07-16 (UTC)
- Environment: production-hosted release candidate using Robokassa sandbox
- Payment revision: `08957a9fd2c906a35b58497ad90b474b95ebb0bb`
- Accepted remediation revision: `598cc22ec1ec4da871465fde64ff0a8f130f8b8a`

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
| Automatic provider ResultURL | PASS | Robokassa delivered invoice `1004` to the public ResultURL, which returned HTTP 200. |
| Direct HTTPS ResultURL, first delivery | PASS | Fresh staging invoice `1003` returned HTTP 200 and `OK1003`. |
| Direct HTTPS ResultURL, duplicate delivery | PASS | Duplicate delivery returned HTTP 200 and `OK1003` without a second activation. |
| Invalid ResultURL signature | PASS | Callback returned HTTP 400 with public error code `PAY_400`. |
| Payment status | PASS | Provider invoice `1004` is `paid` for PRO at 499 RUB. |
| Subscription integrity | PASS | Exactly one active 30-day PRO subscription is linked to invoice `1004`. |
| Webhook idempotency | PASS | Exactly one claimed `payment_result` event exists for invoice `1004`; duplicate-delivery coverage also passed in CI. |
| Telegram notification | PASS | The durable `payment_success_notification` event for invoice `1004` reached `processed`. |
| Stored payload sanitization | PASS | Migration `0010` removed callback signatures from payment and webhook JSONB payloads; both residual counts are zero. |
| Access-log sanitization | PASS | A marker query was absent from API logs; structured logs contain only the callback path without query parameters. |
| Production credential switch | PASS | Production Password #1 and #2 are installed, `ROBOKASSA_TEST_MODE=false`, and generated checkout parameters omit `IsTest`. |
| Automated tests and migrations | PASS | [GitHub Actions CI run #59](https://github.com/kredavto/Tik-Tok-bot-Rus-2/actions/runs/29538855376) passed all jobs with 159 tests and 61.42% coverage. |
| Independent code review | PASS | No P0-P2 findings remained for revision `3a04e6e`. |
| Concurrent worker runtime | PASS | 24 idempotent DB maintenance actors completed on four Dramatiq threads without asyncpg or cross-event-loop errors. |

## Deployment verification

The deployment created verified PostgreSQL backup
`tiktok_loader_20260716T221834Z.dump`, built the application image, applied Alembic migration
`0010_scrub_robokassa_signatures`, and started the API, bot, worker, scheduler, PostgreSQL, and
Redis containers. Public health, readiness, metrics, OpenAPI,
and Content-Security-Policy checks passed at `https://loader.invest-lend.ru`.
The worker was then exercised with 24 concurrent maintenance actors; all database
operations ran through the persistent worker event loop without pool contention.
The pre-existing `tiktokbot` stack and its Cloudflare tunnel remained active and
were not modified.

## Remaining gates

Robokassa sandbox acceptance is complete. No real funds were charged during this run. Remaining
release gates belong to other provider-backed scenarios:

1. Complete TikTok OAuth with an approved production application and test account.
2. Publish a test video through the official TikTok Content Posting API and record its final status.
3. Complete a Telegram Stars test purchase and refund/reconciliation scenario.
4. Promote the accepted release candidate to stable SemVer only after the remaining provider gates pass.

Robokassa documents that the merchant receives payment confirmation through
ResultURL and that duplicate deliveries must be handled by the merchant:
[payment interface](https://docs.robokassa.ru/ru/pay-interface.html) and
[notifications and redirects](https://docs.robokassa.ru/ru/notifications-and-redirects).

## Secret handling

Passwords, Telegram tokens, signatures, complete checkout URLs, user identifiers, and
raw callback payloads are intentionally excluded from this evidence file.
