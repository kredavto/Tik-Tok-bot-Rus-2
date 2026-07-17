# Video Publication Lifecycle

Upload job storage rules are documented in [Upload Jobs Entity](upload-jobs-entity.md).

End-to-end publication sequence is documented in [Sequence Flows](sequence-flows.md).

## Statuses

- `NEW`
- `VALIDATING`
- `PREPARING`
- `QUEUED`
- `UPLOADING`
- `PROCESSING`
- `PUBLISHED`
- `FAILED`
- `CANCELLED`

## Flow

1. User starts upload.
2. Bot checks TikTok connection and daily limit.
3. Bot receives the video.
4. Worker validates container, signature, size, duration, and FFprobe metadata.
5. Worker transcodes WEBM to MP4 when needed.
6. User description and hashtags are stored with the upload job.
7. Worker sends the video through the official TikTok API.
8. Current status is stored on `upload_jobs`.
9. Each lifecycle transition is recorded in `upload_job_events`.
10. User receives a Telegram notification.

## Error Rules

- No daily limit is consumed when validation or preparation fails.
- Daily limit is consumed only after official TikTok API acceptance.
- Authorization and platform restriction errors are not retried automatically.
- Temporary failures can be retried by the queue system.
