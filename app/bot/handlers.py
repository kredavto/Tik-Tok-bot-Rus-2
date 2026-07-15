import logging
from urllib.parse import urlencode
from uuid import UUID

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from sqlalchemy import select

from app.bot import messages
from app.bot.keyboards import (
    BTN_CONNECT_TIKTOK,
    BTN_CANCEL,
    BTN_HELP,
    BTN_HISTORY,
    BTN_SETTINGS,
    BTN_STATUS,
    BTN_TARIFFS,
    BTN_UPLOAD,
    PRIVACY_LABELS,
    agreement_keyboard,
    commercial_content_keyboard,
    interactions_keyboard,
    main_menu,
    privacy_keyboard,
    settings_keyboard,
    tariffs_menu,
    upload_confirmation_keyboard,
)
from app.bot.states import BotStates
from app.bot.storage import save_telegram_video
from app.core.config import settings
from app.core.redis import create_oauth_state, enqueue_upload, user_limit_lock
from app.db.models import Plan
from app.db.session import (
    accept_agreement,
    active_plan_code,
    can_upload_today,
    create_stars_payment,
    create_upload_job,
    get_or_create_user,
    get_primary_tiktok_account,
    get_plan_record,
    has_tiktok_account,
    is_intake_enabled,
    list_recent_upload_jobs,
    mark_stars_payment_paid,
    revoke_tiktok_accounts,
    session_scope,
    upsert_tiktok_account,
    validate_stars_checkout,
)
from app.security.crypto import decrypt_secret
from app.services.tiktok import (
    TikTokApiError,
    TikTokClient,
    TikTokCreatorInfo,
    token_is_expired,
)
from app.services.video import cleanup_temp_file, inspect_video

router = Router()
logger = logging.getLogger(__name__)

SUPPORTED_VIDEO_MIME_TYPES = {"video/mp4", "video/quicktime", "video/webm"}


@router.message(Command("start"))
async def start(message: Message, state: FSMContext) -> None:
    assert message.from_user is not None
    async with session_scope() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        accepted = user.agreement_accepted_at is not None

    if not accepted:
        await state.set_state(BotStates.ACCEPT_TERMS)
        await message.answer(messages.WELCOME)
        await message.answer(messages.AGREEMENT, reply_markup=agreement_keyboard())
        return

    await state.set_state(BotStates.MAIN_MENU)
    await message.answer(messages.MAIN_MENU, reply_markup=main_menu())


@router.callback_query(BotStates.ACCEPT_TERMS, F.data == "agreement:accept")
async def accept_agreement_callback(callback: CallbackQuery, state: FSMContext) -> None:
    assert isinstance(callback.message, Message)
    async with session_scope() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        await accept_agreement(session, user)

    await state.set_state(BotStates.CONNECT_TIKTOK)
    await callback.message.answer(
        "Соглашение принято. Теперь можно подключить TikTok через официальный OAuth 2.0.",
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.message(Command("tariffs"))
@router.message(F.text == BTN_TARIFFS)
async def tariffs(message: Message, state: FSMContext) -> None:
    async with session_scope() as session:
        plans = list(
            (
                await session.scalars(
                    select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.price_rub)
                )
            ).all()
        )
    await state.set_state(BotStates.PAYMENT_SELECT_PLAN)
    keyboard_plans = [(plan.id, plan.title, plan.price_rub, plan.price_stars) for plan in plans]
    await message.answer(_tariff_text(plans), reply_markup=tariffs_menu(keyboard_plans))


@router.message(Command("status"))
@router.message(F.text == BTN_STATUS)
async def status(message: Message) -> None:
    assert message.from_user is not None
    await message.answer(await _status_text(message.from_user.id, message.from_user.username))


@router.message(F.text == BTN_CONNECT_TIKTOK)
async def connect_tiktok(message: Message, state: FSMContext) -> None:
    assert message.from_user is not None
    await state.set_state(BotStates.CONNECT_TIKTOK)
    if not settings.tiktok_client_key or not settings.tiktok_redirect_uri:
        await message.answer("TikTok OAuth еще не настроен администратором.")
        return

    async with session_scope() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        oauth_state = await create_oauth_state(str(user.id))

    await state.set_state(BotStates.MAIN_MENU)
    start_url = (
        f"{settings.public_base_url.rstrip('/')}/api/v1/oauth/tiktok/start?"
        f"{urlencode({'state': oauth_state})}"
    )
    await message.answer(f"Подключите TikTok через официальный OAuth 2.0:\n{start_url}")


