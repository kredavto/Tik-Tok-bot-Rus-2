from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import aliased

from app.core.config import settings
from app.core.plans import PLANS, PlanCode
from app.core.upload_status import UploadStatus, validate_upload_transition
from app.db.models import (
    DailyUsage,
    Payment,
    Plan,
    Subscription,
    SystemSetting,
    TikTokAccount,
    UploadJob,
    UploadJobEvent,
    User,
    WebhookEvent,
)
from app.security.crypto import encrypt_secret
from app.services.configuration import seed_system_settings

engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@dataclass(frozen=True)
class SubscriptionExpirationNotice:
    subscription_id: UUID
    telegram_id: int


@dataclass(frozen=True)
class PaymentConfirmation:
    payment: Payment | None
    activated: bool


async def init_db() -> None:
    async with session_scope() as session:
        await seed_plans(session)
        await seed_system_settings(session)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def seed_plans(session: AsyncSession) -> None:
    for plan in PLANS.values():
        existing = await session.get(Plan, plan.code.value)
        duration_days = None if plan.code == PlanCode.FREE else 30
        if existing:
            existing.title = plan.title
            continue
        session.add(
            Plan(
                id=plan.code.value,
                title=plan.title,
                price_rub=plan.price_rub,
                price_stars=plan.price_stars,
                daily_limit=plan.daily_limit,
                duration_days=duration_days,
            )
        )


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
) -> User:
    user_id = await session.scalar(
        pg_insert(User)
        .values(telegram_id=telegram_id, username=username)
        .on_conflict_do_update(
            index_elements=[User.telegram_id],
            set_={"username": username, "updated_at": datetime.now(UTC)},
        )
        .returning(User.id)
    )
    if user_id is None:
        raise RuntimeError("Could not create or update Telegram user")
    user = await session.get(User, user_id)
    if user is None:
        raise RuntimeError("Telegram user disappeared after upsert")
    if not await get_active_subscription(session, user.id):
        await create_free_subscription(session, user.id)
    return user


async def create_free_subscription(session: AsyncSession, user_id: UUID) -> Subscription:
    subscription = Subscription(
        user_id=user_id,
        plan_id=PlanCode.FREE.value,
        status="active",
        starts_at=datetime.now(UTC),
        ends_at=None,
    )
    session.add(subscription)
    await session.flush()
    return subscription


async def get_active_subscription(session: AsyncSession, user_id: UUID) -> Subscription | None:
    now = datetime.now(UTC)
    expired = (
        await session.scalars(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == "active",
                Subscription.ends_at.is_not(None),
                Subscription.ends_at < now,
            )
        )
    ).all()
    for subscription in expired:
        subscription.status = "expired"

    statement = (
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status == "active",
            (Subscription.ends_at.is_(None)) | (Subscription.ends_at >= now),
        )
        .order_by(Subscription.ends_at.desc().nulls_last(), Subscription.created_at.desc())
    )
    return await session.scalar(statement)


async def active_plan_code(session: AsyncSession, user: User) -> str:
    subscription = await get_active_subscription(session, user.id)
    if not subscription:
        await create_free_subscription(session, user.id)
        return PlanCode.FREE.value
    return subscription.plan_id


async def get_plan_record(session: AsyncSession, plan_code: str) -> Plan:
    plan = await session.get(Plan, plan_code)
    if plan is None:
        raise ValueError(f"Unknown plan: {plan_code}")
    return plan


def current_usage_date() -> date:
    try:
        timezone = ZoneInfo(settings.timezone)
    except ZoneInfoNotFoundError as exc:
        raise RuntimeError(f"Unknown TIMEZONE: {settings.timezone}") from exc
    return datetime.now(timezone).date()


