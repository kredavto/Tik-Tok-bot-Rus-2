# TikTok Sandbox Direct Post evidence

- Date: 2026-07-21 (Europe/Moscow)
- Environment: production-hosted release `0.2.0` with TikTok Sandbox credentials
- Transfer method: official Content Posting API `FILE_UPLOAD`

## Scope

The controlled run covered Telegram video intake, FFprobe validation, creator-info retrieval,
explicit privacy and interaction selection, commercial-content disclosure, final consent, worker
dispatch, provider rejection handling, daily-limit integrity, and publication-gate restoration.
The synthetic test video contained no personal data.

## Results

| Check | Result | Evidence |
| --- | --- | --- |
| Telegram video intake | PASS | A 6-second H.264 MP4 was accepted and stored under an isolated UUID path. |
| Creator Info | PASS | Current account options and duration limits came from the official API. |
| Explicit consent | PASS | The user selected `SELF_ONLY`, disabled interactions and commercial disclosure, reviewed the preview, and confirmed publication. |
| Worker dispatch | PASS | One upload job was created and processed once by the Dramatiq worker. |
| Provider initialization | BLOCKED | TikTok returned `unaudited_client_can_only_post_to_private_accounts` before accepting media. |
| Daily quota | PASS | Usage remained `0`; a provider-rejected post did not consume quota. |
| Automatic retry policy | PASS | The platform restriction was not retried automatically. |
| Publication gate | PASS | `TIKTOK_PUBLISH_ENABLED` was restored to `false` immediately after diagnosis. |

## Root cause and remediation

The selected post visibility was `SELF_ONLY`, but the connected target creator account itself was
public. TikTok requires target accounts used by unaudited API clients to be private at posting
time. Set the Sandbox target account to private, query Creator Info again, and repeat the controlled
test. Public-account posting remains blocked until TikTok approves the Direct Post audit.

The application now exposes `TIKTOK_APP_AUDITED`, stops an unaudited flow before confirmation when
Creator Info identifies a public account, returns an actionable user message for the provider code,
and cleans temporary media after any pre-acceptance rejection.

## Security boundary

This evidence excludes the TikTok username, open ID, publish identifiers, OAuth credentials,
Telegram identifiers, provider log IDs, and raw request or callback URLs. No unofficial API,
browser automation, regional bypass, or automatic retry was used.
