import pytest

from app.core.plans import PlanCode
from app.db.session import create_payment, get_or_create_user, init_db, session_scope
from app.services import robokassa


def test_validate_result_signature(monkeypatch) -> None:
    monkeypatch.setattr(robokassa.settings, "robokassa_password2", "secret")
    signature = robokassa._signature("199", "1001", "secret")
    assert robokassa.validate_result_signature("199", "1001", signature)


def test_rejects_invalid_result_signature(monkeypatch) -> None:
    monkeypatch.setattr(robokassa.settings, "robokassa_password2", "secret")
    assert not robokassa.validate_result_signature("199", "1001", "bad")


@pytest.mark.asyncio
async def test_robokassa_order_is_created_with_unique_invoice() -> None:
    await init_db()
    async with session_scope() as session:
        user = await get_or_create_user(session, 777000111, "robokassa_user")
        payment = await create_payment(session, user.id, PlanCode.PRO.value)

    assert payment.provider_invoice_id >= 1001
    assert payment.status == "created"
