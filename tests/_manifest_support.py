from __future__ import annotations

from multica_py._internal.manifest import load_manifest


def guard_eligible_operations() -> frozenset[str]:
    manifest = load_manifest()
    return frozenset(
        entry.sdk_method for entry in manifest if entry.sdk_method and entry.status != "unsupported"
    )
