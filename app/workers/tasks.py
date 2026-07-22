import asyncio
from collections.abc import Coroutine
import logging
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, TypeVar
from uuid import UUID

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNotFound
import aiohttp
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from redis.asyncio import Redis
from sqlalchemy import and_, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.messages import text as bot_text
from app.core.config import settings
from app.core.redis import (
    get_redis,
    payment_notification_lock,
    subscription_notification_lock,
    upload_job_lock,
    user_limit_lock,
)
from app.core.upload_status import UploadStatus
from app.db.models import (
    AdminAction,
    Payment,
    Subscription,
    TikTokAccount,
    UploadJob,
    UploadJobEvent,
    User,
    WebhookEvent,
)
from app.db.session import (
    can_upload_today,
    expire_due_paid_subscriptions,
    list_tiktok_accounts_due_for_refresh,
    mark_subscription_expiration_notified,
    record_accepted_upload,
    session_scope,
    transition_upload_job,
    upsert_tiktok_account,
)
from app.security.crypto import decrypt_secret
from app.services.configuration import get_int_setting
from app.services.tiktok import (
    TikTokApiError,
    TikTokClient,
    TikTokPostOptions,
    TikTokPublishingDisabled,
    token_is_expired,
)
from app.services.video import cleanup_temp_file, inspect_video, prepare_video_for_tiktok

redis_broker = RedisBroker(url=settings.redis_url)
dramatiq.set_broker(redis_broker)

logger = logging.getLogger(__name__)

PERMANENT_TELEGRAM_DELIVERY_ERRORS = (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
)

T = TypeVar("T")
_worker_loop: asyncio.AbstractEventLoop | None = None
_worker_loop_thread: threading.Thread | None = None
_worker_loop_lock = threading.Lock()


def _run_worker_coroutine(coroutine: Coroutine[Any, Any, T]) -> T:
    loop = _get_worker_event_loop()
    return asyncio.run_coroutine_threadsafe(coroutine, loop).result()


def _get_worker_event_loop() -> asyncio.AbstractEventLoop:
    global _worker_loop, _worker_loop_thread
    with _worker_loop_lock:
        if (
            _worker_loop is None
            or _worker_loop_thread is None
            or not _worker_loop_thread.is_alive()
        ):
            _worker_loop = asyncio.new_event_loop()
            _worker_loop_thread = threading.Thread(
                target=_worker_loop.run_forever,
                name="dramatiq-async-runtime",
                daemon=True,
            )
            _worker_loop_thread.start()
        return _worker_loop


@dramatiq.actor(max_retries=0)
def process_upload(upload_id: str, user_id: str) -> None:
    _run_worker_coroutine(_process_upload(upload_id, user_id))


@dramatiq.actor(max_retries=1)
def cleanup_retention() -> None:
    _run_worker_coroutine(_cleanup_retention())


@dramatiq.actor(max_retries=2)
def check_publish_status(upload_id: str, user_id: str, attempt: int = 0) -> None:
    _run_worker_coroutine(_check_publish_status(upload_id, user_id, attempt))


@dramatiq.actor(max_retries=3)
def notify_upload_status(telegram_id: int, status: str) -> None:
    _run_worker_coroutine(_notify_upload_status(telegram_id, status))


@dramatiq.actor(max_retries=2)
def expire_subscriptions() -> None:
    _run_worker_coroutine(_expire_subscriptions())


@dramatiq.actor(max_retries=0)
def refresh_expiring_tiktok_tokens() -> None:
    _run_worker_coroutine(_refresh_expiring_tiktok_tokens())


@dramatiq.actor(max_retries=1)
def reconcile_processing_uploads() -> None:
    _run_worker_coroutine(_reconcile_processing_uploads())


@dramatiq.actor(max_retries=3)
def notify_subscription_expired(subscription_id: str, telegram_id: int) -> None:
    _run_worker_coroutine(_notify_subscription_expired(subscription_id, telegram_id))


@dramatiq.actor(max_retries=3)
def notify_payment_success(event_id: str) -> None:
    _run_worker_coroutine(_notify_payment_success(event_id))


