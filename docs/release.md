# Release Management

## Environments

| Environment | Purpose |
| --- | --- |
| Development | Local development and debugging |
| Staging | Pre-release acceptance testing |
| Production | User-facing runtime |

Environment templates live in `deploy/env.*.example`. Real `.env.*` files are not committed.

## Release Requirements

- CI passes.
- Alembic migrations are tested.
- Docker images build.
- `CHANGELOG.md` is updated.
- OpenAPI contract is current when REST API behavior changes.
- QA acceptance scenarios pass in staging.
- Requirements traceability matrix is current.
- `APP_VERSION`, `app.__version__`, and `pyproject.toml` follow SemVer.
- Production backup is created before deployment.
- Risk impact is reviewed before production deployment.

## Release Flow

1. Create a release branch.
2. Update version and changelog.
3. Run CI checks.
4. Deploy to staging.
5. Run acceptance tests.
6. Approve release.
7. Back up production.
8. Deploy to production.
9. Check `/health`, `/ready`, `/metrics`.
10. Monitor logs and core scenarios after release.

Post-launch release planning, routine checks, and quality gates are described in [Post-Launch Maintenance and Versioning](post-launch-maintenance.md).

Dependency and third-party service updates must follow [Dependencies and Third-Party Services](dependencies-and-integrations.md).

Infrastructure runtime updates must follow [Infrastructure Dependency Management](infrastructure-dependency-management.md).

New functionality must satisfy [Feature Development Plan](feature-development-plan.md) before release approval.

Database migration and version compatibility rules are documented in [Migration and Version Compatibility Plan](migration-compatibility-plan.md).

Every release candidate must satisfy [Change Acceptance Policy](change-acceptance-policy.md).

Acceptance testing must follow [QA Test Data and Acceptance Scenarios](qa-acceptance-scenarios.md).

Requirement coverage must follow [Requirements Traceability Matrix](requirements-traceability.md).

Documentation completeness must follow [Specification Index](specification-index.md).

Environment configuration and secret readiness must follow [Environment Configuration and Secrets Control](environment-configuration-secrets.md).

Technical debt must be reviewed according to [Technical Debt Management](technical-debt-management.md).

License and third-party component checks must follow [License and Third-Party Component Management](license-third-party-management.md).

API versioning, compatibility, and deprecation checks must follow [API Versioning and Client Compatibility](api-versioning-compatibility.md).

Implementation stage readiness must follow [Implementation Roadmap](implementation-roadmap.md).

## Production Update

```bash
ENV_FILE=.env bash deploy/deploy.sh production vX.Y.Z
```

## Rollback

1. Stop intake with `intake_enabled=false` when publication behavior is affected.
2. Confirm the previous release is compatible with the current database schema.
3. Run `ENV_FILE=.env bash deploy/rollback.sh production <ref> --confirm`.
4. Restore a verified database backup only after a separate data-impact review.
5. Check health, readiness, metrics, and key user scenarios.
6. Re-enable intake.

The automation details and database downgrade restriction are documented in
[CI/CD and Deployment Automation](ci-cd-deployment.md).

## API Compatibility

Public REST methods use `/api/v1`. Backward-compatible fields can be added. Removing or changing fields requires a new major API version.
