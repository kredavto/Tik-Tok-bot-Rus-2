from collections.abc import Callable
from datetime import UTC, datetime, timedelta
import hmac
import logging
from pathlib import Path
from typing import Literal
from uuid import UUID

from aiogram import Bot
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.plans import PlanCode
from app.core.redis import enqueue_upload
from app.core.upload_status import UploadStatus
from app.db.models import (
    AdminAction,
    Payment,
    Plan,
    Subscription,
    SystemSetting,
    TikTokAccount,
    UploadJob,
    User,
)
from app.db.session import (
    anonymize_user,
    claim_stars_payment_refund,
    create_payment,
    create_free_subscription,
    expire_active_subscriptions,
    mark_stars_payment_refunded,
    record_upload_job_event,
    release_stars_payment_refund,
    session_scope,
)
from app.security.rbac import ROLE_PERMISSIONS, Permission, Role, assert_permission, normalize_role
from app.services.configuration import (
    export_runtime_configuration,
    import_runtime_configuration,
    is_secret_like,
    validate_runtime_configuration,
    validate_setting_value,
)
from app.services.robokassa import build_payment_url

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

MAX_PAGE_LIMIT = 200


class PlanUpdate(BaseModel):
    price_rub: int | None = Field(default=None, ge=0)
    price_stars: int | None = Field(default=None, ge=1)
    daily_limit: int | None = Field(default=None, ge=0)
    duration_days: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class SettingUpdate(BaseModel):
    value: str
    value_type: Literal["string", "int", "bool", "json"] | None = None
    description: str | None = Field(default=None, max_length=1000)
    is_editable: bool | None = None


class RoleUpdate(BaseModel):
    role: Role


class RobokassaOrderCreate(BaseModel):
    telegram_user_id: int = Field(gt=0)
    plan_id: Literal["pro", "business"]


class StarsRefundReconciliation(BaseModel):
    outcome: Literal["refunded", "not_refunded"]


class ConfigurationImport(BaseModel):
    payload: dict


class Page(BaseModel):
    limit: int = Field(default=50, ge=1, le=MAX_PAGE_LIMIT)
    offset: int = Field(default=0, ge=0)


RETRYABLE_UPLOAD_ERROR_MARKERS = (
    "temporary",
    "network",
    "timeout",
    "connection",
    "queue dispatch",
)


async def require_admin(
    authorization: str | None = Header(default=None),
) -> User:
    if not settings.admin_api_token or settings.admin_api_telegram_id is None:
        raise HTTPException(status_code=503, detail="Admin API is not configured")
    supplied_token = authorization.removeprefix("Bearer ") if authorization else ""
    if not hmac.compare_digest(supplied_token, settings.admin_api_token):
        raise HTTPException(status_code=401, detail="Invalid admin token")

    allowed_ids = {item.strip() for item in settings.admin_telegram_ids.split(",") if item.strip()}
    if str(settings.admin_api_telegram_id) not in allowed_ids:
        raise HTTPException(status_code=403, detail="Admin is not allowed")

    async with session_scope() as session:
        admin = await session.scalar(
            select(User).where(User.telegram_id == settings.admin_api_telegram_id)
        )
        if not admin:
            raise HTTPException(status_code=401, detail="Admin was not found")
        if admin.is_blocked or not admin.is_admin or normalize_role(admin.role) == Role.USER:
            raise HTTPException(status_code=403, detail="Admin access is disabled")
        return admin


def require_permission(permission: Permission) -> Callable:
    async def dependency(admin: User = Depends(require_admin)) -> User:
        assert_permission(admin, permission)
        return admin

    return dependency


def require_csrf(x_csrf_token: str | None = Header(default=None)) -> None:
    if not settings.admin_csrf_token or x_csrf_token != settings.admin_csrf_token:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")


async def log_admin_action(
    session: AsyncSession,
    admin: User,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    metadata: dict | None = None,
    ip_address: str | None = None,
) -> None:
    session.add(
        AdminAction(
            admin_user_id=admin.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata_json=metadata,
            ip_address=ip_address,
        )
    )


def request_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()[:45]
    return request.client.host[:45] if request.client else None