@dramatiq.actor(max_retries=1)
def dispatch_payment_notifications() -> None:
    _run_worker_coroutine(_dispatch_payment_notifications())


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
    accepted_by_tiktok = False
    local_path: str | None = None
    try:
        await redis.setex(f"upload:{upload_id}:status", 86400, UploadStatus.VALIDATING.value)
        async with session_scope() as session:
            upload = await session.get(UploadJob, UUID(upload_id))
            user = await session.get(User, UUID(user_id))
            if not upload or not user or str(upload.user_id) != user_id:
                await redis.setex(f"upload:{upload_id}:status", 86400, UploadStatus.FAILED.value)
                return
            local_path = upload.local_path
            if upload.status != UploadStatus.NEW.value:
                logger.info(
                    "Upload job is not eligible for initial processing",
                    extra={"upload_id": upload_id, "status": upload.status},
                )
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
                await _notify(
                    bot, user.telegram_id, bot_text("publish_error", reason="недопустимый формат")
                )
                await cleanup_temp_file(upload.local_path)
                return

            account = (
                await session.get(TikTokAccount, upload.tiktok_account_id)
                if upload.tiktok_account_id
                else None
            )
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

            async with user_limit_lock(user_id):
                allowed, used, limit = await can_upload_today(session, user)
                if not allowed:
                    await transition_upload_job(
                        session,
                        upload,
                        UploadStatus.FAILED,
                        f"Daily limit exceeded before TikTok acceptance: {used}/{limit}",
                    )
                    await redis.setex(f"upload:{upload_id}:status", 86400, upload.status)
                    await _notify(
                        bot, user.telegram_id, bot_text("limit_exceeded", used=used, limit=limit)
                    )
                    return

                client = TikTokClient(access_token)
                creator = await client.query_creator_info()
                if (
                    creator.max_video_post_duration_sec
                    and inspection.duration_sec is not None
                    and inspection.duration_sec > creator.max_video_post_duration_sec
                ):
                    await transition_upload_job(
                        session,
                        upload,
                        UploadStatus.FAILED,
                        "Video duration exceeds the current TikTok creator limit.",
                    )
                    await _notify(
                        bot,
                        user.telegram_id,
                        bot_text(
                            "publish_error", reason="ролик превышает лимит длительности TikTok"
                        ),
                    )
                    return
                if upload.privacy_level not in creator.privacy_level_options:
                    await transition_upload_job(
                        session,
                        upload,
                        UploadStatus.FAILED,
                        "TikTok privacy options changed before publication.",
                    )
                    await _notify(
                        bot,
                        user.telegram_id,
                        bot_text(
                            "publish_error", reason="настройки приватности аккаунта изменились"
                        ),
                    )
                    return

                if not settings.tiktok_app_audited and upload.privacy_level != "SELF_ONLY":
                    await transition_upload_job(
                        session,
                        upload,
                        UploadStatus.FAILED,
                        "Unaudited TikTok clients require SELF_ONLY visibility.",
                    )
                    await _notify(
                        bot,
                        user.telegram_id,
                        bot_text(
                            "publish_error",
                            reason="до завершения аудита выберите видимость «Только я»",
                        ),
                    )
                    return

                await transition_upload_job(
                    session, upload, UploadStatus.UPLOADING, "Uploading to TikTok"
                )
                result = await client.publish_video(
                    Path(prepared_path),
                    upload.caption or "Tik_Tok_Loader",
                    TikTokPostOptions(
                        privacy_level=upload.privacy_level,
                        disable_comment=upload.disable_comment or creator.comment_disabled,
                        disable_duet=upload.disable_duet or creator.duet_disabled,
                        disable_stitch=upload.disable_stitch or creator.stitch_disabled,
                        brand_content_toggle=upload.brand_content_toggle,
                        brand_organic_toggle=upload.brand_organic_toggle,
                    ),
                )
                await _persist_tiktok_acceptance(session, upload, user, result.publish_id)
                accepted_by_tiktok = True

            await _finish_accepted_upload(
                redis=redis,
                bot=bot,
                upload_id=upload_id,
                user_id=user_id,
                telegram_id=user.telegram_id,
                local_path=upload.local_path,
            )
    except TikTokPublishingDisabled:
        await _mark_upload_failed(
            upload_id, "TikTok publishing is disabled until official API approval."
        )
        await redis.setex(f"upload:{upload_id}:status", 86400, UploadStatus.FAILED.value)
        if telegram_id:
            await _notify(
                bot, telegram_id, bot_text("publish_error", reason="официальный API еще не включен")
            )
    except TikTokApiError as exc:
        await _mark_upload_failed(upload_id, f"TikTok API error: {exc.code}")
        await redis.setex(f"upload:{upload_id}:status", 86400, UploadStatus.FAILED.value)
        if telegram_id:
            await _notify(
                bot,
                telegram_id,
                bot_text("publish_error", reason=_tiktok_upload_error_reason(exc.code)),
            )
        logger.warning(
            "TikTok API rejected upload", extra={"upload_id": upload_id, "code": exc.code}
        )
    except Exception:
        logger.exception("Upload processing failed", extra={"upload_id": upload_id})
        if accepted_by_tiktok:
            await _set_upload_cache_status(redis, upload_id, UploadStatus.PROCESSING)
        else:
            await _mark_upload_failed(upload_id, "Temporary upload processing error.")
            await _set_upload_cache_status(redis, upload_id, UploadStatus.FAILED)
            if telegram_id:
                await _notify(
                    bot,
                    telegram_id,
                    bot_text("publish_error", reason="временная ошибка обработки"),
                )
    finally:
        logger.info(
            "Upload processing finished",
            extra={
                "upload_id": upload_id,
                "duration_ms": round((time.monotonic() - started) * 1000, 2),
            },
        )
        await redis.aclose()
        await _cleanup_unaccepted_upload(local_path, accepted_by_tiktok)
        if bot:
            await bot.session.close()


