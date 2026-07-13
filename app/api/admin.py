from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.upload_status import UploadStatus
from app.db.models import AdminAction, Payment, Plan, Subscription, SystemSetting, UploadJob, User
from app.db.session import anonymize_user, get_or_create_user, session_scope
from app.security.rbac import Permission, Role, assert_permission, normalize_role
from app.services.configuration import (
    export_runtime_configuration,
    import_runtime_configuration,
    validate_runtime_configuration,
)

router = APIRouter(prefix="/admin", tags=["admin"])

MAX_PAGE_LIMIT = 200


class PlanUpdate(BaseModel):
    price_rub: int | None = Field(default=None, ge=0)
    daily_limit: int | None = Field(default=None, ge=0)
    duration_days: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class SettingUpdate(BaseModel):
    value: str


class RoleUpdate(BaseModel):
    role: Role


class ConfigurationImport(BaseModel):
    payload: dict


class Page(BaseModel):
    limit: int = Field(default=50, ge=1, le=MAX_PAGE_LIMIT)
    offset: int = Field(default=0, ge=0)


async def require_admin(
    authorization: str | None = Header(default=None),
    x_admin_telegram_id: int | None = Header(default=None),
) -> User:
    if not settings.admin_api_token:
        raise HTTPException(status_code=503, detail="Admin API is not configured")
    if authorization != f"Bearer {settings.admin_api_token}":
        raise HTTPException(status_code=401, detail="Invalid admin token")
    if x_admin_telegram_id is None:
        raise HTTPException(status_code=401, detail="Missing admin Telegram ID")

    allowed_ids = {item.strip() for item in settings.admin_telegram_ids.split(",") if item.strip()}
    if str(x_admin_telegram_id) not in allowed_ids:
        raise HTTPException(status_code=403, detail="Admin is not allowed")

    async with session_scope() as session:
        admin = await get_or_create_user(session, x_admin_telegram_id, None)
        admin.is_admin = True
        if normalize_role(admin.role) == Role.USER:
            admin.role = Role.SUPER_ADMIN.value
        admin_id = admin.id

    async with session_scope() as session:
        loaded_admin = await session.get(User, admin_id)
        if not loaded_admin:
            raise HTTPException(status_code=401, detail="Admin was not found")
        return loaded_admin


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
) -> None:
    session.add(
        AdminAction(
            admin_user_id=admin.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata_json=metadata,
        )
    )


@router.get("/dashboard")
async def dashboard(admin: User = Depends(require_permission(Permission.VIEW_STATS))) -> dict:
    async with session_scope() as session:
        users_total = await session.scalar(select(func.count(User.id)))
        payments_paid = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount_rub), 0)).where(Payment.status == "paid")
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
            select(func.coalesce(func.sum(Payment.amount_rub), 0)).where(Payment.status == "paid")
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


@router.post("/users/{user_id}/block")
async def block_user(
    user_id: UUID,
    admin: User = Depends(require_permission(Permission.MANAGE_USERS)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    async with session_scope() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_blocked = True
        await log_admin_action(session, admin, "block_user", "user", str(user_id))
    return {"status": "blocked"}


@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: UUID,
    admin: User = Depends(require_permission(Permission.MANAGE_USERS)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    async with session_scope() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_blocked = False
        await log_admin_action(session, admin, "unblock_user", "user", str(user_id))
    return {"status": "unblocked"}


@router.post("/users/{user_id}/anonymize")
async def anonymize_user_data(
    user_id: UUID,
    admin: User = Depends(require_permission(Permission.MANAGE_USERS)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    async with session_scope() as session:
        anonymized = await anonymize_user(session, user_id)
        if not anonymized:
            raise HTTPException(status_code=404, detail="User not found")
        await log_admin_action(session, admin, "anonymize_user", "user", str(user_id))
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
            session, admin, "update_plan", "plan", plan_id, payload.model_dump(exclude_none=True)
        )
    return {"status": "updated"}


@router.get("/payments")
async def payments(
    limit: int = Query(default=50, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(require_permission(Permission.VIEW_PAYMENTS)),
) -> dict:
    async with session_scope() as session:
        rows = (
            await session.scalars(
                select(Payment).order_by(Payment.created_at.desc()).limit(limit).offset(offset)
            )
        ).all()
        total = await session.scalar(select(func.count(Payment.id)))
    return {
        "items": [
            {
                "id": str(payment.id),
                "inv_id": payment.provider_invoice_id,
                "plan_id": payment.plan_id,
                "amount_rub": payment.amount_rub,
                "status": payment.status,
                "created_at": payment.created_at.isoformat(),
            }
            for payment in rows
        ],
        "limit": limit,
        "offset": offset,
        "total": total or 0,
    }


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
                "created_at": job.created_at.isoformat(),
            }
            for job in rows
        ],
        "limit": limit,
        "offset": offset,
        "total": total or 0,
    }


@router.get("/settings")
async def system_settings(
    admin: User = Depends(require_permission(Permission.MANAGE_SETTINGS)),
) -> list[dict]:
    async with session_scope() as session:
        rows = (await session.scalars(select(SystemSetting).order_by(SystemSetting.key))).all()
    return [
        {"key": row.key, "value": row.value, "updated_at": row.updated_at.isoformat()}
        for row in rows
    ]


@router.put("/settings/{key}")
async def update_setting(
    key: str,
    payload: SettingUpdate,
    admin: User = Depends(require_permission(Permission.MANAGE_SETTINGS)),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    async with session_scope() as session:
        row = await session.scalar(select(SystemSetting).where(SystemSetting.key == key))
        if not row:
            row = SystemSetting(key=key, value=payload.value)
            session.add(row)
        else:
            row.value = payload.value
        await log_admin_action(session, admin, "update_setting", "system_setting", key)
    return {"status": "updated"}


@router.get("/configuration/export")
async def export_configuration(
    admin: User = Depends(require_permission(Permission.MANAGE_SETTINGS)),
) -> dict:
    async with session_scope() as session:
        exported = await export_runtime_configuration(session)
        await log_admin_action(session, admin, "export_configuration", "configuration")
    return exported


@router.post("/configuration/import")
async def import_configuration(
    payload: ConfigurationImport,
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
        )
    return {"status": "imported"}


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    payload: RoleUpdate,
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
        )
    return {"status": "updated"}
