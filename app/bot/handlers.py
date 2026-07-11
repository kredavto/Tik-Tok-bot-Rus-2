from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

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
    agreement_keyboard,
    main_menu,
    settings_keyboard,
    tariffs_menu,
    upload_confirmation_keyboard,
)
from app.bot.states import BotStates
from app.bot.storage import save_telegram_video
from app.core.config import settings
from app.core.plans import PLANS, get_plan
from app.core.redis import create_oauth_state, enqueue_upload, user_limit_lock
from app.db.session import (
    accept_agreement,
    active_plan_code,
    can_upload_today,
    create_payment,
    create_upload_job,
    get_or_create_user,
    has_tiktok_account,
    is_intake_enabled,
    list_recent_upload_jobs,
    revoke_tiktok_accounts,
    session_scope,
)
from app.services.robokassa import build_payment_url
from app.services.tiktok import build_oauth_url

router = Router()

SUPPORTED_VIDEO_MIME_TYPES = {"video/mp4", "video/quicktime", "video/webm"}


@router.message(Command("start"))
async def start(message: Message, state: FSMContext) -> None:
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
    await state.set_state(BotStates.PAYMENT_SELECT_PLAN)
    await message.answer(_tariff_text(), reply_markup=tariffs_menu())


@router.message(Command("status"))
@router.message(F.text == BTN_STATUS)
async def status(message: Message) -> None:
    await message.answer(await _status_text(message.from_user.id, message.from_user.username))


@router.message(F.text == BTN_CONNECT_TIKTOK)
async def connect_tiktok(message: Message, state: FSMContext) -> None:
    await state.set_state(BotStates.CONNECT_TIKTOK)
    if not settings.tiktok_client_key or not settings.tiktok_redirect_uri:
        await message.answer("TikTok OAuth еще не настроен администратором.")
        return

    async with session_scope() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        oauth_state = await create_oauth_state(str(user.id))

    await state.set_state(BotStates.MAIN_MENU)
    await message.answer(f"Подключите TikTok через официальный OAuth 2.0:\n{build_oauth_url(oauth_state)}")


@router.message(F.text == BTN_UPLOAD)
async def start_upload(message: Message, state: FSMContext) -> None:
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
    file_id = None
    file_size = None
    mime_type = None
    is_video_document = (
        message.document and message.document.mime_type and message.document.mime_type.startswith("video/")
    )

    if message.video:
        file_id = message.video.file_id
        file_size = message.video.file_size
        mime_type = message.video.mime_type
    elif is_video_document:
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

    await state.update_data(file_id=file_id, local_path=str(local_path))
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
    hashtags = message.text or ""
    await state.update_data(hashtags=hashtags)
    data = await state.get_data()
    await state.set_state(BotStates.CONFIRM_UPLOAD)
    await message.answer(
        messages.CONFIRM_UPLOAD.format(
            description=data.get("description") or "Без описания",
            hashtags=hashtags or "Без хештегов",
        ),
        reply_markup=upload_confirmation_keyboard(),
    )


@router.callback_query(BotStates.CONFIRM_UPLOAD, F.data == "upload:confirm")
async def confirm_upload(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    async with user_limit_lock(str(callback.from_user.id)):
        async with session_scope() as session:
            user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
            allowed, used, limit = await can_upload_today(session, user)
            if not allowed:
                await callback.message.answer(messages.LIMIT_EXCEEDED.format(used=used, limit=limit))
                await callback.answer()
                return

            job = await create_upload_job(
                session=session,
                user_id=user.id,
                telegram_file_id=data["file_id"],
                local_path=data["local_path"],
                caption=_compose_caption(data.get("description"), data.get("hashtags")),
            )
            job_id = job.id

    await enqueue_upload(str(job_id), str(user.id))
    await state.set_state(BotStates.MAIN_MENU)
    await callback.message.answer(messages.UPLOAD_QUEUED, reply_markup=main_menu())
    await callback.answer()


@router.callback_query(BotStates.CONFIRM_UPLOAD, F.data == "upload:cancel")
async def cancel_upload(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BotStates.MAIN_MENU)
    await callback.message.answer("Загрузка отменена.", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data.startswith("buy:"))
async def buy_callback(callback: CallbackQuery, state: FSMContext) -> None:
    plan_code = callback.data.split(":", 1)[1]
    plan = get_plan(plan_code)
    if plan.price_rub <= 0:
        await callback.answer("Этот тариф уже доступен бесплатно.", show_alert=True)
        return

    async with session_scope() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        payment = await create_payment(session, user.id, plan.code.value, plan.price_rub)

    url = build_payment_url(
        payment.provider_invoice_id,
        plan.price_rub,
        f"Тариф {plan.title} на 30 дней",
    )
    # Payment completion is finalized only by Robokassa ResultURL.
    await state.set_state(BotStates.PAYMENT_WAIT)
    await callback.message.answer(f"Ссылка на оплату тарифа {plan.title}:\n{url}")
    await callback.answer()


@router.message(F.text == BTN_HISTORY)
async def history(message: Message) -> None:
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
    async with session_scope() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        await revoke_tiktok_accounts(session, user.id)
    await callback.message.answer(messages.TIKTOK_REVOKED, reply_markup=main_menu())
    await callback.answer()


@router.message(F.text == BTN_CANCEL)
async def cancel_current_operation(message: Message, state: FSMContext) -> None:
    await state.set_state(BotStates.MAIN_MENU)
    await message.answer(messages.CANCELLED, reply_markup=main_menu())


@router.message(F.text == BTN_HELP)
async def help_message(message: Message) -> None:
    await message.answer(messages.HELP)


def _compose_caption(description: str | None, hashtags: str | None) -> str:
    return "\n\n".join(part for part in [description, hashtags] if part)


def _tariff_text() -> str:
    lines = ["Тарифы:"]
    for plan in PLANS.values():
        price = "бесплатно" if plan.price_rub == 0 else f"{plan.price_rub} руб./30 дней"
        lines.append(f"{plan.title}: {price}, {plan.daily_limit} видео в сутки")
    return "\n".join(lines)


async def _status_text(telegram_id: int, username: str | None) -> str:
    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, username)
        allowed, used, limit = await can_upload_today(session, user)
        plan = get_plan(await active_plan_code(session, user))
    marker = "доступна" if allowed else "исчерпана"
    return f"Тариф: {plan.title}\nСегодня: {used}/{limit}\nЗагрузка: {marker}"
