# QA Test Data and Acceptance Scenarios

Requirement-to-test mapping is maintained in [Requirements Traceability Matrix](requirements-traceability.md).

## Test Users

Prepare these accounts in staging:

| Test User | Purpose |
| --- | --- |
| FREE user | Validate free daily limit and default plan assignment |
| PRO user | Validate paid plan behavior and daily limit |
| BUSINESS user | Validate higher paid limit |
| Administrator | Validate admin API and audit log |
| User without TikTok | Validate TikTok connection requirement |

Use test credentials and staging-only data. Do not use production secrets in QA environments.

## Acceptance Scenarios

### QA-REG-001: New User Registration

Automation: implemented in `tests/test_subscriptions.py` and `tests/test_bot_fsm.py`.

Expected result:

- User is created.
- Terms flow works.
- FREE plan is assigned.
- Audit and diagnostic logs contain expected entries.

### QA-OAUTH-001: TikTok OAuth Connection

Automation: OAuth state, URL, signature, and encrypted storage paths are covered. Final provider
authorization remains a staging check.

Expected result:

- OAuth starts through official TikTok authorization.
- Callback validates `state`.
- Tokens are encrypted before storage.
- User receives a successful connection notification.

### QA-UPL-001: Successful Video Publication

Automation: video validation, FSM options, queue locking, TikTok client mocks, and status history
are covered. Final publication through an approved TikTok application remains a staging check.

Expected result:

- Upload job is created.
- Video is validated.
- Job is queued and processed.
- Official TikTok API acceptance is recorded.
- User daily usage is incremented only after acceptance.
- User receives final notification.

### QA-LIMIT-001: Daily Limit Exceeded

Automation: implemented in `tests/test_subscriptions.py`, including concurrent first-use checks.

Expected result:

- User cannot exceed the plan limit.
- No extra upload is accepted.
- User receives a clear limit notification.
- Logs include user and correlation context.

### QA-PAY-001: PRO Purchase Through Robokassa

Automation: signature, order creation, amount validation, and duplicate ResultURL activation are
covered. A Robokassa test-mode round trip remains a staging check.

Expected result:

- Payment order and `InvId` are created.
- Robokassa ResultURL signature, amount, currency, and `InvId` are verified.
- Subscription activates only after ResultURL.
- SuccessURL does not activate subscription.
- User receives payment success notification.

### QA-SUB-001: Automatic Return to FREE

Automation: implemented in `tests/test_subscriptions.py`.

Expected result:

- Expired PRO or BUSINESS subscription is marked expired.
- FREE becomes active.
- User history remains intact.
- User receives expiration or plan-change notification when applicable.

### QA-WEBHOOK-001: Repeated Webhook

Automation: payment idempotency and webhook signature rejection are covered. Provider redelivery
is also checked during staging acceptance.

Expected result:

- Duplicate webhook is detected.
- Processing is idempotent.
- Payment or subscription is not activated twice.
- Webhook event history contains enough diagnostic detail.

### QA-QUEUE-001: Temporary Queue Failure Recovery

Automation: scheduler lease recovery, worker lock exclusion, and bounded TikTok chunk retries are
covered.

Expected result:

- Temporary failure is retried safely.
- Non-retryable failures are not retried automatically.
- Job status remains consistent.
- Daily usage is not double-counted.

## Success Criteria

All acceptance scenarios must:

- Finish with the expected result.
- Produce no unhandled exceptions.
- Preserve database integrity.
- Produce required logs, audit records, and diagnostic identifiers.
- Send correct user notifications.
- Leave queues and counters in a consistent state.

## Release Rule

A release candidate is not ready until required QA scenarios pass in staging or an equivalent controlled environment.