async def get_daily_usage(session: AsyncSession, user_id: UUID, usage_date: date) -> DailyUsage:
    await session.execute(
        pg_insert(DailyUsage)
        .values(user_id=user_id, usage_date=usage_date, upload_count=0)
        .on_conflict_do_nothing(index_elements=[DailyUsage.user_id, DailyUsage.usage_date])
    )
    usage = await session.scalar(
        select(DailyUsage)
        .where(DailyUsage.user_id == user_id, DailyUsage.usage_date == usage_date)
        .with_for_update()
    )
    if usage is None:
        raise RuntimeError("Daily usage row disappeared after upsert")
    return usage


async def can_upload_today(session: AsyncSession, user: User) -> tuple[bool, int, int]:
    plan = await get_plan_record(session, await active_plan_code(session, user))
    usage = await get_daily_usage(session, user.id, current_usage_date())
    return usage.upload_count < plan.daily_limit, usage.upload_count, plan.daily_limit


async def consume_daily_upload(session: AsyncSession, user: User) -> tuple[bool, int, int]:
    plan = await get_plan_record(session, await active_plan_code(session, user))
    usage = await get_daily_usage(session, user.id, current_usage_date())
    if usage.upload_count >= plan.daily_limit:
        return False, usage.upload_count, plan.daily_limit
    usage.upload_count += 1
    return True, usage.upload_count, plan.daily_limit


async def record_accepted_upload(session: AsyncSession, user: User) -> int:
    """Record a publication that TikTok has already accepted."""
    usage = await get_daily_usage(session, user.id, current_usage_date())
    usage.upload_count += 1
    return usage.upload_count


async def accept_agreement(session: AsyncSession, user: User) -> None:
    user.agreement_accepted_at = datetime.now(UTC)


async def has_tiktok_account(session: AsyncSession, user_id: UUID) -> bool:
    account_id = await session.scalar(
        select(TikTokAccount.id).where(TikTokAccount.user_id == user_id)
    )
    return account_id is not None


async def get_primary_tiktok_account(session: AsyncSession, user_id: UUID) -> TikTokAccount | None:
    return await session.scalar(
        select(TikTokAccount)
        .where(TikTokAccount.user_id == user_id)
        .order_by(TikTokAccount.created_at.desc())
    )


async def upsert_tiktok_account(
    session: AsyncSession,
    user_id: UUID,
    open_id: str,
    display_name: str | None,
    access_token: str,
    refresh_token: str | None,
    expires_in: int | None,
    scopes: str | None,
) -> TikTokAccount:
    account = await session.scalar(
        select(TikTokAccount).where(
            TikTokAccount.user_id == user_id, TikTokAccount.open_id == open_id
        )
    )
    expires_at = datetime.now(UTC) + timedelta(seconds=expires_in or 0) if expires_in else None
    if not account:
        account = TikTokAccount(
            user_id=user_id,
            open_id=open_id,
            display_name=display_name,
            access_token_encrypted=encrypt_secret(access_token),
            refresh_token_encrypted=encrypt_secret(refresh_token) if refresh_token else None,
            token_expires_at=expires_at,
            scopes=scopes,
        )
        session.add(account)
    else:
        account.display_name = display_name
        account.access_token_encrypted = encrypt_secret(access_token)
        account.refresh_token_encrypted = encrypt_secret(refresh_token) if refresh_token else None
        account.token_expires_at = expires_at
        account.scopes = scopes
        account.refresh_blocked_at = None
        account.refresh_error_code = None
    await session.flush()
    return account


async def revoke_tiktok_accounts(session: AsyncSession, user_id: UUID) -> int:
    accounts = (
        await session.scalars(select(TikTokAccount).where(TikTokAccount.user_id == user_id))
    ).all()
    for account in accounts:
        await session.delete(account)
    return len(accounts)


async def anonymize_user(session: AsyncSession, user_id: UUID) -> bool:
    user = await session.get(User, user_id)
    if not user:
        return False
    await revoke_tiktok_accounts(session, user_id)
    user.telegram_id = -abs(user.id.int % 9_000_000_000)
    user.username = None
    user.role = "USER"
    user.is_admin = False
    user.is_blocked = True
    user.agreement_accepted_at = None
    return True


