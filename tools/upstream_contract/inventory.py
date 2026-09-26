"""Closed public-CLI inventory primitives.

Evidence is deliberately represented separately from approval.  The
collector may suggest rows, but only this reviewed shape can be accepted by
the approved-contract validator or the deterministic renderer.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import cast

_COMMIT = re.compile(r"^[0-9a-f]{40}$")

DISPOSITIONS = frozenset(
    {"typed", "typed-equivalent", "transport", "presentation-only", "outside-public-scope"}
)
ITEM_KINDS = frozenset({"command", "input", "output", "field", "transport"})
PUBLIC_KINDS = frozenset({"command", "input", "output", "field", "transport"})


class InventoryError(ValueError):
    """Raised when the approved public inventory is not closed."""


@dataclass(frozen=True, slots=True)
class InventoryItem:
    inventory_id: str
    kind: str
    identity: str
    disposition: str
    source_ref_ids: tuple[str, ...]
    test_ref_ids: tuple[str, ...]
    public_symbol: str | None
    transport: str | None
    compatibility: str
    rationale: str


@dataclass(frozen=True, slots=True)
class PublicInventory:
    schema_version: int
    complete: bool
    items: tuple[InventoryItem, ...]
    source_commit: str
    source_evidence_ref: str
    help_evidence_ref: str
    expected_identities: tuple[tuple[str, tuple[str, ...]], ...]
    reconciliation: tuple[tuple[str, tuple[str, ...]], ...]

    @property
    def by_id(self) -> dict[str, InventoryItem]:
        return {item.inventory_id: item for item in self.items}

    @property
    def expected_by_kind(self) -> dict[str, tuple[str, ...]]:
        return dict(self.expected_identities)

    @property
    def reconciliation_by_kind(self) -> dict[str, tuple[str, ...]]:
        return dict(self.reconciliation)


@dataclass(frozen=True, slots=True)
class HelpCommand:
    """One normalized node from recursive CLI help."""

    path: tuple[str, ...]
    positional: str = ""
    aliases: tuple[str, ...] = ()
    hidden: bool = False
    flags: tuple[str, ...] = ()


def _help_path(item: HelpCommand) -> tuple[str, ...]:
    return item.path


def _help_node(raw: object, prefix: tuple[str, ...] = ()) -> tuple[HelpCommand, ...]:
    if not isinstance(raw, dict):
        raise InventoryError("help command nodes must be objects")
    raw_dict = cast("dict[str, object]", raw)
    path_value = raw_dict.get("path", raw_dict.get("command"))
    if isinstance(path_value, str):
        path = tuple(path_value.split())
    elif isinstance(path_value, list) and all(isinstance(item, str) for item in path_value):
        path = tuple(cast("str", item) for item in path_value)
    else:
        raise InventoryError("help command path must be a string or list")
    path = prefix + path
    aliases_value = raw_dict.get("aliases", [])
    flags_value = raw_dict.get("flags", [])
    if not isinstance(aliases_value, list) or not all(
        isinstance(item, str) for item in aliases_value
    ):
        raise InventoryError("help command aliases must be strings")
    if not isinstance(flags_value, list) or not all(isinstance(item, str) for item in flags_value):
        raise InventoryError("help command flags must be strings")
    aliases = tuple(cast("str", item) for item in cast("list[object]", aliases_value))
    flags = tuple(cast("str", item) for item in cast("list[object]", flags_value))
    node = HelpCommand(
        path=path,
        positional=_string(raw.get("positional", ""), "help positional", nonblank=False),
        aliases=aliases,
        hidden=raw_dict.get("hidden", False) is True,
        flags=flags,
    )
    children = raw_dict.get("children", raw_dict.get("commands", []))
    if not isinstance(children, list):
        raise InventoryError("help command children must be a list")
    result = [node]
    for child in children:
        result.extend(_help_node(child, path))
    return tuple(result)


def parse_recursive_help(value: str | bytes | object) -> tuple[HelpCommand, ...]:
    """Normalize JSON recursive-help output into deterministic command nodes."""

    raw: object = value
    if isinstance(value, bytes):
        raw = value.decode("utf-8")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise InventoryError("recursive help must be JSON evidence") from exc
    if isinstance(raw, list):
        nodes: list[HelpCommand] = []
        for item in raw:
            nodes.extend(_help_node(item))
        return tuple(sorted(nodes, key=_help_path))
    return tuple(sorted(_help_node(raw), key=_help_path))


def reconcile_command_inventory(
    source_commands: Iterable[tuple[str, ...]], help_commands: Iterable[HelpCommand]
) -> dict[str, tuple[tuple[str, ...], ...]]:
    """Compare source registrations with recursive public help leaves."""

    source = {tuple(command) for command in source_commands}
    help_nodes = tuple(help_commands)
    paths = {node.path for node in help_nodes}
    leaves = {
        node.path
        for node in help_nodes
        if not any(other != node.path and other[: len(node.path)] == node.path for other in paths)
    }
    public_help = {node.path for node in help_nodes if not node.hidden and node.path in leaves}
    hidden = {node.path for node in help_nodes if node.hidden and node.path in leaves}
    return {
        "source_only": tuple(sorted(source - public_help - hidden)),
        "help_only": tuple(sorted(public_help - source)),
        "hidden": tuple(sorted(hidden)),
        "matched": tuple(sorted(source & public_help)),
    }


def _string(value: object, label: str, *, nonblank: bool = True) -> str:
    if not isinstance(value, str) or (nonblank and not value.strip()):
        raise InventoryError(f"{label} must be a nonblank string")
    return value


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise InventoryError(f"{label} must be a list")
    result = tuple(
        _string(item, f"{label}[{index}]") for index, item in enumerate(cast("list[object]", value))
    )
    if len(result) != len(set(result)):
        raise InventoryError(f"{label} must not contain duplicates")
    return result


def _mapping_key(pair: tuple[object, object]) -> str:
    return str(pair[0])


def _string_tuple_map(
    value: object,
    label: str,
    *,
    allowed_keys: frozenset[str] | None = None,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if not isinstance(value, dict):
        raise InventoryError(f"{label} must be an object")
    result: list[tuple[str, tuple[str, ...]]] = []
    pairs = list(cast("dict[object, object]", value).items())
    pairs.sort(key=_mapping_key)
    for key, raw_values in pairs:
        kind = _string(key, f"{label} key")
        if allowed_keys is not None and kind not in allowed_keys:
            raise InventoryError(f"{label} contains unknown kind {kind!r}")
        result.append((kind, _string_tuple(raw_values, f"{label}.{kind}")))
    return tuple(result)


def parse_inventory(raw: object) -> PublicInventory:
    """Parse and semantically validate an approved inventory document."""

    if not isinstance(raw, dict):
        raise InventoryError("inventory must be an object")
    raw_dict = cast("dict[str, object]", raw)
    required = {
        "schema_version",
        "complete",
        "items",
        "source_commit",
        "source_evidence_ref",
        "help_evidence_ref",
        "expected_identities",
        "reconciliation",
    }
    if set(raw_dict) != required:
        raise InventoryError("inventory has unknown or missing keys")
    if raw_dict["schema_version"] != 1:
        raise InventoryError("inventory schema_version must be 1")
    if not isinstance(raw_dict["complete"], bool):
        raise InventoryError("inventory.complete must be boolean")
    source_commit = _string(raw_dict["source_commit"], "inventory.source_commit")
    if not _COMMIT.fullmatch(source_commit):
        raise InventoryError("inventory.source_commit must be a full lowercase hexadecimal commit")
    source_evidence_ref = _string(raw_dict["source_evidence_ref"], "inventory.source_evidence_ref")
    help_evidence_ref = _string(raw_dict["help_evidence_ref"], "inventory.help_evidence_ref")
    expected_identities = _string_tuple_map(
        raw_dict["expected_identities"],
        "inventory.expected_identities",
        allowed_keys=ITEM_KINDS,
    )
    reconciliation = _string_tuple_map(
        raw_dict["reconciliation"],
        "inventory.reconciliation",
        allowed_keys=frozenset(
            {"source_only", "help_only", "unresolved_factories", "unresolved_aliases"}
        ),
    )
    raw_items = raw_dict["items"]
    if not isinstance(raw_items, list):
        raise InventoryError("inventory.items must be a list")
    items: list[InventoryItem] = []
    for index, raw_item in enumerate(cast("list[object]", raw_items)):
        label = f"inventory.items[{index}]"
        if not isinstance(raw_item, dict):
            raise InventoryError(f"{label} must be an object")
        raw_item_dict = cast("dict[str, object]", raw_item)
        required_item = {
            "inventory_id",
            "kind",
            "identity",
            "disposition",
            "source_ref_ids",
            "test_ref_ids",
            "public_symbol",
            "transport",
            "compatibility",
            "rationale",
        }
        if set(raw_item_dict) != required_item:
            raise InventoryError(f"{label} has unknown or missing keys")
        kind = _string(raw_item_dict["kind"], f"{label}.kind")
        if kind not in ITEM_KINDS:
            raise InventoryError(f"{label}.kind is not approved")
        disposition = _string(raw_item_dict["disposition"], f"{label}.disposition")
        if disposition not in DISPOSITIONS:
            raise InventoryError(f"{label}.disposition is not approved")
        public_symbol = raw_item_dict["public_symbol"]
        if public_symbol is not None:
            public_symbol = _string(public_symbol, f"{label}.public_symbol")
        transport = raw_item_dict["transport"]
        if transport is not None:
            transport = _string(transport, f"{label}.transport")
        if disposition in {"typed", "typed-equivalent"} and public_symbol is None:
            raise InventoryError(f"{label} typed disposition requires public_symbol")
        if disposition == "transport" and transport is None:
            raise InventoryError(f"{label} transport disposition requires transport")
        if disposition in {"presentation-only", "outside-public-scope"} and not _string(
            raw_item_dict["rationale"], f"{label}.rationale"
        ):
            raise InventoryError(f"{label} exclusion disposition requires rationale")
        items.append(
            InventoryItem(
                _string(raw_item_dict["inventory_id"], f"{label}.inventory_id"),
                kind,
                _string(raw_item_dict["identity"], f"{label}.identity"),
                disposition,
                _string_tuple(raw_item_dict["source_ref_ids"], f"{label}.source_ref_ids"),
                _string_tuple(raw_item_dict["test_ref_ids"], f"{label}.test_ref_ids"),
                public_symbol,
                transport,
                _string(raw_item_dict["compatibility"], f"{label}.compatibility"),
                _string(raw_item_dict["rationale"], f"{label}.rationale"),
            )
        )
    ids = [item.inventory_id for item in items]
    identities = [(item.kind, item.identity) for item in items]
    if len(ids) != len(set(ids)):
        raise InventoryError("inventory IDs must be unique")
    if len(identities) != len(set(identities)):
        raise InventoryError("inventory identities must be unique per kind")
    complete = raw_dict["complete"]
    if complete and not items:
        raise InventoryError("a complete inventory must contain reviewed items")
    if complete and any(not item.source_ref_ids or not item.test_ref_ids for item in items):
        raise InventoryError("every complete inventory item needs source and test evidence")
    expected_by_kind = {kind: tuple(sorted(values)) for kind, values in expected_identities}
    if complete and set(expected_by_kind) != ITEM_KINDS:
        raise InventoryError("complete inventory must declare every approved item kind")
    actual_by_kind: dict[str, list[str]] = {}
    for item in items:
        actual_by_kind.setdefault(item.kind, []).append(item.identity)
    actual = {kind: tuple(sorted(values)) for kind, values in actual_by_kind.items()}
    if complete and actual != expected_by_kind:
        raise InventoryError("inventory does not exactly cover expected public identities")
    reconciliation_by_kind = dict(reconciliation)
    if complete and any(reconciliation_by_kind.values()):
        raise InventoryError("inventory contains unresolved source/help review items")
    return PublicInventory(
        1,
        complete,
        tuple(items),
        source_commit,
        source_evidence_ref,
        help_evidence_ref,
        expected_identities,
        reconciliation,
    )


def validate_inventory(
    raw: object,
    *,
    source_ref_ids: Iterable[str] = (),
    test_ref_ids: Iterable[str] = (),
    expected_identities: Mapping[str, str] | None = None,
) -> PublicInventory:
    """Validate references and optional expected public identity coverage."""

    inventory = parse_inventory(raw)
    known_sources = set(source_ref_ids)
    known_tests = set(test_ref_ids)
    for item in inventory.items:
        if known_sources and not set(item.source_ref_ids) <= known_sources:
            raise InventoryError(f"{item.inventory_id} references unknown source evidence")
        if known_tests and not set(item.test_ref_ids) <= known_tests:
            raise InventoryError(f"{item.inventory_id} references unknown test evidence")
        if item.disposition == "outside-public-scope" and item.kind in PUBLIC_KINDS:
            if item.public_symbol is not None or item.transport is not None:
                raise InventoryError(
                    f"{item.inventory_id} outside-public-scope rows cannot expose a public link"
                )
    if expected_identities is not None:
        actual = {item.inventory_id: item.identity for item in inventory.items}
        if actual != dict(expected_identities):
            raise InventoryError("inventory does not exactly cover the expected public identities")
    return inventory


__all__ = [
    "DISPOSITIONS",
    "ITEM_KINDS",
    "InventoryError",
    "InventoryItem",
    "PublicInventory",
    "parse_inventory",
    "validate_inventory",
]
