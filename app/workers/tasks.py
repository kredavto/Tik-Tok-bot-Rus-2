import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from aiogram import Bot
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from sqlalchemy import select

from app.bot.messages import text as bot_text
from app.core.config import settings
from app.core.redis import get_redis, upload_job_lock, user_limit_lock
from app.core.upload_status import UploadStatus
from app.db.models import AdminAction, UploadJob, UploadJobEvent, User, WebhookEvent
from app.db.session import (
    consume_daily_upload,
    get_primary_tiktok_account,
    session_scope,
    transition_upload_job,
    upsert_tiktok_account,
)
from app.security.crypto import decrypt_secret
from app.services.tiktok import TikTokApiError, TikTokClient, TikTokPublishingDisabled, token_is_expired
from app.services.video import cleanup_temp_file, inspect_video, prepare_video_for_tiktok

redis_broker = RedisBroker(url=settings.redis_url)
dramatiq.set_broker(redis_broker)

logger = logging.getLogger(__name__)


@dramatiq.actor(max_retries=3)
def process_upload(upload_id: str, user_id: str) -> None:
    asyncio.run(_process_upload(upload_id, user_id))


@dramatiq.actor(max_retries=1)
def cleanup_retention() -> None:
    asyncio.run(_cleanup_retention())


async def _process_upload(upload_id: str, user_id: str) -> None:
    started = time.monotonic()
    async with upload_job_lock(upload_id) as acquired:
        if not acquired:
            logger.info("Upload job is already being processed", extra={"upload_id": upload_id})
            return
        await _process_upload_locked(upload_id, user_id, started)


async def _process_upload_locked(upload_id: str, user_id: str, started: float) -> None:
    redis = get_redis()
    bot = Bot(token=settings.bot_token) if settings.bot_token else None
    telegram_id: int | None = None
    try:
        await redis.setex(f"upload:{upload_id}:status", 86400, UploadStatus.VALIDATING.value)
        async with session_scope() as session:
            upload = await session.get(UploadJob, UUID(upload_id))
            user = await session.get(User, UUID(user_id))
            if not upload or not user or str(upload.user_id) != user_id:
                await redis.setex(f"upload:{upload_id}:status", 86400, UploadStatus.FAILED.value)
                return
            telegram_id = user.telegram_id

            await transition_upload_job(session, upload, UploadStatus.VALIDATING, "Checking video")
            inspection = await inspect_video(upload.local_path)
            if not inspection.is_valid:
                await transition_upload_job(
                    session,
                    upload,
                    UploadStatus.FAILED,
                    inspection.error or "Invalid video format.",
                )
                await redis.setex(f"upload:{upload_id}:status", 86400, upload.status)
                await _notify(bot, user.telegram_id, bot_text("publish_error", reason="недопустимый формат"))
                await cleanup_temp_file(upload.local_path)
                return

            account = await get_primary_tiktok_account(session, upload.user_id)
            if not account:
                await transition_upload_job(
                    session,
                    upload,
                    UploadStatus.FAILED,
                    "TikTok account is not connected.",
                )
                await redis.setex(f"upload:{upload_id}:status", 86400, upload.status)
                await _notify(bot, user.telegram_id, bot_text("tiktok_not_connected"))
                return

            await transition_upload_job(session, upload, UploadStatus.PREPARING, "Preparing video")
            prepared_path = await prepare_video_for_tiktok(upload.local_path)
            await transition_upload_job(session, upload, UploadStatus.QUEUED, "Ready to publish")
            await redis.setex(f"upload:{upload_id}:status", 86400, upload.status)
            access_token = decrypt_secret(account.access_token_encrypted)
            if token_is_expired(account.token_expires_at) and account.refresh_token_encrypted:
                refreshed = await TikTokClient().refresh_access_token(
                    decrypt_secret(account.refresh_token_encrypted)
                )
                await upsert_tiktok_account(
                    session=session,
                    user_id=upload.user_id,
                    open_id=refreshed.open_id,
                    display_name=account.display_name,
                    access_token=refreshed.access_token,
                    refresh_token=refreshed.refresh_token,
                    expires_in=refreshed.expires_in,
                    scopes=refreshed.scope or account.scopes,
                )
                access_token = refreshed.access_token

            result = await TikTokClient(access_token).publish_video(
                Path(prepared_path),
                upload.caption or "Tik_Tok_Loader",
            )
            await transition_upload_job(session, upload, UploadStatus.UPLOADING, "TikTok accepted upload")
            async with user_limit_lock(user_id):
                allowed, used, limit = await consume_daily_upload(session, user)
                if not allowed:
                    await transition_upload_job(
                        session,
                        upload,
                        UploadStatus.FAILED,
                        f"Daily limit exceeded after TikTok acceptance: {used}/{limit}",
                    )
                    await redis.setex(f"upload:{upload_id}:status", 86400, upload.status)
                    await _notify(bot, user.telegram_id, bot_text("limit_exceeded", used=used, limit=limit))
                    return
            upload.tiktok_publish_id = result.publish_id
            await transition_upload_job(session, upload, UploadStatus.PROCESSING, "TikTok is processing publication")
            await redis.setex(f"upload:{upload_id}:status", 86400, upload.status)
            await _notify(bot, user.telegram_id, bot_text("publish_success"))
            await cleanup_temp_file(upload.local_path)
    except TikTokPublishingDisabled:
        await _mark_upload_failed(upload_id, "TikTok publishing is disabled until official API approval.")
        await redis.setex(f"upload:{upload_id}:status", 86400, UploadStatus.FAILED.value)
        if telegram_id:
            await _notify(bot, telegram_id, bot_text("publish_error", reason="официальный API еще не включен"))
    except TikTokApiError as exc:
        await _mark_upload_failed(upload_id, f"TikTok API error: {exc.code}")
        await redis.setex(f"upload:{upload_id}:status", 86400, UploadStatus.FAILED.value)
        if telegram_id:
            await _notify(
                bot,
                telegram_id,
                bot_text("publish_error", reason="TikTok вернул ограничение или ошибку авторизации"),
            )
        logger.warning("TikTok API rejected upload", extra={"upload_id": upload_id, "code": exc.code})
    except Exception:
        logger.exception("Upload processing failed", extra={"upload_id": upload_id})
        await redis.setex(f"upload:{upload_id}:status", 86400, UploadStatus.FAILED.value)
        raise
    finally:
        logger.info(
            "Upload processing finished",
            extra={"upload_id": upload_id, "duration_ms": round((time.monotonic() - started) * 1000, 2)},
        )
        await redis.aclose()
        if bot:
            await bot.session.close()