@router.message(F.text == BTN_UPLOAD)
async def start_upload(message: Message, state: FSMContext) -> None:
    assert message.from_user is not None
    async with session_scope() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        intake_enabled = await is_intake_enabled(session)
        connected = await has_tiktok_account(session, user.id)
        allowed, used, limit = await can_upload_today(session, user)

    if not intake_enabled:
        await message.answer(messages.INTAKE_DISABLED)
        return
    if not connected:
        await message.answer(messages.TIKTOK_NOT_CONNECTED)
        return
    if not allowed:
        await message.answer(messages.LIMIT_EXCEEDED.format(used=used, limit=limit))
        return

    await state.set_state(BotStates.UPLOAD_VIDEO)
    await message.answer(messages.SEND_VIDEO)


@router.message(BotStates.UPLOAD_VIDEO, F.video | F.document)
async def receive_video(message: Message, bot: Bot, state: FSMContext) -> None:
    assert message.from_user is not None
    file_id = None
    file_size = None
    mime_type = None
    is_video_document = (
        message.document
        and message.document.mime_type
        and message.document.mime_type.startswith("video/")
    )

    if message.video:
        file_id = message.video.file_id
        file_size = message.video.file_size
        mime_type = message.video.mime_type
    elif message.document is not None and is_video_document:
        file_id = message.document.file_id
        file_size = message.document.file_size
        mime_type = message.document.mime_type

    if not file_id or (mime_type and mime_type not in SUPPORTED_VIDEO_MIME_TYPES):
        await message.answer(messages.INVALID_VIDEO)
        return
    if file_size and file_size > settings.max_video_size_mb * 1024 * 1024:
        await message.answer(messages.VIDEO_TOO_LARGE.format(max_mb=settings.max_video_size_mb))
        return

    async with session_scope() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        local_path = await save_telegram_video(bot, file_id, user.id)

    inspection = await inspect_video(str(local_path))
    if not inspection.is_valid:
        await cleanup_temp_file(str(local_path))
        await message.answer(messages.INVALID_VIDEO)
        return

    await state.update_data(
        file_id=file_id,
        local_path=str(local_path),
        duration_sec=inspection.duration_sec,
    )
    await state.set_state(BotStates.VIDEO_DESCRIPTION)
    await message.answer(messages.ASK_DESCRIPTION)


@router.message(BotStates.UPLOAD_VIDEO)
async def receive_invalid_video(message: Message) -> None:
    await message.answer(messages.INVALID_VIDEO)


@router.message(BotStates.VIDEO_DESCRIPTION)
async def receive_description(message: Message, state: FSMContext) -> None:
    description = message.text or ""
    await state.update_data(description=description)
    await state.set_state(BotStates.VIDEO_HASHTAGS)
    await message.answer(messages.ASK_HASHTAGS)


@router.message(BotStates.VIDEO_HASHTAGS)
async def receive_hashtags(message: Message, state: FSMContext) -> None:
    assert message.from_user is not None
    hashtags = message.text or ""
    await state.update_data(hashtags=hashtags)
    data = await state.get_data()
    try:
        account_id, creator = await _load_creator_info(
            message.from_user.id,
            message.from_user.username,
        )
    except Exception:
        logger.exception("TikTok creator info request failed")
        await _discard_pending_upload(state)
        await state.set_state(BotStates.MAIN_MENU)
        await message.answer(messages.CREATOR_INFO_ERROR, reply_markup=main_menu())
        return

    duration_sec = float(data.get("duration_sec") or 0)
    if creator.max_video_post_duration_sec and duration_sec > creator.max_video_post_duration_sec:
        await _discard_pending_upload(state)
        await state.set_state(BotStates.MAIN_MENU)
        await message.answer(
            messages.CREATOR_DURATION_EXCEEDED.format(
                max_sec=creator.max_video_post_duration_sec,
            ),
            reply_markup=main_menu(),
        )
        return
    if not creator.privacy_level_options:
        await _discard_pending_upload(state)
        await state.set_state(BotStates.MAIN_MENU)
        await message.answer(messages.CREATOR_INFO_ERROR, reply_markup=main_menu())
        return

    await state.update_data(
        tiktok_account_id=str(account_id),
        creator_nickname=creator.nickname or creator.username,
        privacy_options=list(creator.privacy_level_options),
        comment_available=not creator.comment_disabled,
        duet_available=not creator.duet_disabled,
        stitch_available=not creator.stitch_disabled,
        allow_comment=False,
        allow_duet=False,
        allow_stitch=False,
    )
    await state.set_state(BotStates.VIDEO_PRIVACY)
    await message.answer(
        messages.ASK_PRIVACY.format(nickname=creator.nickname or creator.username),
        reply_markup=privacy_keyboard(list(creator.privacy_level_options)),
    )


