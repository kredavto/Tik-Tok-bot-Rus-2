from aiogram.fsm.state import State, StatesGroup


class BotStates(StatesGroup):
    START = State()
    ACCEPT_TERMS = State()
    CONNECT_TIKTOK = State()
    MAIN_MENU = State()
    UPLOAD_VIDEO = State()
    VIDEO_DESCRIPTION = State()
    VIDEO_HASHTAGS = State()
    CONFIRM_UPLOAD = State()
    PAYMENT_SELECT_PLAN = State()
    PAYMENT_WAIT = State()
    SETTINGS = State()
