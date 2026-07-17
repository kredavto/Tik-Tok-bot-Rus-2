# User Guide

User-facing errors must follow [Error Codes and Exception Handling](error-handling.md).

## Start

1. Open the Telegram bot.
2. Send `/start`.
3. Accept the user agreement.
4. Connect TikTok through official OAuth 2.0.

## Upload Video

1. Tap `📤 Загрузить видео`.
2. Send MP4, MOV, or WEBM.
3. Enter a description.
4. Enter hashtags.
5. Confirm publication.

The bot validates and prepares the video, then sends it to TikTok only through the official Content Posting API.

## Tariffs

- FREE: 2 videos per day.
- PRO: 5 videos per day.
- BUSINESS: 10 videos per day.

Paid plans purchased in the bot are invoiced in Telegram Stars and activate only after Telegram
confirms `successful_payment`. Use `/paysupport` for payment support without sending passwords,
one-time codes, or card details.

Use `/terms` at any time to review the user agreement accepted during registration.

## TikTok Disconnect

Open settings and tap `Отключить TikTok`. Stored OAuth tokens are deleted.

## Errors

The bot shows a short user-safe message. Internal details, tokens, and provider secrets are never shown.
