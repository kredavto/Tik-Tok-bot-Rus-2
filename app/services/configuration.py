from datetime import UTC, datetime
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Plan, SystemSetting

CONFIG_EXPORT_VERSION = 1
SECRET_LIKE_KEYS = ("SECRET", "PASSWORD", "TOKEN", "KEY")
SETTING_VALUE_TYPES = frozenset({"string", "int", "bool", "json"})
DEFAULT_SYSTEM_SETTINGS = (
    {
        "key": "intake_enabled",
        "value": "true",
        "value_type": "bool",
        "description": "Разрешить прием новых заданий публикации",
    },
    {
        "key": "video_retention_hours",
        "value": "24",
        "value_type": "int",
        "description": "Срок хранения временных видео, часы",
    },
    {
        "key": "log_retention_days",
        "value": "90",
        "value_type": "int",
        "description": "Срок хранения событий webhook и публикаций, дни",
    },
    {
        "key": "backup_retention_days",
        "value": "14",
        "value_type": "int",
        "description": "Срок хранения локальных резервных копий, дни",
    },
    {
        "key": "audit_log_retention_days",
        "value": "365",
        "value_type": "int",
        "description": "Срок хранения журнала действий администратора, дни",
    },
)


def is_secret_like(key: str) -> bool:
    normalized = key.upper()
    return any(part in normalized for part in SECRET_LIKE_KEYS)


def validate_setting_value(value: str, value_type: str) -> None:
    if value_type not in SETTING_VALUE_TYPES:
        raise ValueError(f"Unsupported setting value type: {value_type}")
    if value_type == "int":
        int(value)
    elif value_type == "bool" and value.lower() not in {"true", "false"}:
        raise ValueError("Boolean setting must be true or false")
    elif value_type == "json":
        json.loads(value)


async def seed_system_settings(session: AsyncSession) -> None:
    """Create operational defaults without overwriting administrator changes."""
    existing_keys = set(await session.scalars(select(SystemSetting.key)))
    for definition in DEFAULT_SYSTEM_SETTINGS:
        if definition["key"] not in existing_keys:
            session.add(SystemSetting(**definition))


async def get_int_setting(session: AsyncSession, key: str, fallback: int) -> int:
    setting = await session.scalar(select(SystemSetting).where(SystemSetting.key == key))
    if not setting:
        return fallback
    try:
        value = int(setting.value)
    except ValueError:
        return fallback
    return value if value >= 0 else fallback


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
                "price_stars": plan.price_stars,
                "daily_limit": plan.daily_limit,
                "duration_days": plan.duration_days,
                "is_active": plan.is_active,
            }
            for plan in plans
        ],
        "system_settings": [
            {
                "key": item.key,
                "value": item.value,
                "value_type": item.value_type,
                "description": item.description,
                "is_editable": item.is_editable,
            }
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
        validate_setting_value(
            str(item.get("value", "")),
            str(item.get("value_type", "string")),
        )
    for plan in payload.get("plans", []):
        if int(plan["price_rub"]) < 0:
            raise ValueError("Plan price must be non-negative")
        if plan.get("price_stars") is not None and int(plan["price_stars"]) <= 0:
            raise ValueError("Plan Stars price must be positive")
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
        price_stars = plan_payload.get("price_stars")
        plan.price_stars = int(price_stars) if price_stars is not None else None
        plan.daily_limit = int(plan_payload["daily_limit"])
        plan.duration_days = plan_payload.get("duration_days")
        plan.is_active = bool(plan_payload.get("is_active", True))

    for setting_payload in payload.get("system_settings", []):
        key = setting_payload["key"]
        setting = await session.scalar(select(SystemSetting).where(SystemSetting.key == key))
        value_type = str(setting_payload.get("value_type", "string"))
        validate_setting_value(str(setting_payload["value"]), value_type)
        if not setting:
            setting = SystemSetting(
                key=key,
                value=str(setting_payload["value"]),
                value_type=value_type,
                description=setting_payload.get("description"),
                is_editable=bool(setting_payload.get("is_editable", True)),
            )
            session.add(setting)
        else:
            if not setting.is_editable:
                raise ValueError(f"Setting is not editable: {key}")
            setting.value = str(setting_payload["value"])
            setting.value_type = value_type
            setting.description = setting_payload.get("description")
