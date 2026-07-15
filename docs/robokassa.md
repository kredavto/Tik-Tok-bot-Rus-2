# Robokassa Setup

> Policy boundary: PRO and BUSINESS are digital services consumed inside Telegram. The bot must use
> Telegram Stars for in-bot checkout and must not show Robokassa as an alternative payment method.
> This integration remains available only for an approved external sales channel. Operators create
> checkout links through the authenticated admin API; the Telegram bot itself continues to offer
> Stars only.

End-to-end payment sequence is documented in [Sequence Flows](sequence-flows.md).

## Tariff Mapping

| Plan | Amount | Period |
| --- | ---: | --- |
| PRO | 499 RUB | 30 days |
| Business | 999 RUB | 30 days |

FREE does not use Robokassa.

## Signature Rules

Payment link signature:

```text
MerchantLogin:OutSum:InvId:Password1
```

Result URL signature:

```text
OutSum:InvId:Password2
```

`ROBOKASSA_HASH_ALGORITHM` must match the technical settings of the shop and accepts `md5`,
`sha256`, or `sha512`. Signatures are compared in constant time. The application formats `OutSum`
with two decimal places when it creates a checkout and validates the exact callback value returned
by Robokassa.

## External Checkout

An ADMIN or SUPER_ADMIN creates an order for an existing Telegram user with:

```http
POST /api/v1/admin/payments/robokassa/orders
Content-Type: application/json

{"telegram_user_id": 123456789, "plan_id": "pro"}
```

The endpoint requires the admin bearer token, admin Telegram ID, and CSRF token. It returns a
single signed `checkout_url`, records an audit action, and never returns either Robokassa password.
Do not place this endpoint or its checkout link in the Telegram digital-goods flow.

## Activation Rules

Only Result URL activates a subscription. Success URL is informational and never changes payment or subscription status.

Subscription state and history rules are documented in [Subscriptions Entity](subscriptions-entity.md).

Payment storage and idempotency rules are documented in [Payments Entity](payments-entity.md).

The backend validates:

- Result URL signature.
- `InvId`.
- Amount.
- Currency when Robokassa sends it.
- Repeated notifications idempotently.

Robokassa merchant credentials must stay only in `.env`.

## Sandbox Acceptance

1. Use the dedicated test Password #1 and Password #2 and set `ROBOKASSA_TEST_MODE=true`.
2. Confirm the configured hash algorithm matches the shop settings.
3. Create a fresh external checkout through the admin API and open the returned URL.
4. Complete the simulated payment in Robokassa; no real money is charged.
5. Verify the public ResultURL returned `OK{InvId}`, the payment became `paid`, exactly one paid
   subscription is active, and a duplicate callback does not activate another subscription.
6. Store only sanitized evidence: timestamp, release SHA, invoice ID, amount, HTTP outcome, payment
   status, active-subscription count, and webhook status.

Production passwords and `ROBOKASSA_TEST_MODE=false` may be installed only after this scenario
passes against the same release candidate.