def upload_job_is_retryable(job: UploadJob) -> bool:
    error = (job.error_message or "").lower()
    return (
        job.status == UploadStatus.FAILED.value
        and job.tiktok_publish_id is None
        and any(marker in error for marker in RETRYABLE_UPLOAD_ERROR_MARKERS)
    )


@router.get("/session")
async def admin_session(admin: User = Depends(require_admin)) -> dict:
    role = normalize_role(admin.role)
    return {
        "telegram_id": admin.telegram_id,
        "role": role.value,
        "permissions": sorted(permission.value for permission in ROLE_PERMISSIONS[role]),
    }


@router.get("/dashboard")
async def dashboard(admin: User = Depends(require_permission(Permission.VIEW_STATS))) -> dict:
    async with session_scope() as session:
        users_total = await session.scalar(select(func.count(User.id)))
        payments_paid = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount_rub), 0)).where(
                Payment.status == "paid",
                Payment.provider == "robokassa",
            )
        )
        stars_paid = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount_stars), 0)).where(
                Payment.status == "paid",
                Payment.provider == "telegram_stars",
            )
        )
        queued = await session.scalar(
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
        errors = await session.scalar(
            select(func.count(UploadJob.id)).where(UploadJob.status == UploadStatus.FAILED.value)
        )
    return {
        "users_total": users_total or 0,
        "revenue_rub": payments_paid or 0,
        "revenue_stars": stars_paid or 0,
        "queue_active": queued or 0,
        "publication_errors": errors or 0,
    }


@router.get("/analytics")
async def analytics(admin: User = Depends(require_permission(Permission.VIEW_STATS))) -> dict:
    today = datetime.now(UTC).date()
    since_24h = datetime.now(UTC) - timedelta(days=1)
    async with session_scope() as session:
        users_total = await session.scalar(select(func.count(User.id)))
        new_users = await session.scalar(
            select(func.count(User.id)).where(User.created_at >= since_24h)
        )
        uploads_today = await session.scalar(
            select(func.count(UploadJob.id)).where(
                func.date(UploadJob.created_at) == today.isoformat()
            )
        )
        revenue = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount_rub), 0)).where(
                Payment.status == "paid",
                Payment.provider == "robokassa",
            )
        )
        stars_revenue = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount_stars), 0)).where(
                Payment.status == "paid",
                Payment.provider == "telegram_stars",
            )
        )
        tiktok_errors = await session.scalar(
            select(func.count(UploadJob.id)).where(UploadJob.error_message.ilike("%TikTok%"))
        )
        plan_rows = (
            await session.execute(
                select(Subscription.plan_id, func.count(Subscription.id))
                .where(Subscription.status == "active")
                .group_by(Subscription.plan_id)
            )
        ).all()
    plans = {plan_id: count for plan_id, count in plan_rows}
    free_total = plans.get("free", 0) or 1
    return {
        "users_total": users_total or 0,
        "new_registrations_24h": new_users or 0,
        "active_by_plan": plans,
        "uploads_today": uploads_today or 0,
        "robokassa_revenue_rub": revenue or 0,
        "telegram_stars_revenue": stars_revenue or 0,
        "free_to_pro_conversion": round((plans.get("pro", 0) / free_total) * 100, 2),
        "free_to_business_conversion": round((plans.get("business", 0) / free_total) * 100, 2),
        "tiktok_api_errors": tiktok_errors or 0,
    }


@router.get("/users")
async def users(
    telegram_id: int | None = Query(default=None),
    username: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(require_permission(Permission.VIEW_USERS)),
) -> dict:
    async with session_scope() as session:
        statement = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        count_statement = select(func.count(User.id))
        if telegram_id:
            statement = statement.where(User.telegram_id == telegram_id)
            count_statement = count_statement.where(User.telegram_id == telegram_id)
        if username:
            statement = statement.where(User.username.ilike(f"%{username}%"))
            count_statement = count_statement.where(User.username.ilike(f"%{username}%"))
        rows = (await session.scalars(statement)).all()
        total = await session.scalar(count_statement)
    return {
        "items": [
            {
                "id": str(user.id),
                "telegram_id": user.telegram_id,
                "username": user.username,
                "role": user.role,
                "is_blocked": user.is_blocked,
                "created_at": user.created_at.isoformat(),
            }
            for user in rows
        ],
        "limit": limit,
        "offset": offset,
        "total": total or 0,
    }


