# Configuration Management

## Sources

- Secrets are stored only in `.env` or a managed secret store.
- Runtime non-secret settings are stored in PostgreSQL `system_settings`.
- Tariffs, RUB reference prices, and independent Telegram Stars prices are stored in PostgreSQL
  `plans`.

System setting storage rules are documented in [System Settings Entity](system-settings-entity.md).

Environment-specific `.env` and secret management rules are documented in [Environment Configuration and Secrets Control](environment-configuration-secrets.md).

## Export

```bash
curl https://your-domain.example/admin/configuration/export \
  -H "Authorization: Bearer $ADMIN_API_TOKEN"
```

The export contains no secret-like keys such as passwords, tokens, keys, or secrets.

## Import

```bash
curl -X POST https://your-domain.example/admin/configuration/import \
  -H "Authorization: Bearer $ADMIN_API_TOKEN" \
  -H "X-CSRF-Token: $ADMIN_CSRF_TOKEN" \
  -H "Content-Type: application/json" \
  -d @runtime-config.json
```

Before import, the current runtime configuration is recorded in `admin_actions` as an audit backup.

## Audit

The following are recorded:

- Tariff updates.
- System setting updates.
- Configuration export.
- Configuration import.
- Administrative actions.

## Startup Validation

Required settings are validated during startup. Missing required parameters cause safe startup failure without logging secrets.

## Documentation Rule

Any configuration change that affects behavior must update this guide, `.env.example`, and related tests where applicable.
