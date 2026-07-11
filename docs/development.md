# Development Standards

All development must preserve the requirements in [Architecture Summary](architecture-summary.md) and the subsystem boundaries in [Project Component Map](component-map.md).

The full documentation entry point is [Specification Index](specification-index.md).

## Repository Structure

```text
Tik-Tok-bot-Rus-2/
├── app/
├── tests/
├── docs/
├── deploy/
├── alembic/
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

## Coding Standards

- Python 3.12.
- Type hints for public functions, methods, and data structures.
- Ruff for linting and formatting checks.
- Public functions and classes should include docstrings when their behavior is not obvious from the name and type signature.
- Business logic, API handlers, data access, security, worker code, and infrastructure code stay in separate modules.

Project terminology and naming rules are documented in [Glossary and Naming Conventions](glossary-naming.md).

## Git Workflow

1. Create a feature branch from the latest `main`.
2. Make focused commits.
3. Add or update tests.
4. Add Alembic migrations for schema changes.
5. Update documentation and `CHANGELOG.md`.
6. Open a pull request.
7. Pass CI.
8. Complete code review before merge.

Do not commit:

- `.env`
- secrets
- private keys
- production backups
- raw OAuth tokens

Repository workflow details and branch protection recommendations are documented in [GitHub Workflow](github-workflow.md).

Feature expansion rules are documented in [Feature Development Plan](feature-development-plan.md).

Database validation, constraints, transactions, and data consistency rules are documented in [Data Quality and Integrity](data-quality-integrity.md).

Entity relationships are documented in [Logical Data Model](data-model.md).

Post-launch change acceptance rules are documented in [Change Acceptance Policy](change-acceptance-policy.md).

Technical debt tracking and review rules are documented in [Technical Debt Management](technical-debt-management.md).

## Quality Gates

Before merge:

```bash
ruff format --check .
ruff check .
mypy app
pytest
docker compose run --rm api alembic upgrade head
docker compose build
detect-secrets scan --all-files --exclude-files '\.git/.*|\.env\.example'
```

## Compatibility

Public REST methods use `/api/v1`. New API versions must be introduced without breaking existing clients.

REST response format and API compatibility rules are documented in [REST API Standards](rest-api-standards.md).