def _tiktok_upload_error_reason(code: str) -> str:
    if code == "unaudited_client_can_only_post_to_private_accounts":
        return "для тестового режима TikTok-аккаунт должен быть приватным"
    if code in {"access_token_invalid", "scope_not_authorized"}:
        return "нужно заново подключить TikTok и проверить разрешение video.publish"
    return "TikTok вернул ограничение или ошибку авторизации"


def _tiktok_processing_error_reason(reason: str) -> str:
    if reason == "internal":
        return "временная ошибка на стороне TikTok; повторите публикацию позже"
    return "TikTok отклонил публикацию"


async def _cleanup_unaccepted_upload(local_path: str | None, accepted: bool) -> None:
    if local_path and not accepted:
        await cleanup_temp_file(local_path)


async def _persist_tiktok_acceptance(
    session: AsyncSession,
    upload: UploadJob,
    user: User,
    publish_id: str,
) -> None:
    await record_accepted_upload(session, user)
    upload.tiktok_publish_id = publish_id
    await transition_upload_job(
        session,
        upload,
        UploadStatus.PROCESSING,
        "TikTok is processing publication",
    )
    # TikTok has already accepted the upload. Persist that fact before any local
    # notification, cache, queue, or file-cleanup operation can fail.
    await session.commit()


async def _reconcile_processing_uploads() -> int:
    async with session_scope() as session:
        jobs = (
            await session.execute(
                select(UploadJob.id, UploadJob.user_id)
                .where(
                    UploadJob.status == UploadStatus.PROCESSING.value,
                    UploadJob.tiktok_publish_id.is_not(None),
                )
                .order_by(UploadJob.updated_at)
                .limit(settings.maintenance_batch_size)
            )
        ).all()

    for upload_id, user_id in jobs:
        check_publish_status.send(str(upload_id), str(user_id), 0)
    return len(jobs)


async def _finish_accepted_upload(
    *,
    redis: Redis,
    bot: Bot | None,
    upload_id: str,
    user_id: str,
    telegram_id: int,
    local_path: str,
) -> None:
    try:
        check_publish_status.send_with_options(
            args=(upload_id, user_id, 0),
            delay=30_000,
        )
    except Exception:
        logger.exception(
            "Could not enqueue TikTok status check",
            extra={"upload_id": upload_id},
        )

    await _set_upload_cache_status(redis, upload_id, UploadStatus.PROCESSING)
    await _notify(bot, telegram_id, bot_text("publish_success"))
    try:
        await cleanup_temp_file(local_path)
    except Exception:
        logger.exception(
            "Could not remove accepted upload file",
            extra={"upload_id": upload_id},
        )