async def _mark_upload_failed(upload_id: str, error_message: str) -> None:
    async with session_scope() as session:
        upload = await session.get(UploadJob, UUID(upload_id))
        if upload:
            await transition_upload_job(session, upload, UploadStatus.FAILED, error_message)


async def _notify(bot: Bot | None, telegram_id: int, text: str) -> None:
    if bot:
        await bot.send_message(telegram_id, text)


async def _cleanup_retention() -> None:
    now = datetime.now(UTC)
    video_cutoff = now - timedelta(hours=settings.video_retention_hours)
    log_cutoff = now - timedelta(days=settings.log_retention_days)
    audit_cutoff = now - timedelta(days=settings.audit_log_retention_days)
    backup_cutoff = now - timedelta(days=settings.backup_retention_days)

    async with session_scope() as session:
        terminal_jobs = (
            await session.scalars(
                select(UploadJob).where(
                    UploadJob.created_at < video_cutoff,
                    UploadJob.status.in_(
                        [
                            UploadStatus.FAILED.value,
                            UploadStatus.CANCELLED.value,
                            UploadStatus.PUBLISHED.value,
                        ]
                    ),
                )
            )
        ).all()
        for job in terminal_jobs:
            await cleanup_temp_file(job.local_path)

        old_webhooks = (
            await session.scalars(select(WebhookEvent).where(WebhookEvent.created_at < log_cutoff))
        ).all()
        for event in old_webhooks:
            await session.delete(event)

        old_upload_events = (
            await session.scalars(select(UploadJobEvent).where(UploadJobEvent.created_at < log_cutoff))
        ).all()
        for event in old_upload_events:
            await session.delete(event)

        old_admin_actions = (
            await session.scalars(select(AdminAction).where(AdminAction.created_at < audit_cutoff))
        ).all()
        for action in old_admin_actions:
            await session.delete(action)

    backup_dir = Path(settings.backup_dir)
    if backup_dir.exists():
        for backup in backup_dir.glob("*"):
            if backup.is_file():
                modified_at = datetime.fromtimestamp(backup.stat().st_mtime, tz=UTC)
                if modified_at < backup_cutoff:
                    backup.unlink()
