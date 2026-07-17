# Release Candidate Manifest

The release candidate manifest is deterministic, secret-free evidence that identifies the exact
source tree proposed for staging. It complements CI results and provider-backed acceptance records;
it does not replace either of them.

## Current Release

The current stable production version is `0.2.0`. The version is synchronized across
`pyproject.toml`, `app.__version__`, the application configuration default, and all environment
templates. `CHANGELOG.md` contains a matching release heading.

The release was promoted from `0.2.0-rc.1` after automated quality gates, production Robokassa
acceptance, and a real Telegram Stars payment and refund scenario passed. TikTok publication stays
disabled by configuration until official OAuth, Sandbox, and Content Posting acceptance are
complete. The manifest builder continues to reject any prerelease when the supplied runtime
environment contains `APP_ENV=production`.

## Manifest Contents

The JSON artifact contains:

- schema version, project name, application version, and release channel;
- target environment when a runtime `.env` is supplied;
- full Git commit SHA and deterministic commit timestamp;
- path, byte size, and SHA-256 digest for every tracked source file;
- aggregate SHA-256 digest for the tracked source tree;
- the single Alembic head and migration count;
- the list of required quality gates; and
- version-source identifiers and their common non-secret version value.

The artifact never copies file contents, environment values other than `APP_ENV` and
`APP_VERSION`, tokens, passwords, signatures, OAuth payloads, or payment data.

## Local Generation

Generate evidence only from a clean tracked worktree:

```bash
python tools/build_release_candidate.py
```

The default output is written under ignored `dist/release/`. For a staging deployment:

```bash
python tools/build_release_candidate.py \
  --env-file .env \
  --output .deploy/release-manifest.json
```

`--allow-dirty` is available only for development diagnostics. A manifest created with that option
is not release evidence because its Git SHA may not describe working-tree changes.

## CI and Deployment

GitHub Actions creates `release-candidate-manifest` only after quality, PostgreSQL integration,
migration, coverage, container-build, and non-root checks succeed. The artifact is retained for 30
days and is attached to the exact workflow commit.

The deployment script regenerates `.deploy/release-manifest.json` after checking out the requested
commit and before building the application image. It also compares the server-side `APP_VERSION`
with every version source. A mismatch, dirty tracked tree, invalid SemVer, multiple Alembic heads,
or production prerelease stops deployment before image construction.

## Staging Evidence

Record these values in the staging acceptance result:

- manifest filename and artifact URL;
- application version and full Git SHA;
- aggregate source-tree SHA-256;
- Alembic head;
- CI workflow URL; and
- sanitized acceptance outcomes from the staging runbook.

The production approver must be able to match the promoted stable commit to the accepted release
candidate and review every change introduced during promotion.
