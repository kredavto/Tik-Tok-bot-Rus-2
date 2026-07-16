import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
import random
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.api import main as api_main
from app.core.plans import PlanCode
from app.db.models import Payment, Subscription, User, WebhookEvent
from app.db.session import (
    active_plan_code,
    create_payment,
    create_stars_payment,
    get_or_create_user,
    init_db,
    mark_payment_paid,
    session_scope,
)
from app.services import robokassa
from app.workers import tasks


class FakeRedis:
    async def incr(self, _: str) -> int:
        return 1

    async def expire(self, _: str, __: int) -> None:
        return None

    async def aclose(self) -> None:
        return None


@pytest.mark.parametrize(
    ("algorithm", "expected"),
    [
        ("md5", "aca914e7bbfb0fe54ed3b42a1ce34e45"),  # pragma: allowlist secret
        (
            "sha256",
            "".join(
                (
                    "3cc87fe5ecb5519e",  # pragma: allowlist secret
                    "8bc67a253e014d5f",  # pragma: allowlist secret
                    "637c0e4238709d1c",  # pragma: allowlist secret
                    "df0a2c6b39241205",  # pragma: allowlist secret
                )
            ),
        ),
        (
            "sha512",
            "".join(
                (
                    "5c72bf409a73e2db",  # pragma: allowlist secret
                    "7109747d13a8f818",  # pragma: allowlist secret
                    "746306ec2f64e5ac",  # pragma: allowlist secret
                    "e64a3f93f9c92ff2",  # pragma: allowlist secret
                    "612edb873b159006",  # pragma: allowlist secret
                    "216ef1e7c6e80082",  # pragma: allowlist secret
                    "1b5698860f141901",  # pragma: allowlist secret
                    "9c724b81804a116c",  # pragma: allowlist secret
                )
            ),
        ),
    ],
)
def test_signature_matches_known_vectors(algorithm: str, expected: str) -> None:
    assert (
        robokassa._signature("merchant", "499.00", 123, "password1", algorithm=algorithm)
        == expected
    )


def test_validate_result_signature(monkeypatch) -> None:
    monkeypatch.setattr(robokassa.settings, "robokassa_password2", "secret")
    monkeypatch.setattr(robokassa.settings, "robokassa_hash_algorithm", "sha256")
    signature = robokassa._signature("199.00", "1001", "secret")
    assert robokassa.validate_result_signature("199.00", "1001", signature.upper())


def test_rejects_invalid_result_signature(monkeypatch) -> None:
    monkeypatch.setattr(robokassa.settings, "robokassa_password2", "secret")
    assert not robokassa.validate_result_signature("199", "1001", "bad")


def test_payment_url_uses_exact_amount_hash_and_test_flag(monkeypatch) -> None:
    monkeypatch.setattr(robokassa.settings, "robokassa_login", "merchant")
    monkeypatch.setattr(robokassa.settings, "robokassa_password1", "password1")
    monkeypatch.setattr(robokassa.settings, "robokassa_hash_algorithm", "md5")
    monkeypatch.setattr(robokassa.settings, "robokassa_test_mode", True)

    url = robokassa.build_payment_url(123, 499, "BUSINESS")
    query = parse_qs(urlparse(url).query)

    assert query["OutSum"] == ["499.00"]
    assert query["InvId"] == ["123"]
    assert query["IsTest"] == ["1"]
    assert query["SignatureValue"] == [
        "aca914e7bbfb0fe54ed3b42a1ce34e45"  # pragma: allowlist secret
    ]
    assert "password1" not in url


@pytest.mark.asyncio
async def test_robokassa_order_is_created_with_unique_invoice() -> None:
    await init_db()
    async with session_scope() as session:
        user = await get_or_create_user(session, 777000111, "robokassa_user")
        payment = await create_payment(session, user.id, PlanCode.PRO.value)

    assert payment.provider_invoice_id >= 1001
    assert payment.status == "created"


