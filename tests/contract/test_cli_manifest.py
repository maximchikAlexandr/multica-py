from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict, cast

from multica_py._internal.manifest import (
    CLI_MANIFEST_PATH,
    load_manifest,
    load_manifest_document,
    validate_manifest_sdk_mapping,
)

RAW_INVENTORY_PATH = Path("tests/fixtures/provenance/upstream_commands.json")


class RawInventoryMeta(TypedDict):
    pinned_sha: str


class RawInventory(TypedDict):
    _meta: RawInventoryMeta
    commands: list[str]
    aliases: dict[str, str]


def _load_raw_inventory() -> RawInventory:
    with open(RAW_INVENTORY_PATH, encoding="utf-8") as f:
        return cast("RawInventory", json.load(f))


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


def test_raw_inventory_sha_matches_manifest() -> None:
    raw = _load_raw_inventory()
    manifest = load_manifest_document()
    assert raw["_meta"]["pinned_sha"] == manifest.meta.pinned_sha


def test_every_upstream_command_in_manifest() -> None:
    raw = _load_raw_inventory()
    manifest = load_manifest_document()
    manifest_cmds = {e.command for e in manifest.commands}
    for cmd in raw["commands"]:
        assert cmd in manifest_cmds, f"Upstream command {cmd!r} missing from manifest"


def test_no_manifest_command_without_upstream_explanation() -> None:
    raw = _load_raw_inventory()
    manifest = load_manifest_document()
    upstream = set(raw["commands"])
    for entry in manifest.commands:
        cmd = entry.command
        if cmd not in upstream:
            status = entry.status
            assert status, (
                f"Command {cmd!r} not in upstream inventory and has no status explanation"
            )
            assert entry.reason, f"Command {cmd!r} has status {status!r} but no reason"


def test_every_alias_in_manifest() -> None:
    raw = _load_raw_inventory()
    manifest = load_manifest_document()
    manifest_aliases: dict[str, str] = {}
    for e in manifest.commands:
        for a in e.aliases:
            manifest_aliases[a] = e.command
    for alias, target in raw["aliases"].items():
        assert alias in manifest_aliases, f"Alias {alias!r} (-> {target}) missing from manifest"
        assert manifest_aliases[alias] == target, (
            f"Alias {alias!r} maps to {manifest_aliases[alias]!r}, expected {target!r}"
        )


def test_manifest_covers_all_upstream_commands() -> None:
    raw = _load_raw_inventory()
    manifest = load_manifest_document()
    supported = [e for e in manifest.commands if not e.status]
    assert len(supported) >= len(raw["commands"]) - 2
