from app.security.rbac import Permission, Role, has_permission, normalize_role


def test_support_has_read_only_admin_permissions() -> None:
    assert has_permission(Role.SUPPORT, Permission.VIEW_USERS)
    assert has_permission(Role.SUPPORT, Permission.VIEW_PAYMENTS)
    assert not has_permission(Role.SUPPORT, Permission.MANAGE_USERS)
    assert not has_permission(Role.SUPPORT, Permission.MANAGE_SETTINGS)


def test_admin_can_manage_users_and_plans_but_not_settings() -> None:
    assert has_permission(Role.ADMIN, Permission.MANAGE_USERS)
    assert has_permission(Role.ADMIN, Permission.MANAGE_PLANS)
    assert not has_permission(Role.ADMIN, Permission.MANAGE_SETTINGS)


def test_super_admin_has_all_permissions() -> None:
    for permission in Permission:
        assert has_permission(Role.SUPER_ADMIN, permission)


def test_unknown_role_falls_back_to_user() -> None:
    assert normalize_role("unknown") == Role.USER
    assert has_permission("unknown", Permission.UPLOAD_VIDEO)
    assert not has_permission("unknown", Permission.VIEW_USERS)
