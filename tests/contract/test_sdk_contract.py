from __future__ import annotations

import pathlib
from typing import cast

import pytest

from tools.upstream_contract.contract import validate_contract
from tools.upstream_contract.generation import (
    RUNTIME_PATH,
    TRANSIENT_PATHS,
    _ensure_transient_root,
    render_files,
)

APPROVED = pathlib.Path("contracts/sdk-contract.json")


def test_sdk_contract() -> None:
    contract = validate_contract(APPROVED)
    files = render_files(APPROVED)
    assert files[0].path == RUNTIME_PATH
    assert tuple(item.path for item in files[1:]) == TRANSIENT_PATHS
    assert len(contract.operations) == len(contract.operation_ids)
    assert len(contract.binding_descriptors) == sum(
        len(operation.entrypoints) for operation in contract.operations
    )
    assert len(contract.test_vectors) == 89
    assert (
        tuple((item.operation_id, item.entrypoint_id) for item in contract.binding_descriptors)
        != ()
    )
    assert all("state" not in str(item.path) for item in files)


def test_transient_output_rejects_tracked_paths(tmp_path: pathlib.Path) -> None:
    with pytest.raises(ValueError):
        _ensure_transient_root(pathlib.Path("contracts"))
    outside = _ensure_transient_root(tmp_path)
    assert outside == tmp_path.resolve()


def test_runtime_projection_is_single_authoritative_output() -> None:
    files = render_files(APPROVED)
    runtime = files[0].content
    assert runtime.count(b"TARGET_VERSION") == 2
    assert b"approved_contract" not in runtime
    assert b"source path" not in runtime
    assert b"OPERATION_BINDINGS" in runtime
    assert b"OPERATION_CONVENTIONS" in runtime


def test_generated_runtime_tracks_target_and_copy_search_descriptors() -> None:
    contract = validate_contract(APPROVED)
    runtime = render_files(APPROVED)[0].content
    assert b"TARGET_VERSION = '0.4.28'" in runtime
    assert b"MIN_CLI_VERSION = '0.4.28'" in runtime
    assert b"MAX_CLI_VERSION = '0.4.39'" in runtime

    descriptors = {
        item.operation_id: item
        for item in contract.binding_descriptors
        if item.operation_id in {"agents.copy", "issues.search"}
    }
    for descriptor in descriptors.values():
        descriptor_header = (
            f"{descriptor.operation_id!r}, {descriptor.entrypoint_id!r}, {descriptor.command!r}"
        ).encode()
        assert descriptor_header in runtime


def test_generated_trigger_contract_is_pinned_and_obsolete_inputs_are_absent() -> None:
    contract = validate_contract(APPROVED)
    catalogs = cast("dict[str, object]", contract.raw["catalogs"])
    bindings = cast("dict[str, object]", catalogs["bindings"])
    add_binding = cast("dict[str, object]", bindings["autopilot_trigger_add"])
    update_binding = cast("dict[str, object]", bindings["autopilot_trigger_update"])
    assert add_binding["mappings"] == [
        ["autopilot_id", "pos:0", "path:autopilot_id"],
        ["kind", "--kind", "json_body:kind"],
        ["cron_expression", "--cron", "json_body:cron_expression"],
        ["timezone", "--timezone", "json_body:timezone"],
        ["label", "--label", "json_body:label"],
    ]
    assert update_binding["mappings"] == [
        ["autopilot_id", "pos:0", "path:autopilot_id"],
        ["trigger_id", "pos:1", "path:trigger_id"],
        ["cron_expression", "--cron", "json_body:cron_expression"],
        ["timezone", "--timezone", "json_body:timezone"],
        ["label", "--label", "json_body:label"],
        ["enabled", "--enabled", "json_body:enabled"],
    ]
    assert "title" not in str(add_binding)
    assert "title" not in str(update_binding)
    assert "kind" not in str(update_binding)

    binary = next(
        item for item in contract.compatibility.verified_binaries if item.version == "0.4.38"
    )
    assert binary.commit.startswith("47dc75741")
    assert (binary.build_date, binary.go_version, binary.os, binary.arch) == (
        "2026-09-02T09:52:29Z",
        "go1.26.7",
        "darwin",
        "arm64",
    )
    version_review = next(
        item
        for item in contract.compatibility.reviewed_responses
        if item.operation_id == "maintenance.version"
    )
    assert version_review.fields == ("version", "commit", "date", "go", "os", "arch")
    assert "47dc75741" in version_review.omission_policy
