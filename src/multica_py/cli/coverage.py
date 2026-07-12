from __future__ import annotations

from multica_py._internal.manifest import (
    CLI_MANIFEST_PATH,
    load_manifest,
    load_manifest_document,
    validate_manifest_sdk_mapping,
)


def coverage() -> int:
    try:
        manifest = load_manifest()
    except FileNotFoundError:
        print(f"Manifest not found at {CLI_MANIFEST_PATH}")
        return 1

    document = load_manifest_document()
    pinned_sha = document.meta.pinned_sha
    total = len(manifest)
    supported = [e for e in manifest if e.status != "unsupported"]
    unsupported = [e for e in manifest if e.status == "unsupported"]
    mapped = sum(1 for e in supported if e.sdk_method)
    errors = validate_manifest_sdk_mapping(manifest)

    print(f"Pinned upstream: {pinned_sha}")
    print(f"Total CLI commands: {total}")
    print(f"SDK methods: {mapped}")
    print(
        f"Coverage: {mapped}/{len(supported)} ({mapped / len(supported) * 100:.1f}%)\n"
        if supported
        else ""
    )

    if errors:
        print("Errors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    if mapped < len(supported):
        print(f"WARNING: {len(supported) - mapped} commands are not mapped to any SDK method")
        return 1

    for u in unsupported:
        cmd = u.command
        reason = u.reason or "no reason given"
        print(f"  Unsupported: {cmd} — {reason}")

    return 0
