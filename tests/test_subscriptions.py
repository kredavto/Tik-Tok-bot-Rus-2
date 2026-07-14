import random
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.core.plans import PlanCode
from app.db.models import Subscription
from app.db.session import (
    active_plan_code,
    can_upload_today,
    consume_daily_upload,
    create_paid_subscription,
    expire_due_paid_subscriptions,
    get_or_create_user,
    init_db,
    mark_subscription_expiration_notified,
    session_scope,
)


@pytest.mark.asyncio
async def test_new_user_gets_free_plan() -> None:
    await init_db()
    telegram_id = random.randint(10_000_000, 99_999_999)
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "new_user")
        assert await active_plan_code(session, user) == PlanCode.FREE.value


@pytest.mark.asyncio
async def test_daily_limit_is_consumed_transactionally() -> None:
    await init_db()
    telegram_id = random.randint(100_000_000, 199_999_999)
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "limit_user")
        assert await can_upload_today(session, user) == (True, 0, 2)
        assert await consume_daily_upload(session, user) == (True, 1, 2)
        assert await consume_daily_upload(session, user) == (True, 2, 2)
        assert await consume_daily_upload(session, user) == (False, 2, 2)


@pytest.mark.asyncio
async def test_paid_subscription_overrides_free_plan() -> None:
    await init_db()
    telegram_id = random.randint(200_000_000, 299_999_999)
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "paid_user")
        await create_paid_subscription(session, user.id, PlanCode.PRO.value)
        assert await active_plan_code(session, user) == PlanCode.PRO.value
        assert await can_upload_today(session, user) == (True, 0, 5)
        active_count = await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.user_id == user.id,
                Subscription.status == "active",
            )
        )
        assert active_count == 1


@pytest.mark.asyncio
async def test_expired_paid_subscription_returns_to_free_once() -> None:
    await init_db()
    telegram_id = random.randint(300_000_000, 399_999_999)
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "expired_user")
        paid = await create_paid_subscription(session, user.id, PlanCode.PRO.value)
        paid.ends_at = datetime.now(UTC) - timedelta(minutes=1)
        paid_id = paid.id

    async with session_scope() as session:
        notices = await expire_due_paid_subscriptions(session, batch_size=10)
        assert [(notice.subscription_id, notice.telegram_id) for notice in notices] == [
            (paid_id, telegram_id)
        ]
        user = await get_or_create_user(session, telegram_id, "expired_user")
        assert await active_plan_code(session, user) == PlanCode.FREE.value
        assert await mark_subscription_expiration_notified(session, paid_id) is True
        assert await mark_subscription_expiration_notified(session, paid_id) is False

    async with session_scope() as session:
        assert await expire_due_paid_subscriptions(session, batch_size=10) == []


@pytest.mark.asyncio
async def test_paid_upgrade_does_not_emit_expiration_notice() -> None:
    await init_db()
    telegram_id = random.randint(400_000_000, 499_999_999)
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "upgrade_user")
        previous = await create_paid_subscription(session, user.id, PlanCode.PRO.value)
        await create_paid_subscription(session, user.id, PlanCode.BUSINESS.value)
        assert previous.expiration_notified_at is not None

    async with session_scope() as session:
        assert await expire_due_paid_subscriptions(session, batch_size=10) == []
