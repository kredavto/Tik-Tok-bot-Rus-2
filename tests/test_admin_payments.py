import random
from uuid import UUID

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import RefundStarPayment
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.api import admin as admin_api
from app.api import main as api_main
from app.core.plans import PlanCode
from app.db.models import AdminAction, Payment, Subscription, User
from app.db.session import (
    create_stars_payment,
    get_or_create_user,
    init_db,
    mark_stars_payment_paid,
    session_scope,
)
from app.security.rbac import Role


class FakeRedis:
    async def incr(self, _: str) -> int:
        return 1

    async def expire(self, _: str, __: int) -> None:
        return None

    async def aclose(self) -> None:
        return None


class FakeBotSession:
    async def close(self) -> None:
        return None


class FakeBot:
    calls = 0
    result: bool | Exception = True

    def __init__(self, token: str) -> None:
        assert token
        self.session = FakeBotSession()

    async def refund_star_payment(
        self,
        user_id: int,
        telegram_payment_charge_id: str,
    ) -> bool:
        assert user_id > 0
        assert telegram_payment_charge_id
        type(self).calls += 1
        if isinstance(type(self).result, Exception):
            raise type(self).result
        return type(self).result


async def _admin_and_user(role: Role = Role.ADMIN) -> tuple[User, User]:
    await init_db()
    async with session_scope() as session:
        admin = await get_or_create_user(
            session,
            random.randint(2_000_000_000, 2_099_999_999),
            "payments_admin",
        )
        admin.role = role.value
        admin.is_admin = role in {Role.ADMIN, Role.SUPER_ADMIN}
        user = await get_or_create_user(
            session,
            random.randint(2_100_000_000, 2_199_999_999),
            "payments_user",
        )
        return admin, user


def _configure_http(monkeypatch: pytest.MonkeyPatch, admin: User) -> None:
    async def override_admin() -> User:
        return admin

    api_main.app.dependency_overrides[admin_api.require_admin] = override_admin
    monkeypatch.setattr(api_main, "get_redis", lambda: FakeRedis())
    monkeypatch.setattr(admin_api.settings, "admin_csrf_token", "csrf-test-token")


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    api_main.app.dependency_overrides.clear()
    FakeBot.calls = 0
    FakeBot.result = True