async def _set_upload_cache_status(redis: Redis, upload_id: str, status: UploadStatus) -> None:
    try:
        await redis.setex(f"upload:{upload_id}:status", 86400, status.value)
    except Exception:
        logger.exception(
            "Could not update cached upload status",
            extra={"upload_id": upload_id, "status": status.value},
        )


async def _mark_upload_failed(upload_id: str, error_message: str) -> None:
    async with session_scope() as session:
        upload = await session.get(UploadJob, UUID(upload_id))
        if upload and upload.status not in {
            UploadStatus.PUBLISHED.value,
            UploadStatus.FAILED.value,
            UploadStatus.CANCELLED.value,
        }:
            await transition_upload_job(session, upload, UploadStatus.FAILED, error_message)


async def _notify(bot: Bot | None, telegram_id: int, text: str) -> None:
    if bot:
        try:
            await bot.send_message(telegram_id, text)
        except Exception:
            logger.exception(
                "Telegram notification failed",
                extra={"telegram_id": telegram_id},
            )


async def _notify_upload_status(telegram_id: int, status: str) -> None:
    if not settings.bot_token:
        return
    bot = Bot(token=settings.bot_token)
    try:
        if status == UploadStatus.PUBLISHED.value:
            message = bot_text("publish_complete")
        elif status == "TIKTOK_REVOKED":
            message = bot_text("tiktok_revoked")
        elif status == "TIKTOK_REAUTH_REQUIRED":
            message = bot_text("tiktok_reauth_required")
        else:
            message = bot_text("publish_error", reason="TikTok отклонил публикацию")
        await bot.send_message(telegram_id, message)
    finally:
        await bot.session.close()


async def _expire_subscriptions() -> None:
    async with session_scope() as session:
        notices = await expire_due_paid_subscriptions(
            session,
            batch_size=settings.maintenance_batch_size,
        )

    for notice in notices:
        notify_subscription_expired.send(str(notice.subscription_id), notice.telegram_id)
    logger.info("Subscription expiration sweep completed", extra={"notice_count": len(notices)})


async def _notify_subscription_expired(subscription_id: str, telegram_id: int) -> None:
    async with subscription_notification_lock(subscription_id) as acquired:
        if not acquired:
            return

        subscription_uuid = UUID(subscription_id)
        async with session_scope() as session:
            subscription = await session.get(Subscription, subscription_uuid)
            if (
                subscription is None
                or subscription.status != "expired"
                or subscription.expiration_notified_at is not None
            ):
                return

        if not settings.bot_token:
            logger.warning(
                "Subscription expiration notification deferred because bot token is unavailable",
                extra={"subscription_id": subscription_id},
            )
            return

        bot = Bot(token=settings.bot_token)
        try:
            await bot.send_message(telegram_id, bot_text("subscription_expired"))
        finally:
            await bot.session.close()

        async with session_scope() as session:
            await mark_subscription_expiration_notified(session, subscription_uuid)


async def _dispatch_payment_notifications() -> None:
    async with session_scope() as session:
        event_ids = list(
            await session.scalars(
                select(WebhookEvent.id)
                .where(
                    WebhookEvent.provider == "internal",
                    WebhookEvent.event_type == "payment_success_notification",
                    WebhookEvent.status == "pending",
                )
                .order_by(WebhookEvent.created_at)
                .limit(settings.maintenance_batch_size)
            )
        )
    for event_id in event_ids:
        notify_payment_success.send(str(event_id))


