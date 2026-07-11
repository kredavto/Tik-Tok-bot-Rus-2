# TikTok Developer Configuration

## Application Configuration

- Store `TIKTOK_CLIENT_KEY` and `TIKTOK_CLIENT_SECRET` only in `.env` or a managed secret store.
- Do not commit TikTok credentials.
- Use separate TikTok developer applications for development, staging, and production when needed.
- Keep `TIKTOK_REDIRECT_URI` synchronized with the production HTTPS callback URL.
- Document every TikTok Developer Portal setting change in the operations journal or admin audit log.

## OAuth Settings

Before release, verify:

- Redirect URI exactly matches `TIKTOK_REDIRECT_URI`.
- Required scopes are approved in TikTok Developer Portal.
- `video.publish` is approved before production publication is enabled.
- OAuth `state` validation works.
- Access token expiration is handled.
- Refresh token renewal flow works.
- Token refresh errors do not expose tokens in logs.

## Webhook Settings

TikTok webhook configuration must:

- Use HTTPS.
- Match the production public domain.
- Include `TIKTOK_WEBHOOK_SECRET` when signature verification is enabled.
- Verify inbound webhook signatures.
- Process events idempotently.
- Log delivery, validation, and processing errors without exposing secrets.

## Production Pre-Release Check

Before every production release:

1. Confirm TikTok Developer Portal app status.
2. Confirm production Redirect URI.
3. Confirm approved scopes.
4. Confirm webhook URL and secret.
5. Run a test OAuth authorization with a test TikTok account.
6. Confirm encrypted token storage.
7. Confirm refresh flow behavior.
8. Confirm official Content Posting API behavior in staging or controlled production test.
9. Confirm no bypass, browser automation, or unofficial API behavior exists.

TikTok account persistence rules are documented in [TikTok Accounts Entity](tiktok-accounts-entity.md).

## Change Control

Changes to TikTok Developer settings must include:

- Date and owner.
- Environment.
- Changed setting.
- Reason for change.
- Expected impact.
- Verification result.
- Rollback plan when applicable.

## Compliance Rule

If TikTok rejects authorization, scope, publication, region, account, policy, or webhook processing, the application must report the restriction and must not attempt circumvention.
