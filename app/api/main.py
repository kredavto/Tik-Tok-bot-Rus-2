import hashlib
import hmac
import time
from uuid import UUID, uuid4

from aiogram import Bot
from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse, Response
from sqlalchemy import func, select, text

from app.core.config import require_settings, settings
from app.core.logging import configure_logging
from app.core.redis import create_oauth_state, get_redis, pop_oauth_state
from app.core.upload_status import UploadStatus
from app.db.models import Payment, Subscription, UploadJob, User
from app.db.session import (
    engine,
    get_or_create_user,
    init_db,
    mark_payment_paid,
    record_webhook_event,
    session_scope,
    upsert_tiktok_account,
)
from app.services.robokassa import validate_result_signature
from app.services.tiktok import TikTokApiError, TikTokClient, build_oauth_url
from app.api.admin import router as admin_router
from app.bot.messages import text as bot_text

configure_logging()
app = FastAPI(title="Tik_Tok_Loader API")
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


@app.on_event("startup")
async def startup() -> None:
    require_settings("database_url", "redis_url", "public_base_url")
    await init_db()


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
        payments_paid = await session.scalar(select(func.count(Payment.id)).where(Payment.status == "paid"))
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
    telegram_id: int = Query(...),
    username: str | None = Query(default=None),
) -> RedirectResponse:
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, username)
        state = await create_oauth_state(str(user.id))
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

    async with session_scope() as session:
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

    return {"status": "connected", "message": "TikTok account connected. Return to Telegram bot."}


@app.post("/api/v1/webhooks/telegram")
@app.post("/webhooks/telegram")
async def telegram_webhook(request: Request) -> dict[str, str]:
    if settings.telegram_webhook_secret:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(token, settings.telegram_webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret")

    payload = await request.json()
    async with session_scope() as session:
        await record_webhook_event(
            session,
            provider="telegram",
            event_type="update",
            external_id=str(payload.get("update_id", "")),
            payload=payload,
            status="received",
        )
    return {"status": "ok"}


@app.post("/api/v1/webhooks/tiktok")
@app.post("/webhooks/tiktok")
async def tiktok_webhook(request: Request) -> dict[str, str]:
    METRICS["tiktok_webhooks_total"] += 1
    raw_body = await request.body()
    if settings.tiktok_webhook_secret:
        signature = request.headers.get("X-TikTok-Signature", "")
        expected = hmac.new(
            settings.tiktok_webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid TikTok webhook signature")

    payload = await request.json()
    async with session_scope() as session:
        await record_webhook_event(
            session,
            provider="tiktok",
            event_type=str(payload.get("event", "unknown")),
            external_id=str(payload.get("event_id") or payload.get("publish_id") or ""),
            payload=payload,
            status="received",
        )
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
