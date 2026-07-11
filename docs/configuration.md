# Configuration

Only `.env.example` is stored in Git. Real `.env` files are environment-specific and must not be committed.

Confidential data handling and secret rotation rules are defined in [Confidential Data Policy](confidential-data-policy.md).

Environment-specific configuration and secret control rules are defined in [Environment Configuration and Secrets Control](environment-configuration-secrets.md).

Use separate files for development, staging, and production, then copy the selected file to `.env` on the server.

Application: `APP_ENV`, `APP_VERSION`, `APP_HOST`, `APP_PORT`, `PUBLIC_BASE_URL`, `TIMEZONE`.

Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_ADMIN_IDS`.

Database: `DATABASE_URL`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.

Redis: `REDIS_URL`.

TikTok API: `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REDIRECT_URI`, `TIKTOK_WEBHOOK_SECRET`.

TikTok Developer Portal setup and pre-release checks are described in [TikTok Developer Configuration](tiktok-developer-configuration.md).

Robokassa: `ROBOKASSA_MERCHANT_LOGIN`, `ROBOKASSA_PASSWORD_1`, `ROBOKASSA_PASSWORD_2`, `ROBOKASSA_RESULT_URL`, `ROBOKASSA_SUCCESS_URL`, `ROBOKASSA_FAIL_URL`.

Security: `TOKEN_ENCRYPTION_KEY`, `ADMIN_API_TOKEN`, `ADMIN_CSRF_TOKEN`.

Generate Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

After `.env` is filled, local deployment starts with:

```bash
docker compose up -d
```

Runtime non-secret settings and tariffs can be exported/imported through the admin API. See [Configuration Management](configuration-management.md).
