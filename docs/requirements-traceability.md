# Requirements Traceability Matrix

## Purpose

Each functional requirement must have a stable identifier and a visible link to implementation, tests, and documentation.

## Current Matrix

| ID | Requirement | Component | Test evidence | Docs | Status |
| --- | --- | --- | --- | --- | --- |
| `REQ-001` | User registration | Bot / DB | `QA-REG-001`; subscriptions and FSM tests | [Users](users-entity.md), [QA](qa-acceptance-scenarios.md) | Implemented |
| `REQ-002` | TikTok OAuth | API / OAuth | `QA-OAUTH-001`; API and TikTok tests | [TikTok Config](tiktok-developer-configuration.md), [Public API](public-rest-api.md) | Implemented; staging pending |
| `REQ-003` | Paid plans | Robokassa | `QA-PAY-001`; payment idempotency tests | [Payments](payments-entity.md), [Robokassa](robokassa.md) | Implemented; staging pending |
| `REQ-004` | Video publication | Worker / TikTok | `QA-UPL-001`; FSM, video, worker, and lifecycle tests | [Upload Jobs](upload-jobs-entity.md), [Lifecycle](video-lifecycle.md) | Implemented; staging pending |
| `REQ-005` | Daily limits | Usage service | `QA-LIMIT-001`; quota concurrency tests | [Daily Usage](daily-usage-entity.md) | Implemented |
| `NFR-001` | Core NFR controls | Cross-cutting | CI quality, coverage, migration, container | [NFR](non-functional-requirements.md), [Tests](test-strategy.md) | Implemented; production evidence pending |
| `NFR-002` | Security audit | Audit | Admin, tracing, webhook, secret scan | [Security Audit](security-logging-audit.md) | Implemented |
| `NFR-003` | Infrastructure dependencies | Operations | Container and post-update checks | [Infrastructure](infrastructure-dependency-management.md) | Implemented; staging pending |
| `NFR-004` | Confidential data | Security | Encryption and secret-scan tests | [Data Policy](confidential-data-policy.md) | Implemented |
| `DOC-001` | Documentation maintenance | Documentation | Unified build and release review | [Spec Index](specification-index.md) | Implemented |
| `CFG-001` | Environment and secrets | Configuration | Config and deploy-validator tests | [Environment](environment-configuration-secrets.md) | Implemented |
| `TD-001` | Technical debt | Development | Release readiness review | [Technical Debt](technical-debt-management.md) | Process defined |
| `DEP-001` | Licenses and components | Dependencies | Dependency and release review | [Licenses](license-third-party-management.md) | Process defined |
| `API-001` | API compatibility | REST / OpenAPI | OpenAPI checker and API tests | [API Versioning](api-versioning-compatibility.md) | Implemented |
| `ROAD-001` | Implementation roadmap | Delivery | Preflight, smoke, and roadmap control points | [Roadmap](implementation-roadmap.md), [Staging Runbook](staging-acceptance-runbook.md) | Stage 10 automation done; external acceptance pending |
| `OPS-001` | Controlled production launch | Operations | Deploy validator and webhook-management tests | [Production Launch](production-launch.md), [Staging Runbook](staging-acceptance-runbook.md) | Implemented; provider evidence pending |

## Maintenance Rules

- Every new requirement receives a unique `REQ-###` identifier.
- Every new acceptance scenario receives a unique `QA-...` identifier.
- Requirement changes must update implementation, tests, and documentation links.
- Removing a requirement must be documented in `CHANGELOG.md`.
- The matrix must be reviewed before every release.
- A requirement is complete only when implementation, automated or manual QA coverage, and documentation are all present.

## Completion Criterion

The project is release-ready only when every approved requirement has traceability to implementation, tests, and documentation.
