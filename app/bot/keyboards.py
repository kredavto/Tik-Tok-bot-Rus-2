from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.core.plans import PLANS, PlanCode

BTN_UPLOAD = "📤 Загрузить видео"
BTN_CONNECT_TIKTOK = "👤 Подключить TikTok"
BTN_TARIFFS = "💳 Тарифы"
BTN_STATUS = "📊 Мой тариф"
BTN_HISTORY = "📚 История загрузок"
BTN_SETTINGS = "⚙️ Настройки"
BTN_HELP = "❓ Помощь"
BTN_CANCEL = "Отмена"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_UPLOAD), KeyboardButton(text=BTN_CONNECT_TIKTOK)],
            [KeyboardButton(text=BTN_TARIFFS), KeyboardButton(text=BTN_STATUS)],
            [KeyboardButton(text=BTN_HISTORY), KeyboardButton(text=BTN_SETTINGS)],
            [KeyboardButton(text=BTN_HELP)],
            [KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
    )


def agreement_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Согласен", callback_data="agreement:accept")]]
    )


def tariffs_menu() -> InlineKeyboardMarkup:
    rows = []
    for plan in PLANS.values():
        if plan.code == PlanCode.FREE:
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{plan.title} - {plan.price_rub} руб.",
                    callback_data=f"buy:{plan.code.value}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def upload_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Отправить", callback_data="upload:confirm"),
                InlineKeyboardButton(text="Отмена", callback_data="upload:cancel"),
            ]
        ]
    )


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отключить TikTok", callback_data="settings:revoke_tiktok")]
        ]
    )
