# Specification Index

This document is the final index for the Tik_Tok_Loader technical specification. All specification parts are treated as one requirement set for development, testing, deployment, operations, and maintenance.

## Purpose

The current documentation set is the authoritative project specification. It is used as:

- Technical assignment.
- Architecture specification.
- Development guide.
- QA and acceptance reference.
- Deployment and operations guide.
- Maintenance and change-control reference.

## Core Specification Groups

| Group | Documents |
| --- | --- |
| Architecture | [Architecture Summary](architecture-summary.md), [Project Component Map](component-map.md), [Sequence Flows](sequence-flows.md), [Glossary and Naming Conventions](glossary-naming.md) |
| Functional behavior | [User Guide](user-guide.md), [Video Lifecycle](video-lifecycle.md), [Telegram Stars](telegram-stars.md), [Robokassa Setup](robokassa.md), [TikTok Developer Configuration](tiktok-developer-configuration.md) |
| Data model | [Logical Data Model](data-model.md), entity specifications for users, TikTok accounts, subscriptions, payments, upload jobs, usage, webhooks, admin actions, and settings |
| API contracts | [REST API Standards](rest-api-standards.md), [API Versioning and Client Compatibility](api-versioning-compatibility.md), [Public REST API](public-rest-api.md), [Administrative REST API](admin-rest-api.md), [OpenAPI and Contract Documentation](openapi-contracts.md), [Error Codes and Exception Handling](error-handling.md) |
| Security and compliance | [Compliance Notes](compliance.md), [Security, Backup, and Monitoring](security.md), [Security Logging and Audit](security-logging-audit.md), [Confidential Data Policy](confidential-data-policy.md), [Environment Configuration and Secrets Control](environment-configuration-secrets.md), [RBAC-related admin documentation](admin-rest-api.md) |
| Operations | [Deployment](deployment.md), [Staging Acceptance Runbook](staging-acceptance-runbook.md), [Production Launch Plan](production-launch.md), [Operations Runbook](operations-runbook.md), [SOP Checklists](sop-checklists.md), [Incident Response and Disaster Recovery](incident-response.md), [Incident Management](incident-management.md) |
| Reliability and scale | [Non-Functional Requirements](non-functional-requirements.md), [Performance and Scaling](performance.md), [Capacity and Performance Management](capacity-management.md), [Queue and Retry Policy](queue-retry-policy.md), [Service Continuity Plan](service-continuity-plan.md) |
| Data protection and retention | [Data Retention](data-retention.md), [File Storage Policy](file-storage-policy.md), [Backup and Restore Policy](backup-restore-policy.md) |
| Release and change control | [Release Management](release.md), [Release Candidate Manifest](release-candidate.md), [Post-Launch Maintenance and Versioning](post-launch-maintenance.md), [Change Acceptance Policy](change-acceptance-policy.md), [Migration and Version Compatibility Plan](migration-compatibility-plan.md), [Infrastructure Dependency Management](infrastructure-dependency-management.md), [License and Third-Party Component Management](license-third-party-management.md), [Technical Debt Management](technical-debt-management.md) |
| Quality control | [Implementation Roadmap](implementation-roadmap.md), [QA Test Data and Acceptance Scenarios](qa-acceptance-scenarios.md), [Acceptance Checklist](acceptance-checklist.md), [Requirements Traceability Matrix](requirements-traceability.md), [Development Standards](development.md) |

## Documentation Maintenance Rules

- Every functionality change must update the relevant documentation section in the same change set.
- Architecture changes must be documented before release approval.
- New entities, API endpoints, background jobs, configuration keys, scenarios, and external integration behavior must be documented together with implementation.
- Documentation version must match the application version and release notes.
- `CHANGELOG.md` must describe user-facing, operational, security, dependency, and documentation changes relevant to the release.
- Requirement links must be kept current in [Requirements Traceability Matrix](requirements-traceability.md).
- Technical debt must be reviewed before release according to [Technical Debt Management](technical-debt-management.md).

## Completeness Control

Before release, verify:

- Documentation matches implemented code.
- Documentation matches automated and manual tests.
- Documentation matches environment variables and configuration templates.
- OpenAPI matches implemented REST endpoints.
- Alembic migrations match the documented data model.
- Operational runbooks match the deployed infrastructure.
- Security, confidential data, logging, backup, and retention policies are current.
- Specification version is fixed for the release.
- Technical debt status is reviewed and documented.
- License and third-party component status is reviewed and documented.
- Implementation roadmap status is reviewed.

## Release Rule

The documentation set must be reviewed before every production release. A release is not ready if code, tests, configuration, deployment procedures, OpenAPI contracts, or operational runbooks contradict the current specification.

## Final Statement

The specification parts form the project documentation foundation for Tik_Tok_Loader. The set must be used as the technical assignment, architecture specification, and maintenance guide for future development.
