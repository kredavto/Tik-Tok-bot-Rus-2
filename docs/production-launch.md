# Production Launch Plan

End-to-end implementation stages are documented in [Implementation Roadmap](implementation-roadmap.md).

## Preparation

- Domain name points to the production server.
- HTTPS certificate is issued and valid.
- Production `.env` is filled and stored outside Git.
- Production secrets are not reused in development or staging.
- PostgreSQL connection works.
- Redis connection works.
- Telegram webhook or polling mode is configured intentionally.
- TikTok OAuth Redirect URI matches the production callback URL.
- Existing Robokassa merchant settings are verified.
- Robokassa ResultURL, SuccessURL, and FailURL use the production HTTPS domain.
- Backup procedure is tested.

Environment and secret readiness must follow [Environment Configuration and Secrets Control](environment-configuration-secrets.md).

## First Startup

```bash
ENV_FILE=.env bash deploy/preflight.sh production
ENV_FILE=.env bash deploy/deploy.sh production vX.Y.Z
docker compose ps
```

Follow [CI/CD and Deployment Automation](ci-cd-deployment.md) for first-certificate bootstrap,
verified backup creation, and deployment behavior.

Production is allowed only after the complete [Staging Acceptance Runbook](staging-acceptance-runbook.md)
has passed for the same release commit. A Telegram token previously disclosed in chat, source,
logs, or Git must be revoked in BotFather; only its replacement may be placed in the production
`.env`.

## Smoke Test

The deployment script automatically verifies versioned health/readiness/metrics endpoints,
OpenAPI callback contracts, admin security headers, and the Telegram webhook registered at the
public HTTPS URL. Then perform these provider-backed scenarios:

1. Register a new Telegram user with `/start`.
2. Accept the user agreement.
3. Confirm FREE plan is assigned.
4. Start TikTok OAuth connection.
5. Confirm TikTok OAuth callback succeeds.
6. Create a PRO Telegram Stars invoice and complete the in-bot acceptance scenario.
7. Through the separately approved external channel, generate a Robokassa PRO payment link.
8. Complete a Robokassa test payment and confirm ResultURL activates PRO exactly once.
9. Upload one test video.
10. Confirm validation, preparation, queueing, worker processing, and TikTok API submission.
11. Confirm admin metrics and logs are visible.
12. Restore the release backup into a disposable database and compare critical record counts.

## Success Criteria

- All containers are running.
- Healthchecks are green.
- Telegram, TikTok, and Robokassa callbacks work.
- FREE, PRO, BUSINESS, and UNLIMIT limits match the specification.
- No critical errors appear in logs.
- Metrics are available to administrators.
- Backups are present and restorable.

## Handover

Save and hand over:

- Production `.env` location and owner.
- Backup location and restore instructions.
- Domain and certificate details.
- Robokassa merchant settings.
- TikTok developer app settings.
- Telegram bot settings.
- Operations runbook and incident process.
- Current Git commit and release version.
