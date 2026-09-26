from __future__ import annotations

import pathlib
import re
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
    assert len(contract.test_vectors) == 113
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
    assert b"TARGET_VERSION = '0.5.3'" in runtime
    assert b"MIN_CLI_VERSION = '0.4.42'" in runtime
    assert b"MAX_CLI_VERSION = '0.5.4'" in runtime

    descriptors = {
        item.operation_id: item
        for item in contract.binding_descriptors
        if item.operation_id in {"agents.copy", "issues.search"}
    }
    assert set(descriptors) == {"agents.copy", "issues.search"}
    for descriptor in descriptors.values():
        descriptor_header = (
            f"{descriptor.operation_id!r}, {descriptor.entrypoint_id!r}, {descriptor.command!r}"
        ).encode()
        assert descriptor_header in runtime


_PROMOTED_COMMAND_OPERATIONS = {
    "multica agent env get": "agents.env.get",
    "multica agent env set": "agents.env.set",
    "multica agent skills add": "agents.skills.add",
    "multica autopilot trigger-rotate-url": "autopilots.trigger_rotate_url",
    "multica autopilot trigger-list": "autopilots.trigger_list",
    "multica chat history": "chats.history",
    "multica chat thread": "chats.thread",
    "multica issue timeline": "issues.timeline",
    "multica issue wakeup events": "issues.wakeups.events",
    "multica issue wakeup list": "issues.wakeups.list",
    "multica issue wakeup get": "issues.wakeups.get",
    "multica issue wakeup disable": "issues.wakeups.disable",
    "multica issue wakeup create": "issues.wakeups.create",
    "multica issue wakeup update": "issues.wakeups.update",
    "multica repo checkout": "repositories.checkout",
    "multica runtime profile list": "runtime_profiles.list",
    "multica runtime profile create": "runtime_profiles.create",
    "multica runtime profile update": "runtime_profiles.update",
    "multica runtime profile delete": "runtime_profiles.delete",
    "multica runtime profile set-path": "runtime_profiles.set_path",
    "multica runtime profile unset-path": "runtime_profiles.unset_path",
    "multica squad activity": "squads.activity",
    "multica squad create": "squads.create",
    "multica squad delete": "squads.delete",
    "multica squad member set-role": "squads.members.set_role",
    "multica squad update": "squads.update",
    "multica workspace create": "workspaces.create",
    "multica workspace member invite": "workspaces.members.invite",
    "multica workspace update": "workspaces.update",
}


def test_promoted_public_operations_have_closed_binding_coverage() -> None:
    contract = validate_contract(APPROVED)
    runtime = render_files(APPROVED)[0].content.decode("utf-8")
    operations = {operation.operation_id: operation for operation in contract.operations}
    descriptors = {
        descriptor.descriptor_id: descriptor for descriptor in contract.binding_descriptors
    }
    vectors = contract.vector_by_id
    responses = contract.response_by_id
    inventory = {item.identity: item for item in contract.inventory.items if item.kind == "command"}
    for identity, operation_id in _PROMOTED_COMMAND_OPERATIONS.items():
        item = inventory[identity]
        operation = operations[operation_id]
        entrypoint = operation.entrypoints[0]
        descriptor = descriptors[entrypoint.binding_id]
        assert item.disposition == "typed"
        assert item.public_symbol == entrypoint.public_symbol
        assert set(item.source_ref_ids) >= set(operation.source_ref_ids)
        assert set(item.test_ref_ids) >= {"T-INVENTORY", "T-WP01-PROMOTION"}
        assert (descriptor.operation_id, descriptor.entrypoint_id) == (operation_id, "default")
        assert entrypoint.response_id in responses
        assert f"generated:{operation_id}:default:canonical" in vectors
        binding_name = f"{descriptor.descriptor_id.upper().replace('.', '_')}_BINDING"
        assert re.search(
            rf"^{re.escape(binding_name)} = GeneratedBinding\(\n"
            rf"    {re.escape(repr(operation_id))}, "
            rf"{re.escape(repr(descriptor.entrypoint_id))},",
            runtime,
            re.MULTILINE,
        )

    scope = cast("dict[str, object]", contract.raw["scope"])
    dispositions = cast("list[dict[str, object]]", scope["family_dispositions"])
    for family in ("chat-read", "issue-wakeup", "runtime-profile"):
        family_row = next(row for row in dispositions if row["family"] == family)
        assert family_row["disposition"] != "defer"
        assert "deferred_evidence" not in family_row


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


