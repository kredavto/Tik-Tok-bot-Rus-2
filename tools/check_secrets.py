from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / ".secrets.baseline"
BINARY_SUFFIXES = {".docx", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".ico"}
TELEGRAM_TOKEN = re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b")
PRIVATE_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")


def candidate_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item.decode() for item in result.stdout.split(b"\0") if item]


def high_risk_findings() -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    for path in candidate_files():
        if path.suffix.lower() in BINARY_SUFFIXES or not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            if TELEGRAM_TOKEN.search(line):
                findings.append((str(path.relative_to(ROOT)), line_number, "Telegram bot token"))
            if PRIVATE_KEY.search(line):
                findings.append((str(path.relative_to(ROOT)), line_number, "private key"))
    return findings


def finding_keys(payload: dict[str, object]) -> set[tuple[str, int, str, str]]:
    keys: set[tuple[str, int, str, str]] = set()
    results = payload.get("results", {})
    if not isinstance(results, dict):
        return keys
    for filename, entries in results.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            keys.add(
                (
                    str(filename),
                    int(entry.get("line_number", 0)),
                    str(entry.get("type", "unknown")),
                    str(entry.get("hashed_secret", "")),
                )
            )
    return keys


def detect_new_findings() -> set[tuple[str, int, str, str]]:
    if not BASELINE.exists():
        raise RuntimeError(".secrets.baseline is missing")
    baseline_payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as temp_dir:
        candidate = Path(temp_dir) / ".secrets.baseline"
        shutil.copyfile(BASELINE, candidate)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "detect_secrets",
                "scan",
                "--baseline",
                str(candidate),
                "--exclude-files",
                r"(^|/)\.secrets\.baseline$|\.(docx|pdf|png|jpg|jpeg|gif|ico)$",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        candidate_payload = json.loads(candidate.read_text(encoding="utf-8"))
    return finding_keys(candidate_payload) - finding_keys(baseline_payload)


def main() -> int:
    failures = 0
    for filename, line_number, detector in high_risk_findings():
        print(f"High-risk secret detected: {filename}:{line_number} ({detector})")
        failures += 1

    try:
        new_findings = detect_new_findings()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"Secret scan could not run: {exc}")
        return 2

    for filename, line_number, detector, _ in sorted(new_findings):
        print(f"New potential secret: {filename}:{line_number} ({detector})")
        failures += 1

    if failures:
        print(f"Secret scan failed with {failures} finding(s).")
        return 1
    print("Secret scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