async def _notify_payment_success(event_id: str) -> None:
    async with payment_notification_lock(event_id) as acquired:
        if not acquired:
            return

        event_uuid = UUID(event_id)
        async with session_scope() as session:
            event = await session.get(WebhookEvent, event_uuid)
            if (
                event is None
                or event.provider != "internal"
                or event.event_type != "payment_success_notification"
                or event.status != "pending"
            ):
                return
            try:
                payment_id = UUID(str(event.payload["payment_id"]))
            except (KeyError, TypeError, ValueError):
                event.status = "rejected"
                event.processed_at = datetime.now(UTC)
                return
            payment = await session.get(Payment, payment_id)
            user = await session.get(User, payment.user_id) if payment else None
            if payment is None or payment.status != "paid" or user is None:
                event.status = "rejected"
                event.processed_at = datetime.now(UTC)
                return
            telegram_id = user.telegram_id
            plan_id = payment.plan_id

        if not settings.bot_token:
            raise RuntimeError("Telegram bot token is unavailable")
        bot = Bot(token=settings.bot_token)
        try:
            await bot.send_message(
                telegram_id,
                bot_text("payment_success", plan=plan_id.upper()),
            )
        except PERMANENT_TELEGRAM_DELIVERY_ERRORS as exc:
            logger.warning(
                "Payment notification permanently rejected by Telegram",
                extra={"event_id": event_id, "error_type": type(exc).__name__},
            )
            await _finish_payment_notification(
                event_uuid,
                status="rejected",
                delivery_error=type(exc).__name__,
            )
            return
        finally:
            await bot.session.close()

        await _finish_payment_notification(event_uuid, status="processed")


async def _finish_payment_notification(
    event_id: UUID,
    *,
    status: str,
    delivery_error: str | None = None,
) -> None:
    async with session_scope() as session:
        event = await session.get(WebhookEvent, event_id)
        if event and event.status == "pending":
            event.status = status
            event.processed_at = datetime.now(UTC)
            if delivery_error:
                event.payload = {**event.payload, "delivery_error": delivery_error}


async def _refresh_expiring_tiktok_tokens() -> None:
    due_before = datetime.now(UTC) + timedelta(seconds=settings.token_refresh_lead_seconds)
    async with session_scope() as session:
        account_ids = await list_tiktok_accounts_due_for_refresh(
            session,
            due_before=due_before,
            batch_size=settings.maintenance_batch_size,
        )

    refreshed = 0
    blocked = 0
    for account_id in account_ids:
        result = await _refresh_tiktok_account(account_id, due_before)
        refreshed += result == "refreshed"
        blocked += result == "blocked"
    logger.info(
        "TikTok token refresh sweep completed",
        extra={"candidate_count": len(account_ids), "refreshed": refreshed, "blocked": blocked},
    )


async def _refresh_tiktok_account(account_id: UUID, due_before: datetime) -> str:
    telegram_id: int | None = None
    async with session_scope() as session:
        account = await session.scalar(
            select(TikTokAccount).where(TikTokAccount.id == account_id).with_for_update()
        )
        if (
            account is None
            or account.refresh_blocked_at is not None
            or account.token_expires_at is None
            or account.token_expires_at > due_before
        ):
            return "skipped"

        user = await session.get(User, account.user_id)
        telegram_id = user.telegram_id if user else None
        if not account.refresh_token_encrypted:
            account.refresh_blocked_at = datetime.now(UTC)
            account.refresh_error_code = "missing_refresh_token"
            result = "blocked"
        else:
            try:
                refreshed_token = await TikTokClient().refresh_access_token(
                    decrypt_secret(account.refresh_token_encrypted)
                )
            except TikTokApiError as exc:
                if exc.status_code == 429 or (exc.status_code and exc.status_code >= 500):
                    logger.warning(
                        "Temporary TikTok token refresh error",
                        extra={"account_id": str(account_id), "code": exc.code},
                    )
                    return "temporary_error"
                account.refresh_blocked_at = datetime.now(UTC)
                account.refresh_error_code = exc.code[:255]
                result = "blocked"
            except (aiohttp.ClientError, TimeoutError, OSError):
                logger.warning(
                    "Temporary network error during TikTok token refresh",
                    extra={"account_id": str(account_id)},
                    exc_info=True,
                )
                return "temporary_error"
            else:
                await upsert_tiktok_account(
                    session=session,
                    user_id=account.user_id,
                    open_id=refreshed_token.open_id,
                    display_name=account.display_name,
                    access_token=refreshed_token.access_token,
                    refresh_token=refreshed_token.refresh_token,
                    expires_in=refreshed_token.expires_in,
                    scopes=refreshed_token.scope or account.scopes,
                )
                result = "refreshed"

    if result == "blocked" and telegram_id is not None:
        notify_upload_status.send(telegram_id, "TIKTOK_REAUTH_REQUIRED")
    return result