@pytest.mark.asyncio
async def test_robokassa_order_endpoint_enforces_csrf_rbac_and_creates_audit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin, user = await _admin_and_user()
    _configure_http(monkeypatch, admin)
    monkeypatch.setattr(admin_api.settings, "robokassa_login", "merchant")
    monkeypatch.setattr(admin_api.settings, "robokassa_password1", "test-password")
    monkeypatch.setattr(admin_api.settings, "robokassa_test_mode", True)
    transport = ASGITransport(app=api_main.app)
    payload = {"telegram_user_id": user.telegram_id, "plan_id": "pro"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        denied = await client.post("/api/v1/admin/payments/robokassa/orders", json=payload)
        response = await client.post(
            "/api/v1/admin/payments/robokassa/orders",
            json=payload,
            headers={"X-CSRF-Token": "csrf-test-token"},
        )

    assert denied.status_code == 403
    assert response.status_code == 201
    body = response.json()
    assert body["currency"] == "RUB"
    assert body["test_mode"] is True
    assert "IsTest=1" in body["checkout_url"]
    assert "test-password" not in body["checkout_url"]
    async with session_scope() as session:
        payment = await session.get(Payment, UUID(body["payment_id"]))
        audit_count = await session.scalar(
            select(func.count(AdminAction.id)).where(
                AdminAction.action == "create_robokassa_order",
                AdminAction.target_id == body["payment_id"],
            )
        )
    assert payment is not None
    assert payment.provider == "robokassa"
    assert audit_count == 1


@pytest.mark.asyncio
async def test_support_role_cannot_create_robokassa_order(monkeypatch: pytest.MonkeyPatch) -> None:
    support, user = await _admin_and_user(Role.SUPPORT)
    _configure_http(monkeypatch, support)
    transport = ASGITransport(app=api_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/payments/robokassa/orders",
            json={"telegram_user_id": user.telegram_id, "plan_id": "pro"},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
    assert response.status_code == 403


async def _paid_stars_payment() -> tuple[User, User, Payment]:
    admin, user = await _admin_and_user()
    async with session_scope() as session:
        payment = await create_stars_payment(session, user.id, PlanCode.PRO.value)
        confirmation = await mark_stars_payment_paid(
            session,
            payment.id,
            user.telegram_id,
            "XTR",
            payment.amount_stars or 0,
            f"admin-refund-{payment.id}",
        )
        assert confirmation.activated
        return admin, user, payment


@pytest.mark.asyncio
async def test_stars_refund_endpoint_is_idempotent_and_returns_user_to_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin, user, payment = await _paid_stars_payment()
    _configure_http(monkeypatch, admin)
    monkeypatch.setattr(admin_api, "Bot", FakeBot)
    transport = ASGITransport(app=api_main.app)
    headers = {"X-CSRF-Token": "csrf-test-token"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        denied = await client.post(f"/api/v1/admin/payments/{payment.id}/refund-stars")
        first = await client.post(
            f"/api/v1/admin/payments/{payment.id}/refund-stars", headers=headers
        )
        second = await client.post(
            f"/api/v1/admin/payments/{payment.id}/refund-stars", headers=headers
        )

    assert denied.status_code == 403
    assert first.status_code == 200
    assert first.json()["status"] == "refunded"
    assert second.status_code == 200
    assert FakeBot.calls == 1
    async with session_scope() as session:
        stored = await session.get(Payment, payment.id)
        free_count = await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.user_id == user.id,
                Subscription.status == "active",
                Subscription.plan_id == PlanCode.FREE.value,
            )
        )
    assert stored is not None
    assert stored.status == "refunded"
    assert free_count == 1


@pytest.mark.asyncio
async def test_stars_refund_network_ambiguity_stays_pending_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin, _, payment = await _paid_stars_payment()
    _configure_http(monkeypatch, admin)
    FakeBot.result = RuntimeError("ambiguous network failure")
    monkeypatch.setattr(admin_api, "Bot", FakeBot)
    transport = ASGITransport(app=api_main.app)
    headers = {"X-CSRF-Token": "csrf-test-token"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post(
            f"/api/v1/admin/payments/{payment.id}/refund-stars", headers=headers
        )
        second = await client.post(
            f"/api/v1/admin/payments/{payment.id}/refund-stars", headers=headers
        )

    assert first.status_code == 502
    assert second.status_code == 200
    assert second.json()["status"] == "refund_pending"
    assert FakeBot.calls == 1
    async with session_scope() as session:
        stored = await session.get(Payment, payment.id)
    assert stored is not None
    assert stored.status == "refund_pending"


@pytest.mark.asyncio
async def test_stars_refund_definitive_rejection_restores_paid_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin, _, payment = await _paid_stars_payment()
    _configure_http(monkeypatch, admin)
    FakeBot.result = False
    monkeypatch.setattr(admin_api, "Bot", FakeBot)
    transport = ASGITransport(app=api_main.app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/admin/payments/{payment.id}/refund-stars",
            headers={"X-CSRF-Token": "csrf-test-token"},
        )

    assert response.status_code == 502
    assert FakeBot.calls == 1
    async with session_scope() as session:
        stored = await session.get(Payment, payment.id)
    assert stored is not None
    assert stored.status == "paid"


@pytest.mark.asyncio
async def test_stars_refund_definitive_exception_restores_paid_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin, _, payment = await _paid_stars_payment()
    _configure_http(monkeypatch, admin)
    FakeBot.result = TelegramBadRequest(
        RefundStarPayment(user_id=1, telegram_payment_charge_id="test-charge"),
        "provider rejected the refund",
    )
    monkeypatch.setattr(admin_api, "Bot", FakeBot)
    transport = ASGITransport(app=api_main.app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/admin/payments/{payment.id}/refund-stars",
            headers={"X-CSRF-Token": "csrf-test-token"},
        )

    assert response.status_code == 502
    async with session_scope() as session:
        stored = await session.get(Payment, payment.id)
    assert stored is not None
    assert stored.status == "paid"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("provider_outcome", "expected_status"),
    [("not_refunded", "paid"), ("refunded", "refunded")],
)
async def test_stars_refund_manual_reconciliation_is_audited(
    monkeypatch: pytest.MonkeyPatch,
    provider_outcome: str,
    expected_status: str,
) -> None:
    admin, _, payment = await _paid_stars_payment()
    async with session_scope() as session:
        claim = await admin_api.claim_stars_payment_refund(session, payment.id)
        assert claim.claimed
    _configure_http(monkeypatch, admin)
    transport = ASGITransport(app=api_main.app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/admin/payments/{payment.id}/reconcile-stars-refund",
            json={"outcome": provider_outcome},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == expected_status
    async with session_scope() as session:
        stored = await session.get(Payment, payment.id)
        audit_count = await session.scalar(
            select(func.count(AdminAction.id)).where(
                AdminAction.action == "reconcile_stars_refund",
                AdminAction.target_id == str(payment.id),
            )
        )
    assert stored is not None
    assert stored.status == expected_status
    assert audit_count == 1