@pytest.mark.asyncio
async def test_result_url_confirmation_is_idempotent_under_concurrency() -> None:
    await init_db()
    telegram_id = random.randint(800_000_000, 899_999_999)
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "payment_race")
        payment = await create_payment(session, user.id, PlanCode.PRO.value)
        inv_id = payment.provider_invoice_id
        user_id = user.id

    async def confirm() -> bool:
        async with session_scope() as session:
            result = await mark_payment_paid(session, inv_id, "499.00")
            return result.activated

    activations = await asyncio.gather(confirm(), confirm())

    assert sorted(activations) == [False, True]
    async with session_scope() as session:
        stored_payment = await session.scalar(
            select(Payment).where(Payment.provider_invoice_id == inv_id)
        )
        active_count = await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.user_id == user_id,
                Subscription.status == "active",
            )
        )
        stored_user = await session.get(User, user_id)

    assert stored_payment is not None
    assert stored_payment.status == "paid"
    assert stored_payment.subscription_id is not None
    assert active_count == 1
    assert stored_user is not None
    async with session_scope() as session:
        assert await active_plan_code(session, stored_user) == PlanCode.PRO.value


@pytest.mark.asyncio
async def test_result_url_http_contract_validates_and_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await init_db()
    telegram_id = random.randint(1_000_000_000, 1_099_999_999)
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "payment_http")
        payment = await create_payment(session, user.id, PlanCode.PRO.value)
        inv_id = payment.provider_invoice_id
        user_id = user.id

    signing_value = "result" + "-url-credential"
    monkeypatch.setattr(robokassa.settings, "robokassa_password2", signing_value)
    monkeypatch.setattr(robokassa.settings, "robokassa_hash_algorithm", "sha256")
    monkeypatch.setattr(api_main, "get_redis", lambda: FakeRedis())

    def failed_enqueue(_: str) -> None:
        raise RuntimeError("notification broker unavailable")

    monkeypatch.setattr(api_main.notify_payment_success, "send", failed_enqueue)
    out_sum = "499.00"
    signature = robokassa._signature(out_sum, str(inv_id), signing_value)
    payload = {
        "OutSum": out_sum,
        "InvId": str(inv_id),
        "SignatureValue": signature,
        "OutCurrLabel": "RUB",
    }
    transport = ASGITransport(app=api_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post("/api/v1/payments/robokassa/result", data=payload)
        duplicate = await client.post("/api/v1/payments/robokassa/result", data=payload)
        invalid = await client.post(
            "/api/v1/payments/robokassa/result",
            data={**payload, "SignatureValue": "invalid"},
        )

    assert first.status_code == 200
    assert first.text == f"OK{inv_id}"
    assert duplicate.status_code == 200
    assert duplicate.text == f"OK{inv_id}"
    assert invalid.status_code == 400
    async with session_scope() as session:
        stored = await session.scalar(select(Payment).where(Payment.provider_invoice_id == inv_id))
        active_count = await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.user_id == user_id,
                Subscription.status == "active",
            )
        )
        pending_notification_count = await session.scalar(
            select(func.count(WebhookEvent.id)).where(
                WebhookEvent.provider == "internal",
                WebhookEvent.event_type == "payment_success_notification",
                WebhookEvent.status == "pending",
                WebhookEvent.external_id == str(payment.id),
            )
        )
    assert stored is not None
    assert stored.status == "paid"
    assert active_count == 1
    assert pending_notification_count == 1


