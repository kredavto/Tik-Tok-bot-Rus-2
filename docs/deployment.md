# Deployment

Target: VPS in the Netherlands, managed through Termius or any SSH client.

## Server Checklist

1. Create an Ubuntu 24.04 VPS in the Netherlands.
2. Point a domain or subdomain to the server.
3. Connect through Termius with SSH keys.
4. Update the system and install Docker.
5. Clone `kredavto/Tik-Tok-bot-Rus-2`.
6. Create production `.env`.
7. Start Docker Compose.
8. Configure Nginx and HTTPS.
9. Configure Telegram, TikTok, and Robokassa webhooks.
10. Check service health.

For first go-live, follow [Production Launch Plan](production-launch.md).

Infrastructure runtime updates must follow [Infrastructure Dependency Management](infrastructure-dependency-management.md).

## Commands

```bash
git clone https://github.com/kredavto/Tik-Tok-bot-Rus-2.git
cd Tik-Tok-bot-Rus-2
cp .env.example .env
nano .env
docker compose up -d --build
docker compose logs -f api bot worker scheduler
```

For staging and production, use the checked automation instead of running these commands
individually:

```bash
ENV_FILE=.env bash deploy/preflight.sh production
ENV_FILE=.env bash deploy/deploy.sh production vX.Y.Z
```

The checked-out application version must equal `APP_VERSION` in `.env`. A release candidate such as
`0.2.0-rc.1` is accepted for staging and rejected for production until promoted to a stable SemVer.
Each deployment records a deterministic source manifest under `.deploy/release-manifest.json`.

The complete certificate bootstrap, deployment, backup, restore, rollback, and CI procedure is in
[CI/CD and Deployment Automation](ci-cd-deployment.md).

Run migrations explicitly before first start or during deploy:

```bash
docker compose run --rm api alembic upgrade head
```

Migration safety, compatibility, and rollback rules are documented in [Migration and Version Compatibility Plan](migration-compatibility-plan.md).

Health checks:

```bash
curl https://your-domain.example/health
curl https://your-domain.example/ready
curl https://your-domain.example/metrics
docker compose ps scheduler
```

After HTTPS is active, open the administrative console at:

```text
https://your-domain.example/admin-ui/
```

Access requires a Telegram ID listed in `TELEGRAM_ADMIN_IDS`, `ADMIN_API_TOKEN`, and
`ADMIN_CSRF_TOKEN`. Generate independent high-entropy values for production. The browser console
does not persist them after the page is reloaded or closed.

The API image contains `alembic.ini` and the complete `alembic/` migration tree. The scheduler
healthcheck reads its Redis heartbeat; an unhealthy scheduler means subscription expiry, token
refresh, and retention cleanup are not being dispatched.

## Systemd Alternative

Use Docker Compose for the first deployment. If systemd is required, copy
`deploy/tiktok-loader-bot.service` to `/etc/systemd/system/` and adjust paths.

## Robokassa URLs

Configure these in the Robokassa dashboard after the HTTP webhook service is added:

- Result URL: `https://your-domain.example/api/v1/payments/robokassa/result`
- Success URL: `https://your-domain.example/api/v1/payments/robokassa/success`
- Fail URL: `https://your-domain.example/api/v1/payments/robokassa/fail`

The FastAPI service exposes Robokassa result, success, and fail endpoints.

## Telegram Webhook

Development can use `TELEGRAM_DELIVERY_MODE=polling`. Production uses
`TELEGRAM_DELIVERY_MODE=webhook`; the deployment command registers and verifies
`https://<domain>/api/v1/webhooks/telegram`, FastAPI verifies
`X-Telegram-Bot-Api-Secret-Token` and dispatches the update through aiogram. FSM data is stored in
Redis so multiple API instances share state. The bot service monitors the registered URL for
configuration drift without changing it automatically.

Manage the webhook explicitly inside the container when diagnosing a deployment:

```bash
docker compose run --rm --no-deps bot python -m app.bot.webhook verify
docker compose run --rm --no-deps bot python -m app.bot.webhook configure
```

Never configure a bot token that has appeared in chat, logs, source files, or Git. Revoke it in
BotFather and place the replacement only in the server-side `.env`.

## Environments

Use separate files outside Git for each environment:

- `.env.development`
- `.env.staging`
- `.env.production`

Copy the selected file to `.env` on the server. Never commit real `.env` files.

Staging and production use `NGINX_TEMPLATE=https.conf.template`, set `DOMAIN` to the
`PUBLIC_BASE_URL` host, and provide `fullchain.pem` and `privkey.pem` under `TLS_CERT_DIR`.
