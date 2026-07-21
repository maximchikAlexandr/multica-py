from __future__ import annotations

from multica_py._internal.manifest import load_manifest


def guard_eligible_operations() -> frozenset[str]:
    manifest = load_manifest()
    return frozenset(
        entry.sdk_method for entry in manifest if entry.sdk_method and entry.status != "unsupported"
    )


def project_resource_sdk_methods() -> frozenset[str]:
    return frozenset(
        {
            "projects.resources.list",
            "projects.resources.add_local_directory",
            "projects.resources.update_local_directory",
            "projects.resources.remove",
        }
    )


def issue_project_sdk_methods() -> frozenset[str]:
    return frozenset({"issues.create", "issues.update"})
