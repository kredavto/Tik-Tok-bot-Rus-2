import hmac
import json
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import UUID, uuid4

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse, Response
from pydantic import ValidationError
from sqlalchemy import func, select, text

from app.api.admin import router as admin_router
from app.bot.application import create_dispatcher
from app.bot.messages import text as bot_text
from app.core.config import settings, validate_runtime_settings
from app.core.logging import configure_logging
from app.core.redis import get_redis, oauth_state_exists, pop_oauth_state
from app.core.upload_status import UploadStatus
from app.db.models import Payment, Subscription, TikTokAccount, UploadJob, User, WebhookEvent
from app.db.session import (
    engine,
    init_db,
    mark_payment_paid,
    record_webhook_event,
    session_scope,
    transition_upload_job,
    upsert_tiktok_account,
)
from app.services.robokassa import validate_result_signature
from app.services.tiktok import (
    TikTokApiError,
    TikTokClient,
    build_oauth_url,
    validate_webhook_signature,
)
from app.workers.tasks import notify_upload_status

configure_logging()
logger = logging.getLogger(__name__)

telegram_bot: Bot | None = None
telegram_dispatcher: Dispatcher | None = None


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global telegram_bot, telegram_dispatcher
    validate_runtime_settings()
    await init_db()
    if settings.telegram_delivery_mode == "webhook":
        telegram_bot = Bot(token=settings.bot_token)
        telegram_dispatcher = create_dispatcher()
    try:
        yield
    finally:
        if telegram_dispatcher:
            await telegram_dispatcher.storage.close()
        if telegram_bot:
            await telegram_bot.session.close()
        telegram_dispatcher = None
        telegram_bot = None


app = FastAPI(title="Tik_Tok_Loader API", lifespan=lifespan)
app.include_router(admin_router)

METRICS = {
    "http_requests_total": 0,
    "robokassa_results_total": 0,
    "tiktok_oauth_callbacks_total": 0,
    "tiktok_webhooks_total": 0,
}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "request_id": getattr(request.state, "request_id", None),
                "correlation_id": getattr(request.state, "correlation_id", None),
            }
        },
    )


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    correlation_id = request.headers.get("X-Correlation-ID", request_id)
    request.state.request_id = request_id
    request.state.correlation_id = correlation_id
    started = time.monotonic()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Response-Time-ms"] = str(round((time.monotonic() - started) * 1000, 2))
    METRICS["http_requests_total"] += 1
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path in {"/health", "/ready", "/metrics"}:
        return await call_next(request)

    client = request.client.host if request.client else "unknown"
    bucket = int(time.time() // 60)
    key = f"rate:{client}:{bucket}"
    redis = get_redis()
    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 120)
        if count > settings.rate_limit_per_minute:
            raise HTTPException(status_code=429, detail="Too many requests")
    finally:
        await redis.aclose()
    return await call_next(request)


@app.get("/api/v1/health")
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/ready")
@app.get("/ready")
async def ready() -> dict[str, str]:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("select 1"))
        redis = get_redis()
        try:
            await redis.ping()
        finally:
            await redis.aclose()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Service is not ready") from exc
    return {"status": "ready"}


@app.get("/api/v1/metrics")
@app.get("/metrics")
async def metrics() -> Response:
    dynamic_metrics = await _collect_dynamic_metrics()
    merged = {**METRICS, **dynamic_metrics}
    body = "\n".join(f"tiktok_loader_{key} {value}" for key, value in merged.items()) + "\n"
    return Response(content=body, media_type="text/plain; version=0.0.4")


async def _collect_dynamic_metrics() -> dict[str, int]:
    async with session_scope() as session:
        registrations = await session.scalar(select(func.count(User.id)))
        successful_publications = await session.scalar(
            select(func.count(UploadJob.id)).where(UploadJob.status == UploadStatus.PUBLISHED.value)
        )
        publication_errors = await session.scalar(
            select(func.count(UploadJob.id)).where(UploadJob.status == UploadStatus.FAILED.value)
        )
        payments_paid = await session.scalar(
            select(func.count(Payment.id)).where(Payment.status == "paid")
        )
        queue_size = await session.scalar(
            select(func.count(UploadJob.id)).where(
                UploadJob.status.in_(
                    [
                        UploadStatus.NEW.value,
                        UploadStatus.VALIDATING.value,
                        UploadStatus.PREPARING.value,
                        UploadStatus.QUEUED.value,
                        UploadStatus.UPLOADING.value,
                    ]
                )
            )
        )
        plan_rows = (
            await session.execute(
                select(Subscription.plan_id, func.count(Subscription.id))
                .where(Subscription.status == "active")
                .group_by(Subscription.plan_id)
            )
        ).all()
    plan_counts = {plan_id: count for plan_id, count in plan_rows}
    return {
        "registrations_total": int(registrations or 0),
        "publications_success_total": int(successful_publications or 0),
        "publications_error_total": int(publication_errors or 0),
        "payments_success_total": int(payments_paid or 0),
        "upload_queue_size": int(queue_size or 0),
        "subscriptions_free": int(plan_counts.get("free", 0) or 0),
        "subscriptions_pro": int(plan_counts.get("pro", 0) or 0),
        "subscriptions_business": int(plan_counts.get("business", 0) or 0),
    }


