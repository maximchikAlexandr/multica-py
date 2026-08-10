from __future__ import annotations

import datetime
import hashlib
import importlib
import inspect
import pathlib
import typing
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from multica_py import Command
from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.models.common import ActionResult, Page
from multica_py.process import ManagedProcess
from tests.cases.operations import (
    GENERATED_OPERATION_CASES,
    LEGACY_ARGV_MIGRATION,
    OPERATION_CASES,
    RESOURCE_SPECS,
    OperationCase,
    _resource_attr,
    discover_public_methods,
)
from tools.upstream_contract.contract import ContractCatalog, Entrypoint, validate_contract

_RESOURCE_MAP: dict[str, type] = dict(RESOURCE_SPECS)


def _call_contracts(method: object) -> tuple[tuple[inspect.Signature, object], ...]:
    assert inspect.isfunction(method)
    functions = typing.get_overloads(method) or (method,)
    return tuple(
        (
            inspect.signature(function).replace(return_annotation=inspect.Signature.empty),
            typing.get_type_hints(function)["return"],
        )
        for function in functions
    )


def _contains_type(annotation: object, expected: object) -> bool:
    if annotation is expected or typing.get_origin(annotation) is expected:
        return True
    return any(_contains_type(argument, expected) for argument in typing.get_args(annotation))


def _approved_entrypoint(case: OperationCase, contract: ContractCatalog) -> Entrypoint:
    assert case.contract_operation_id is not None
    entrypoint_id = (
        case.id.removeprefix("generated:").rsplit(":", 2)[1]
        if case.id.startswith("generated:")
        else "default"
    )
    for operation in contract.operations:
        if operation.operation_id != case.contract_operation_id:
            continue
        for entrypoint in operation.entrypoints:
            if entrypoint.entrypoint_id == entrypoint_id:
                return entrypoint
    raise AssertionError(f"case is not present in approved contract: {case.id}")


def _configure_mock(mock_transport: MagicMock, case: OperationCase) -> None:
    if case.transport_side_effect is not None:
        if case.transport_method == "run_bytes":
            mock_transport.run_bytes.side_effect = case.transport_side_effect
        elif case.transport_method == "run_text":
            mock_transport.run_text.side_effect = case.transport_side_effect
        elif case.transport_method == "spawn":
            mock_transport.spawn.side_effect = case.transport_side_effect
        return
    if case.transport_method == "spawn":
        mock_transport.spawn.return_value = MagicMock()
    elif case.transport_method == "run_bytes":
        mock_transport.run_bytes.return_value = RawCommandResult(
            argv=tuple(case.expected_argv),
            exit_code=case.exit_code,
            stdout=case.stdout or b"{}",
            stderr=case.stderr,
            duration=datetime.timedelta(),
        )
    elif case.transport_method == "run_text":
        text = (case.stdout or b"{}").decode("utf-8", errors="replace")
        mock_transport.run_text.return_value = TextResult(
            text=text,
            stderr=case.stderr.decode("utf-8", errors="replace"),
            exit_code=case.exit_code,
        )


def _assert_transport_call(mock_transport: MagicMock, case: OperationCase) -> None:
    transport = cast("CliTransport", mock_transport)
    initial_profile = case.snapshot_profiles[0] if case.snapshot_profiles is not None else None
    mock_transport.build_full_argv.side_effect = lambda args: (
        ("multica", "--profile", initial_profile, *args)
        if initial_profile is not None
        else ("multica", *args)
    )
    config = ClientConfig(profile=initial_profile)
    if case.public_route:
        client = MulticaClient(config)
        resource: object = client
        for attribute in case.sdk_method.split(".")[:-1]:
            resource = getattr(resource, attribute)
        setattr(resource, "_transport", transport)
    else:
        ra = _resource_attr(case.sdk_method)
        cls = _RESOURCE_MAP[ra]
        resource = cls(transport, config)
    try:
        command = getattr(resource, f"{case.method}_command")(*case.args, **dict(case.kwargs))
    except Exception as exc:
        if case.expected_exception is None:
            raise
        assert isinstance(exc, case.expected_exception)
        mock_transport.run_bytes.assert_not_called()
        mock_transport.run_text.assert_not_called()
        mock_transport.spawn.assert_not_called()
        return
    assert command.commands == case.expected_commands
    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()
    mock_transport.spawn.assert_not_called()
    if case.expected_exception is None:
        result = command.run()
    else:
        with pytest.raises(case.expected_exception):
            command.run()
        result = None

    if case.expected_exception is None and case.assert_result is not None:
        case.assert_result(result, mock_transport)

    expected_argvs = case.expected_transport_argvs or (case.expected_argv,)
    transport_call = getattr(mock_transport, case.transport_method)
    assert transport_call.call_count == len(expected_argvs)
    for call, expected_argv in zip(transport_call.call_args_list, expected_argvs, strict=True):
        actual_argv = cast("tuple[str, ...]", call.args[0])
        normalized = list(actual_argv)
        for position in case.dynamic_argv_positions:
            normalized[position] = expected_argv[position]
        assert tuple(normalized) == expected_argv

    if case.transport_method == "run_bytes":
        for call in mock_transport.run_bytes.call_args_list:
            assert call.kwargs.get("stdin") == case.stdin
            assert call.kwargs.get("timeout") == (
                datetime.timedelta(seconds=case.timeout) if case.timeout is not None else None
            )
    elif case.transport_method == "run_text":
        assert mock_transport.run_text.call_count == len(expected_argvs)
    elif case.transport_method == "spawn":
        assert mock_transport.spawn.call_count == len(expected_argvs)