async def _check_publish_status(upload_id: str, user_id: str, attempt: int) -> None:
    bot = Bot(token=settings.bot_token) if settings.bot_token else None
    try:
        async with upload_job_lock(upload_id) as acquired:
            if not acquired:
                return
            async with session_scope() as session:
                upload = await session.get(UploadJob, UUID(upload_id))
                user = await session.get(User, UUID(user_id))
                if (
                    not upload
                    or not user
                    or upload.status != UploadStatus.PROCESSING.value
                    or not upload.tiktok_publish_id
                    or not upload.tiktok_account_id
                ):
                    return
                account = await session.get(TikTokAccount, upload.tiktok_account_id)
                if not account:
                    await transition_upload_job(
                        session,
                        upload,
                        UploadStatus.FAILED,
                        "TikTok account was disconnected while publication was processing.",
                    )
                    return

                result = await TikTokClient(
                    decrypt_secret(account.access_token_encrypted)
                ).get_post_status(upload.tiktok_publish_id)
                if result.status == "PUBLISH_COMPLETE":
                    await transition_upload_job(
                        session,
                        upload,
                        UploadStatus.PUBLISHED,
                        "TikTok publication completed",
                    )
                    await _notify(bot, user.telegram_id, bot_text("publish_complete"))
                    return
                if result.status == "FAILED":
                    reason = result.fail_reason or "unknown"
                    await transition_upload_job(
                        session,
                        upload,
                        UploadStatus.FAILED,
                        f"TikTok processing failed: {reason}",
                    )
                    await _notify(
                        bot,
                        user.telegram_id,
                        bot_text(
                            "publish_error",
                            reason=_tiktok_processing_error_reason(reason),
                        ),
                    )
                    return

        if attempt < 11:
            delay_seconds = min(300, 30 * (2 ** min(attempt, 4)))
            check_publish_status.send_with_options(
                args=(upload_id, user_id, attempt + 1),
                delay=delay_seconds * 1000,
            )
    finally:
        if bot:
            await bot.session.close()


async def _cleanup_retention() -> None:
    now = datetime.now(UTC)
    async with session_scope() as session:
        video_retention_hours = await get_int_setting(
            session, "video_retention_hours", settings.video_retention_hours
        )
        log_retention_days = await get_int_setting(
            session, "log_retention_days", settings.log_retention_days
        )
        audit_retention_days = await get_int_setting(
            session, "audit_log_retention_days", settings.audit_log_retention_days
        )
        backup_retention_days = await get_int_setting(
            session, "backup_retention_days", settings.backup_retention_days
        )
        video_cutoff = now - timedelta(hours=video_retention_hours)
        log_cutoff = now - timedelta(days=log_retention_days)
        audit_cutoff = now - timedelta(days=audit_retention_days)

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

        pending_payment_notification = and_(
            WebhookEvent.provider == "internal",
            WebhookEvent.event_type == "payment_success_notification",
            WebhookEvent.status == "pending",
        )
        old_webhooks = (
            await session.scalars(
                select(WebhookEvent).where(
                    WebhookEvent.created_at < log_cutoff,
                    not_(pending_payment_notification),
                )
            )
        ).all()
        for webhook_event in old_webhooks:
            await session.delete(webhook_event)

        old_upload_events = (
            await session.scalars(
                select(UploadJobEvent).where(UploadJobEvent.created_at < log_cutoff)
            )
        ).all()
        for upload_event in old_upload_events:
            await session.delete(upload_event)

        old_admin_actions = (
            await session.scalars(select(AdminAction).where(AdminAction.created_at < audit_cutoff))
        ).all()
        for action in old_admin_actions:
            await session.delete(action)

    backup_cutoff = now - timedelta(days=backup_retention_days)
    backup_dir = Path(settings.backup_dir)
    if backup_dir.exists():
        for backup in backup_dir.glob("*"):
            if backup.is_file():
                modified_at = datetime.fromtimestamp(backup.stat().st_mtime, tz=UTC)
                if modified_at < backup_cutoff:
                    backup.unlink()
