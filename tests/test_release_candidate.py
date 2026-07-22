from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import UniqueConstraint

from app.core.release_candidate import (
    REQUIRED_QUALITY_GATES,
    ReleaseCandidateError,
    alembic_heads,
    build_release_manifest,
    collect_version_report,
    digest_source_files,
    serialize_manifest,
    validate_release_target,
    validate_semver,
)
from app.db.models import Payment, SystemSetting, User


ROOT = Path(__file__).resolve().parents[1]


def test_current_release_version_is_consistent() -> None:
    report = collect_version_report(ROOT)

    assert report.version == "0.2.0"
    assert set(report.sources.values()) == {report.version}


def test_release_candidate_cli_bootstraps_repository_imports() -> None:
    result = subprocess.run(
        [sys.executable, "-I", str(ROOT / "tools/build_release_candidate.py"), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Build a deterministic release candidate manifest" in result.stdout


def test_runtime_environment_version_must_match(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("APP_VERSION=9.9.9\n", encoding="utf-8")

    with pytest.raises(ReleaseCandidateError, match="do not match"):
        collect_version_report(ROOT, env_file=env_file)


@pytest.mark.parametrize("value", ["1", "v1.2.3", "01.2.3", "1.2.3-"])
def test_invalid_semver_is_rejected(value: str) -> None:
    with pytest.raises(ReleaseCandidateError, match="Invalid SemVer"):
        validate_semver(value)


def test_source_tree_digest_is_order_independent(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("alpha", encoding="utf-8")
    (tmp_path / "b.txt").write_text("beta", encoding="utf-8")

    first_files, first_digest = digest_source_files(tmp_path, ["b.txt", "a.txt"])
    second_files, second_digest = digest_source_files(tmp_path, ["a.txt", "b.txt"])

    assert first_files == second_files
    assert first_digest == second_digest


def test_current_migration_tree_has_one_head() -> None:
    heads, count = alembic_heads(ROOT)

    assert heads == ["0011_unlimit_and_usage_refunds"]
    assert count == 11


@pytest.mark.parametrize(
    ("model", "column_name", "index_name"),
    [
        (User, "telegram_id", "ix_users_telegram_id"),
        (Payment, "provider_invoice_id", "ix_payments_provider_invoice_id"),
        (SystemSetting, "key", "ix_system_settings_key"),
    ],
)
def test_unique_lookup_columns_match_migration_constraints(
    model: type[User] | type[Payment] | type[SystemSetting],
    column_name: str,
    index_name: str,
) -> None:
    table = model.__table__
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    index = next(item for item in table.indexes if item.name == index_name)

    assert (column_name,) in unique_columns
    assert tuple(column.name for column in index.columns) == (column_name,)
    assert index.unique is False


def test_manifest_is_deterministic_and_contains_no_file_contents() -> None:
    tracked_paths = [
        "pyproject.toml",
        "app/__init__.py",
        "app/core/config.py",
        ".env.example",
        "deploy/env.development.example",
        "deploy/env.staging.example",
        "deploy/env.production.example",
        "CHANGELOG.md",
    ]
    kwargs = {
        "root": ROOT,
        "git_sha": "a" * 40,
        "commit_timestamp": "2026-07-14T09:00:00+03:00",
        "tracked_paths": tracked_paths,
    }

    first = build_release_manifest(**kwargs)
    second = build_release_manifest(**kwargs)
    serialized = serialize_manifest(first)

    assert first == second
    assert first["version"] == "0.2.0"
    assert first["release_channel"] == "stable"
    assert first["database"]["alembic_heads"] == ["0011_unlimit_and_usage_refunds"]
    assert first["required_quality_gates"] == list(REQUIRED_QUALITY_GATES)
    assert "replace_me" not in serialized
    assert "TELEGRAM_BOT_TOKEN=" not in serialized
    assert serialized == serialize_manifest(second)


def test_manifest_rejects_invalid_git_sha() -> None:
    with pytest.raises(ReleaseCandidateError, match="Git SHA"):
        build_release_manifest(
            root=ROOT,
            git_sha="not-a-sha",
            commit_timestamp="2026-07-14T09:00:00+03:00",
            tracked_paths=["pyproject.toml"],
        )


def test_prerelease_cannot_target_production() -> None:
    with pytest.raises(ReleaseCandidateError, match="cannot be deployed"):
        validate_release_target("0.2.0-rc.1", "production")
