# Acceptance Checklist

Final implementation must satisfy [Architecture Summary](architecture-summary.md).

Non-functional requirements must be validated according to [Non-Functional Requirements](non-functional-requirements.md).

Documentation completeness must be checked against [Specification Index](specification-index.md).

Implementation progress must be checked against [Implementation Roadmap](implementation-roadmap.md).

## Functional Readiness

- New Telegram user registration works.
- FREE plan is assigned automatically.
- User agreement flow works.
- TikTok OAuth 2.0 connection uses the official TikTok authorization flow.
- TikTok OAuth tokens are encrypted in storage.
- Video upload FSM works: video, description, hashtags, confirmation.
- Video validation and preparation work for MP4, MOV, and WEBM.
- Upload lifecycle events are recorded.
- FREE, PRO, and BUSINESS limits match the specification.
- Robokassa payment link generation works for PRO and BUSINESS.
- Robokassa ResultURL activates paid subscriptions.
- SuccessURL does not activate subscriptions.
- User can disconnect TikTok.

## Technical Readiness

- `docker compose up -d` starts all services.
- PostgreSQL and Redis are not exposed publicly.
- API, PostgreSQL, Redis, and Nginx healthchecks pass.
- Alembic migrations apply cleanly.
- Migration compatibility checks are complete.
- CI passes Ruff format, Ruff lint, MyPy, tests, Alembic, Docker build, and secret scan.
- `.env` files are not committed.
- `.env.example` is complete and current.
- Confidential data handling and secret rotation policy is documented.
- Environment configuration and secret readiness are verified.
- OpenAPI is available at `/docs` and `/openapi.json`.
- API version compatibility and deprecation impact have been reviewed.
- Requirements traceability matrix is current.
- Specification index is current.
- Technical debt register has been reviewed.
- License and third-party component register has been reviewed.
- Non-functional requirements have been checked.

## Operational Readiness

- Production `.env` is prepared.
- HTTPS is configured.
- Telegram, TikTok, and Robokassa callbacks are configured.
- PostgreSQL backup works.
- Restore drill has been tested on staging.
- Backup and restore policy is documented and current.
- `/health`, `/ready`, and `/metrics` are monitored.
- Security logging and audit requirements are verified.
- Capacity thresholds and scaling actions are documented.
- Service continuity plan is documented and current.
- Infrastructure dependency update policy is documented and current.
- Incident management process is documented.
- Operations runbook is current.
- Release and rollback procedures are documented.

## Final Sign-Off

Project is ready for production only after functional, integration, security, and operational checks pass successfully.

Required QA scenarios are documented in [QA Test Data and Acceptance Scenarios](qa-acceptance-scenarios.md).

Requirement coverage is tracked in [Requirements Traceability Matrix](requirements-traceability.md).

The first production run should follow [Production Launch Plan](production-launch.md).

Post-launch support should follow [Post-Launch Maintenance and Versioning](post-launch-maintenance.md).

Future changes should be accepted through [Change Acceptance Policy](change-acceptance-policy.md).
