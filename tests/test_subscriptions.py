import random

import pytest

from app.core.plans import PlanCode
from app.db.session import (
    active_plan_code,
    can_upload_today,
    consume_daily_upload,
    create_paid_subscription,
    get_or_create_user,
    init_db,
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

