from pathlib import Path

from aiogram import Bot

from app.core.config import settings


async def save_telegram_video(bot: Bot, file_id: str, user_id: object) -> Path:
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    user_dir = settings.storage_dir / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    file = await bot.get_file(file_id)
    if not file.file_path:
        raise RuntimeError("Telegram did not return a downloadable file path.")
    suffix = Path(file.file_path or "video.mp4").suffix or ".mp4"
    target = user_dir / f"{file.file_unique_id}{suffix}"
    await bot.download_file(file.file_path, destination=target)
    return target
