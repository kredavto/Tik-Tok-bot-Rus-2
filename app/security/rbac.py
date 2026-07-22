from enum import StrEnum

from fastapi import HTTPException

from app.db.models import User


class Role(StrEnum):
    USER = "USER"
    SUPPORT = "SUPPORT"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class Permission(StrEnum):
    VIEW_OWN_PROFILE = "VIEW_OWN_PROFILE"
    UPLOAD_VIDEO = "UPLOAD_VIDEO"
    CONNECT_TIKTOK = "CONNECT_TIKTOK"
    BUY_SUBSCRIPTION = "BUY_SUBSCRIPTION"
    VIEW_STATS = "VIEW_STATS"
    VIEW_USERS = "VIEW_USERS"
    MANAGE_USERS = "MANAGE_USERS"
    VIEW_PAYMENTS = "VIEW_PAYMENTS"
    MANAGE_PAYMENTS = "MANAGE_PAYMENTS"
    VIEW_UPLOAD_JOBS = "VIEW_UPLOAD_JOBS"
    VIEW_ERROR_LOGS = "VIEW_ERROR_LOGS"
    MANAGE_PLANS = "MANAGE_PLANS"
    MANAGE_SETTINGS = "MANAGE_SETTINGS"
    MANAGE_ROLES = "MANAGE_ROLES"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.USER: {
        Permission.VIEW_OWN_PROFILE,
        Permission.UPLOAD_VIDEO,
        Permission.CONNECT_TIKTOK,
        Permission.BUY_SUBSCRIPTION,
    },
    Role.SUPPORT: {
        Permission.VIEW_STATS,
        Permission.VIEW_USERS,
        Permission.VIEW_PAYMENTS,
        Permission.VIEW_UPLOAD_JOBS,
        Permission.VIEW_ERROR_LOGS,
    },
    Role.ADMIN: {
        Permission.VIEW_STATS,
        Permission.VIEW_USERS,
        Permission.MANAGE_USERS,
        Permission.VIEW_PAYMENTS,
        Permission.MANAGE_PAYMENTS,
        Permission.VIEW_UPLOAD_JOBS,
        Permission.VIEW_ERROR_LOGS,
        Permission.MANAGE_PLANS,
    },
    Role.SUPER_ADMIN: set(Permission),
}


def normalize_role(value: str | None) -> Role:
    """Return a valid role, falling back to USER for unknown values."""
    try:
        return Role((value or Role.USER.value).upper())
    except ValueError:
        return Role.USER


def has_permission(role: str | Role, permission: Permission) -> bool:
    """Check whether a role grants a server-side permission."""
    normalized = role if isinstance(role, Role) else normalize_role(role)
    return permission in ROLE_PERMISSIONS[normalized]


def assert_permission(user: User, permission: Permission) -> None:
    """Raise an HTTP 403 error when a user lacks a required permission."""
    if not has_permission(user.role, permission):
        raise HTTPException(status_code=403, detail=f"Permission required: {permission.value}")
