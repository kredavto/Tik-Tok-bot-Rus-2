# Risk Management

## Operational Constraints

- Use only official TikTok interfaces.
- Do not perform actions outside granted OAuth permissions.
- Do not store secrets in Git.
- External integrations must handle temporary unavailability.
- Do not retry TikTok authorization errors or platform restriction errors automatically.

## Risk Register

| Risk | Controls |
| --- | --- |
| External API unavailable | Retry temporary failures only, log errors, keep queue state durable |
| Robokassa payment errors | Validate ResultURL signature, amount, currency, and InvId; process idempotently; audit all status changes |
| Load growth | Scale API workers and Dramatiq workers horizontally; paginate admin lists; monitor queue size |
| PostgreSQL failure | Back up regularly and test restores on staging |
| Redis failure | Keep canonical upload/payment/subscription state in PostgreSQL; restart services safely |
| Bad release | Back up before deploy, test on staging, deploy step-by-step, monitor after release |
| Secret leakage | Keep secrets in `.env` or secret storage only; CI secret scan; never export secret-like settings |
| Video processing failure | Validate files before publishing; do not consume daily quota until official TikTok API accepts publication |

## Change Control

Before production changes:

1. Assess API, database, security, and user-flow impact.
2. Add or update tests.
3. Update documentation.
4. Test in staging.
5. Create a production backup.
6. Deploy step-by-step.
7. Monitor `/health`, `/ready`, `/metrics`, queues, payments, and TikTok API errors.

## Resilience Criteria

The system must preserve user history, payment records, subscriptions, upload metadata, and audit trails during temporary external failures and controlled restarts.

