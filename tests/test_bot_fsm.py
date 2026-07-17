from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock, MagicMock
from uuid import uuid4

import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, Message

from app.bot import handlers
from app.bot.states import BotStates
from app.services.tiktok import TikTokCreatorInfo


class FakeState:
    def __init__(self, data: dict[str, object] | None = None) -> None:
        self.data = dict(data or {})
        self.current: State | None = None

    async def set_state(self, state: State) -> None:
        self.current = state

    async def update_data(
        self,
        data: dict[str, object] | None = None,
        **kwargs: object,
    ) -> dict[str, object]:
        self.data.update(data or {})
        self.data.update(kwargs)
        return self.data

    async def get_data(self) -> dict[str, object]:
        return dict(self.data)

    async def clear(self) -> None:
        self.data.clear()
        self.current = None


def make_message(text: str = "") -> MagicMock:
    message = MagicMock(spec=Message)
    message.text = text
    message.from_user = SimpleNamespace(id=12345, username="qa_user")
    message.answer = AsyncMock()
    return message


def make_callback(data: str) -> MagicMock:
    callback = MagicMock(spec=CallbackQuery)
    callback.data = data
    callback.from_user = SimpleNamespace(id=12345, username="qa_user")
    callback.message = make_message()
    callback.answer = AsyncMock()
    return callback


def configure_stars_checkout(
    monkeypatch: pytest.MonkeyPatch,
    *,
    price_rub: int = 0,
) -> tuple[object, object]:
    plan = SimpleNamespace(
        id="pro",
        title="PRO",
        is_active=True,
        price_rub=price_rub,
        price_stars=199,
        duration_days=30,
    )
    payment = SimpleNamespace(id=uuid4(), amount_stars=199)

    class FakeSession:
        async def get(self, _model: object, _key: str) -> object:
            return plan

    @asynccontextmanager
    async def fake_session_scope():
        yield FakeSession()

    async def fake_user(_session: object, _telegram_id: int, _username: str | None):
        return SimpleNamespace(id=uuid4())

    async def fake_payment(_session: object, _user_id: object, _plan_id: str):
        return payment

    monkeypatch.setattr(handlers, "session_scope", fake_session_scope)
    monkeypatch.setattr(handlers, "get_or_create_user", fake_user)
    monkeypatch.setattr(handlers, "create_stars_payment", fake_payment)
    return plan, payment


@pytest.mark.asyncio
async def test_upload_fsm_collects_creator_options(monkeypatch: pytest.MonkeyPatch) -> None:
    account_id = uuid4()
    creator = TikTokCreatorInfo(
        username="creator",
        nickname="Creator",
        privacy_level_options=("SELF_ONLY", "PUBLIC_TO_EVERYONE"),
        comment_disabled=False,
        duet_disabled=True,
        stitch_disabled=False,
        max_video_post_duration_sec=180,
    )

    async def load_creator_info(_telegram_id: int, _username: str | None):
        return account_id, creator

    monkeypatch.setattr(handlers, "_load_creator_info", load_creator_info)
    state = FakeState({"duration_sec": 30.0, "local_path": "/tmp/video.mp4"})

    description = make_message("Описание")
    await handlers.receive_description(description, state)  # type: ignore[arg-type]
    assert state.current == BotStates.VIDEO_HASHTAGS

    hashtags = make_message("#тест")
    await handlers.receive_hashtags(hashtags, state)  # type: ignore[arg-type]

    assert state.current == BotStates.VIDEO_PRIVACY
    assert state.data["tiktok_account_id"] == str(account_id)
    assert state.data["privacy_options"] == ["SELF_ONLY", "PUBLIC_TO_EVERYONE"]
    assert state.data["comment_available"] is True
    assert state.data["duet_available"] is False
    hashtags.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_upload_fsm_rejects_unavailable_privacy() -> None:
    state = FakeState({"privacy_options": ["SELF_ONLY"]})
    callback = make_callback("privacy:PUBLIC_TO_EVERYONE")

    await handlers.select_privacy(callback, state)  # type: ignore[arg-type]

    assert state.current is None
    callback.answer.assert_awaited_once_with(
        "Этот вариант недоступен для аккаунта.",
        show_alert=True,
    )


@pytest.mark.asyncio
async def test_private_upload_rejects_branded_content() -> None:
    state = FakeState({"privacy_level": "SELF_ONLY"})
    callback = make_callback("commercial:branded")

    await handlers.select_commercial_content(callback, state)  # type: ignore[arg-type]

    assert state.current is None
    assert "brand_content_toggle" not in state.data
    callback.answer.assert_awaited_once_with(
        "Платное партнерство недоступно для приватной публикации.",
        show_alert=True,
    )