async def create_upload_job(
    session: AsyncSession,
    user_id: UUID,
    tiktok_account_id: UUID,
    telegram_file_id: str,
    local_path: str,
    caption: str | None,
    privacy_level: str,
    disable_comment: bool,
    disable_duet: bool,
    disable_stitch: bool,
    brand_content_toggle: bool,
    brand_organic_toggle: bool,
) -> UploadJob:
    job = UploadJob(
        user_id=user_id,
        tiktok_account_id=tiktok_account_id,
        telegram_file_id=telegram_file_id,
        local_path=local_path,
        caption=caption,
        privacy_level=privacy_level,
        disable_comment=disable_comment,
        disable_duet=disable_duet,
        disable_stitch=disable_stitch,
        brand_content_toggle=brand_content_toggle,
        brand_organic_toggle=brand_organic_toggle,
        status=UploadStatus.NEW.value,
    )
    session.add(job)
    await session.flush()
    await record_upload_job_event(session, job, UploadStatus.NEW, "Upload job created")
    return job


async def transition_upload_job(
    session: AsyncSession,
    upload_job: UploadJob,
    status: UploadStatus,
    message: str | None = None,
) -> None:
    validate_upload_transition(upload_job.status, status)
    upload_job.status = status.value
    if status == UploadStatus.FAILED and message:
        upload_job.error_message = message
    await record_upload_job_event(session, upload_job, status, message)


async def record_upload_job_event(
    session: AsyncSession,
    upload_job: UploadJob,
    status: UploadStatus,
    message: str | None = None,
) -> UploadJobEvent:
    event = UploadJobEvent(
        upload_job_id=upload_job.id,
        user_id=upload_job.user_id,
        status=status.value,
        message=message,
    )
    session.add(event)
    await session.flush()
    return event


async def list_recent_upload_jobs(
    session: AsyncSession,
    user_id: UUID,
    limit: int = 10,
) -> list[UploadJob]:
    statement = (
        select(UploadJob)
        .where(UploadJob.user_id == user_id)
        .order_by(UploadJob.created_at.desc())
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())


async def create_paid_subscription(
    session: AsyncSession,
    user_id: UUID,
    plan_code: str,
) -> Subscription:
    now = datetime.now(UTC)
    user = await session.get(User, user_id, with_for_update=True)
    if user is None:
        raise ValueError(f"Unknown user: {user_id}")
    plan = await get_plan_record(session, plan_code)
    if plan_code == PlanCode.FREE.value or not plan.is_active or not plan.duration_days:
        raise ValueError(f"Plan is not available for purchase: {plan_code}")
    await expire_active_subscriptions(session, user_id)
    subscription = Subscription(
        user_id=user_id,
        plan_id=plan_code,
        status="active",
        starts_at=now,
        ends_at=now + timedelta(days=plan.duration_days),
    )
    session.add(subscription)
    await session.flush()
    return subscription


async def expire_active_subscriptions(session: AsyncSession, user_id: UUID) -> None:
    now = datetime.now(UTC)
    statement = select(Subscription).where(
        Subscription.user_id == user_id,
        Subscription.status == "active",
    )
    subscriptions = (await session.scalars(statement)).all()
    for subscription in subscriptions:
        subscription.status = "expired"
        if subscription.plan_id != PlanCode.FREE.value:
            subscription.expiration_notified_at = now
        if not subscription.ends_at or subscription.ends_at > now:
            subscription.ends_at = now