@app.get("/api/v1/oauth/tiktok/start")
@app.get("/oauth/tiktok/start")
async def oauth_tiktok_start(
    state: str = Query(..., min_length=32, max_length=128),
) -> RedirectResponse:
    if not await oauth_state_exists(state):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    return RedirectResponse(build_oauth_url(state))


@app.get("/api/v1/oauth/tiktok/callback")
@app.get("/oauth/tiktok/callback")
@app.get("/tiktok/callback")
async def tiktok_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> dict[str, str]:
    METRICS["tiktok_oauth_callbacks_total"] += 1
    if error:
        raise HTTPException(status_code=400, detail=f"TikTok authorization failed: {error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth code or state")

    user_id = await pop_oauth_state(state)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    client = TikTokClient()
    try:
        token = await client.exchange_code(code)
        user_info = await TikTokClient(token.access_token).get_user_info()
    except TikTokApiError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    telegram_id: int | None = None
    async with session_scope() as session:
        user = await session.get(User, UUID(user_id))
        if user is None:
            raise HTTPException(status_code=400, detail="OAuth user no longer exists")
        telegram_id = user.telegram_id
        await record_webhook_event(
            session,
            provider="tiktok",
            event_type="oauth_callback",
            external_id=token.open_id,
            payload={"scope": token.scope},
            status="processed",
        )
        await upsert_tiktok_account(
            session=session,
            user_id=UUID(user_id),
            open_id=user_info.open_id,
            display_name=user_info.display_name,
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            expires_in=token.expires_in,
            scopes=token.scope,
        )

    if telegram_id and settings.bot_token:
        bot = Bot(token=settings.bot_token)
        try:
            await bot.send_message(telegram_id, bot_text("tiktok_connected"))
        except Exception:
            logger.exception("Could not send TikTok connection notification")
        finally:
            await bot.session.close()

    return {"status": "connected", "message": "TikTok account connected. Return to Telegram bot."}


@app.post(settings.telegram_webhook_path)
@app.post("/webhooks/telegram")
async def telegram_webhook(request: Request) -> dict[str, str]:
    if settings.telegram_delivery_mode != "webhook" or not telegram_bot or not telegram_dispatcher:
        raise HTTPException(status_code=503, detail="Telegram webhook delivery is not enabled")

    token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not hmac.compare_digest(token, settings.telegram_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret")

    payload = await request.json()
    external_id = str(payload.get("update_id", ""))
    if not external_id:
        raise HTTPException(status_code=400, detail="Missing Telegram update_id")

    async with session_scope() as session:
        event = await session.scalar(
            select(WebhookEvent).where(
                WebhookEvent.provider == "telegram",
                WebhookEvent.event_type == "update",
                WebhookEvent.external_id == external_id,
            )
        )
        if event and event.status == "processed":
            return {"status": "ok"}
        if event:
            event.payload = payload
            event.status = "received"
        else:
            event = await record_webhook_event(
                session,
                provider="telegram",
                event_type="update",
                external_id=external_id,
                payload=payload,
                status="received",
            )
        event_id = event.id

    try:
        update = Update.model_validate(payload, context={"bot": telegram_bot})
        await telegram_dispatcher.feed_update(telegram_bot, update)
    except ValidationError as exc:
        await _mark_telegram_event(event_id, "rejected")
        raise HTTPException(status_code=400, detail="Invalid Telegram update") from exc
    except Exception as exc:
        await _mark_telegram_event(event_id, "failed")
        logger.exception("Telegram update processing failed", extra={"update_id": external_id})
        raise HTTPException(status_code=500, detail="Telegram update processing failed") from exc

    await _mark_telegram_event(event_id, "processed")
    return {"status": "ok"}


async def _mark_telegram_event(event_id: UUID, status: str) -> None:
    async with session_scope() as session:
        event = await session.get(WebhookEvent, event_id)
        if event:
            event.status = status
            event.processed_at = datetime.now(UTC) if status == "processed" else None


@app.post("/api/v1/webhooks/tiktok")
@app.post("/webhooks/tiktok")
async def tiktok_webhook(request: Request) -> dict[str, str]:
    METRICS["tiktok_webhooks_total"] += 1
    raw_body = await request.body()
    signature = request.headers.get("TikTok-Signature", "")
    if not validate_webhook_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail="Invalid TikTok webhook signature")

    payload = await request.json()
    if payload.get("client_key") and payload["client_key"] != settings.tiktok_client_key:
        raise HTTPException(status_code=401, detail="Invalid TikTok client key")

    content = payload.get("content") or {}
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Invalid TikTok webhook content") from exc
    if not isinstance(content, dict):
        raise HTTPException(status_code=400, detail="Invalid TikTok webhook content")

    event_type = str(payload.get("event", "unknown"))
    publish_id = str(content.get("publish_id") or payload.get("publish_id") or "")
    external_id = publish_id or ":".join(
        [
            event_type,
            str(payload.get("create_time", "")),
            str(payload.get("user_openid", "")),
        ]
    )
    async with session_scope() as session:
        existing = await session.scalar(
            select(WebhookEvent).where(
                WebhookEvent.provider == "tiktok",
                WebhookEvent.event_type == event_type,
                WebhookEvent.external_id == external_id,
                WebhookEvent.status == "processed",
            )
        )
        if existing:
            return {"status": "ok"}

        event = await record_webhook_event(
            session,
            provider="tiktok",
            event_type=event_type,
            external_id=external_id,
            payload=payload,
            status="received",
        )

        upload = (
            await session.scalar(select(UploadJob).where(UploadJob.tiktok_publish_id == publish_id))
            if publish_id
            else None
        )
        if upload and upload.status == UploadStatus.PROCESSING.value:
            if event_type in {"post.publish.complete", "video.publish.completed"}:
                await transition_upload_job(
                    session,
                    upload,
                    UploadStatus.PUBLISHED,
                    "TikTok publication completed by webhook",
                )
                user = await session.get(User, upload.user_id)
                if user:
                    notify_upload_status.send(user.telegram_id, UploadStatus.PUBLISHED.value)
            elif event_type in {"post.publish.failed", "video.upload.failed"}:
                reason = str(content.get("reason") or "unknown")
                await transition_upload_job(
                    session,
                    upload,
                    UploadStatus.FAILED,
                    f"TikTok processing failed: {reason}",
                )
                user = await session.get(User, upload.user_id)
                if user:
                    notify_upload_status.send(user.telegram_id, UploadStatus.FAILED.value)

        if event_type == "authorization.removed":
            open_id = str(payload.get("user_openid") or "")
            account = await session.scalar(
                select(TikTokAccount).where(TikTokAccount.open_id == open_id)
            )
            if account:
                user = await session.get(User, account.user_id)
                await session.delete(account)
                if user:
                    notify_upload_status.send(user.telegram_id, "TIKTOK_REVOKED")

        event.status = "processed"
        event.processed_at = datetime.now(UTC)
    return {"status": "ok"}


