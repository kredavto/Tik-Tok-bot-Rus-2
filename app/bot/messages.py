import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache
def _catalog(locale: str = "ru") -> dict[str, str]:
    path = Path(__file__).parent / "locales" / f"{locale}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def text(key: str, locale: str = "ru", **kwargs: Any) -> str:
    template = _catalog(locale)[key]
    return template.format(**kwargs)


WELCOME = text("welcome")
AGREEMENT = text("agreement")
MAIN_MENU = text("main_menu")
TIKTOK_NOT_CONNECTED = text("tiktok_not_connected")
LIMIT_EXCEEDED = text("limit_exceeded")
SEND_VIDEO = text("send_video")
INVALID_VIDEO = text("invalid_video")
VIDEO_TOO_LARGE = text("video_too_large")
ASK_DESCRIPTION = text("ask_description")
ASK_HASHTAGS = text("ask_hashtags")
CONFIRM_UPLOAD = text("confirm_upload")
UPLOAD_QUEUED = text("upload_queued")
PAYMENT_ERROR = text("payment_error")
NETWORK_ERROR = text("network_error")
HELP = text("help")
SETTINGS = text("settings")
TIKTOK_REVOKED = text("tiktok_revoked")
CANCELLED = text("cancelled")
INTAKE_DISABLED = text("intake_disabled")
