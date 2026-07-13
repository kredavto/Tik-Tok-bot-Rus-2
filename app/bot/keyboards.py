from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

BTN_UPLOAD = "📤 Загрузить видео"
BTN_CONNECT_TIKTOK = "👤 Подключить TikTok"
BTN_TARIFFS = "💳 Тарифы"
BTN_STATUS = "📊 Мой тариф"
BTN_HISTORY = "📚 История загрузок"
BTN_SETTINGS = "⚙️ Настройки"
BTN_HELP = "❓ Помощь"
BTN_CANCEL = "Отмена"

PRIVACY_LABELS = {
    "PUBLIC_TO_EVERYONE": "Все",
    "MUTUAL_FOLLOW_FRIENDS": "Друзья",
    "FOLLOWER_OF_CREATOR": "Подписчики",
    "SELF_ONLY": "Только я",
}


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


def tariffs_menu(plans: list[tuple[str, str, int]]) -> InlineKeyboardMarkup:
    rows = []
    for plan_code, title, price_rub in plans:
        if price_rub <= 0:
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{title} - {price_rub} руб.",
                    callback_data=f"buy:{plan_code}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def upload_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Опубликовать и согласиться",
                    callback_data="upload:confirm",
                ),
                InlineKeyboardButton(text="Отмена", callback_data="upload:cancel"),
            ]
        ]
    )


def privacy_keyboard(options: list[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=PRIVACY_LABELS.get(option, option),
                    callback_data=f"privacy:{option}",
                )
            ]
            for option in options
        ]
    )


def interactions_keyboard(
    *,
    allow_comment: bool,
    allow_duet: bool,
    allow_stitch: bool,
    comment_available: bool,
    duet_available: bool,
    stitch_available: bool,
) -> InlineKeyboardMarkup:
    def row(label: str, key: str, selected: bool, available: bool) -> list[InlineKeyboardButton]:
        if not available:
            return [
                InlineKeyboardButton(
                    text=f"Недоступно: {label}", callback_data="interaction:unavailable"
                )
            ]
        marker = "Включено" if selected else "Выключено"
        return [InlineKeyboardButton(text=f"{label}: {marker}", callback_data=f"interaction:{key}")]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            row("Комментарии", "comment", allow_comment, comment_available),
            row("Дуэты", "duet", allow_duet, duet_available),
            row("Сшивание", "stitch", allow_stitch, stitch_available),
            [InlineKeyboardButton(text="Продолжить", callback_data="interaction:continue")],
        ]
    )


def commercial_content_keyboard(allow_branded_content: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Нет продвижения", callback_data="commercial:none")],
        [InlineKeyboardButton(text="Продвигаю свой бренд", callback_data="commercial:organic")],
    ]
    if allow_branded_content:
        rows.extend(
            [
                [
                    InlineKeyboardButton(
                        text="Платное партнерство", callback_data="commercial:branded"
                    )
                ],
                [InlineKeyboardButton(text="Оба варианта", callback_data="commercial:both")],
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отключить TikTok", callback_data="settings:revoke_tiktok")]
        ]
    )
