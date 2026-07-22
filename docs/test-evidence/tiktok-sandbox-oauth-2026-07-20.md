# TikTok Sandbox OAuth acceptance evidence

- Date: 2026-07-20 (UTC)
- Environment: production-hosted release `0.2.0` with TikTok Sandbox credentials
- Application revision: `6a3c6363364db33015466dce14c3851d52d7af1e`
- Public callback: `https://loader.invest-lend.ru/api/v1/oauth/tiktok/callback`

## Scope

The acceptance run covered Sandbox Target User enrollment, Telegram `/connect`, official TikTok
OAuth 2.0 authorization, one-time state enforcement, token exchange, encrypted token persistence,
Telegram notification, Creator Info access, log sanitization, and production health checks. No
video was uploaded or published during this run.

## Results

| Check | Result | Evidence |
| --- | --- | --- |
| Sandbox Target User | PASS | One authorized test account is listed in the selected Sandbox. |
| Telegram OAuth entry point | PASS | `/connect` returned a fresh HTTPS OAuth URL with a server-side one-time state. |
| Official authorization | PASS | TikTok granted `user.info.basic,video.publish` through `www.tiktok.com/v2/auth/authorize/`. |
| Public callback | PASS | The callback exchanged the authorization code and created one TikTok account record. |
| Replay protection | PASS | Reusing the consumed callback state returned public error `AUTH_400` and created no duplicate account. |
| Telegram notification | PASS | The user received the successful TikTok connection notification. |
| Access-token storage | PASS | The stored access token is Fernet ciphertext and decrypts only with the server-side key. |
| Refresh-token storage | PASS | The stored refresh token is Fernet ciphertext and decrypts only with the server-side key. |
| Token lifetime | PASS | The stored access-token expiry is in the future. |
| Creator Info | PASS | The official API returned three privacy options, a 3600-second maximum duration, and available comments. |
| Log sanitization | PASS | Recent API and bot logs contained zero sensitive OAuth marker hits. |
| Service health | PASS | Public `/api/v1/health` and `/api/v1/ready` returned healthy and ready. |

## Security boundary

The acceptance evidence excludes the TikTok username, open ID, authorization code, OAuth state,
access token, refresh token, client key, client secret, Telegram token, and raw callback URL. The
application stores only encrypted OAuth tokens and a sanitized webhook event payload containing
the granted scope.

## Remaining gates

TikTok Sandbox OAuth acceptance is complete. `TIKTOK_PUBLISH_ENABLED` remains disabled until a
separate controlled video-publication scenario is approved and recorded. Production publication
also remains subject to TikTok application review and the platform restrictions returned by the
official Content Posting API.
