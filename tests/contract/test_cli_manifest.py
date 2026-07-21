from __future__ import annotations

from multica_py._internal.manifest import (
    CLI_MANIFEST_PATH,
    load_manifest,
    load_manifest_document,
    validate_manifest_sdk_mapping,
)


def test_manifest_exists() -> None:
    assert CLI_MANIFEST_PATH.exists()


def test_manifest_is_valid_json() -> None:
    manifest = load_manifest()
    assert isinstance(manifest, tuple)


def test_manifest_has_no_duplicate_mappings() -> None:
    manifest = load_manifest()
    errors = validate_manifest_sdk_mapping(manifest)
    assert not errors, f"Manifest validation errors: {errors}"


def test_manifest_commands_have_required_fields() -> None:
    manifest = load_manifest()
    for entry in manifest:
        assert entry.command, f"Entry missing command: {entry}"
        assert entry.output_mode, f"Entry {entry.command} missing output_mode"


def test_manifest_unsupported_commands_have_reason() -> None:
    manifest = load_manifest()
    for entry in manifest:
        if entry.status == "unsupported":
            assert entry.reason, f"Unsupported command {entry.command} missing reason"
            assert entry.sdk_method == "", (
                f"Unsupported command {entry.command} should have empty sdk_method"
            )


def test_manifest_allowed_status_values() -> None:
    manifest = load_manifest()
    allowed = {"", "unsupported", "hidden", "deprecated"}
    for entry in manifest:
        assert entry.status in allowed, f"Entry {entry.command} has invalid status: {entry.status}"


def test_manifest_source_files_present() -> None:
    manifest = load_manifest()
    for entry in manifest:
        if entry.status == "unsupported":
            continue
        assert entry.source_file, f"Entry {entry.command} missing source_file"


def test_manifest_pinned_sha_matches() -> None:
    document = load_manifest_document()
    assert len(document.meta.pinned_sha) == 40
    assert document.meta.source_base.endswith(f"{document.meta.pinned_sha}/server/cmd/multica/")


def test_manifest_includes_project_resource_commands() -> None:
    manifest = load_manifest()
    commands = {entry.command for entry in manifest}
    expected = {
        "project resource list",
        "project resource add",
        "project resource update",
        "project resource remove",
    }
    missing = expected - commands
    assert not missing, f"Missing project resource commands: {missing}"