@router.get("/users/{user_id}")
async def user_detail(
    user_id: UUID,
    admin: User = Depends(require_permission(Permission.VIEW_USERS)),
) -> dict:
    async with session_scope() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        subscription = await session.scalar(
            select(Subscription)
            .where(Subscription.user_id == user_id, Subscription.status == "active")
            .order_by(Subscription.created_at.desc())
        )
        tiktok_accounts = (
            await session.scalars(
                select(TikTokAccount)
                .where(TikTokAccount.user_id == user_id)
                .order_by(TikTokAccount.created_at.desc())
            )
        ).all()
        payment_rows = (
            await session.scalars(
                select(Payment)
                .where(Payment.user_id == user_id)
                .order_by(Payment.created_at.desc())
                .limit(10)
            )
        ).all()
        upload_rows = (
            await session.scalars(
                select(UploadJob)
                .where(UploadJob.user_id == user_id)
                .order_by(UploadJob.created_at.desc())
                .limit(10)
            )
        ).all()

    return {
        "id": str(user.id),
        "telegram_id": user.telegram_id,
        "username": user.username,
        "role": user.role,
        "is_blocked": user.is_blocked,
        "agreement_accepted_at": (
            user.agreement_accepted_at.isoformat() if user.agreement_accepted_at else None
        ),
        "created_at": user.created_at.isoformat(),
        "subscription": (
            {
                "id": str(subscription.id),
                "plan_id": subscription.plan_id,
                "starts_at": subscription.starts_at.isoformat(),
                "ends_at": subscription.ends_at.isoformat() if subscription.ends_at else None,
            }
            if subscription
            else None
        ),
        "tiktok_accounts": [
            {
                "id": str(account.id),
                "display_name": account.display_name,
                "connected_at": account.created_at.isoformat(),
                "token_expires_at": (
                    account.token_expires_at.isoformat() if account.token_expires_at else None
                ),
                "refresh_blocked": account.refresh_blocked_at is not None,
            }
            for account in tiktok_accounts
        ],
        "payments": [
            {
                "id": str(payment.id),
                "inv_id": payment.provider_invoice_id,
                "plan_id": payment.plan_id,
                "amount_rub": payment.amount_rub,
                "status": payment.status,
                "created_at": payment.created_at.isoformat(),
            }
            for payment in payment_rows
        ],
        "upload_jobs": [
            {
                "id": str(job.id),
                "status": job.status,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat(),
            }
            for job in upload_rows
        ],
    }


