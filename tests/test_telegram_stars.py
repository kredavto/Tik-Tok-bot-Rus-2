import asyncio
import random

import pytest
from sqlalchemy import func, select

from app.core.plans import PlanCode
from app.db.models import Payment, Plan, Subscription
from app.db.session import (
    create_stars_payment,
    get_or_create_user,
    init_db,
    mark_stars_payment_paid,
    session_scope,
    validate_stars_checkout,
)


async def _create_stars_order(telegram_id: int) -> tuple[Payment, int]:
    await init_db()
    async with session_scope() as session:
        plan = await session.get(Plan, PlanCode.PRO.value)
        assert plan is not None
        plan.price_stars = 250
        user = await get_or_create_user(session, telegram_id, "stars_user")
        payment = await create_stars_payment(session, user.id, PlanCode.PRO.value)
        return payment, user.telegram_id


@pytest.mark.asyncio
async def test_stars_checkout_requires_exact_user_currency_and_amount() -> None:
    payment, telegram_id = await _create_stars_order(random.randint(1_100_000_000, 1_199_999_999))

    async with session_scope() as session:
        assert await validate_stars_checkout(session, payment.id, telegram_id, "XTR", 250)
        assert not await validate_stars_checkout(session, payment.id, telegram_id, "RUB", 250)
        assert not await validate_stars_checkout(session, payment.id, telegram_id, "XTR", 249)
        assert not await validate_stars_checkout(session, payment.id, telegram_id + 1, "XTR", 250)


@pytest.mark.asyncio
async def test_stars_confirmation_is_idempotent_under_concurrency() -> None:
    payment, telegram_id = await _create_stars_order(random.randint(1_200_000_000, 1_299_999_999))
    charge_id = f"stars-charge-{payment.id}"

    async def confirm() -> bool:
        async with session_scope() as session:
            result = await mark_stars_payment_paid(
                session,
                payment.id,
                telegram_id,
                "XTR",
                250,
                charge_id,
            )
            return result.activated

    activations = await asyncio.gather(confirm(), confirm())

    assert sorted(activations) == [False, True]
    async with session_scope() as session:
        stored = await session.get(Payment, payment.id)
        active_count = await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.user_id == payment.user_id,
                Subscription.status == "active",
            )
        )
    assert stored is not None
    assert stored.status == "paid"
    assert stored.provider == "telegram_stars"
    assert stored.currency == "XTR"
    assert stored.provider_charge_id == charge_id
    assert active_count == 1


@pytest.mark.asyncio
async def test_stars_confirmation_rejects_reused_charge_id() -> None:
    first, first_telegram_id = await _create_stars_order(
        random.randint(1_300_000_000, 1_399_999_999)
    )
    second, second_telegram_id = await _create_stars_order(
        random.randint(1_400_000_000, 1_499_999_999)
    )
    charge_id = f"stars-charge-{first.id}"

    async with session_scope() as session:
        accepted = await mark_stars_payment_paid(
            session, first.id, first_telegram_id, "XTR", 250, charge_id
        )
        assert accepted.activated

    async with session_scope() as session:
        rejected = await mark_stars_payment_paid(
            session, second.id, second_telegram_id, "XTR", 250, charge_id
        )
        assert rejected.payment is None

    async with session_scope() as session:
        second_payment = await session.get(Payment, second.id)
    assert second_payment is not None
    assert second_payment.status == "created"
