from __future__ import annotations

from multica_py._internal.manifest import (
    load_manifest,
    load_manifest_document,
    resolve_dotted_path,
)
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from tests._manifest_support import (
    issue_project_sdk_methods,
    operation_case_sdk_methods,
    project_resource_sdk_methods,
)


def _is_type_object(value: object) -> bool:
    return hasattr(value, "__mro__") and hasattr(value, "__bases__")


def test_every_command_has_sdk_mapping() -> None:
    manifest = load_manifest()
    missing = [e for e in manifest if e.status != "unsupported" and not e.sdk_method]
    assert not missing, f"Commands missing SDK mappings: {[e.command for e in missing]}"


def test_every_command_has_output_mode() -> None:
    manifest = load_manifest()
    missing = [e for e in manifest if not e.output_mode]
    assert not missing, f"Commands missing output_mode: {[e.command for e in missing]}"


def test_no_duplicate_sdk_mappings() -> None:
    manifest = load_manifest()
    sdk_methods = [e.sdk_method for e in manifest if e.sdk_method]
    duplicates = {m for m in sdk_methods if sdk_methods.count(m) > 1}
    assert not duplicates, f"Duplicate SDK mappings: {duplicates}"


def test_all_issue_families_present() -> None:
    manifest = load_manifest()
    commands: set[str] = {e.command for e in manifest}
    expected_prefixes = {
        "issue ",
        "issue comment ",
        "issue metadata ",
        "issue subscriber ",
        "issue label ",
    }
    for prefix in expected_prefixes:
        assert any(c.startswith(prefix) for c in commands), f"No commands with prefix {prefix}"


def test_all_core_families_present() -> None:
    manifest = load_manifest()
    commands: set[str] = {e.command for e in manifest}
    expected = {
        "auth status",
        "issue list",
        "issue create",
        "issue update",
        "project list",
        "project resource list",
        "label list",
        "agent list",
        "skill list",
        "autopilot list",
        "repo list",
        "runtime list",
        "config show",
        "version",
        "daemon status",
        "workspace list",
        "setup cloud",
    }
    for cmd in expected:
        assert cmd in commands, f"Missing required command: {cmd}"


def test_aliases_are_registered() -> None:
    manifest = load_manifest()
    all_aliases: list[str] = []
    for e in manifest:
        all_aliases.extend(e.aliases)
    assert len(all_aliases) > 0, "No aliases registered in manifest"


def test_manifest_has_meta() -> None:
    document = load_manifest_document()
    assert document.meta.pinned_sha, "Manifest meta missing pinned_sha"
    assert document.meta.source_base, "Manifest meta missing source_base"


def test_manifest_coverage_count() -> None:
    manifest = load_manifest()
    assert len(manifest) >= 100, f"Manifest only has {len(manifest)} entries, expected >= 100"


def test_every_sdk_method_resolves_on_client() -> None:
    manifest = load_manifest()
    client = MulticaClient(ClientConfig())
    for entry in manifest:
        sdk = entry.sdk_method
        if not sdk:
            continue
        resolved = resolve_dotted_path(client, sdk)
        assert resolved is not None, (
            f"sdk_method {sdk!r} (command {entry.command}) does not exist on MulticaClient"
        )
        if callable(resolved):
            continue
        assert not _is_type_object(resolved), (
            f"sdk_method {sdk!r} resolved to a class, expected a callable or attribute"
        )


def test_project_resource_sdk_methods_are_manifest_mapped() -> None:
    manifest = load_manifest()
    mapped = {entry.sdk_method for entry in manifest if entry.sdk_method}
    missing = project_resource_sdk_methods() - mapped
    assert not missing, f"Missing manifest mappings for project resources: {missing}"


def test_issue_project_paths_use_existing_issue_commands() -> None:
    manifest = load_manifest()
    mapped = {entry.sdk_method for entry in manifest if entry.sdk_method}
    assert issue_project_sdk_methods().issubset(mapped)


def test_operation_cases_cover_guard_eligible_manifest() -> None:
    manifest = load_manifest()
    mapped = {entry.sdk_method for entry in manifest if entry.sdk_method}
    assert operation_case_sdk_methods().issubset(mapped)
