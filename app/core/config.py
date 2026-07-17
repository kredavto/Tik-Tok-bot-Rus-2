from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
    )

    app_env: str = Field("development", alias="APP_ENV")
    app_version: str = Field("0.2.0", alias="APP_VERSION")
    app_host: str = Field("0.0.0.0", alias="APP_HOST")
    app_port: int = Field(8080, alias="APP_PORT")
    api_workers: int = Field(1, alias="API_WORKERS")
    public_base_url: str = Field("http://localhost:8080", alias="PUBLIC_BASE_URL")
    timezone: str = Field("Europe/Moscow", alias="TIMEZONE")

    bot_token: str = Field("", validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN", "BOT_TOKEN"))
    telegram_webhook_secret: str = Field("", alias="TELEGRAM_WEBHOOK_SECRET")
    telegram_delivery_mode: Literal["polling", "webhook"] = Field(
        "polling",
        alias="TELEGRAM_DELIVERY_MODE",
    )
    telegram_webhook_path: str = Field(
        "/api/v1/webhooks/telegram",
        alias="TELEGRAM_WEBHOOK_PATH",
    )
    telegram_webhook_check_seconds: int = Field(
        300,
        ge=30,
        alias="TELEGRAM_WEBHOOK_CHECK_SECONDS",
    )
    admin_telegram_ids: str = Field(
        "",
        validation_alias=AliasChoices("TELEGRAM_ADMIN_IDS", "ADMIN_TELEGRAM_IDS"),
    )

    database_url: str = Field(
        "postgresql+asyncpg://tiktok:tiktok@postgres:5432/tiktok_loader",
        alias="DATABASE_URL",
    )
    postgres_db: str = Field("tiktok_loader", alias="POSTGRES_DB")
    postgres_user: str = Field("tiktok", alias="POSTGRES_USER")
    postgres_password: str = Field("", alias="POSTGRES_PASSWORD")

    redis_url: str = Field("redis://redis:6379/0", alias="REDIS_URL")
    storage_dir: Path = Field(Path("./data/videos"), alias="STORAGE_DIR")

    tiktok_client_key: str = Field("", alias="TIKTOK_CLIENT_KEY")
    tiktok_client_secret: str = Field("", alias="TIKTOK_CLIENT_SECRET")
    tiktok_redirect_uri: str = Field("", alias="TIKTOK_REDIRECT_URI")
    tiktok_webhook_secret: str = Field("", alias="TIKTOK_WEBHOOK_SECRET")
    tiktok_publish_enabled: bool = Field(False, alias="TIKTOK_PUBLISH_ENABLED")

    robokassa_login: str = Field(
        "",
        validation_alias=AliasChoices("ROBOKASSA_MERCHANT_LOGIN", "ROBOKASSA_LOGIN"),
    )
    robokassa_password1: str = Field(
        "",
        validation_alias=AliasChoices("ROBOKASSA_PASSWORD_1", "ROBOKASSA_PASSWORD1"),
    )
    robokassa_password2: str = Field(
        "",
        validation_alias=AliasChoices("ROBOKASSA_PASSWORD_2", "ROBOKASSA_PASSWORD2"),
    )
    robokassa_result_url: str = Field("", alias="ROBOKASSA_RESULT_URL")
    robokassa_success_url: str = Field("", alias="ROBOKASSA_SUCCESS_URL")
    robokassa_fail_url: str = Field("", alias="ROBOKASSA_FAIL_URL")
    robokassa_test_mode: bool = Field(True, alias="ROBOKASSA_TEST_MODE")
    robokassa_hash_algorithm: Literal["md5", "sha256", "sha512"] = Field(
        "md5",
        alias="ROBOKASSA_HASH_ALGORITHM",
    )

    token_encryption_key: str = Field("", alias="TOKEN_ENCRYPTION_KEY")
    admin_api_token: str = Field("", alias="ADMIN_API_TOKEN")
    admin_api_telegram_id: int | None = Field(None, alias="ADMIN_API_TELEGRAM_ID")
    admin_csrf_token: str = Field("", alias="ADMIN_CSRF_TOKEN")

    rate_limit_per_minute: int = Field(120, alias="RATE_LIMIT_PER_MINUTE")
    backup_dir: str = Field("./backups", alias="BACKUP_DIR")
    max_video_size_mb: int = Field(100, alias="MAX_VIDEO_SIZE_MB")
    max_video_duration_sec: int = Field(300, alias="MAX_VIDEO_DURATION_SEC")
    dramatiq_processes: int = Field(1, alias="DRAMATIQ_PROCESSES")
    dramatiq_threads: int = Field(4, alias="DRAMATIQ_THREADS")
    scheduler_tick_seconds: int = Field(10, ge=5, alias="SCHEDULER_TICK_SECONDS")
    subscription_sweep_seconds: int = Field(60, ge=10, alias="SUBSCRIPTION_SWEEP_SECONDS")
    token_refresh_sweep_seconds: int = Field(900, ge=60, alias="TOKEN_REFRESH_SWEEP_SECONDS")
    retention_sweep_seconds: int = Field(3600, ge=300, alias="RETENTION_SWEEP_SECONDS")
    status_reconcile_seconds: int = Field(300, ge=60, alias="STATUS_RECONCILE_SECONDS")
    token_refresh_lead_seconds: int = Field(3600, ge=300, alias="TOKEN_REFRESH_LEAD_SECONDS")
    maintenance_batch_size: int = Field(100, ge=1, le=1000, alias="MAINTENANCE_BATCH_SIZE")
    video_retention_hours: int = Field(24, alias="VIDEO_RETENTION_HOURS")
    log_retention_days: int = Field(90, alias="LOG_RETENTION_DAYS")
    backup_retention_days: int = Field(14, alias="BACKUP_RETENTION_DAYS")
    audit_log_retention_days: int = Field(365, alias="AUDIT_LOG_RETENTION_DAYS")


settings = Settings()  # type: ignore[call-arg]


def require_settings(*names: str) -> None:
    missing = [name for name in names if not getattr(settings, name)]
    if missing:
        raise RuntimeError(f"Missing required configuration: {', '.join(missing)}")


def validate_runtime_settings() -> None:
    require_settings("database_url", "redis_url", "public_base_url")

    if not settings.telegram_webhook_path.startswith("/"):
        raise RuntimeError("TELEGRAM_WEBHOOK_PATH must start with '/'")

    if settings.telegram_delivery_mode == "webhook":
        require_settings("bot_token", "telegram_webhook_secret")
        public_url = urlparse(settings.public_base_url)
        if public_url.scheme != "https" or not public_url.netloc:
            raise RuntimeError("Webhook mode requires an HTTPS PUBLIC_BASE_URL")

    if settings.tiktok_publish_enabled:
        require_settings(
            "tiktok_client_key",
            "tiktok_client_secret",
            "tiktok_redirect_uri",
            "token_encryption_key",
        )

    if not settings.robokassa_test_mode:
        require_settings(
            "robokassa_login",
            "robokassa_password1",
            "robokassa_password2",
            "robokassa_result_url",
            "robokassa_success_url",
            "robokassa_fail_url",
        )
