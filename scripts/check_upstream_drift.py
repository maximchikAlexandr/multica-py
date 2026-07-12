#!/usr/bin/env python3
"""Check if current upstream multica CLI differs from the pinned manifest."""

import pathlib
import subprocess
import sys

from multica_py._internal.manifest import load_manifest_document

MANIFEST_PATH = (
    pathlib.Path(__file__).parent.parent / "src" / "multica_py" / "_generated" / "cli_manifest.json"
)


def _load_manifest_commands(path: pathlib.Path) -> tuple[str, ...]:
    return tuple(entry.command for entry in load_manifest_document(path).commands)


def main() -> int:
    try:
        result = subprocess.run(
            ["multica", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        print(f"Current multica CLI available (exit code: {result.returncode})")
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"Cannot check upstream: {e}")
        return 0

    if not MANIFEST_PATH.exists():
        print(f"Manifest not found at {MANIFEST_PATH}")
        return 1

    document = load_manifest_document(MANIFEST_PATH)
    manifest_commands = _load_manifest_commands(MANIFEST_PATH)

    print(f"Pinned SHA: {document.meta.pinned_sha}")
    print(f"Manifest entries: {len(manifest_commands)}")

    cmd_count = len(manifest_commands)
    mapped = sum(1 for e in document.commands if e.sdk_method)

    if mapped < cmd_count:
        print(f"WARNING: {cmd_count - mapped} commands not mapped")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
