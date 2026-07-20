# TikTok Developer Configuration

## Application Configuration

- Store `TIKTOK_CLIENT_KEY` and `TIKTOK_CLIENT_SECRET` only in `.env` or a managed secret store.
- Do not commit TikTok credentials.
- Use separate TikTok developer applications for development, staging, and production when needed.
- Keep `TIKTOK_REDIRECT_URI` synchronized with the production HTTPS callback URL.
- Document every TikTok Developer Portal setting change in the operations journal or admin audit log.

### Production portal values

Use these exact public values for the production application:

| Setting | Value |
|---|---|
| Application name | `Tik_Tok_loader` |
| Web URL | `https://loader.invest-lend.ru/` |
| Terms of Service URL | `https://loader.invest-lend.ru/legal/terms` |
| Privacy Policy URL | `https://loader.invest-lend.ru/legal/privacy` |
| Redirect URI | `https://loader.invest-lend.ru/api/v1/oauth/tiktok/callback` |
| Webhook URL | `https://loader.invest-lend.ru/api/v1/webhooks/tiktok` |
| Product | Content Posting API |
| OAuth scopes | `user.info.basic`, `video.publish` |

The application icon is stored at `app/public/static/app-icon.png`. It is an original 1024 x
1024 PNG and does not use TikTok or Telegram trademarks.

Recommended short description:

> Telegram bot that lets users securely publish their own videos to TikTok through the official API.

Recommended review explanation:

> Tik_Tok_loader is a Telegram bot for users to publish videos they own to their TikTok account.
> The user connects TikTok through OAuth 2.0 with user.info.basic and video.publish. Before upload,
> the bot queries current creator information, shows the target account and available privacy,
> interaction, and commercial-content settings, and requires explicit confirmation. A background
> worker transfers the file through the official Content Posting API and reports processing and
> final status. OAuth tokens are encrypted and users can disconnect at any time. The service does
> not collect TikTok passwords and does not use unofficial APIs, interface automation, or regional
> restriction bypasses.

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
- Signatures use the TikTok app `TIKTOK_CLIENT_SECRET`; no separate webhook secret is accepted by
  the official verification algorithm.
- Verify the `TikTok-Signature` timestamp and HMAC against the unmodified request body.
- Reject webhook timestamps older than five minutes to limit replay attacks.
- Process events idempotently.
- Log delivery, validation, and processing errors without exposing secrets.

## Production Pre-Release Check

Before every production release:

1. Confirm TikTok Developer Portal app status.
2. Confirm production Redirect URI.
3. Confirm approved scopes.
4. Confirm webhook URL and `TIKTOK_CLIENT_SECRET` signature verification.
5. Run a test OAuth authorization with a test TikTok account.
6. Confirm encrypted token storage.
7. Confirm refresh flow behavior.
8. Confirm official Content Posting API behavior in staging or controlled production test.
9. Confirm no bypass, browser automation, or unofficial API behavior exists.

## Review Evidence

The first review submission must include a demo video recorded with a Sandbox account. The demo
must show the complete user-controlled flow:

1. Start the Telegram bot and accept the service terms.
2. Open TikTok OAuth and approve only the requested scopes.
3. Return to the bot with the connected TikTok account displayed.
4. Upload an owned test video and review creator information.
5. Manually choose privacy and interaction settings with no preselected privacy value.
6. Show the video preview, leave commercial-content disclosure off by default, then demonstrate
   the optional multi-select disclosure controls and the applicable TikTok label.
7. Show the literal Music Usage Confirmation declaration and, for branded content, the Branded
   Content Policy declaration immediately before the publish button.
8. Show the processing status and final private post in the test TikTok account.
9. Disconnect TikTok and confirm that stored OAuth credentials are removed.

Do not submit the application for review until the portal draft, Sandbox flow, and demo video have
all been checked against the current production build.

## Required Direct Post UX

Before every publication the bot must query `/v2/post/publish/creator_info/query/` and:

1. Display the TikTok creator nickname.
2. Require a manual choice from the returned privacy options, with no default.
3. Enforce the creator-specific maximum video duration.
4. Let the user explicitly enable Comment, Duet, and Stitch only when TikTok allows them.
5. Collect commercial-content disclosure and prevent branded content with `SELF_ONLY` visibility.
6. Display a preview of the exact video selected for publication.
7. Display the applicable Music Usage Confirmation and Branded Content Policy declaration.
8. Obtain explicit publication consent before any media is transferred to TikTok.
9. Poll `/v2/post/publish/status/fetch/` or process final Content Posting webhooks.

Unaudited TikTok clients remain restricted to `SELF_ONLY` posts and other platform limits. TikTok
also requires every target creator account to be set to private at posting time. Keep
`TIKTOK_APP_AUDITED=false` until the Direct Post audit is approved; the bot then blocks public
creator accounts before confirmation. The system must report these restrictions and must not
attempt to bypass them.

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