@router.callback_query(BotStates.VIDEO_PRIVACY, F.data.startswith("privacy:"))
async def select_privacy(callback: CallbackQuery, state: FSMContext) -> None:
    assert callback.data is not None
    assert isinstance(callback.message, Message)
    privacy_level = callback.data.split(":", 1)[1]
    data = await state.get_data()
    if privacy_level not in data.get("privacy_options", []):
        await callback.answer("Этот вариант недоступен для аккаунта.", show_alert=True)
        return
    await state.update_data(privacy_level=privacy_level)
    await state.set_state(BotStates.VIDEO_INTERACTIONS)
    data = await state.get_data()
    await callback.message.answer(
        messages.ASK_INTERACTIONS,
        reply_markup=_interactions_markup(data),
    )
    await callback.answer()


@router.callback_query(BotStates.VIDEO_INTERACTIONS, F.data == "interaction:unavailable")
async def unavailable_interaction(callback: CallbackQuery) -> None:
    await callback.answer("Эта настройка отключена в аккаунте TikTok.", show_alert=True)


@router.callback_query(BotStates.VIDEO_INTERACTIONS, F.data.startswith("interaction:"))
async def select_interactions(callback: CallbackQuery, state: FSMContext) -> None:
    assert callback.data is not None
    assert isinstance(callback.message, Message)
    action = callback.data.split(":", 1)[1]
    data = await state.get_data()
    if action == "continue":
        await state.set_state(BotStates.VIDEO_COMMERCIAL)
        allow_branded = data.get("privacy_level") != "SELF_ONLY"
        await callback.message.answer(
            messages.ASK_COMMERCIAL,
            reply_markup=commercial_content_keyboard(allow_branded),
        )
        await callback.answer()
        return

    field = {
        "comment": "allow_comment",
        "duet": "allow_duet",
        "stitch": "allow_stitch",
    }.get(action)
    availability_field = {
        "comment": "comment_available",
        "duet": "duet_available",
        "stitch": "stitch_available",
    }.get(action)
    if not field or not availability_field or not data.get(availability_field, False):
        await callback.answer("Эта настройка недоступна.", show_alert=True)
        return

    await state.update_data({field: not bool(data.get(field, False))})
    await callback.message.edit_reply_markup(
        reply_markup=_interactions_markup(await state.get_data())
    )
    await callback.answer()


@router.callback_query(BotStates.VIDEO_COMMERCIAL, F.data.startswith("commercial:"))
async def select_commercial_content(callback: CallbackQuery, state: FSMContext) -> None:
    assert callback.data is not None
    assert isinstance(callback.message, Message)
    selection = callback.data.split(":", 1)[1]
    if selection not in {"none", "organic", "branded", "both"}:
        await callback.answer("Некорректный вариант.", show_alert=True)
        return
    data = await state.get_data()
    if data.get("privacy_level") == "SELF_ONLY" and selection in {"branded", "both"}:
        await callback.answer(
            "Платное партнерство недоступно для приватной публикации.",
            show_alert=True,
        )
        return

    await state.update_data(
        brand_content_toggle=selection in {"branded", "both"},
        brand_organic_toggle=selection in {"organic", "both"},
        commercial_selection=selection,
    )
    await state.set_state(BotStates.CONFIRM_UPLOAD)
    data = await state.get_data()
    await callback.message.answer(
        messages.CONFIRM_UPLOAD.format(
            nickname=data.get("creator_nickname") or "TikTok",
            description=data.get("description") or "Без описания",
            hashtags=data.get("hashtags") or "Без хештегов",
            privacy=PRIVACY_LABELS.get(data["privacy_level"], data["privacy_level"]),
            comments=_enabled_label(data.get("allow_comment", False)),
            duet=_enabled_label(data.get("allow_duet", False)),
            stitch=_enabled_label(data.get("allow_stitch", False)),
            commercial=_commercial_label(selection),
        ),
        reply_markup=upload_confirmation_keyboard(),
    )
    await callback.answer()


