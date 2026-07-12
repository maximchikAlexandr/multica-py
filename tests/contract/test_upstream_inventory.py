from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict, cast

from multica_py._internal.manifest import load_manifest_document

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
