# Infrastructure Dependency Management

This document defines how Tik_Tok_Loader controls infrastructure component versions, operating system updates, container updates, and runtime dependency compatibility.

## Controlled Components

| Component | Control Area |
| --- | --- |
| Ubuntu Server 24.04 LTS | OS packages, kernel security updates, SSH, firewall, and system libraries |
| Docker Engine and Docker Compose | Container runtime, Compose plugin, networking, and volumes |
| Nginx | Reverse proxy, TLS termination, headers, and upstream routing |
| PostgreSQL | Database engine version, backup compatibility, migrations, and extensions |
| Redis | Queue/cache runtime version, memory behavior, and persistence settings |
| Python and project libraries | Python runtime, application dependencies, and version constraints |
| Docker base images | Security patches, Python image compatibility, and OS package updates |

## Update Policy

- Check OS, Docker, Docker Compose, Nginx, PostgreSQL, Redis, Python library, and base image updates regularly.
- Test updates in staging before production rollout.
- Create a production backup before updating production infrastructure.
- Document performed updates in `CHANGELOG.md` or the operations journal, depending on release scope.
- Verify compatibility after every update.
- Avoid direct critical infrastructure changes in production without a rollback plan.

## Security Control

- Install critical security updates in a timely manner.
- Review Docker base image vulnerabilities before release.
- Remove unused OS packages, Python libraries, containers, images, and volumes when safe.
- Keep TLS/SSL certificate expiration under regular control.
- Confirm PostgreSQL and Redis remain inaccessible from the public internet.
- Keep secrets in `.env` or an approved secret store only.

## Production Update Procedure

1. Review the change scope and affected services.
2. Create a PostgreSQL backup and save current production configuration.
3. Apply the update in staging.
4. Run migrations and acceptance checks in staging when applicable.
5. Schedule production work in a low-activity window.
6. Apply the update to production.
7. Restart only affected services when possible.
8. Check `/health`, `/ready`, and `/metrics`.
9. Verify key user scenarios.
10. Review logs for new critical errors.
11. Document the update result.

## Compatibility Checks

After infrastructure updates, verify:

- Telegram bot responds to `/start`.
- FastAPI health, readiness, and metrics endpoints respond.
- PostgreSQL accepts connections and Alembic state is correct.
- Redis accepts connections and queues operate normally.
- Worker processes jobs without duplicate processing.
- Nginx serves HTTPS and proxies callbacks correctly.
- Robokassa ResultURL processing still verifies signatures.
- TikTok OAuth start and callback URLs still match public HTTPS configuration.
- Video validation and FFmpeg/FFprobe behavior remain compatible.

## Successful Update Criteria

An infrastructure update is successful only when:

- All services pass health checks.
- Key user flows work correctly.
- Logs contain no new critical errors.
- Backup and rollback paths are known.
- Update actions and outcomes are documented.

## Related Documents

- [Dependencies and Third-Party Services](dependencies-and-integrations.md)
- [License and Third-Party Component Management](license-third-party-management.md)
- [Deployment](deployment.md)
- [Release Management](release.md)
- [Security, Backup, and Monitoring](security.md)
- [SOP Checklists](sop-checklists.md)
- [Capacity and Performance Management](capacity-management.md)
