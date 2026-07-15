# Telegram Stars Payments

## Scope and Compliance

PRO and BUSINESS are digital services consumed inside Telegram. Purchases initiated by the bot must
therefore use Telegram Stars (`XTR`) in accordance with the official Telegram payment rules for
digital goods and services.

The bot must not present Robokassa, bank-card links, phone transfers, or another currency as an
alternative checkout method for the same digital subscription inside Telegram.

Official references:

- [Telegram Stars payments for bots](https://core.telegram.org/bots/payments-stars)
- [Telegram Stars API](https://core.telegram.org/api/stars)

## Tariff Configuration

`plans.price_stars` stores the positive integer Stars price for each paid plan. The approved prices
are `199 XTR` for PRO and `499 XTR` for BUSINESS. Values are managed through the administrative API
and panel and are independent from `price_rub`; no automatic RUB-to-XTR conversion is allowed.

## Payment Flow

1. The user selects PRO or BUSINESS.
2. The backend creates a `payments` row with provider `telegram_stars`, currency `XTR`, and a unique
   payment UUID.
3. The bot sends an invoice with currency `XTR`, an empty provider-token requirement, and the payment
   UUID in the invoice payload.
4. The bot validates the `pre_checkout_query` user, currency, amount, plan, and payment status and
   answers within the Telegram deadline.
5. A subscription is activated only after the bot receives `successful_payment`.
6. `telegram_payment_charge_id` is stored as `provider_charge_id` and is unique per provider.
7. Duplicate delivery returns the previously processed result and never creates another subscription.

## Security and Support

- Do not activate a plan from an invoice send result or pre-checkout request.
- Do not trust invoice payload, user ID, amount, or currency without a database comparison.
- Never log Telegram bot tokens, payment credentials, or user banking data.
- Keep `/paysupport` available and provide a safe support process.
- Refunds must use Telegram's `refundStarPayment` method and update the immutable payment history to
  `refunded`; they must not be implemented as an undocumented manual balance adjustment.

## Acceptance Criteria

- Exact user, amount, currency, provider, and payment ID are validated.
- Concurrent duplicate confirmations activate one subscription.
- Reuse of a charge ID for another payment is rejected.
- PRO is invoiced for `199 XTR` and BUSINESS for `499 XTR` by default.
- PRO and BUSINESS Stars prices can be changed without a source-code release.
- RUB and XTR revenue are reported separately.
