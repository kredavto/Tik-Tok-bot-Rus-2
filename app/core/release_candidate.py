from __future__ import annotations

import ast
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import tomllib
from typing import Any, Iterable

from app.core.deploy_validation import parse_env_file


SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
VERSION_ENV_FILES = (
    ".env.example",
    "deploy/env.development.example",
    "deploy/env.staging.example",
    "deploy/env.production.example",
)
REQUIRED_QUALITY_GATES = (
    "format",
    "lint",
    "type-check",
    "openapi",
    "secret-scan",
    "migration-lifecycle",
    "tests-and-coverage",
    "container-build",
    "non-root-runtime",
)


class ReleaseCandidateError(RuntimeError):
    """Raised when source state cannot produce a trustworthy release candidate."""


@dataclass(frozen=True)
class SourceFileDigest:
    path: str
    sha256: str
    size: int


@dataclass(frozen=True)
class VersionReport:
    version: str
    sources: dict[str, str]


def validate_semver(value: str) -> str:
    if not SEMVER_PATTERN.fullmatch(value):
        raise ReleaseCandidateError(f"Invalid SemVer version: {value}")
    return value


def _assignment_string(path: Path, variable_name: str, *, class_name: str | None = None) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    body: Iterable[ast.stmt] = tree.body
    if class_name:
        class_node = next(
            (
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == class_name
            ),
            None,
        )
        if class_node is None:
            raise ReleaseCandidateError(f"{path}: class {class_name} was not found")
        body = class_node.body

    for node in body:
        target_name: str | None = None
        value: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            target_name = target.id if isinstance(target, ast.Name) else None
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            target_name = node.target.id if isinstance(node.target, ast.Name) else None
            value = node.value
        if target_name != variable_name or value is None:
            continue
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return value.value
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "Field"
            and value.args
            and isinstance(value.args[0], ast.Constant)
            and isinstance(value.args[0].value, str)
        ):
            return value.args[0].value
    raise ReleaseCandidateError(f"{path}: {variable_name} string assignment was not found")


def collect_version_report(root: Path, env_file: Path | None = None) -> VersionReport:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    sources = {
        "pyproject.toml": str(project["project"]["version"]),
        "app/__init__.py": _assignment_string(root / "app/__init__.py", "__version__"),
        "app/core/config.py": _assignment_string(
            root / "app/core/config.py",
            "app_version",
            class_name="Settings",
        ),
    }
    for relative_path in VERSION_ENV_FILES:
        sources[relative_path] = parse_env_file(root / relative_path).get("APP_VERSION", "")
    if env_file is not None:
        sources["runtime-env"] = parse_env_file(env_file).get("APP_VERSION", "")

    versions = set(sources.values())
    if len(versions) != 1:
        details = ", ".join(f"{name}={value or '<missing>'}" for name, value in sources.items())
        raise ReleaseCandidateError(f"Version sources do not match: {details}")
    version = validate_semver(versions.pop())
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## [{version}]" not in changelog:
        raise ReleaseCandidateError(f"CHANGELOG.md has no release heading for {version}")
    return VersionReport(version=version, sources=sources)


def digest_source_files(
    root: Path, relative_paths: Iterable[str]
) -> tuple[list[SourceFileDigest], str]:
    digests: list[SourceFileDigest] = []
    aggregate = sha256()
    for relative_path in sorted(set(relative_paths)):
        path = root / relative_path
        if not path.is_file():
            raise ReleaseCandidateError(f"Tracked source file is missing: {relative_path}")
        content = path.read_bytes()
        digest = sha256(content).hexdigest()
        item = SourceFileDigest(path=relative_path, sha256=digest, size=len(content))
        digests.append(item)
        aggregate.update(relative_path.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(digest.encode("ascii"))
        aggregate.update(b"\0")
        aggregate.update(str(len(content)).encode("ascii"))
        aggregate.update(b"\n")
    if not digests:
        raise ReleaseCandidateError("Release candidate has no tracked source files")
    return digests, aggregate.hexdigest()


def alembic_heads(root: Path) -> tuple[list[str], int]:
    revisions: set[str] = set()
    parents: set[str] = set()
    migration_files = sorted((root / "alembic/versions").glob("*.py"))
    for path in migration_files:
        if path.name == "__init__.py":
            continue
        revision = _assignment_string(path, "revision")
        revisions.add(revision)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
                continue
            if node.target.id != "down_revision" or node.value is None:
                continue
            try:
                parent_value = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                parent_value = None
            if isinstance(parent_value, str):
                parents.add(parent_value)
            elif isinstance(parent_value, (tuple, list)):
                parents.update(item for item in parent_value if isinstance(item, str))
    heads = sorted(revisions - parents)
    if len(heads) != 1:
        raise ReleaseCandidateError(f"Expected exactly one Alembic head, found: {heads}")
    return heads, len(revisions)


def build_release_manifest(
    *,
    root: Path,
    git_sha: str,
    commit_timestamp: str,
    tracked_paths: Iterable[str],
    env_file: Path | None = None,
) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{40}", git_sha):
        raise ReleaseCandidateError("Git SHA must contain 40 lowercase hexadecimal characters")
    version_report = collect_version_report(root, env_file=env_file)
    files, tree_digest = digest_source_files(root, tracked_paths)
    heads, migration_count = alembic_heads(root)
    version_match = SEMVER_PATTERN.fullmatch(version_report.version)
    if version_match is None:
        raise ReleaseCandidateError(f"Invalid SemVer version: {version_report.version}")
    prerelease = version_match.group(4)
    target_environment = "unspecified"
    if env_file is not None:
        target_environment = parse_env_file(env_file).get("APP_ENV", "") or "unspecified"
        if target_environment == "production" and prerelease:
            raise ReleaseCandidateError(
                "Prerelease versions cannot be deployed to the production environment"
            )
    return {
        "schema_version": 1,
        "project": "Tik_Tok_Loader",
        "version": version_report.version,
        "release_channel": "candidate" if prerelease else "stable",
        "target_environment": target_environment,
        "source": {
            "git_sha": git_sha,
            "commit_timestamp": commit_timestamp,
            "tree_sha256": tree_digest,
            "files": [item.__dict__ for item in files],
        },
        "database": {
            "alembic_heads": heads,
            "migration_count": migration_count,
        },
        "required_quality_gates": list(REQUIRED_QUALITY_GATES),
        "version_sources": version_report.sources,
    }


def serialize_manifest(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
