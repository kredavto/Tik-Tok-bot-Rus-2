from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

from app.core.release_candidate import (
    ReleaseCandidateError,
    build_release_manifest,
    serialize_manifest,
)


ROOT = Path(__file__).resolve().parents[1]


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def _require_clean_tracked_state() -> None:
    status = _git("status", "--porcelain", "--untracked-files=no")
    if status:
        raise ReleaseCandidateError(
            "Tracked files must be clean before building a release candidate"
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a deterministic release candidate manifest")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if not args.allow_dirty:
            _require_clean_tracked_state()
        git_sha = _git("rev-parse", "HEAD")
        commit_timestamp = _git("show", "-s", "--format=%cI", "HEAD")
        manifest = build_release_manifest(
            root=ROOT,
            git_sha=git_sha,
            commit_timestamp=commit_timestamp,
            tracked_paths=_tracked_paths(),
            env_file=args.env_file,
        )
        output = args.output or (
            ROOT / "dist/release" / f"Tik_Tok_Loader-{manifest['version']}-{git_sha[:12]}.json"
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialize_manifest(manifest), encoding="utf-8")
    except (
        OSError,
        ValueError,
        KeyError,
        subprocess.SubprocessError,
        ReleaseCandidateError,
    ) as exc:
        print(f"Release candidate validation failed: {exc}")
        return 1

    print(f"Release candidate manifest: {output}")
    print(f"Source tree SHA-256: {manifest['source']['tree_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
