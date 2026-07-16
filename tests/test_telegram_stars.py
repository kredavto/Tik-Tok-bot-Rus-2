import asyncio
import random

import pytest
from sqlalchemy import func, select

from app.core.plans import PlanCode
from app.db.models import Payment, Plan, Subscription
from app.db.session import (
    active_plan_code,
    claim_stars_payment_refund,
    create_stars_payment,
    get_or_create_user,
    init_db,
    mark_stars_payment_paid,
    mark_stars_payment_refunded,
    mark_stars_payment_refunded_by_charge,
    release_stars_payment_refund,
    session_scope,
    validate_stars_checkout,
)


async def _create_stars_order(telegram_id: int) -> tuple[Payment, int]:
    await init_db()
    async with session_scope() as session:
        plan = await session.get(Plan, PlanCode.PRO.value)
        assert plan is not None
        assert plan.price_stars == 199
        user = await get_or_create_user(session, telegram_id, "stars_user")
        payment = await create_stars_payment(session, user.id, PlanCode.PRO.value)
        return payment, user.telegram_id


@pytest.mark.asyncio
async def test_stars_checkout_requires_exact_user_currency_and_amount() -> None:
    payment, telegram_id = await _create_stars_order(random.randint(1_100_000_000, 1_199_999_999))

    async with session_scope() as session:
        assert await validate_stars_checkout(session, payment.id, telegram_id, "XTR", 199)
        assert not await validate_stars_checkout(session, payment.id, telegram_id, "RUB", 199)
        assert not await validate_stars_checkout(session, payment.id, telegram_id, "XTR", 198)
        assert not await validate_stars_checkout(session, payment.id, telegram_id + 1, "XTR", 199)


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
                199,
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
            session, first.id, first_telegram_id, "XTR", 199, charge_id
        )
        assert accepted.activated

    async with session_scope() as session:
        rejected = await mark_stars_payment_paid(
            session, second.id, second_telegram_id, "XTR", 199, charge_id
        )
        assert rejected.payment is None

    async with session_scope() as session:
        second_payment = await session.get(Payment, second.id)
    assert second_payment is not None
    assert second_payment.status == "created"


@pytest.mark.asyncio
@pytest.mark.parametrize("terminal_status", ["refund_pending", "refunded"])
async def test_stars_confirmation_cannot_reactivate_refund_state(terminal_status: str) -> None:
    payment, telegram_id = await _create_stars_order(random.randint(1_500_000_000, 1_599_999_999))
    charge_id = f"stars-terminal-{payment.id}"
    async with session_scope() as session:
        paid = await mark_stars_payment_paid(
            session, payment.id, telegram_id, "XTR", 199, charge_id
        )
        assert paid.activated
    async with session_scope() as session:
        claim = await claim_stars_payment_refund(session, payment.id)
        assert claim.claimed
        if terminal_status == "refunded":
            refunded = await mark_stars_payment_refunded(session, payment.id)
            assert refunded.activated

    async with session_scope() as session:
        replay = await mark_stars_payment_paid(
            session, payment.id, telegram_id, "XTR", 199, charge_id
        )
        assert replay.payment is None
        assert not replay.activated
    async with session_scope() as session:
        stored = await session.get(Payment, payment.id)
        active_count = await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.user_id == payment.user_id,
                Subscription.status == "active",
            )
        )
    assert stored is not None
    assert stored.status == terminal_status
    assert active_count == 1


@pytest.mark.asyncio
async def test_stars_refund_is_idempotent_and_returns_active_plan_to_free() -> None:
    payment, telegram_id = await _create_stars_order(random.randint(1_600_000_000, 1_699_999_999))
    charge_id = f"stars-refund-{payment.id}"
    async with session_scope() as session:
        paid = await mark_stars_payment_paid(
            session, payment.id, telegram_id, "XTR", 199, charge_id
        )
        assert paid.activated

    async with session_scope() as session:
        claim = await claim_stars_payment_refund(session, payment.id)
        assert claim.claimed
        assert claim.telegram_id == telegram_id
    async with session_scope() as session:
        first = await mark_stars_payment_refunded(session, payment.id)
        assert first.activated
    async with session_scope() as session:
        second = await mark_stars_payment_refunded(session, payment.id)
        assert second.payment is not None
        assert not second.activated
        user = await get_or_create_user(session, telegram_id, "stars_user")
        assert await active_plan_code(session, user) == PlanCode.FREE.value

    async with session_scope() as session:
        stored = await session.get(Payment, payment.id)
    assert stored is not None
    assert stored.status == "refunded"


@pytest.mark.asyncio
async def test_stars_refund_claim_is_not_sent_twice_and_can_be_released() -> None:
    payment, telegram_id = await _create_stars_order(random.randint(1_700_000_000, 1_799_999_999))
    charge_id = f"stars-refund-pending-{payment.id}"
    async with session_scope() as session:
        paid = await mark_stars_payment_paid(
            session, payment.id, telegram_id, "XTR", 199, charge_id
        )
        assert paid.activated

    async with session_scope() as session:
        first = await claim_stars_payment_refund(session, payment.id)
        assert first.claimed
    async with session_scope() as session:
        duplicate = await claim_stars_payment_refund(session, payment.id)
        assert duplicate.payment is not None
        assert duplicate.payment.status == "refund_pending"
        assert not duplicate.claimed
        assert duplicate.telegram_id is None
        assert await release_stars_payment_refund(session, payment.id)
    async with session_scope() as session:
        retry = await claim_stars_payment_refund(session, payment.id)
        assert retry.claimed


@pytest.mark.asyncio
async def test_stars_refund_service_event_recovers_pending_local_state() -> None:
    payment, telegram_id = await _create_stars_order(random.randint(1_800_000_000, 1_899_999_999))
    charge_id = f"stars-refund-event-{payment.id}"
    async with session_scope() as session:
        paid = await mark_stars_payment_paid(
            session, payment.id, telegram_id, "XTR", 199, charge_id
        )
        assert paid.activated
    async with session_scope() as session:
        claim = await claim_stars_payment_refund(session, payment.id)
        assert claim.claimed

    async with session_scope() as session:
        first = await mark_stars_payment_refunded_by_charge(session, charge_id)
        assert first.activated
    async with session_scope() as session:
        duplicate = await mark_stars_payment_refunded_by_charge(session, charge_id)
        assert duplicate.payment is not None
        assert not duplicate.activated