@pytest.mark.asyncio
async def test_payment_notification_outbox_is_delivered_idempotently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await init_db()
    telegram_id = random.randint(1_100_000_000, 1_199_999_999)
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "payment_notification")
        payment = await create_payment(session, user.id, PlanCode.PRO.value)
        confirmation = await mark_payment_paid(session, payment.provider_invoice_id, "499.00")
        event_id = confirmation.notification_event_id
    assert event_id is not None

    @asynccontextmanager
    async def acquired_lock(_: str):
        yield True

    sent_messages: list[tuple[int, str]] = []

    class FakeBotSession:
        async def close(self) -> None:
            return None

    class FakeBot:
        def __init__(self, token: str) -> None:
            assert token
            self.session = FakeBotSession()

        async def send_message(self, target: int, message: str) -> None:
            sent_messages.append((target, message))

    monkeypatch.setattr(tasks, "payment_notification_lock", acquired_lock)
    monkeypatch.setattr(tasks, "Bot", FakeBot)
    monkeypatch.setattr(tasks.settings, "bot_token", "12345678" + ":" + "A" * 35)

    await tasks._notify_payment_success(str(event_id))
    await tasks._notify_payment_success(str(event_id))

    async with session_scope() as session:
        event = await session.get(WebhookEvent, event_id)
    assert event is not None
    assert event.status == "processed"
    assert len(sent_messages) == 1
    assert sent_messages[0][0] == telegram_id


@pytest.mark.asyncio
async def test_retention_preserves_pending_payment_notification(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    await init_db()
    telegram_id = random.randint(1_200_000_000, 1_299_999_999)
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "payment_retention")
        payment = await create_payment(session, user.id, PlanCode.PRO.value)
        confirmation = await mark_payment_paid(session, payment.provider_invoice_id, "499.00")
        pending_event_id = confirmation.notification_event_id
        assert pending_event_id is not None
        pending_event = await session.get(WebhookEvent, pending_event_id)
        assert pending_event is not None
        pending_event.created_at = datetime.now(UTC) - timedelta(days=2)
        terminal_event = WebhookEvent(
            provider="internal",
            event_type="payment_success_notification",
            external_id="terminal-event",
            payload={"payment_id": str(payment.id)},
            status="processed",
            created_at=datetime.now(UTC) - timedelta(days=2),
            processed_at=datetime.now(UTC) - timedelta(days=2),
        )
        session.add(terminal_event)
        await session.flush()
        terminal_event_id = terminal_event.id

    async def zero_retention(*_: object) -> int:
        return 0

    monkeypatch.setattr(tasks, "get_int_setting", zero_retention)
    monkeypatch.setattr(tasks.settings, "backup_dir", str(tmp_path))

    await tasks._cleanup_retention()

    async with session_scope() as session:
        pending_event = await session.get(WebhookEvent, pending_event_id)
        terminal_event = await session.get(WebhookEvent, terminal_event_id)
    assert pending_event is not None
    assert pending_event.status == "pending"
    assert terminal_event is None


@pytest.mark.asyncio
@pytest.mark.parametrize("out_sum", ["498.99", "not-a-number"])
async def test_result_url_rejects_invalid_amount(out_sum: str) -> None:
    await init_db()
    telegram_id = random.randint(900_000_000, 999_999_999)
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "payment_amount")
        payment = await create_payment(session, user.id, PlanCode.PRO.value)
        inv_id = payment.provider_invoice_id
        user_id = user.id

    async with session_scope() as session:
        confirmation = await mark_payment_paid(session, inv_id, out_sum)
        assert confirmation.activated is False
        assert confirmation.payment is not None
        assert confirmation.payment.status == "failed"

    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "payment_amount")
        assert user.id == user_id
        assert await active_plan_code(session, user) == PlanCode.FREE.value


@pytest.mark.asyncio
async def test_result_url_rejects_non_robokassa_payment() -> None:
    await init_db()
    async with session_scope() as session:
        user = await get_or_create_user(
            session, random.randint(1_500_000_000, 1_599_999_999), "wrong_provider"
        )
        payment = await create_stars_payment(session, user.id, PlanCode.PRO.value)
        inv_id = payment.provider_invoice_id

    async with session_scope() as session:
        confirmation = await mark_payment_paid(session, inv_id, "499.00")

    assert confirmation.payment is None
    assert confirmation.activated is False
