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
3. The bot sends a single-chat invoice with currency `XTR`, omits `provider_token`, and puts the
   payment UUID in the invoice payload. Forwarded copies cannot be paid directly.
4. The bot validates the `pre_checkout_query` user, currency, amount, plan, and payment status and
   answers within the Telegram deadline.
5. A subscription is activated only after the bot receives `successful_payment`.
6. `telegram_payment_charge_id` is stored as `provider_charge_id` and is unique per provider.
7. Duplicate delivery returns the previously processed result and never creates another subscription.

## Security and Support

- Do not activate a plan from an invoice send result or pre-checkout request.
- Stars availability and checkout must depend on `price_stars`, not on the independent RUB price.
- A definitive Bot API rejection marks the local order `failed`. A transport-level ambiguous result
  leaves it `created` so a delivered invoice can still pass pre-checkout validation.
- Do not trust invoice payload, user ID, amount, or currency without a database comparison.
- Never log Telegram bot tokens, payment credentials, or user banking data.
- Keep `/paysupport` available and provide a safe support process.
- Keep `/terms` available so users can review the accepted terms before and after checkout.
- Register `/terms`, `/paysupport`, and the other supported commands in Telegram when configuring
  the production webhook.
- Refunds must use Telegram's `refundStarPayment` method and update the immutable payment history to
  `refunded`; they must not be implemented as an undocumented manual balance adjustment.
- ADMIN and SUPER_ADMIN perform eligible refunds through
  `POST /api/v1/admin/payments/{payment_id}/refund-stars`. The operation first commits a
  `refund_pending` claim under a database row lock, then calls Telegram outside the transaction.
- A repeated request while `refund_pending` never sends a second refund. A definitive rejection
  returns the payment to `paid`; an ambiguous network result stays pending for reconciliation.
- Telegram's `refunded_payment` service event finalizes local payment and subscription state if the
  provider refund succeeded but the API process failed before its final database commit.
- If a network result remains ambiguous and no service event arrives, an ADMIN can perform a
  provider-side check and use the guarded reconciliation endpoint to finalize `refunded` or restore
  `paid`; the decision is recorded in `admin_actions`.
- A delayed duplicate `successful_payment` is accepted only while the local payment is `created`;
  it can never reactivate `refund_pending` or `refunded` state.
- Requested and completed refund stages are recorded in the administrator audit log. A completed
  refund returns the affected active subscription to FREE.

## Acceptance Criteria

- Exact user, amount, currency, provider, and payment ID are validated.
- Concurrent duplicate confirmations activate one subscription.
- Reuse of a charge ID for another payment is rejected.
- PRO is invoiced for `199 XTR` and BUSINESS for `499 XTR` by default.
- PRO and BUSINESS Stars prices can be changed without a source-code release.
- `/terms` and `/paysupport` remain available in production.
- RUB and XTR revenue are reported separately.
- Repeated Stars refund requests do not call Telegram or alter subscription state twice.
- Ambiguous refund results remain recoverable and are finalized idempotently from Telegram's service
  event or through permission-checked, CSRF-protected, audited manual reconciliation.

## Production Acceptance Evidence

The provider-backed Telegram Stars scenario was completed on 2026-07-17 against the production
bot. The PRO Stars price was changed through the audited administrative API from the approved
`199 XTR` value to a temporary `10 XTR` acceptance value; RUB pricing was not changed.

- Telegram confirmed one `10 XTR` payment and the application persisted one unique provider charge.
- The successful payment activated one PRO subscription; two independently created but unpaid
  invoices remained non-activating records.
- The official `refundStarPayment` operation returned success, the payment moved to `refunded`,
  and the test PRO subscription moved to `cancelled`.
- Exactly one FREE subscription became active after the refund.
- The PRO Stars price was restored to `199 XTR` through the administrative API.
- Price changes and both refund stages are present in `admin_actions`; provider charge identifiers
  and personal data are intentionally excluded from this document.
- Public health, readiness, metrics, OpenAPI, security-header, and Telegram webhook smoke checks
  passed after the scenario.