def test_prior_binary_provenance_and_reviewed_responses_are_exact() -> None:
    contract = validate_contract(APPROVED)
    binary = next(
        item for item in contract.compatibility.verified_binaries if item.version == "0.5.2"
    )
    assert binary.commit.startswith("d45aba1cd")
    assert (binary.build_date, binary.go_version, binary.os, binary.arch) == (
        "2026-09-23T10:42:33Z",
        "go1.26.8",
        "darwin",
        "arm64",
    )
    assert {item.operation_id for item in contract.compatibility.reviewed_responses} == {
        "agents.tasks",
        "labels.create",
        "labels.list",
        "labels.update",
        "runtimes.delete",
        "skills.list",
        "issues.create",
        "issues.runs",
        "issues.run_messages",
    }


def test_retained_inventory_is_reconciled() -> None:
    contract = validate_contract(APPROVED)
    operation_ids = {operation.operation_id for operation in contract.operations}
    scope = cast("dict[str, object]", contract.raw["scope"])
    scoped_operation_ids = set(cast("list[str]", scope["operation_ids"]))
    relation_ids = tuple(
        test_ref.test_ref_id
        for test_ref in contract.test_refs
        if test_ref.test_ref_id.startswith("relation:")
    )

    assert len(operation_ids) == 193
    assert operation_ids == scoped_operation_ids
    assert len(contract.responses) == 98
    assert len(contract.compatibility.response_registry) == 167
    assert (
        sum(item.disposition == "unchanged" for item in contract.compatibility.response_registry)
        == 167
    )
    assert (
        sum(item.disposition == "changed" for item in contract.compatibility.response_registry) == 0
    )
    assert relation_ids == tuple(f"relation:R{index:02d}" for index in range(1, 39) if index != 34)


def test_checkout_is_contract_first_until_successor_resource_implementation() -> None:
    from multica_py.resources.repositories import RepositoryResource

    contract = validate_contract(APPROVED)
    operation_ids = {operation.operation_id for operation in contract.operations}
    assert any("repoCheckoutCmd" in source_ref.symbol for source_ref in contract.source_refs)
    assert "repositories.checkout" in operation_ids
    assert not hasattr(RepositoryResource, "checkout")


def test_removed_plugin_surface_and_autopilot_priority_are_absent() -> None:
    import importlib
    import inspect

    from multica_py._internal.transport import CliTransport
    from multica_py.client import MulticaClient
    from multica_py.config import ClientConfig
    from multica_py.entities.workspaces import Workspace
    from multica_py.enums import AutopilotExecutionMode
    from multica_py.resources.autopilots import AutopilotResource

    contract = validate_contract(APPROVED)
    assert not any(item.operation_id.startswith("plugins.") for item in contract.operations)
    assert not hasattr(MulticaClient, "plugins")
    assert not hasattr(Workspace, "plugins")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("multica_py.resources.plugins")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("multica_py.models.plugins")

    resource = AutopilotResource(CliTransport(ClientConfig()), ClientConfig())
    for method in (
        resource.create,
        resource.create_command,
        resource.update,
        resource.update_command,
    ):
        assert "priority" not in inspect.signature(method).parameters
    create = resource.create_command(
        "Nightly", agent="agent-1", execution_mode=AutopilotExecutionMode.create_issue
    )
    assert create._plan.steps[0].argv == (
        "autopilot",
        "create",
        "--title",
        "Nightly",
        "--agent",
        "agent-1",
        "--mode",
        "create_issue",
        "--output",
        "json",
    )
    with pytest.raises(TypeError):
        resource.create_command(  # type: ignore[call-arg]
            "Nightly",
            agent="agent-1",
            execution_mode=AutopilotExecutionMode.create_issue,
            priority="none",
        )
    with pytest.raises(TypeError):
        resource.update_command("ap-1", priority="none")  # type: ignore[call-arg]
