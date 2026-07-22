import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.db.models import WebhookEvent
from app.db.session import claim_webhook_event, init_db, session_scope


@pytest.mark.asyncio
async def test_webhook_delivery_claim_is_atomic_under_concurrency() -> None:
    await init_db()
    external_id = str(uuid4())

    async def claim() -> bool:
        async with session_scope() as session:
            event = await claim_webhook_event(
                session,
                provider="telegram",
                event_type="update",
                external_id=external_id,
                payload={"update_id": external_id},
            )
            return event is not None

    claims = await asyncio.gather(claim(), claim())

    assert sorted(claims) == [False, True]
    async with session_scope() as session:
        count = await session.scalar(
            select(func.count(WebhookEvent.id)).where(
                WebhookEvent.deduplication_key == f"telegram:update:{external_id}"
            )
        )
    assert count == 1