@pytest.mark.asyncio
async def test_upload_fsm_reaches_confirmation() -> None:
    state = FakeState(
        {
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "creator_nickname": "Creator",
            "description": "Описание",
            "hashtags": "#тест",
            "allow_comment": True,
            "allow_duet": False,
            "allow_stitch": True,
        }
    )
    callback = make_callback("commercial:organic")

    await handlers.select_commercial_content(callback, state)  # type: ignore[arg-type]

    assert state.current == BotStates.CONFIRM_UPLOAD
    assert state.data["brand_content_toggle"] is False
    assert state.data["brand_organic_toggle"] is True
    callback.message.answer.assert_awaited_once()
    callback.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_cleans_pending_file_and_returns_to_main_menu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cleaned: list[str] = []

    async def cleanup(path: str) -> None:
        cleaned.append(path)

    monkeypatch.setattr(handlers, "cleanup_temp_file", cleanup)
    state = FakeState({"local_path": "/tmp/pending.mp4", "description": "draft"})
    message = make_message()

    await handlers.cancel_current_operation(message, state)  # type: ignore[arg-type]

    assert cleaned == ["/tmp/pending.mp4"]
    assert state.data == {}
    assert state.current == BotStates.MAIN_MENU
    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_stars_invoice_is_independent_from_rub_and_single_chat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, payment = configure_stars_checkout(monkeypatch, price_rub=0)
    callback = make_callback("buy:pro")
    bot = SimpleNamespace(send_invoice=AsyncMock())
    state = FakeState()

    await handlers.buy_callback(callback, bot, state)  # type: ignore[arg-type]

    assert state.current == BotStates.PAYMENT_WAIT
    call = bot.send_invoice.await_args.kwargs
    assert call["currency"] == "XTR"
    assert call["start_parameter"] == f"stars_{payment.id.hex}"
    assert "provider_token" not in call


@pytest.mark.asyncio
async def test_definitive_invoice_rejection_marks_payment_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, payment = configure_stars_checkout(monkeypatch)
    callback = make_callback("buy:pro")
    bot = SimpleNamespace(
        send_invoice=AsyncMock(side_effect=TelegramBadRequest(MagicMock(), "definitive rejection"))
    )
    mark_failed = AsyncMock(return_value=True)
    monkeypatch.setattr(handlers, "mark_stars_payment_failed", mark_failed)
    state = FakeState()

    await handlers.buy_callback(callback, bot, state)  # type: ignore[arg-type]

    assert state.current is None
    mark_failed.assert_awaited_once_with(ANY, payment.id)
    callback.answer.assert_awaited_once_with(handlers.messages.PAYMENT_ERROR, show_alert=True)


@pytest.mark.asyncio
async def test_ambiguous_invoice_delivery_remains_payable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_stars_checkout(monkeypatch)
    callback = make_callback("buy:pro")
    bot = SimpleNamespace(
        send_invoice=AsyncMock(side_effect=TelegramNetworkError(MagicMock(), "network failure"))
    )
    mark_failed = AsyncMock()
    monkeypatch.setattr(handlers, "mark_stars_payment_failed", mark_failed)
    state = FakeState()

    await handlers.buy_callback(callback, bot, state)  # type: ignore[arg-type]

    assert state.current is None
    mark_failed.assert_not_awaited()
    callback.answer.assert_awaited_once_with(handlers.messages.NETWORK_ERROR, show_alert=True)


@pytest.mark.asyncio
async def test_terms_command_keeps_payment_terms_accessible() -> None:
    message = make_message("/terms")

    await handlers.payment_terms(message)  # type: ignore[arg-type]

    message.answer.assert_awaited_once_with(handlers.messages.AGREEMENT)


def test_fsm_contains_all_specified_states() -> None:
    expected = {
        "START",
        "ACCEPT_TERMS",
        "CONNECT_TIKTOK",
        "MAIN_MENU",
        "UPLOAD_VIDEO",
        "VIDEO_DESCRIPTION",
        "VIDEO_HASHTAGS",
        "VIDEO_PRIVACY",
        "VIDEO_INTERACTIONS",
        "VIDEO_COMMERCIAL",
        "CONFIRM_UPLOAD",
        "PAYMENT_SELECT_PLAN",
        "PAYMENT_WAIT",
        "SETTINGS",
    }

    assert {state.state.rsplit(":", 1)[-1] for state in BotStates} == expected
