from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Plan, SystemSetting

CONFIG_EXPORT_VERSION = 1
SECRET_LIKE_KEYS = ("SECRET", "PASSWORD", "TOKEN", "KEY")


def is_secret_like(key: str) -> bool:
    normalized = key.upper()
    return any(part in normalized for part in SECRET_LIKE_KEYS)


async def export_runtime_configuration(session: AsyncSession) -> dict[str, Any]:
    plans = (await session.scalars(select(Plan).order_by(Plan.id))).all()
    settings = (await session.scalars(select(SystemSetting).order_by(SystemSetting.key))).all()
    return {
        "version": CONFIG_EXPORT_VERSION,
        "exported_at": datetime.now(UTC).isoformat(),
        "plans": [
            {
                "id": plan.id,
                "title": plan.title,
                "price_rub": plan.price_rub,
                "daily_limit": plan.daily_limit,
                "duration_days": plan.duration_days,
                "is_active": plan.is_active,
            }
            for plan in plans
        ],
        "system_settings": [
            {"key": item.key, "value": item.value}
            for item in settings
            if not is_secret_like(item.key)
        ],
    }


def validate_runtime_configuration(payload: dict[str, Any]) -> None:
    if payload.get("version") != CONFIG_EXPORT_VERSION:
        raise ValueError("Unsupported configuration version")
    for item in payload.get("system_settings", []):
        key = str(item.get("key", ""))
        if not key or is_secret_like(key):
            raise ValueError(f"Secret or invalid setting cannot be imported: {key}")
    for plan in payload.get("plans", []):
        if int(plan["price_rub"]) < 0:
            raise ValueError("Plan price must be non-negative")
        if int(plan["daily_limit"]) < 0:
            raise ValueError("Plan daily limit must be non-negative")


async def import_runtime_configuration(session: AsyncSession, payload: dict[str, Any]) -> None:
    validate_runtime_configuration(payload)
    for plan_payload in payload.get("plans", []):
        plan = await session.get(Plan, plan_payload["id"])
        if not plan:
            plan = Plan(id=plan_payload["id"], title=plan_payload["title"])
            session.add(plan)
        plan.title = plan_payload["title"]
        plan.price_rub = int(plan_payload["price_rub"])
        plan.daily_limit = int(plan_payload["daily_limit"])
        plan.duration_days = plan_payload.get("duration_days")
        plan.is_active = bool(plan_payload.get("is_active", True))

    for setting_payload in payload.get("system_settings", []):
        key = setting_payload["key"]
        setting = await session.scalar(select(SystemSetting).where(SystemSetting.key == key))
        if not setting:
            setting = SystemSetting(key=key, value=str(setting_payload["value"]))
            session.add(setting)
        else:
            setting.value = str(setting_payload["value"])