@pytest.mark.parametrize("case", list(OPERATION_CASES), ids=lambda c: c.id)
def test_operation(case: OperationCase, mock_transport: MagicMock) -> None:
    _configure_mock(mock_transport, case)
    _assert_transport_call(mock_transport, case)


def test_discovered_public_methods() -> None:
    discovered = discover_public_methods()
    contract = validate_contract(pathlib.Path("contracts/sdk-contract.json"))
    canonical_cases = tuple(c for c in OPERATION_CASES if c.is_canonical)
    canonical = {c.sdk_method for c in canonical_cases}
    assert discovered == canonical
    assert len(canonical_cases) == len(canonical)
    governed = {c.sdk_method for c in canonical_cases if c.contract_operation_id is not None}
    assert governed == discovered
    assert len(governed) == sum(len(operation.entrypoints) for operation in contract.operations)
    assert len(contract.operation_ids) == len(contract.operations)
    assert len(OPERATION_CASES) == 224
    assert len({c.id for c in OPERATION_CASES}) == 224
    assert sum(not c.is_canonical for c in OPERATION_CASES) == 100
    presence_catalog = cast(
        "dict[str, object]",
        cast("dict[str, object]", contract.raw["catalogs"])["presence"],
    )
    for case in canonical_cases:
        entrypoint = _approved_entrypoint(case, contract)
        assert case.expected_category == entrypoint.category, case.sdk_method
        assert case.expected_response_id == entrypoint.response_id, case.sdk_method
        assert case.expected_typed_input_id == entrypoint.typed_input_id, case.sdk_method
        assert case.expected_input_mode == entrypoint.input_mode, case.sdk_method
        assert case.presence_policy_ids == entrypoint.presence_policy_ids, case.sdk_method
        assert len(case.presence_policy_ids) == len(set(case.presence_policy_ids))
        assert set(case.presence_policy_ids) <= set(presence_catalog), case.sdk_method
        if entrypoint.input_mode == "direct":
            assert entrypoint.typed_input_id is None
            assert not entrypoint.presence_policy_ids
        elif entrypoint.input_mode.startswith("dual_"):
            assert entrypoint.typed_input_id is not None
        else:
            raise AssertionError(f"unknown approved input mode: {entrypoint.input_mode}")
        cls = _RESOURCE_MAP[case.resource_attr]
        eager = getattr(cls, case.method)
        command = getattr(cls, f"{case.method}_command", None)
        assert command is not None, case.sdk_method
        assert case.expected_commands, case.sdk_method
        eager_contracts = _call_contracts(eager)
        command_contracts = _call_contracts(command)
        assert len(eager_contracts) == len(command_contracts), case.sdk_method
        for (eager_signature, eager_return), (command_signature, command_return) in zip(
            eager_contracts, command_contracts, strict=True
        ):
            assert command_signature == eager_signature, case.sdk_method
            assert typing.get_origin(command_return) is Command, case.sdk_method
            assert typing.get_args(command_return) == (eager_return,), case.sdk_method
        if entrypoint.typed_input_id is not None:
            assert any(
                entrypoint.typed_input_id in repr(signature)
                for signature, _return in eager_contracts
            ), case.sdk_method
    generated = tuple(c for c in OPERATION_CASES if c.id.startswith("generated:"))
    manual = tuple(c for c in OPERATION_CASES if not c.id.startswith("generated:"))
    assert len(generated) == 58
    assert len(manual) == 166
    assert {c.id for c in generated} == {c.id for c in GENERATED_OPERATION_CASES}
    assert all(c.source_ref is None for c in generated)
    assert all(c.source_ref is not None for c in manual)
    assert all(c.contract_operation_id is not None for c in generated)
    assert all(c.expected_category is not None for c in canonical_cases)
    assert all(c.expected_response_id is not None for c in canonical_cases)