@router.post("/users/{user_id}/block")
async def block_user(
    user_id: UUID,
    request: Request,
    admin: User = Depends(require_permission(Permission.MANAGE_USERS)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    async with session_scope() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_blocked = True
        await log_admin_action(
            session,
            admin,
            "block_user",
            "user",
            str(user_id),
            ip_address=request_ip(request),
        )
    return {"status": "blocked"}


@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: UUID,
    request: Request,
    admin: User = Depends(require_permission(Permission.MANAGE_USERS)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    async with session_scope() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_blocked = False
        await log_admin_action(
            session,
            admin,
            "unblock_user",
            "user",
            str(user_id),
            ip_address=request_ip(request),
        )
    return {"status": "unblocked"}


@router.post("/users/{user_id}/force-free")
async def force_free_plan(
    user_id: UUID,
    request: Request,
    admin: User = Depends(require_permission(Permission.MANAGE_USERS)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    async with session_scope() as session:
        user = await session.scalar(select(User).where(User.id == user_id).with_for_update())
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        previous = await session.scalar(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == "active",
            )
        )
        previous_plan = previous.plan_id if previous else None
        await expire_active_subscriptions(session, user_id)
        await create_free_subscription(session, user_id)
        await log_admin_action(
            session,
            admin,
            "force_free_plan",
            "user",
            str(user_id),
            {"previous_plan": previous_plan, "new_plan": PlanCode.FREE.value},
            request_ip(request),
        )
    return {"status": "free"}


@router.post("/users/{user_id}/anonymize")
async def anonymize_user_data(
    user_id: UUID,
    request: Request,
    admin: User = Depends(require_permission(Permission.MANAGE_USERS)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    async with session_scope() as session:
        anonymized = await anonymize_user(session, user_id)
        if not anonymized:
            raise HTTPException(status_code=404, detail="User not found")
        await log_admin_action(
            session,
            admin,
            "anonymize_user",
            "user",
            str(user_id),
            ip_address=request_ip(request),
        )
    return {"status": "anonymized"}


@router.get("/plans")
async def plans(admin: User = Depends(require_permission(Permission.MANAGE_PLANS))) -> list[dict]:
    async with session_scope() as session:
        rows = (await session.scalars(select(Plan))).all()
    return [
        {
            "id": plan.id,
            "title": plan.title,
            "price_rub": plan.price_rub,
            "price_stars": plan.price_stars,
            "daily_limit": plan.daily_limit,
            "duration_days": plan.duration_days,
            "is_active": plan.is_active,
        }
        for plan in rows
    ]


@router.patch("/plans/{plan_id}")
async def update_plan(
    plan_id: str,
    payload: PlanUpdate,
    request: Request,
    admin: User = Depends(require_permission(Permission.MANAGE_PLANS)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    async with session_scope() as session:
        plan = await session.get(Plan, plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        for key, value in payload.model_dump(exclude_none=True).items():
            setattr(plan, key, value)
        await log_admin_action(
            session,
            admin,
            "update_plan",
            "plan",
            plan_id,
            payload.model_dump(exclude_none=True),
            request_ip(request),
        )
    return {"status": "updated"}


@router.get("/payments")
async def payments(
    limit: int = Query(default=50, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
    inv_id: int | None = Query(default=None, ge=1),
    admin: User = Depends(require_permission(Permission.VIEW_PAYMENTS)),
) -> dict:
    async with session_scope() as session:
        statement = select(Payment).order_by(Payment.created_at.desc())
        count_statement = select(func.count(Payment.id))
        if status:
            statement = statement.where(Payment.status == status)
            count_statement = count_statement.where(Payment.status == status)
        if inv_id:
            statement = statement.where(Payment.provider_invoice_id == inv_id)
            count_statement = count_statement.where(Payment.provider_invoice_id == inv_id)
        rows = (await session.scalars(statement.limit(limit).offset(offset))).all()
        total = await session.scalar(count_statement)
    return {
        "items": [
            {
                "id": str(payment.id),
                "inv_id": payment.provider_invoice_id,
                "plan_id": payment.plan_id,
                "amount_rub": payment.amount_rub,
                "amount_stars": payment.amount_stars,
                "currency": payment.currency,
                "provider": payment.provider,
                "status": payment.status,
                "created_at": payment.created_at.isoformat(),
            }
            for payment in rows
        ],
        "limit": limit,
        "offset": offset,
        "total": total or 0,
    }


@router.post("/payments/robokassa/orders", status_code=201)
async def create_robokassa_order(
    payload: RobokassaOrderCreate,
    request: Request,
    admin: User = Depends(require_permission(Permission.MANAGE_PAYMENTS)),
    _: None = Depends(require_csrf),
) -> dict:
    async with session_scope() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == payload.telegram_user_id)
        )
        if user is None:
            raise HTTPException(status_code=404, detail="Telegram user not found")
        payment = await create_payment(session, user.id, payload.plan_id)
        checkout_url = build_payment_url(
            payment.provider_invoice_id,
            payment.amount_rub,
            f"Tik_Tok_Loader {payload.plan_id.upper()} subscription",
        )
        await log_admin_action(
            session,
            admin,
            "create_robokassa_order",
            "payment",
            str(payment.id),
            {
                "inv_id": payment.provider_invoice_id,
                "plan_id": payment.plan_id,
                "test_mode": settings.robokassa_test_mode,
            },
            request_ip(request),
        )
    return {
        "payment_id": str(payment.id),
        "inv_id": payment.provider_invoice_id,
        "amount_rub": payment.amount_rub,
        "currency": payment.currency,
        "status": payment.status,
        "checkout_url": checkout_url,
        "test_mode": settings.robokassa_test_mode,
    }


@router.post("/payments/{payment_id}/refund-stars")
async def refund_stars_payment(
    payment_id: UUID,
    request: Request,
    admin: User = Depends(require_permission(Permission.MANAGE_PAYMENTS)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    async with session_scope() as session:
        claim = await claim_stars_payment_refund(session, payment_id)
        if claim.payment is None:
            raise HTTPException(status_code=404, detail="Payment not found")
        if claim.payment.status == "refunded":
            return {"status": "refunded", "payment_id": str(claim.payment.id)}
        if claim.payment.status == "refund_pending" and not claim.claimed:
            return {"status": "refund_pending", "payment_id": str(claim.payment.id)}
        if not claim.claimed or claim.telegram_id is None or not claim.payment.provider_charge_id:
            raise HTTPException(status_code=409, detail="Payment is not refundable")
        telegram_id = claim.telegram_id
        provider_charge_id = claim.payment.provider_charge_id
        await log_admin_action(
            session,
            admin,
            "refund_stars_payment_requested",
            "payment",
            str(payment_id),
            {"status": "refund_pending"},
            request_ip(request),
        )

    bot = Bot(token=settings.bot_token)
    try:
        refunded = await bot.refund_star_payment(
            user_id=telegram_id,
            telegram_payment_charge_id=provider_charge_id,
        )
    except Exception as exc:
        logger.exception(
            "Telegram Stars refund result is unknown", extra={"payment_id": str(payment_id)}
        )
        async with session_scope() as session:
            await log_admin_action(
                session,
                admin,
                "refund_stars_payment_pending_reconciliation",
                "payment",
                str(payment_id),
                {"status": "refund_pending", "error_type": type(exc).__name__},
                request_ip(request),
            )
        raise HTTPException(
            status_code=502,
            detail="Telegram refund result is pending reconciliation",
        ) from exc
    finally:
        await bot.session.close()

    if not refunded:
        async with session_scope() as session:
            released = await release_stars_payment_refund(session, payment_id)
            if not released:
                raise HTTPException(
                    status_code=502,
                    detail="Telegram refund result is pending reconciliation",
                )
            await log_admin_action(
                session,
                admin,
                "refund_stars_payment_rejected",
                "payment",
                str(payment_id),
                {"status": "paid", "provider_result": False},
                request_ip(request),
            )
        raise HTTPException(status_code=502, detail="Telegram did not confirm the refund")

    async with session_scope() as session:
        confirmation = await mark_stars_payment_refunded(session, payment_id)
        if confirmation.payment is None:
            raise HTTPException(status_code=502, detail="Payment refund requires reconciliation")
        await log_admin_action(
            session,
            admin,
            "refund_stars_payment",
            "payment",
            str(payment_id),
            {"status": "refunded"},
            request_ip(request),
        )
    return {"status": "refunded", "payment_id": str(payment_id)}


@router.post("/payments/{payment_id}/reconcile-stars-refund")
async def reconcile_stars_refund(
    payment_id: UUID,
    payload: StarsRefundReconciliation,
    request: Request,
    admin: User = Depends(require_permission(Permission.MANAGE_PAYMENTS)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    async with session_scope() as session:
        if payload.outcome == "refunded":
            confirmation = await mark_stars_payment_refunded(session, payment_id)
            if confirmation.payment is None:
                raise HTTPException(status_code=409, detail="Refund cannot be finalized")
            status = "refunded"
        else:
            released = await release_stars_payment_refund(session, payment_id)
            if not released:
                raise HTTPException(status_code=409, detail="Refund cannot be released")
            status = "paid"
        await log_admin_action(
            session,
            admin,
            "reconcile_stars_refund",
            "payment",
            str(payment_id),
            {"provider_outcome": payload.outcome, "status": status},
            request_ip(request),
        )
    return {"status": status, "payment_id": str(payment_id)}


@router.get("/upload-jobs")
async def upload_jobs(
    limit: int = Query(default=50, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
    admin: User = Depends(require_permission(Permission.VIEW_UPLOAD_JOBS)),
) -> dict:
    async with session_scope() as session:
        statement = (
            select(UploadJob).order_by(UploadJob.created_at.desc()).limit(limit).offset(offset)
        )
        count_statement = select(func.count(UploadJob.id))
        if status:
            statement = statement.where(UploadJob.status == status)
            count_statement = count_statement.where(UploadJob.status == status)
        rows = (await session.scalars(statement)).all()
        total = await session.scalar(count_statement)
    return {
        "items": [
            {
                "id": str(job.id),
                "user_id": str(job.user_id),
                "status": job.status,
                "error_message": job.error_message,
                "retryable": upload_job_is_retryable(job),
                "created_at": job.created_at.isoformat(),
            }
            for job in rows
        ],
        "limit": limit,
        "offset": offset,
        "total": total or 0,
    }


@router.get("/errors")
async def publication_errors(
    limit: int = Query(default=50, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(require_permission(Permission.VIEW_ERROR_LOGS)),
) -> dict:
    async with session_scope() as session:
        statement = (
            select(UploadJob)
            .where(UploadJob.status == UploadStatus.FAILED.value)
            .order_by(UploadJob.created_at.desc())
        )
        rows = (await session.scalars(statement.limit(limit).offset(offset))).all()
        total = await session.scalar(
            select(func.count(UploadJob.id)).where(UploadJob.status == UploadStatus.FAILED.value)
        )
    return {
        "items": [
            {
                "id": str(job.id),
                "user_id": str(job.user_id),
                "error_message": job.error_message,
                "retryable": upload_job_is_retryable(job),
                "created_at": job.created_at.isoformat(),
            }
            for job in rows
        ],
        "limit": limit,
        "offset": offset,
        "total": total or 0,
    }


@router.post("/upload-jobs/{job_id}/retry")
async def retry_upload_job(
    job_id: UUID,
    request: Request,
    admin: User = Depends(require_permission(Permission.MANAGE_USERS)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    user_id: UUID
    async with session_scope() as session:
        job = await session.scalar(
            select(UploadJob).where(UploadJob.id == job_id).with_for_update()
        )
        if not job:
            raise HTTPException(status_code=404, detail="Upload job not found")
        if not upload_job_is_retryable(job):
            raise HTTPException(status_code=409, detail="Upload job is not safe to retry")
        if not Path(job.local_path).is_file():
            raise HTTPException(status_code=409, detail="Temporary video file is unavailable")

        previous_error = job.error_message
        job.status = UploadStatus.NEW.value
        job.error_message = None
        await record_upload_job_event(
            session,
            job,
            UploadStatus.NEW,
            "Retry requested by administrator",
        )
        await log_admin_action(
            session,
            admin,
            "retry_upload_job",
            "upload_job",
            str(job_id),
            {"previous_error": previous_error},
            request_ip(request),
        )
        user_id = job.user_id

    try:
        await enqueue_upload(str(job_id), str(user_id))
    except Exception as exc:
        async with session_scope() as session:
            job = await session.get(UploadJob, job_id, with_for_update=True)
            if job and job.status == UploadStatus.NEW.value:
                job.status = UploadStatus.FAILED.value
                job.error_message = "Temporary queue dispatch error."
                await record_upload_job_event(
                    session,
                    job,
                    UploadStatus.FAILED,
                    job.error_message,
                )
        raise HTTPException(status_code=503, detail="Queue dispatch failed") from exc
    return {"status": "queued"}


@router.get("/settings")
async def system_settings(
    admin: User = Depends(require_permission(Permission.MANAGE_SETTINGS)),
) -> list[dict]:
    async with session_scope() as session:
        rows = (await session.scalars(select(SystemSetting).order_by(SystemSetting.key))).all()
    return [
        {
            "key": row.key,
            "value": row.value,
            "value_type": row.value_type,
            "description": row.description,
            "is_editable": row.is_editable,
            "updated_at": row.updated_at.isoformat(),
        }
        for row in rows
        if not is_secret_like(row.key)
    ]


@router.put("/settings/{key}")
async def update_setting(
    key: str,
    payload: SettingUpdate,
    request: Request,
    admin: User = Depends(require_permission(Permission.MANAGE_SETTINGS)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    if is_secret_like(key):
        raise HTTPException(status_code=400, detail="Secret-like settings must remain in .env")
    async with session_scope() as session:
        row = await session.scalar(select(SystemSetting).where(SystemSetting.key == key))
        if row and not row.is_editable:
            raise HTTPException(status_code=409, detail="Setting is not editable")
        value_type = payload.value_type or (row.value_type if row else "string")
        try:
            validate_setting_value(payload.value, value_type)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not row:
            row = SystemSetting(
                key=key,
                value=payload.value,
                value_type=value_type,
                description=payload.description,
                is_editable=payload.is_editable if payload.is_editable is not None else True,
                updated_by=admin.id,
            )
            session.add(row)
        else:
            row.value = payload.value
            row.value_type = value_type
            if payload.description is not None:
                row.description = payload.description
            if payload.is_editable is not None:
                row.is_editable = payload.is_editable
            row.updated_by = admin.id
        await log_admin_action(
            session,
            admin,
            "update_setting",
            "system_setting",
            key,
            {"value_type": value_type, "is_editable": row.is_editable},
            request_ip(request),
        )
    return {"status": "updated"}


@router.get("/audit-actions")
async def audit_actions(
    action: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(require_permission(Permission.VIEW_ERROR_LOGS)),
) -> dict:
    async with session_scope() as session:
        statement = (
            select(AdminAction, User.telegram_id)
            .join(User, User.id == AdminAction.admin_user_id)
            .order_by(AdminAction.created_at.desc())
        )
        count_statement = select(func.count(AdminAction.id))
        if action:
            statement = statement.where(AdminAction.action == action)
            count_statement = count_statement.where(AdminAction.action == action)
        if target_type:
            statement = statement.where(AdminAction.target_type == target_type)
            count_statement = count_statement.where(AdminAction.target_type == target_type)
        rows = (await session.execute(statement.limit(limit).offset(offset))).all()
        total = await session.scalar(count_statement)
    return {
        "items": [
            {
                "id": str(audit.id),
                "admin_telegram_id": telegram_id,
                "action": audit.action,
                "target_type": audit.target_type,
                "target_id": audit.target_id,
                "metadata": audit.metadata_json,
                "ip_address": audit.ip_address,
                "created_at": audit.created_at.isoformat(),
            }
            for audit, telegram_id in rows
        ],
        "limit": limit,
        "offset": offset,
        "total": total or 0,
    }


@router.get("/configuration/export")
async def export_configuration(
    request: Request,
    admin: User = Depends(require_permission(Permission.MANAGE_SETTINGS)),
) -> dict:
    async with session_scope() as session:
        exported = await export_runtime_configuration(session)
        await log_admin_action(
            session,
            admin,
            "export_configuration",
            "configuration",
            ip_address=request_ip(request),
        )
    return exported


@router.post("/configuration/import")
async def import_configuration(
    payload: ConfigurationImport,
    request: Request,
    admin: User = Depends(require_permission(Permission.MANAGE_SETTINGS)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    try:
        validate_runtime_configuration(payload.payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    async with session_scope() as session:
        backup = await export_runtime_configuration(session)
        await import_runtime_configuration(session, payload.payload)
        await log_admin_action(
            session,
            admin,
            "import_configuration",
            "configuration",
            metadata={"backup": backup, "imported_version": payload.payload.get("version")},
            ip_address=request_ip(request),
        )
    return {"status": "imported"}


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    payload: RoleUpdate,
    request: Request,
    admin: User = Depends(require_permission(Permission.MANAGE_ROLES)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    async with session_scope() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        old_role = user.role
        user.role = payload.role.value
        user.is_admin = payload.role in {Role.ADMIN, Role.SUPER_ADMIN}
        await log_admin_action(
            session,
            admin,
            "update_user_role",
            "user",
            str(user_id),
            {"old_role": old_role, "new_role": payload.role.value},
            request_ip(request),
        )
    return {"status": "updated"}
