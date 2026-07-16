from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.deploy_validation import parse_env_file, validate_environment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate staging or production deployment env")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--environment", choices=("staging", "production"), required=True)
    args = parser.parse_args()

    try:
        values = parse_env_file(args.env_file)
    except (OSError, ValueError) as exc:
        print(f"Environment validation failed: {exc}")
        return 2

    result = validate_environment(values, args.environment)
    if result.is_valid:
        print(f"Environment validation passed for {args.environment}.")
        return 0
    print(f"Environment validation failed with {len(result.errors)} error(s):")
    for error in result.errors:
        print(f"- {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