def test_approved_result_categories_are_closed() -> None:
    """Keep public result shapes aligned with the approved convention matrix."""
    from multica_py.models.relations import (
        CursorLazyCollection,
        LazyCollection,
        OffsetLazyCollection,
    )

    contract = validate_contract(pathlib.Path("contracts/sdk-contract.json"))
    responses = {response.response_id: response for response in contract.responses}
    canonical = {case.sdk_method: case for case in OPERATION_CASES if case.is_canonical}
    void_actions = {
        "agents.archive",
        "agents.avatar",
        "agents.restore",
        "agents.skills.set",
        "autopilots.delete",
        "autopilots.trigger_delete",
        "configuration.set",
        "issues.cancel_task",
        "issues.comments.delete",
        "issues.comments.resolve",
        "issues.comments.unresolve",
        "issues.metadata.delete",
        "issues.rerun",
        "issues.subscribers.add",
        "issues.subscribers.remove",
        "labels.delete",
        "projects.delete",
        "projects.resources.remove",
        "runtimes.delete",
        "skills.delete",
        "skills.files.delete",
        "squads.members.add",
        "squads.members.remove",
        "workspaces.switch",
        "workspaces.watch",
        "workspaces.unwatch",
    }
    natural_action_exceptions = {
        "attachments.upload_bytes",
        "auth.logout",
        "daemon.restart",
        "daemon.stop",
        "issues.assign",
        "issues.metadata.set_typed",
        "issues.reorder",
    }
    page_response_ids = {
        response.response_id
        for response in responses.values()
        if response.public_type_id.startswith("Page[")
        or response.response_id
        in {
            "comment_page",
            "comment_thread_page",
            "issue_list_page",
            "autopilot_list_page",
            "autopilot_run_list_page",
        }
    }
    page_response_ids.add("issue_children_result")

    # Relation snapshots are deliberately outside the canonical Page migration.
    for relation_type in (LazyCollection, OffsetLazyCollection, CursorLazyCollection):
        assert typing.get_origin(typing.get_type_hints(relation_type.all)["return"]) is tuple

    for sdk_method, case in canonical.items():
        assert case.expected_response_id in responses, sdk_method
        cls = _RESOURCE_MAP[case.resource_attr]
        annotation = typing.get_type_hints(getattr(cls, case.method))["return"]
        category = case.expected_category
        response_id = case.expected_response_id
        assert category is not None and response_id is not None
        if category == "collection":
            if sdk_method == "issues.metadata.list":
                assert annotation == dict[str, object] or typing.get_origin(annotation) is dict
            elif sdk_method == "issues.usage":
                assert annotation.__name__ == "IssueUsage"
            else:
                assert response_id in page_response_ids, sdk_method
                assert _contains_type(annotation, Page) or annotation.__name__ in {
                    "IssueListPage",
                    "AutopilotListPage",
                    "AutopilotRunListPage",
                    "IssueChildrenResult",
                }, sdk_method
        elif category == "action":
            if sdk_method in void_actions:
                assert response_id == "action_result_none", sdk_method
                assert _contains_type(annotation, ActionResult), sdk_method
            elif sdk_method in {"auth.login", "issues.deprioritize"}:
                assert response_id == "action_result_str", sdk_method
                assert _contains_type(annotation, ActionResult), sdk_method
            elif sdk_method in {"repositories.add", "repositories.remove"}:
                assert response_id == "action_result_repository_mutation_result", sdk_method
                assert _contains_type(annotation, ActionResult), sdk_method
            elif sdk_method == "runtimes.update":
                assert response_id == "action_result_runtime_update_result"
                assert _contains_type(annotation, ActionResult), sdk_method
            elif sdk_method not in natural_action_exceptions:
                raise AssertionError(f"unapproved action category: {sdk_method}")
            else:
                assert not _contains_type(annotation, ActionResult), sdk_method
        elif category == "process":
            assert response_id == "process", sdk_method
            assert annotation is ManagedProcess, sdk_method
        else:
            assert not _contains_type(annotation, ActionResult), sdk_method


