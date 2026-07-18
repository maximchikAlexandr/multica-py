#!/usr/bin/env python3
"""Scan live diagnostic artifacts for secret leakage."""

from __future__ import annotations

import json
import pathlib
import re
import sys

from tests.live.diagnostics import VERIFICATION_CODE

REDACTED = "***"
ENV_SECRET_PREFIXES = ("POSTGRES_PASSWORD=", "JWT_SECRET=")
TOKEN_FIELD = re.compile(r'"token"\s*:\s*"([^"]*)"')
BEARER_TOKEN = re.compile(r"Bearer (\S+)")


def scan_text_content(text: str, label: str) -> list[str]:
    """Scan text lines for secret leakage patterns.

    Args:
        text: File or blob content to inspect.
        label: Human-readable path label for findings.

    Returns:
        Human-readable finding strings; empty when clean.
    """
    findings: list[str] = []
    for line in text.splitlines():
        for prefix in ENV_SECRET_PREFIXES:
            if line.startswith(prefix):
                value = line.partition("=")[2].strip()
                if value and value != REDACTED:
                    findings.append(f"{label}: {prefix[:-1]} leaked")
        token_match = TOKEN_FIELD.search(line)
        if token_match is not None and token_match.group(1) != REDACTED:
            findings.append(f"{label}: token field not redacted")
        bearer_match = BEARER_TOKEN.search(line)
        if bearer_match is not None and bearer_match.group(1) != REDACTED:
            findings.append(f"{label}: bearer token not redacted")
        if VERIFICATION_CODE in line:
            findings.append(f"{label}: verification code leaked")
    return findings


def scan_artifact_directory(artifact_root: pathlib.Path) -> list[str]:
    """Scan every file under an artifact root for secret leakage patterns.

    Args:
        artifact_root: Directory that would be uploaded as CI diagnostics.

    Returns:
        Human-readable finding strings; empty when clean.
    """
    if not artifact_root.is_dir():
        return []
    findings: list[str] = []
    for path in sorted(artifact_root.rglob("*")):
        if not path.is_file() or path.name == "secret-scan.json":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(artifact_root)
        findings.extend(scan_text_content(text, str(rel)))
    scan_path = artifact_root / "secret-scan.json"
    if scan_path.is_file():
        payload = json.loads(scan_path.read_text(encoding="utf-8"))
        count = payload.get("finding_count")
        if isinstance(count, int) and count > 0:
            findings.append(f"secret-scan.json: {count} registered secret leak(s)")
    return findings


def scan_extra_paths(extra_paths: list[pathlib.Path]) -> list[str]:
    """Scan standalone files outside an artifact root.

    Args:
        extra_paths: Additional files such as workspace-root JUnit reports.

    Returns:
        Human-readable finding strings; empty when clean.
    """
    findings: list[str] = []
    for path in extra_paths:
        if not path.is_file():
            findings.append(f"{path}: extra scan target missing")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        findings.extend(scan_text_content(text, str(path)))
    return findings


def scan_live_artifacts(
    artifact_root: pathlib.Path,
    extra_paths: list[pathlib.Path] | None = None,
) -> list[str]:
    """Scan artifact directories and optional extra files for secret leakage.

    Args:
        artifact_root: Directory that would be uploaded as CI diagnostics.
        extra_paths: Additional files to scan before upload.

    Returns:
        Human-readable finding strings; empty when clean.
    """
    findings = scan_artifact_directory(artifact_root)
    if extra_paths:
        findings.extend(scan_extra_paths(extra_paths))
    return findings


def main(argv: list[str] | None = None) -> int:
    """Run artifact scan from CLI."""
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 1:
        print(
            "usage: scan_live_artifacts.py <artifact-root> [extra-path ...]",
            file=sys.stderr,
        )
        return 2
    findings = scan_live_artifacts(pathlib.Path(args[0]), [pathlib.Path(item) for item in args[1:]])
    if findings:
        print("\n".join(findings), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
