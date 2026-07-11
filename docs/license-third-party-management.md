# License and Third-Party Component Management

This document defines how Tik_Tok_Loader tracks third-party components, validates licenses, and controls dependency security.

## Component Registry

The dependency registry must cover:

- Python runtime and project packages from `pyproject.toml`.
- FastAPI and aiogram.
- SQLAlchemy and Alembic.
- Redis and PostgreSQL.
- FFmpeg and FFprobe.
- Docker, Docker Compose, and Nginx.
- Docker base images.
- CI tools, linters, type checkers, test tools, and secret scanners.

Each registry entry should include:

| Field | Purpose |
| --- | --- |
| Component | Package, image, binary, or service name |
| Version | Current allowed or deployed version |
| Source | Package index, official image, vendor site, OS package, or repository |
| License | License name and link when available |
| Usage | Runtime, development, CI, deployment, or operations |
| Owner | Person or team responsible for review |
| Notes | Exceptions, constraints, or special usage conditions |

## License Checks

- Record licenses for all external libraries and runtime components.
- Check license compatibility before adding a dependency.
- Document exceptions and special conditions before release approval.
- Recheck license metadata when dependencies are upgraded.
- Avoid dependencies with unclear origin or incompatible licensing.

## Security Control

- Regularly check known vulnerabilities for Python packages, Docker base images, OS packages, PostgreSQL, Redis, Nginx, FFmpeg, and CI tools.
- Update dependencies only after staging verification.
- Remove unused libraries, binaries, images, and tooling when safe.
- Keep versions constrained in dependency files and deployment configuration.
- Document dependency and component changes in `CHANGELOG.md` when they affect runtime, security, operations, or compatibility.

## Review Before Adding a Dependency

Before adding a third-party component:

1. Confirm the component is necessary and not already covered by an existing dependency.
2. Confirm the source is trustworthy.
3. Confirm the license is acceptable for the project.
4. Confirm maintenance activity and security posture.
5. Confirm staging compatibility.
6. Update dependency files, documentation, tests, and `CHANGELOG.md` where relevant.

## Release Requirements

Before release:

- Dependency versions are documented.
- License exceptions are reviewed.
- Known critical vulnerabilities are resolved or explicitly risk-accepted.
- Unused dependencies are reviewed for removal.
- Staging verification passes after dependency changes.

## Related Documents

- [Dependencies and Third-Party Services](dependencies-and-integrations.md)
- [Infrastructure Dependency Management](infrastructure-dependency-management.md)
- [Release Management](release.md)
- [Technical Debt Management](technical-debt-management.md)