def test_approved_symbols_signatures_and_canonical_vectors_are_complete() -> None:
    contract = validate_contract(pathlib.Path("contracts/sdk-contract.json"))

    def contract_key(case: OperationCase) -> tuple[str, str]:
        assert case.contract_operation_id is not None
        if case.id.startswith("generated:"):
            _, entrypoint, _ = case.id.removeprefix("generated:").rsplit(":", 2)
            return case.contract_operation_id, entrypoint
        return case.contract_operation_id, "default"

    canonical_by_operation = {
        contract_key(case): case
        for case in OPERATION_CASES
        if case.is_canonical and case.contract_operation_id is not None
    }
    assert set(canonical_by_operation) == {
        (operation.operation_id, entrypoint.entrypoint_id)
        for operation in contract.operations
        for entrypoint in operation.entrypoints
    }
    assert len(canonical_by_operation) == sum(
        case.is_canonical and case.contract_operation_id is not None for case in OPERATION_CASES
    )
    catalogs = cast("dict[str, object]", contract.raw["catalogs"])
    signatures = cast("dict[str, object]", catalogs["signatures"])
    for operation in contract.operations:
        for entrypoint in operation.entrypoints:
            module_name, class_name, method_name = entrypoint.public_symbol.rsplit(".", 2)
            resource = getattr(importlib.import_module(module_name), class_name)
            method = getattr(resource, method_name)
            assert inspect.isfunction(method)
            assert entrypoint.signature_id in signatures
            assert (
                canonical_by_operation[(operation.operation_id, entrypoint.entrypoint_id)].method
                == method_name
            )


def test_legacy_payload_bijection() -> None:
    from tests.cases.legacy_payloads import LEGACY_PAYLOAD_FINGERPRINTS

    final_by_id: dict[str, OperationCase] = {c.id: c for c in OPERATION_CASES}

    def payload(case: OperationCase) -> tuple[object, ...]:
        return (
            case.resource_attr,
            case.method,
            case.args,
            tuple(sorted(dict(case.kwargs).items())),
            case.transport_method,
            case.expected_argv,
            case.stdin,
            case.timeout,
            case.stdout,
        )

    expected_legacy_ids = {f"legacy:{index:03d}" for index in range(1, 149)}
    assert set(LEGACY_ARGV_MIGRATION) == expected_legacy_ids
    assert len(LEGACY_ARGV_MIGRATION) == 148
    assert len(LEGACY_PAYLOAD_FINGERPRINTS) == 148
    removed = {
        "legacy:014": "removed:attachments.list",
        "legacy:016": "removed:attachments.download-v0420",
        "legacy:069": "removed:repositories.get",
        "legacy:070": "removed:repositories.checkout",
        "legacy:072": "removed:runtimes.get",
        "legacy:083": "removed:users.list",
        "legacy:084": "removed:users.get",
        "legacy:148": "removed:attachments.download_bytes-v0420",
    }
    assert {key: LEGACY_ARGV_MIGRATION[key] for key in removed} == removed
    final_migration = {
        key: value for key, value in LEGACY_ARGV_MIGRATION.items() if key not in removed
    }
    assert len(final_migration.values()) == len(set(final_migration.values())) == 140
    assert set(final_migration.values()).issubset(final_by_id)

    legacy_by_id = {
        f"legacy:{index:03d}": fingerprint
        for index, fingerprint in enumerate(LEGACY_PAYLOAD_FINGERPRINTS, start=1)
    }
    for legacy_id, final_id in LEGACY_ARGV_MIGRATION.items():
        if legacy_id in removed:
            continue
        actual = hashlib.sha256(repr(payload(final_by_id[final_id])).encode()).hexdigest()
        assert legacy_by_id[legacy_id] == actual


@pytest.mark.parametrize(
    "case",
    [case for case in OPERATION_CASES if case.snapshot_profiles is not None],
    ids=lambda case: case.id,
)
def test_command_preview_snapshot_case(case: OperationCase) -> None:
    assert case.snapshot_profiles is not None
    profile_a, profile_b = case.snapshot_profiles
    client = MulticaClient(ClientConfig(profile=profile_a))
    run_bytes = MagicMock(
        return_value=RawCommandResult(
            argv=case.expected_argv,
            exit_code=0,
            stdout=case.stdout,
            stderr=b"",
            duration=datetime.timedelta(),
        )
    )
    with patch.object(client._transport, "run_bytes", run_bytes):
        command = getattr(client.issues, f"{case.method}_command")(*case.args, **dict(case.kwargs))
        switched = client.with_profile(profile_b)

        assert command.commands == case.expected_commands
        assert switched.issues.get_command(cast("str", case.args[0])).commands == (
            "multica --profile profile-b issue get i1 --output json",
        )
        assert getattr(command.run(), "id") == "i1"
        assert run_bytes.call_args.args[0] == case.expected_argv
