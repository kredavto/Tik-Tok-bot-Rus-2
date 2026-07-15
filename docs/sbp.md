# SBP Merchant Payments

## Supported Model

SBP support must use an official C2B merchant QR or payment URL issued by a participating acquiring
bank or the SBP infrastructure. A QR generated from a telephone number, plain text, `tel:` link, bank
name, or card-transfer instruction is not an SBP merchant QR and must not be presented as one.

Official references:

- [SBP for business](https://www.sbp.nspk.ru/business)
- [SBP business FAQ](https://sbp.nspk.ru/faq/business)
- [SBP QR FAQ](https://sbp.nspk.ru/faq/qr)
- [Alfa-Bank API release notes](https://developers.alfabank.ru/release-notes)

## Acquiring Requirements

Before enabling SBP, the project owner must:

1. Conclude a merchant acquiring agreement with a participating bank.
2. Register the merchant and payment points.
3. Obtain an official static QR payload or authenticated API credentials for dynamic QR creation.
4. Obtain a signed callback or status API for payment confirmation.
5. Confirm fiscal-receipt and refund requirements with the acquiring bank and accountant.

The preferred receiving bank is Alfa-Bank. The recipient phone and receiving-bank preference are
operational personal data and must be configured in the bank/SBP profile and protected server-side;
they must not be committed to Git or embedded as plain text in application assets.

## Bank Selection

The payer selects the source bank in the official SBP payment interface after scanning the QR. The
bot does not create separate QR codes for Sberbank, Alfa-Bank, and T-Bank and does not encode a
"default bank" into a homemade QR. The recipient's default bank is controlled through the recipient's
SBP settings.

## Tariff QR Assets

After verified payloads are received, separate assets may be provisioned for PRO and BUSINESS under
server-managed storage. Each asset must retain its bank-issued payload exactly and be accompanied by
server-side payment verification. A QR image alone must never activate a subscription.

## Telegram Distribution Boundary

Because PRO and BUSINESS are digital services inside Telegram, SBP must not be exposed in the bot as
an alternative checkout method to Telegram Stars. Any future SBP channel requires a separate policy
and legal review and must not create a path that violates Telegram's digital-goods payment rules.

## Acceptance Criteria

- QR payload provenance is recorded and verified against the acquiring bank.
- Payment amount, merchant, order, currency, and status are verified server-side.
- Callback and status reconciliation are idempotent.
- Screenshot, Success URL, user message, or QR scan alone never activates a subscription.
- Refund and fiscalization procedures are documented and tested in staging.
