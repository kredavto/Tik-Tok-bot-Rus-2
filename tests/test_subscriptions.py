import asyncio
import random
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import func, select

from app.core.plans import PlanCode
from app.db.models import DailyUsage, Subscription, UploadJob, User
from app.db.session import (
    active_plan_code,
    can_upload_today,
    consume_daily_upload,
    create_paid_subscription,
    current_usage_date,
    expire_due_paid_subscriptions,
    get_or_create_user,
    init_db,
    mark_subscription_expiration_notified,
    record_accepted_upload,
    refund_failed_upload_usage,
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
async def test_unlimit_plan_never_exhausts_daily_limit() -> None:
    await init_db()
    telegram_id = random.randint(800_000_000, 899_999_999)
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "unlimit_user")
        await create_paid_subscription(session, user.id, PlanCode.UNLIMIT.value)
        for expected_count in range(1, 21):
            assert await consume_daily_upload(session, user) == (True, expected_count, 0)
        assert await can_upload_today(session, user) == (True, 20, 0)


@pytest.mark.asyncio
async def test_failed_tiktok_upload_refunds_usage_once() -> None:
    await init_db()
    telegram_id = random.randint(900_000_000, 999_999_999)
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "refund_user")
        job = UploadJob(
            user_id=user.id,
            telegram_file_id="telegram-file-id",
            local_path="/tmp/refund-video.mp4",
            usage_date=current_usage_date(),
        )
        session.add(job)
        await session.flush()
        await record_accepted_upload(session, user, job.usage_date)
        assert await can_upload_today(session, user) == (True, 1, 2)
        assert await refund_failed_upload_usage(session, job) is True
        assert await refund_failed_upload_usage(session, job) is False
        assert await can_upload_today(session, user) == (True, 0, 2)


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


@pytest.mark.asyncio
async def test_concurrent_registration_creates_one_user_and_subscription() -> None:
    await init_db()
    telegram_id = random.randint(500_000_000, 599_999_999)

    async def register() -> UUID:
        async with session_scope() as session:
            user = await get_or_create_user(session, telegram_id, "registration_race")
            return user.id

    user_ids = await asyncio.gather(*(register() for _ in range(4)))

    assert len(set(user_ids)) == 1
    async with session_scope() as session:
        user_count = await session.scalar(
            select(func.count(User.id)).where(User.telegram_id == telegram_id)
        )
        active_count = await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.user_id == user_ids[0],
                Subscription.status == "active",
            )
        )
    assert user_count == 1
    assert active_count == 1


@pytest.mark.asyncio
async def test_concurrent_first_usage_check_creates_one_counter() -> None:
    await init_db()
    telegram_id = random.randint(600_000_000, 699_999_999)
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "usage_race")
        user_id = user.id

    async def check_limit() -> tuple[bool, int, int]:
        async with session_scope() as session:
            user = await session.get(User, user_id)
            assert user is not None
            return await can_upload_today(session, user)

    results = await asyncio.gather(*(check_limit() for _ in range(4)))

    assert results == [(True, 0, 2)] * 4
    async with session_scope() as session:
        usage_count = await session.scalar(
            select(func.count(DailyUsage.id)).where(DailyUsage.user_id == user_id)
        )
    assert usage_count == 1