@router.callback_query(BotStates.CONFIRM_UPLOAD, F.data == "upload:confirm")
async def confirm_upload(callback: CallbackQuery, state: FSMContext) -> None:
    assert isinstance(callback.message, Message)
    data = await state.get_data()
    async with user_limit_lock(str(callback.from_user.id)):
        async with session_scope() as session:
            user = await get_or_create_user(
                session, callback.from_user.id, callback.from_user.username
            )
            allowed, used, limit = await can_upload_today(session, user)
            if not allowed:
                await callback.message.answer(
                    messages.LIMIT_EXCEEDED.format(used=used, limit=limit)
                )
                await callback.answer()
                return

            job = await create_upload_job(
                session=session,
                user_id=user.id,
                tiktok_account_id=UUID(data["tiktok_account_id"]),
                telegram_file_id=data["file_id"],
                local_path=data["local_path"],
                caption=_compose_caption(data.get("description"), data.get("hashtags")),
                privacy_level=data["privacy_level"],
                disable_comment=not data.get("allow_comment", False),
                disable_duet=not data.get("allow_duet", False),
                disable_stitch=not data.get("allow_stitch", False),
                brand_content_toggle=data.get("brand_content_toggle", False),
                brand_organic_toggle=data.get("brand_organic_toggle", False),
            )
            job_id = job.id

    await enqueue_upload(str(job_id), str(user.id))
    await state.clear()
    await state.set_state(BotStates.MAIN_MENU)
    await callback.message.answer(messages.UPLOAD_QUEUED, reply_markup=main_menu())
    await callback.answer()


@router.callback_query(BotStates.CONFIRM_UPLOAD, F.data == "upload:cancel")
async def cancel_upload(callback: CallbackQuery, state: FSMContext) -> None:
    assert isinstance(callback.message, Message)
    await _discard_pending_upload(state)
    await state.set_state(BotStates.MAIN_MENU)
    await callback.message.answer("Загрузка отменена.", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data.startswith("buy:"))
async def buy_callback(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    assert callback.data is not None
    assert isinstance(callback.message, Message)
    plan_code = callback.data.split(":", 1)[1]
    async with session_scope() as session:
        plan = await session.get(Plan, plan_code)
        if (
            not plan
            or not plan.is_active
            or plan.price_rub <= 0
            or plan.price_stars is None
            or plan.price_stars <= 0
        ):
            await callback.answer("Тариф недоступен для покупки.", show_alert=True)
            return
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        payment = await create_stars_payment(session, user.id, plan.id)

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Тариф {plan.title}",
        description=f"Подписка {plan.title} на {plan.duration_days or 30} дней",
        payload=f"stars:{payment.id}",
        currency="XTR",
        prices=[LabeledPrice(label=plan.title, amount=payment.amount_stars or 0)],
    )
    await state.set_state(BotStates.PAYMENT_WAIT)
    await callback.answer()


@router.callback_query(F.data == "payment:unavailable")
async def payment_unavailable(callback: CallbackQuery) -> None:
    await callback.answer(messages.STARS_NOT_CONFIGURED, show_alert=True)


@router.pre_checkout_query()
async def stars_pre_checkout(query: PreCheckoutQuery) -> None:
    payment_id = _stars_payment_id(query.invoice_payload)
    valid = False
    if payment_id is not None:
        async with session_scope() as session:
            valid = await validate_stars_checkout(
                session,
                payment_id,
                query.from_user.id,
                query.currency,
                query.total_amount,
            )
    await query.answer(
        ok=valid,
        error_message=None if valid else messages.PAYMENT_VALIDATION_ERROR,
    )


@router.message(F.successful_payment)
async def stars_payment_success(message: Message, state: FSMContext) -> None:
    assert message.from_user is not None
    successful_payment = message.successful_payment
    assert successful_payment is not None
    payment_id = _stars_payment_id(successful_payment.invoice_payload)
    if payment_id is None:
        await message.answer(messages.PAYMENT_VALIDATION_ERROR)
        return

    async with session_scope() as session:
        confirmation = await mark_stars_payment_paid(
            session,
            payment_id,
            message.from_user.id,
            successful_payment.currency,
            successful_payment.total_amount,
            successful_payment.telegram_payment_charge_id,
        )
        if confirmation.payment is None:
            await message.answer(messages.PAYMENT_VALIDATION_ERROR)
            return
        plan = await get_plan_record(session, confirmation.payment.plan_id)

    await state.clear()
    await state.set_state(BotStates.MAIN_MENU)
    if confirmation.activated:
        await message.answer(
            messages.text("payment_success", plan=plan.title),
            reply_markup=main_menu(),
        )
    else:
        await message.answer(messages.PAYMENT_ALREADY_PROCESSED, reply_markup=main_menu())


@router.message(Command("paysupport"))
async def payment_support(message: Message) -> None:
    await message.answer(messages.PAYMENT_SUPPORT)