@app.post("/api/v1/payments/robokassa/result", response_class=PlainTextResponse)
@app.post("/payments/robokassa/result", response_class=PlainTextResponse)
async def robokassa_result(
    request: Request,
    out_sum: str = Form(alias="OutSum"),
    inv_id: str = Form(alias="InvId"),
    signature_value: str = Form(alias="SignatureValue"),
) -> str:
    METRICS["robokassa_results_total"] += 1
    payload = dict(await request.form())
    async with session_scope() as session:
        await record_webhook_event(
            session,
            provider="robokassa",
            event_type="payment_result",
            external_id=inv_id,
            payload=payload,
        )
    if not validate_result_signature(out_sum, inv_id, signature_value):
        async with session_scope() as session:
            await record_webhook_event(
                session,
                provider="robokassa",
                event_type="payment_result_invalid_signature",
                external_id=inv_id,
                payload={"InvId": inv_id},
                status="rejected",
            )
        raise HTTPException(status_code=400, detail="Invalid Robokassa signature")

    currency = payload.get("Currency") or payload.get("IncCurrLabel") or "RUB"
    if currency not in ("RUB", ""):
        raise HTTPException(status_code=400, detail="Invalid payment currency")

    async with session_scope() as session:
        payment = await mark_payment_paid(session, int(inv_id), out_sum, raw_payload=payload)
        user = await session.get(User, payment.user_id) if payment else None

    if not payment or payment.status != "paid":
        raise HTTPException(status_code=400, detail="Payment was not accepted")
    if user:
        await _notify_payment_success(user.telegram_id, payment.plan_id)
    return f"OK{inv_id}"


@app.get("/api/v1/payments/robokassa/success")
@app.get("/payments/robokassa/success")
async def robokassa_success() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "Payment page returned success. Subscription status changes only after ResultURL.",
    }


@app.get("/api/v1/payments/robokassa/fail")
@app.get("/payments/robokassa/fail")
async def robokassa_fail() -> dict[str, str]:
    return {"status": "failed", "message": "Payment was not completed. Return to Telegram bot."}


async def _notify_payment_success(telegram_id: int, plan_id: str) -> None:
    if not settings.bot_token:
        return
    bot = Bot(token=settings.bot_token)
    try:
        await bot.send_message(
            telegram_id,
            bot_text("payment_success", plan=plan_id.upper()),
        )
    finally:
        await bot.session.close()
