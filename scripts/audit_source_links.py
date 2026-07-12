#!/usr/bin/env python3
"""Verify all coverage rows reference the pinned SHA and resolvable source paths."""

import re
import sys
from collections.abc import Sequence
from pathlib import Path

from multica_py._internal.manifest import ManifestEntry, load_manifest_document

COVERAGE_FILE = "specs/001-full-cli-sdk/contracts/cli-coverage.md"
MANIFEST_FILE = "src/multica_py/_generated/cli_manifest.json"


def _load_manifest_meta() -> tuple[str, str]:
    document = load_manifest_document(Path(MANIFEST_FILE))
    return document.meta.pinned_sha, document.meta.source_base


def check_coverage_md() -> list[str]:
    errors: list[str] = []
    pinned_sha, _source_base = _load_manifest_meta()
    try:
        with open(COVERAGE_FILE, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        errors.append(f"Coverage file not found: {COVERAGE_FILE}")
        return errors

    refs: list[str] = re.findall(r"blob/([a-f0-9]+)/", content)
    for sha in refs:
        if sha != pinned_sha:
            errors.append(f"Reference uses non-pinned SHA {sha} in {COVERAGE_FILE}")

    if not errors:
        print(f"[OK] All {len(refs)} references use pinned SHA {pinned_sha}")
    return errors


def check_manifest_source_files() -> list[str]:
    errors: list[str] = []
    manifest_path = Path(MANIFEST_FILE)
    if not manifest_path.exists():
        errors.append(f"Manifest not found: {MANIFEST_FILE}")
        return errors

    document = load_manifest_document(manifest_path)
    pinned_sha = document.meta.pinned_sha
    source_base = document.meta.source_base.rstrip("/") + "/"
    commands: Sequence[ManifestEntry] = document.commands
    print(f"[OK] Manifest pinned_sha matches {pinned_sha}")

    for entry in commands:
        cmd = entry.command
        status = entry.status
        if status == "unsupported":
            continue
        if not entry.source_file:
            errors.append(f"Command {cmd} missing source_file")
        else:
            expected_url = f"{source_base}{entry.source_file}"
            print(f"  {cmd} -> {expected_url}")

    if not errors:
        print(
            f"[OK] All {sum(1 for e in commands if e.status != 'unsupported')} "
            f"mapped commands have source_file"
        )
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(check_coverage_md())
    errors.extend(check_manifest_source_files())

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