async def expire_due_paid_subscriptions(
    session: AsyncSession,
    *,
    now: datetime | None = None,
    batch_size: int = 100,
) -> list[SubscriptionExpirationNotice]:
    effective_now = now or datetime.now(UTC)
    due = (
        await session.scalars(
            select(Subscription)
            .where(
                Subscription.status == "active",
                Subscription.plan_id != PlanCode.FREE.value,
                Subscription.ends_at.is_not(None),
                Subscription.ends_at <= effective_now,
            )
            .order_by(Subscription.ends_at)
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
    ).all()

    for subscription in due:
        subscription.status = "expired"
    await session.flush()

    for subscription in due:
        await create_free_subscription(session, subscription.user_id)
    await session.flush()

    active_subscription = aliased(Subscription)
    active_free_exists = (
        select(active_subscription.id)
        .where(
            active_subscription.user_id == Subscription.user_id,
            active_subscription.status == "active",
            active_subscription.plan_id == PlanCode.FREE.value,
        )
        .exists()
    )
    rows = (
        await session.execute(
            select(Subscription.id, User.telegram_id)
            .join(User, User.id == Subscription.user_id)
            .where(
                Subscription.status == "expired",
                Subscription.plan_id != PlanCode.FREE.value,
                Subscription.ends_at.is_not(None),
                Subscription.ends_at <= effective_now,
                Subscription.expiration_notified_at.is_(None),
                active_free_exists,
            )
            .order_by(Subscription.ends_at)
            .limit(batch_size)
            .with_for_update(of=Subscription, skip_locked=True)
        )
    ).all()
    return [
        SubscriptionExpirationNotice(subscription_id=subscription_id, telegram_id=telegram_id)
        for subscription_id, telegram_id in rows
    ]


async def mark_subscription_expiration_notified(
    session: AsyncSession,
    subscription_id: UUID,
) -> bool:
    subscription = await session.get(Subscription, subscription_id, with_for_update=True)
    if (
        subscription is None
        or subscription.status != "expired"
        or subscription.expiration_notified_at is not None
    ):
        return False
    subscription.expiration_notified_at = datetime.now(UTC)
    return True


async def list_tiktok_accounts_due_for_refresh(
    session: AsyncSession,
    *,
    due_before: datetime,
    batch_size: int = 100,
) -> list[UUID]:
    return list(
        (
            await session.scalars(
                select(TikTokAccount.id)
                .where(
                    TikTokAccount.token_expires_at.is_not(None),
                    TikTokAccount.token_expires_at <= due_before,
                    TikTokAccount.refresh_blocked_at.is_(None),
                )
                .order_by(TikTokAccount.token_expires_at)
                .limit(batch_size)
            )
        ).all()
    )


async def create_payment(session: AsyncSession, user_id: UUID, plan_code: str) -> Payment:
    plan = await get_plan_record(session, plan_code)
    if plan_code == PlanCode.FREE.value or not plan.is_active or plan.price_rub <= 0:
        raise ValueError(f"Plan is not available for purchase: {plan_code}")
    payment = Payment(
        user_id=user_id,
        plan_id=plan_code,
        amount_rub=plan.price_rub,
        currency="RUB",
        provider="robokassa",
    )
    session.add(payment)
    await session.flush()
    await record_webhook_event(
        session,
        provider="robokassa",
        event_type="payment_status_changed",
        external_id=str(payment.provider_invoice_id),
        payload={"status": "created", "plan_id": plan_code, "amount_rub": plan.price_rub},
        status="processed",
    )
    return payment


async def create_stars_payment(
    session: AsyncSession,
    user_id: UUID,
    plan_code: str,
) -> Payment:
    plan = await get_plan_record(session, plan_code)
    if (
        plan_code == PlanCode.FREE.value
        or not plan.is_active
        or plan.price_stars is None
        or plan.price_stars <= 0
    ):
        raise ValueError(f"Plan is not available for Stars purchase: {plan_code}")
    payment = Payment(
        user_id=user_id,
        plan_id=plan_code,
        amount_rub=plan.price_rub,
        amount_stars=plan.price_stars,
        currency="XTR",
        provider="telegram_stars",
    )
    session.add(payment)
    await session.flush()
    await record_webhook_event(
        session,
        provider="telegram_stars",
        event_type="payment_status_changed",
        external_id=str(payment.id),
        payload={
            "status": "created",
            "plan_id": plan_code,
            "amount_stars": plan.price_stars,
        },
        status="processed",
    )
    return payment


async def validate_stars_checkout(
    session: AsyncSession,
    payment_id: UUID,
    telegram_id: int,
    currency: str,
    total_amount: int,
) -> bool:
    payment = await session.get(Payment, payment_id)
    if payment is None or payment.provider != "telegram_stars" or payment.status != "created":
        return False
    user = await session.get(User, payment.user_id)
    return bool(
        user
        and user.telegram_id == telegram_id
        and currency == "XTR"
        and payment.currency == "XTR"
        and payment.amount_stars == total_amount
    )


async def mark_stars_payment_paid(
    session: AsyncSession,
    payment_id: UUID,
    telegram_id: int,
    currency: str,
    total_amount: int,
    telegram_payment_charge_id: str,
) -> PaymentConfirmation:
    payment = await session.scalar(
        select(Payment).where(Payment.id == payment_id).with_for_update()
    )
    if payment is None or payment.provider != "telegram_stars":
        return PaymentConfirmation(payment=None, activated=False)

    user = await session.get(User, payment.user_id)
    if user is None or user.telegram_id != telegram_id:
        return PaymentConfirmation(payment=None, activated=False)
    if payment.status == "paid":
        if payment.provider_charge_id == telegram_payment_charge_id:
            return PaymentConfirmation(payment=payment, activated=False)
        return PaymentConfirmation(payment=None, activated=False)
    if (
        currency != "XTR"
        or payment.currency != "XTR"
        or payment.amount_stars != total_amount
        or not telegram_payment_charge_id
    ):
        return PaymentConfirmation(payment=None, activated=False)

    duplicate = await session.scalar(
        select(Payment.id).where(
            Payment.provider == "telegram_stars",
            Payment.provider_charge_id == telegram_payment_charge_id,
            Payment.id != payment.id,
        )
    )
    if duplicate is not None:
        return PaymentConfirmation(payment=None, activated=False)

    subscription = await create_paid_subscription(session, payment.user_id, payment.plan_id)
    payment.subscription_id = subscription.id
    payment.status = "paid"
    payment.provider_charge_id = telegram_payment_charge_id
    payment.paid_at = datetime.now(UTC)
    await record_webhook_event(
        session,
        provider="telegram_stars",
        event_type="payment_status_changed",
        external_id=telegram_payment_charge_id,
        payload={
            "status": "paid",
            "payment_id": str(payment.id),
            "subscription_id": str(subscription.id),
            "amount_stars": total_amount,
        },
        status="processed",
    )
    return PaymentConfirmation(payment=payment, activated=True)


async def mark_stars_payment_refunded(
    session: AsyncSession,
    payment_id: UUID,
) -> PaymentConfirmation:
    payment = await session.scalar(
        select(Payment).where(Payment.id == payment_id).with_for_update()
    )
    if payment is None or payment.provider != "telegram_stars" or payment.currency != "XTR":
        return PaymentConfirmation(payment=None, activated=False)
    if payment.status == "refunded":
        return PaymentConfirmation(payment=payment, activated=False)
    if payment.status != "paid" or not payment.provider_charge_id:
        return PaymentConfirmation(payment=None, activated=False)

    await session.get(User, payment.user_id, with_for_update=True)
    subscription = (
        await session.get(Subscription, payment.subscription_id, with_for_update=True)
        if payment.subscription_id
        else None
    )
    if subscription and subscription.status == "active":
        subscription.status = "cancelled"
        subscription.ends_at = datetime.now(UTC)
        await session.flush()
        await create_free_subscription(session, payment.user_id)

    payment.status = "refunded"
    await record_webhook_event(
        session,
        provider="telegram_stars",
        event_type="payment_status_changed",
        external_id=payment.provider_charge_id,
        payload={"status": "refunded", "payment_id": str(payment.id)},
        status="processed",
    )
    return PaymentConfirmation(payment=payment, activated=True)


async def mark_payment_paid(
    session: AsyncSession,
    inv_id: int,
    out_sum: str,
    raw_payload: dict | None = None,
) -> PaymentConfirmation:
    payment = await session.scalar(
        select(Payment)
        .where(
            Payment.provider_invoice_id == inv_id,
            Payment.provider == "robokassa",
            Payment.currency == "RUB",
        )
        .with_for_update()
    )
    if not payment:
        return PaymentConfirmation(payment=None, activated=False)
    if payment.status == "paid":
        await record_webhook_event(
            session,
            provider="robokassa",
            event_type="payment_status_idempotent",
            external_id=str(inv_id),
            payload={"status": "paid"},
            status="processed",
        )
        return PaymentConfirmation(payment=payment, activated=False)
    if payment.status not in {"created", "pending"}:
        return PaymentConfirmation(payment=None, activated=False)

    expected = Decimal(payment.amount_rub).quantize(Decimal("0.01"))
    try:
        received = Decimal(out_sum).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        received = None
    payment.raw_payload = raw_payload
    if received != expected:
        payment.status = "failed"
        await record_webhook_event(
            session,
            provider="robokassa",
            event_type="payment_status_changed",
            external_id=str(inv_id),
            payload={"status": payment.status, "reason": "amount_mismatch"},
            status="processed",
        )
        return PaymentConfirmation(payment=payment, activated=False)

    subscription = await create_paid_subscription(session, payment.user_id, payment.plan_id)
    payment.subscription_id = subscription.id
    payment.status = "paid"
    payment.paid_at = datetime.now(UTC)
    await record_webhook_event(
        session,
        provider="robokassa",
        event_type="payment_status_changed",
        external_id=str(inv_id),
        payload={"status": "paid", "subscription_id": str(subscription.id)},
        status="processed",
    )
    return PaymentConfirmation(payment=payment, activated=True)


async def record_webhook_event(
    session: AsyncSession,
    provider: str,
    event_type: str,
    payload: dict,
    external_id: str | None = None,
    status: str = "received",
) -> WebhookEvent:
    event = WebhookEvent(
        provider=provider,
        event_type=event_type,
        external_id=external_id,
        payload=payload,
        status=status,
    )
    session.add(event)
    await session.flush()
    return event


async def claim_webhook_event(
    session: AsyncSession,
    provider: str,
    event_type: str,
    external_id: str,
    payload: dict,
    *,
    lease_seconds: int = 900,
) -> WebhookEvent | None:
    """Atomically claim one externally identifiable webhook delivery."""
    now = datetime.now(UTC)
    deduplication_key = f"{provider}:{event_type}:{external_id}"
    event_id = await session.scalar(
        pg_insert(WebhookEvent)
        .values(
            provider=provider,
            event_type=event_type,
            external_id=external_id,
            deduplication_key=deduplication_key,
            payload=payload,
            status="processing",
            locked_until=now + timedelta(seconds=lease_seconds),
        )
        .on_conflict_do_nothing(index_elements=[WebhookEvent.deduplication_key])
        .returning(WebhookEvent.id)
    )
    if event_id is not None:
        return await session.get(WebhookEvent, event_id)

    event = await session.scalar(
        select(WebhookEvent)
        .where(WebhookEvent.deduplication_key == deduplication_key)
        .with_for_update()
    )
    if event is None or event.status == "processed":
        return None
    if event.locked_until is not None and event.locked_until > now:
        return None

    event.payload = payload
    event.status = "processing"
    event.processed_at = None
    event.locked_until = now + timedelta(seconds=lease_seconds)
    return event


async def is_intake_enabled(session: AsyncSession) -> bool:
    setting = await session.scalar(
        select(SystemSetting).where(SystemSetting.key == "intake_enabled")
    )
    if not setting:
        return True
    return setting.value.lower() not in {"0", "false", "no", "off"}
