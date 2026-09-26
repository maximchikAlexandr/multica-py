from __future__ import annotations

import io
from pathlib import Path

import pytest

from multica_py._internal.content import SafeContent
from multica_py._internal.wire_presence import field_presence, presence, struct_presence
from multica_py.models.system import DaemonLaunchOptions
from multica_py.sentinels import Unset
from tools.upstream_contract.inventory import (
    InventoryError,
    parse_inventory,
    parse_recursive_help,
    reconcile_command_inventory,
    validate_inventory,
)


def test_safe_content_materializes_without_closing_caller_stream(tmp_path: Path) -> None:
    stream = io.BytesIO(b"secret")
    content = SafeContent.stream(stream, secret=True)

    materialized = content.materialize()

    assert materialized.data == b"secret"
    assert materialized.redaction_values == ("secret",)
    assert not stream.closed
    path = tmp_path / "content.txt"
    path.write_text("body", encoding="utf-8")
    assert SafeContent.file(path).materialize().data == b"body"


def test_daemon_options_preserve_explicit_false_and_omit_unset() -> None:
    options = DaemonLaunchOptions(foreground=False, reload=True, max_concurrent_tasks=3)

    assert options.foreground is False
    assert options.to_argv() == (
        "--foreground=false",
        "--max-concurrent-tasks",
        "3",
        "--reload=true",
    )
    assert DaemonLaunchOptions().foreground is Unset

    with pytest.raises(ValueError):
        DaemonLaunchOptions(max_concurrent_tasks=0)


def test_wire_presence_distinguishes_missing_null_and_false() -> None:
    assert presence(False) == "value"
    assert field_presence({"enabled": None}, "enabled") == "null"
    assert field_presence({}, "enabled") == "missing"
    assert struct_presence({"enabled": False}, ("enabled", "name")) == (
        ("enabled", "value"),
        ("name", "missing"),
    )


def test_inventory_rejects_unreviewed_rows_and_reconciles_help() -> None:
    item = {
        "inventory_id": "command:issue-list",
        "kind": "command",
        "identity": "issue list",
        "disposition": "typed",
        "source_ref_ids": ["source:issue"],
        "test_ref_ids": ["test:issue"],
        "public_symbol": "multica_py.resources.issues.IssueResource.list",
        "transport": None,
        "compatibility": "requires_cli>=0.5.3",
        "rationale": "Exact source/help and canonical argv evidence.",
    }
    reconciliation: dict[str, list[str]] = {
        "source_only": [],
        "help_only": [],
        "unresolved_factories": [],
        "unresolved_aliases": [],
    }
    raw_inventory: dict[str, object] = {
        "schema_version": 1,
        "complete": False,
        "items": [item],
        "source_commit": "ff8b285497809e084915016c40c2bc5e5991ffbc",
        "source_evidence_ref": "evidence:source",
        "help_evidence_ref": "evidence:help",
        "expected_identities": {"command": ["issue list"]},
        "reconciliation": reconciliation,
    }
    inventory = parse_inventory(raw_inventory)
    assert inventory.by_id["command:issue-list"].identity == "issue list"
    with pytest.raises(InventoryError):
        parse_inventory({**raw_inventory, "items": [{**item, "disposition": "unknown"}]})
    with pytest.raises(InventoryError, match="complete inventory"):
        parse_inventory({**raw_inventory, "complete": True, "items": []})
    with pytest.raises(InventoryError, match="unresolved source/help"):
        extra_items = [
            {**item, "inventory_id": "input:value", "kind": "input", "identity": "value"},
            {**item, "inventory_id": "output:value", "kind": "output", "identity": "value"},
            {
                **item,
                "inventory_id": "field:value",
                "kind": "field",
                "identity": "value",
                "disposition": "typed-equivalent",
            },
            {
                **item,
                "inventory_id": "transport:value",
                "kind": "transport",
                "identity": "value",
                "disposition": "transport",
                "public_symbol": None,
                "transport": "run_bytes",
            },
        ]
        parse_inventory(
            {
                **raw_inventory,
                "complete": True,
                "items": [item, *extra_items],
                "expected_identities": {
                    "command": ["issue list"],
                    "input": ["value"],
                    "output": ["value"],
                    "field": ["value"],
                    "transport": ["value"],
                },
                "reconciliation": {
                    **reconciliation,
                    "unresolved_factories": ["issue-wakeup"],
                },
            }
        )
    with pytest.raises(InventoryError, match="disposition"):
        parse_inventory({**raw_inventory, "items": [{**item, "disposition": "deferred"}]})
    with pytest.raises(InventoryError, match="exactly cover"):
        validate_inventory(raw_inventory, expected_identities={"command:issue-list": "wrong"})

    help_nodes = parse_recursive_help(
        {"path": "issue", "children": [{"path": "list"}, {"path": "probe", "hidden": True}]}
    )
    assert reconcile_command_inventory((("issue", "list"), ("issue", "missing")), help_nodes) == {
        "source_only": (("issue", "missing"),),
        "help_only": (),
        "hidden": (("issue", "probe"),),
        "matched": (("issue", "list"),),
    }
