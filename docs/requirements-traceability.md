# Requirements Traceability Matrix

## Purpose

Each functional requirement must have a stable identifier and a visible link to implementation, tests, and documentation.

## Initial Matrix

| ID | Requirement | Component | Test | Documentation | Status |
| --- | --- | --- | --- | --- | --- |
| `REQ-001` | User registration | Telegram Bot | `QA-REG-001` | [Users Entity](users-entity.md), [QA Scenarios](qa-acceptance-scenarios.md) | Planned |
| `REQ-002` | TikTok OAuth | FastAPI / OAuth | `QA-OAUTH-001` | [TikTok Developer Configuration](tiktok-developer-configuration.md), [Public REST API](public-rest-api.md) | Planned |
| `REQ-003` | PRO/BUSINESS payment | Robokassa | `QA-PAY-001` | [Payments Entity](payments-entity.md), [Robokassa Setup](robokassa.md) | Planned |
| `REQ-004` | Video publication | Worker / TikTok API | `QA-UPL-001` | [Upload Jobs Entity](upload-jobs-entity.md), [Video Lifecycle](video-lifecycle.md) | Planned |
| `REQ-005` | Daily limits | `daily_usage` | `QA-LIMIT-001` | [Daily Usage Entity](daily-usage-entity.md) | Planned |
| `NFR-001` | Performance, reliability, security, maintainability, and scalability controls | Cross-cutting | Release readiness checks | [Non-Functional Requirements](non-functional-requirements.md) | Planned |
| `NFR-002` | Security logging and audit | Observability / Audit | Release readiness checks | [Security Logging and Audit](security-logging-audit.md) | Planned |
| `NFR-003` | Infrastructure dependency management | Deployment / Operations | Post-update checks | [Infrastructure Dependency Management](infrastructure-dependency-management.md) | Planned |
| `NFR-004` | Confidential data management | Security / Configuration | Release readiness checks | [Confidential Data Policy](confidential-data-policy.md) | Planned |
| `DOC-001` | Specification index and documentation maintenance | Documentation | Release readiness checks | [Specification Index](specification-index.md) | Planned |
| `CFG-001` | Environment configuration and secrets control | Configuration / Security | Release readiness checks | [Environment Configuration and Secrets Control](environment-configuration-secrets.md) | Planned |
| `TD-001` | Technical debt management | Development / Maintenance | Release readiness checks | [Technical Debt Management](technical-debt-management.md) | Planned |
| `DEP-001` | License and third-party component management | Dependencies / Release | Release readiness checks | [License and Third-Party Component Management](license-third-party-management.md) | Planned |
| `API-001` | API versioning and client compatibility | REST API / OpenAPI | Compatibility checks | [API Versioning and Client Compatibility](api-versioning-compatibility.md) | Planned |
| `ROAD-001` | Final implementation roadmap | Delivery / Release | Roadmap control points | [Implementation Roadmap](implementation-roadmap.md) | Planned |

## Maintenance Rules

- Every new requirement receives a unique `REQ-###` identifier.
- Every new acceptance scenario receives a unique `QA-...` identifier.
- Requirement changes must update implementation, tests, and documentation links.
- Removing a requirement must be documented in `CHANGELOG.md`.
- The matrix must be reviewed before every release.
- A requirement is complete only when implementation, automated or manual QA coverage, and documentation are all present.

## Completion Criterion

The project is release-ready only when every approved requirement has traceability to implementation, tests, and documentation.
