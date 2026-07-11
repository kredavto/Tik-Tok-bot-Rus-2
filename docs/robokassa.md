# Robokassa Setup

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

The bot contains helpers for both operations in `app.services.robokassa`.

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