@router.message(F.text == BTN_HISTORY)
async def history(message: Message) -> None:
    assert message.from_user is not None
    async with session_scope() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        jobs = await list_recent_upload_jobs(session, user.id)

    if not jobs:
        await message.answer("История загрузок пока пустая.")
        return

    lines = ["Последние загрузки:"]
    for job in jobs:
        lines.append(f"{job.created_at:%Y-%m-%d %H:%M} UTC - {job.status}")
    await message.answer("\n".join(lines))


@router.message(F.text == BTN_SETTINGS)
async def settings_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(BotStates.SETTINGS)
    await message.answer(messages.SETTINGS, reply_markup=settings_keyboard())


@router.callback_query(F.data == "settings:revoke_tiktok")
async def revoke_tiktok(callback: CallbackQuery) -> None:
    assert isinstance(callback.message, Message)
    async with session_scope() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        await revoke_tiktok_accounts(session, user.id)
    await callback.message.answer(messages.TIKTOK_REVOKED, reply_markup=main_menu())
    await callback.answer()


@router.message(F.text == BTN_CANCEL)
async def cancel_current_operation(message: Message, state: FSMContext) -> None:
    await _discard_pending_upload(state)
    await state.set_state(BotStates.MAIN_MENU)
    await message.answer(messages.CANCELLED, reply_markup=main_menu())


@router.message(F.text == BTN_HELP)
async def help_message(message: Message) -> None:
    await message.answer(messages.HELP)


def _compose_caption(description: str | None, hashtags: str | None) -> str:
    return "\n\n".join(part for part in [description, hashtags] if part)


def _stars_payment_id(payload: str) -> UUID | None:
    prefix, separator, value = payload.partition(":")
    if prefix != "stars" or not separator:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


async def _load_creator_info(
    telegram_id: int,
    username: str | None,
) -> tuple[UUID, TikTokCreatorInfo]:
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, username)
        account = await get_primary_tiktok_account(session, user.id)
        if account is None:
            raise TikTokApiError("account_not_connected", "TikTok account is not connected.")

        access_token = decrypt_secret(account.access_token_encrypted)
        if token_is_expired(account.token_expires_at) and account.refresh_token_encrypted:
            refreshed = await TikTokClient().refresh_access_token(
                decrypt_secret(account.refresh_token_encrypted)
            )
            account = await upsert_tiktok_account(
                session=session,
                user_id=user.id,
                open_id=refreshed.open_id,
                display_name=account.display_name,
                access_token=refreshed.access_token,
                refresh_token=refreshed.refresh_token,
                expires_in=refreshed.expires_in,
                scopes=refreshed.scope or account.scopes,
            )
            access_token = refreshed.access_token

        creator = await TikTokClient(access_token).query_creator_info()
        return account.id, creator


def _interactions_markup(data: dict) -> InlineKeyboardMarkup:
    return interactions_keyboard(
        allow_comment=bool(data.get("allow_comment", False)),
        allow_duet=bool(data.get("allow_duet", False)),
        allow_stitch=bool(data.get("allow_stitch", False)),
        comment_available=bool(data.get("comment_available", False)),
        duet_available=bool(data.get("duet_available", False)),
        stitch_available=bool(data.get("stitch_available", False)),
    )


def _enabled_label(value: object) -> str:
    return "разрешены" if value else "запрещены"


def _commercial_label(selection: str) -> str:
    return {
        "none": "нет",
        "organic": "собственный бренд",
        "branded": "платное партнерство",
        "both": "собственный бренд и платное партнерство",
    }[selection]


async def _discard_pending_upload(state: FSMContext) -> None:
    data = await state.get_data()
    local_path = data.get("local_path")
    if local_path:
        await cleanup_temp_file(str(local_path))
    await state.clear()


def _tariff_text(plans: list[Plan]) -> str:
    lines = ["Тарифы:"]
    for plan in plans:
        price = (
            "бесплатно"
            if plan.price_rub == 0
            else f"{plan.price_rub} руб./{plan.duration_days or 30} дней"
        )
        stars = f", {plan.price_stars} Stars" if plan.price_stars else ""
        lines.append(f"{plan.title}: {price}{stars}, {plan.daily_limit} видео в сутки")
    return "\n".join(lines)


async def _status_text(telegram_id: int, username: str | None) -> str:
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, username)
        allowed, used, limit = await can_upload_today(session, user)
        plan = await get_plan_record(session, await active_plan_code(session, user))
    marker = "доступна" if allowed else "исчерпана"
    return f"Тариф: {plan.title}\nСегодня: {used}/{limit}\nЗагрузка: {marker}"
