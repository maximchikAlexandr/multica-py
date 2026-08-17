from __future__ import annotations

import datetime
import hashlib
import importlib
import inspect
import pathlib
import typing
from collections.abc import Callable
from dataclasses import replace
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from multica_py import Command
from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig, OperationOptions
from multica_py.entities.agents import Agent
from multica_py.entities.autopilots import Autopilot
from multica_py.entities.issues import Issue
from multica_py.entities.projects import Project
from multica_py.entities.skills import Skill
from multica_py.entities.squads import Squad
from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.execution import LocalExecutor
from multica_py.models.common import ActionResult, Page
from multica_py.models.issues import IssueListFilter
from multica_py.process import ManagedProcess
from multica_py.resources.issues import IssueResource
from multica_py.resources.projects import ProjectIssueCollection, ProjectResource
from tests.cases.operations import (
    _BOUND_RESOURCE_SPECS,
    GENERATED_OPERATION_CASES,
    ISSUE_INVALID_STATUS_CASES,
    ISSUE_STATUS_CASES,
    OPERATION_CASES,
    PROJECT_INVALID_STATUS_CASES,
    PROJECT_STATUS_CASES,
    RESOURCE_SPECS,
    OperationCase,
    StatusInputCase,
    _resource_attr,
    discover_public_methods,
)
from tools.upstream_contract.contract import ContractCatalog, Entrypoint, validate_contract

_RESOURCE_MAP: dict[str, type] = dict(RESOURCE_SPECS)

_LAZY_OPTIONS_PARITY_EXCEPTIONS = frozenset(
    {
        "projects.issues.all",
        "projects.issues.page",
        "projects.issues.refresh",
    }
)


def _contract_entrypoint_is_implemented(entrypoint: Entrypoint) -> bool:
    module_name, class_name, method_name = entrypoint.public_symbol.rsplit(".", 2)
    try:
        resource = getattr(importlib.import_module(module_name), class_name)
    except (ImportError, AttributeError):
        return False
    return hasattr(resource, method_name)


def _case_class(case: OperationCase) -> type:
    if case.bound_target == "agent":
        from multica_py.entities.agents import Agent

        return Agent
    if case.bound_target == "autopilot":
        from multica_py.entities.autopilots import Autopilot

        return Autopilot
    if case.bound_target == "issue":
        from multica_py.entities.issues import Issue

        return Issue
    if case.bound_target == "project":
        from multica_py.entities.projects import Project

        return Project
    if case.bound_target == "project_issues":
        from multica_py.resources.projects import ProjectIssueCollection

        return ProjectIssueCollection
    if case.bound_target == "skill":
        from multica_py.entities.skills import Skill

        return Skill
    if case.bound_target == "squad":
        from multica_py.entities.squads import Squad

        return Squad
    return _RESOURCE_MAP[case.resource_attr]


def _case_method(case: OperationCase) -> Callable[..., object]:
    return cast("Callable[..., object]", getattr(_case_class(case), case.method))


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


def _assert_eager_command_parity(
    case: OperationCase,
) -> tuple[tuple[inspect.Signature, object], ...]:
    eager = _case_method(case)
    command = getattr(_case_class(case), f"{case.method}_command", None)
    assert command is not None, case.sdk_method
    eager_contracts = _call_contracts(eager)
    command_contracts = _call_contracts(command)
    assert len(eager_contracts) == len(command_contracts), case.sdk_method
    for (eager_signature, eager_return), (command_signature, command_return) in zip(
        eager_contracts, command_contracts, strict=True
    ):
        assert command_signature == eager_signature, case.sdk_method
        if case.sdk_method == "cli.command":
            assert typing.get_origin(eager_return) is Command
            assert typing.get_origin(command_return) is Command
            assert typing.get_args(eager_return) == typing.get_args(command_return)
        else:
            assert typing.get_origin(command_return) is Command, case.sdk_method
            assert typing.get_args(command_return) == (eager_return,), case.sdk_method
    return eager_contracts


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
    if case.sdk_method in {
        "attachments.upload",
        "attachments.upload_bytes",
        "attachments.download_bytes",
    }:
        mock_transport.executor = LocalExecutor()

        if case.sdk_method == "attachments.download_bytes":
            mock_transport.run_bytes.side_effect = case.transport_side_effect
            return

        def staged_upload(argv: tuple[str, ...], **_kwargs: object) -> RawCommandResult:
            staged_path = pathlib.Path(argv[2])
            assert staged_path.is_file()
            expected_name, expected_content = (
                ("manifest.json", b'{"x":1}')
                if case.sdk_method == "attachments.upload_bytes"
                else ("operations.py", pathlib.Path("tests/cases/operations.py").read_bytes())
            )
            assert staged_path.name == expected_name
            assert staged_path.read_bytes() == expected_content
            return RawCommandResult(
                argv=tuple(case.expected_argv),
                exit_code=case.exit_code,
                stdout=case.stdout or b"{}",
                stderr=case.stderr,
                duration=datetime.timedelta(),
            )

        mock_transport.run_bytes.side_effect = staged_upload
        return
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


def _bound_target(case: OperationCase, client: MulticaClient) -> object:
    if case.bound_target == "agent":
        from multica_py.entities.agents import Agent

        return Agent(id="a1", name="Agent", _client=client)
    if case.bound_target == "autopilot":
        from multica_py.entities.autopilots import Autopilot

        return Autopilot(
            id="ap1",
            workspace_id="w1",
            title="Autopilot",
            assignee_type="member",
            assignee_id="u1",
            status="active",
            execution_mode="create_issue",
            created_by_type="member",
            created_by_id="u1",
            _client=client,
        )
    if case.bound_target == "issue":
        from multica_py.entities.issues import Issue

        return Issue(id="i1", title="Issue", status=IssueStatus.todo, _client=client)
    if case.bound_target in {"project", "project_issues"}:
        from multica_py.entities.projects import Project

        project = Project(id="p1", name="Project", status=ProjectStatus.planned, _client=client)
        return project.issues if case.bound_target == "project_issues" else project
    if case.bound_target == "skill":
        from multica_py.entities.skills import Skill

        return Skill(id="s1", name="Skill", _client=client)
    if case.bound_target == "squad":
        from multica_py.entities.squads import Squad

        return Squad(id="sq1", name="Squad", _client=client)
    raise AssertionError(f"unknown bound target: {case.bound_target}")


def _assert_transport_call(mock_transport: MagicMock, case: OperationCase) -> None:
    transport = cast("CliTransport", mock_transport)
    initial_profile = case.snapshot_profiles[0] if case.snapshot_profiles is not None else None
    mock_transport.build_full_argv.side_effect = lambda args: (
        ("multica", "--profile", initial_profile, *args)
        if initial_profile is not None
        else ("multica", *args)
    )
    config = ClientConfig(profile=initial_profile)
    if case.bound_target is not None:
        client = MulticaClient(config)
        client._transport = transport
        client.issues._transport = transport
        client.issues.comments._transport = transport
        client.issues.labels._transport = transport
        client.issues.metadata._transport = transport
        client.issues.subscribers._transport = transport
        client.agents._transport = transport
        client.agents.skills._transport = transport
        client.autopilots._transport = transport
        client.projects._transport = transport
        client.projects.resources._transport = transport
        client.skills._transport = transport
        client.skills.files._transport = transport
        client.squads._transport = transport
        client.squads.members._transport = transport
        resource: object = _bound_target(case, client)
    elif case.public_route:
        client = MulticaClient(config)
        resource = client
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


@pytest.mark.parametrize("case", ISSUE_STATUS_CASES, ids=lambda case: case.name)
def test_issue_list_status_strings_and_enums_have_exact_argv(
    case: StatusInputCase,
    mock_transport: MagicMock,
    raw_result: Callable[..., RawCommandResult],
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    resource = IssueResource(mock_transport, ClientConfig())
    expected = ("issue", "list", "--status", case.expected, "--output", "json")
    for request in (case.value, IssueListFilter(status=case.value)):
        command = (
            resource.list_command(request)
            if isinstance(request, IssueListFilter)
            else resource.list_command(status=request)
        )
        assert command.commands == ("multica " + " ".join(expected),)
        mock_transport.run_bytes.return_value = raw_result(stdout=b'{"issues":[]}')
        if isinstance(request, IssueListFilter):
            resource.list(request)
        else:
            resource.list(status=request)
        mock_transport.run_bytes.assert_called_once_with(expected, stdin=None, timeout=None)
        mock_transport.run_text.assert_not_called()
        mock_transport.spawn.assert_not_called()
        mock_transport.reset_mock()


@pytest.mark.parametrize("case", ISSUE_STATUS_CASES, ids=lambda case: case.name)
def test_root_and_bound_issue_status_actions_have_identical_argv(
    case: StatusInputCase,
    mock_transport: MagicMock,
    raw_result: Callable[..., RawCommandResult],
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    resource = IssueResource(mock_transport, ClientConfig())
    client = MagicMock()
    resource._set_client(client)
    client.issues = resource
    issue = Issue(id="i1", title="Issue", status=IssueStatus.todo, _client=client)
    expected = ("issue", "status", "i1", case.expected, "--output", "json")
    for command in (
        resource.set_status_command("i1", case.value),
        issue.set_status_command(case.value),
    ):
        assert command.commands == ("multica " + " ".join(expected),)
    for action, args in (
        (resource.set_status, ("i1", case.value)),
        (issue.set_status, (case.value,)),
    ):
        mock_transport.run_bytes.return_value = raw_result(
            stdout=(f'{{"id":"i1","title":"Issue","status":"{case.expected}"}}').encode()
        )
        action(*args)
        mock_transport.run_bytes.assert_called_once_with(expected, stdin=None, timeout=None)
        mock_transport.run_text.assert_not_called()
        mock_transport.spawn.assert_not_called()
        mock_transport.reset_mock()


@pytest.mark.parametrize("case", PROJECT_STATUS_CASES, ids=lambda case: case.name)
def test_project_status_eager_and_command_have_identical_argv(
    case: StatusInputCase,
    mock_transport: MagicMock,
    raw_result: Callable[..., RawCommandResult],
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    resource = ProjectResource(mock_transport, ClientConfig())
    expected = ("project", "status", "p1", case.expected, "--output", "json")
    command = resource.set_status_command("p1", case.value)
    assert command.commands == ("multica " + " ".join(expected),)
    mock_transport.run_bytes.return_value = raw_result(
        stdout=(f'{{"id":"p1","title":"Project","status":"{case.expected}"}}').encode()
    )
    project = resource.set_status("p1", case.value)
    assert isinstance(project, Project)
    mock_transport.run_bytes.assert_called_once_with(expected, stdin=None, timeout=None)
    mock_transport.run_text.assert_not_called()
    mock_transport.spawn.assert_not_called()


@pytest.mark.parametrize("value", ISSUE_INVALID_STATUS_CASES, ids=repr)
def test_invalid_issue_status_inputs_fail_locally(value: object, mock_transport: MagicMock) -> None:
    resource = IssueResource(mock_transport, ClientConfig())
    for request in (value, IssueListFilter(status=cast("IssueStatus | str", value))):
        with pytest.raises((ValueError, TypeError)):
            if isinstance(request, IssueListFilter):
                resource.list_command(request)
            else:
                resource.list_command(status=cast("IssueStatus | str", request))
    mock_transport.build_full_argv.assert_not_called()
    mock_transport.run_bytes.assert_not_called()


@pytest.mark.parametrize("value", ISSUE_INVALID_STATUS_CASES, ids=repr)
def test_invalid_root_and_bound_issue_status_inputs_fail_before_transport(
    value: object, mock_transport: MagicMock
) -> None:
    status = cast("IssueStatus | str", value)
    resource = IssueResource(mock_transport, ClientConfig())
    client = MagicMock()
    resource._set_client(client)
    client.issues = resource
    issue = Issue(id="i1", title="Issue", status=IssueStatus.todo, _client=client)
    for action, args in (
        (resource.set_status_command, ("i1", status)),
        (resource.set_status, ("i1", status)),
        (issue.set_status_command, (status,)),
        (issue.set_status, (status,)),
    ):
        with pytest.raises((ValueError, TypeError)):
            action(*args)
    mock_transport.build_full_argv.assert_not_called()
    mock_transport.run_bytes.assert_not_called()


@pytest.mark.parametrize("value", PROJECT_INVALID_STATUS_CASES, ids=repr)
def test_invalid_project_status_inputs_fail_before_transport(
    value: object, mock_transport: MagicMock
) -> None:
    status = cast("ProjectStatus | str", value)
    resource = ProjectResource(mock_transport, ClientConfig())
    for action in (resource.set_status_command, resource.set_status):
        with pytest.raises((ValueError, TypeError)):
            action("p1", status)
    mock_transport.build_full_argv.assert_not_called()
    mock_transport.run_bytes.assert_not_called()


def test_status_models_remain_decoded_enums_and_project_has_no_bound_status_action() -> None:
    assert Issue(id="i1", title="Issue", status=IssueStatus.todo).status is IssueStatus.todo
    assert (
        Project(id="p1", name="Project", status=ProjectStatus.planned).status
        is ProjectStatus.planned
    )
    assert not hasattr(Project, "set_status")


@pytest.mark.parametrize(
    "case",
    [
        case
        for case in OPERATION_CASES
        if (
            case.id.startswith("manual:projects.create:description-file:")
            or case.id.startswith("manual:issues.create:description-")
            or case.id.startswith("manual:issues.create:project-")
            or case.id.startswith("manual:projects.issues.create:description-")
        )
        and case.expected_exception is not None
    ],
    ids=lambda case: case.id,
)
def test_issue_natural_input_invalid_cases_do_not_touch_filesystem_or_transport(
    case: OperationCase,
    mock_transport: MagicMock,
) -> None:
    with (
        patch("builtins.open") as open_mock,
        patch.object(pathlib.Path, "exists") as exists_mock,
        patch.object(pathlib.Path, "stat") as stat_mock,
    ):
        _configure_mock(mock_transport, case)
        _assert_transport_call(mock_transport, case)
    open_mock.assert_not_called()
    exists_mock.assert_not_called()
    stat_mock.assert_not_called()
    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()
    mock_transport.spawn.assert_not_called()


def test_discovered_public_methods() -> None:
    discovered = discover_public_methods()
    contract = validate_contract(pathlib.Path("contracts/sdk-contract.json"))
    canonical_cases = tuple(c for c in OPERATION_CASES if c.is_canonical)
    canonical = {c.sdk_method for c in canonical_cases}
    assert discovered == canonical
    assert len(canonical_cases) == len(canonical)
    governed = {c.sdk_method for c in canonical_cases if c.contract_operation_id is not None}
    assert governed <= discovered
    implemented_entrypoints = {
        (operation.operation_id, entrypoint.entrypoint_id): entrypoint
        for operation in contract.operations
        for entrypoint in operation.entrypoints
        if _contract_entrypoint_is_implemented(entrypoint)
    }
    assert len(governed) == len(implemented_entrypoints)
    assert len(contract.operation_ids) == len(contract.operations)
    assert len(OPERATION_CASES) == 289
    assert len({c.id for c in OPERATION_CASES}) == 289
    assert sum(not c.is_canonical for c in OPERATION_CASES) == 126
    presence_catalog = cast(
        "dict[str, object]",
        cast("dict[str, object]", contract.raw["catalogs"])["presence"],
    )
    for case in canonical_cases:
        eager_contracts = _assert_eager_command_parity(case)
        if case.contract_operation_id is None:
            assert case.bound_target is not None
            continue
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
        assert case.expected_commands, case.sdk_method
        if entrypoint.typed_input_id is not None:
            assert any(
                entrypoint.typed_input_id in repr(signature)
                for signature, _return in eager_contracts
            ), case.sdk_method
    generated = tuple(c for c in OPERATION_CASES if c.id.startswith("generated:"))
    manual = tuple(c for c in OPERATION_CASES if not c.id.startswith("generated:"))
    assert len(generated) == 58
    assert len(manual) == 231
    assert {c.id for c in generated} == {c.id for c in GENERATED_OPERATION_CASES}
    assert all(c.source_ref is None for c in generated)
    assert all(c.source_ref is not None for c in manual)
    assert all(c.contract_operation_id is not None for c in generated)
    assert all(
        c.expected_category is not None
        for c in canonical_cases
        if c.contract_operation_id is not None
    )
    assert all(
        c.expected_response_id is not None
        for c in canonical_cases
        if c.contract_operation_id is not None
    )


def test_bound_discovery_rejects_unregistered_eager_command_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from multica_py.entities._base import _BoundEntity
    from multica_py.models.relations import OffsetLazyCollection

    def ungoverned(_self: object) -> object:
        return None

    def ungoverned_command(_self: object) -> object:
        return None

    for _dotted, resource in _BOUND_RESOURCE_SPECS:
        monkeypatch.setattr(resource, "ungoverned", ungoverned, raising=False)
        monkeypatch.setattr(resource, "ungoverned_command", ungoverned_command, raising=False)
    monkeypatch.setattr(_BoundEntity, "inherited_ungoverned", ungoverned, raising=False)
    monkeypatch.setattr(
        _BoundEntity, "inherited_ungoverned_command", ungoverned_command, raising=False
    )
    monkeypatch.setattr(OffsetLazyCollection, "inherited_ungoverned", ungoverned, raising=False)
    monkeypatch.setattr(
        OffsetLazyCollection, "inherited_ungoverned_command", ungoverned_command, raising=False
    )

    discovered = discover_public_methods()
    canonical = {case.sdk_method for case in OPERATION_CASES if case.is_canonical}
    for dotted, _resource in _BOUND_RESOURCE_SPECS:
        assert f"{dotted}.ungoverned" in discovered
        assert f"{dotted}.inherited_ungoverned" in discovered
    assert discovered != canonical


def test_bound_eager_command_parity_rejects_signature_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = next(case for case in OPERATION_CASES if case.sdk_method == "agents.Agent.set_skills")
    original = Agent.set_skills_command

    def drifted_command(
        self: object,
        skill_ids: tuple[str, ...],
        *,
        drift: str = "",
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[None]]:
        del drift
        return original(cast("Agent", self), skill_ids, options=options)

    monkeypatch.setattr(Agent, "set_skills_command", drifted_command)
    with pytest.raises(AssertionError, match=r"agents\.Agent\.set_skills"):
        _assert_eager_command_parity(case)


def test_discovered_cli_surface_has_normalized_options_parity() -> None:
    """Every discovered CLI pair has matching signatures and typed options."""
    missing_options: set[str] = set()
    for case in OPERATION_CASES:
        if not case.is_canonical:
            continue
        eager = _case_method(case)
        command = getattr(_case_class(case), f"{case.method}_command")
        eager_overloads = typing.get_overloads(eager) or (eager,)
        command_overloads = typing.get_overloads(command) or (command,)
        assert len(eager_overloads) == len(command_overloads), case.sdk_method
        for eager_fn, command_fn in zip(eager_overloads, command_overloads, strict=True):
            for function in (eager_fn, command_fn):
                parameters = tuple(inspect.signature(function).parameters.values())[1:]
                if not parameters or parameters[-1].name != "options":
                    missing_options.add(case.sdk_method)
                    assert case.sdk_method in _LAZY_OPTIONS_PARITY_EXCEPTIONS, case.sdk_method
                    assert case.bound_target == "project_issues", case.sdk_method
                    continue
                assert case.sdk_method not in _LAZY_OPTIONS_PARITY_EXCEPTIONS, case.sdk_method
                option = parameters[-1]
                assert option.kind is inspect.Parameter.KEYWORD_ONLY, case.sdk_method
                assert typing.get_type_hints(function)["options"] == OperationOptions | None
    assert missing_options == _LAZY_OPTIONS_PARITY_EXCEPTIONS


_CHANGED_PUBLIC_SURFACE_SIGNATURES: tuple[tuple[type[object], str, tuple[str, ...]], ...] = (
    (
        IssueResource,
        "create",
        (
            "title",
            "description",
            "description_file",
            "description_input",
            "priority",
            "assignee_id",
            "label_ids",
            "project",
            "project_id",
            "parent_id",
            "options",
        ),
    ),
    (IssueResource, "set_status", ("issue_id", "status", "options")),
    (
        ProjectResource,
        "create",
        ("name", "description", "description_file", "options"),
    ),
    (ProjectResource, "set_status", ("project_id", "status", "options")),
    (
        ProjectIssueCollection,
        "create",
        (
            "title",
            "description",
            "description_file",
            "description_input",
            "priority",
            "assignee_id",
            "label_ids",
            "parent_id",
            "options",
        ),
    ),
    (Issue, "set_status", ("status", "options")),
)


def _signature_parameters(function: object) -> tuple[inspect.Parameter, ...]:
    assert inspect.isfunction(function)
    parameters = tuple(inspect.signature(function).parameters.values())
    if parameters and parameters[0].name in {"self", "cls"}:
        return parameters[1:]
    return parameters


@pytest.mark.parametrize(
    ("owner", "method_name", "expected_names"),
    _CHANGED_PUBLIC_SURFACE_SIGNATURES,
    ids=lambda case: case if isinstance(case, str) else None,
)
def test_changed_public_surface_is_explicit_and_command_parity(
    owner: type[object],
    method_name: str,
    expected_names: tuple[str, ...],
) -> None:
    eager = getattr(owner, method_name)
    command = getattr(owner, f"{method_name}_command")
    eager_overloads = typing.get_overloads(eager) or (eager,)
    command_overloads = typing.get_overloads(command) or (command,)
    assert len(eager_overloads) == len(command_overloads)
    for eager_fn, command_fn in zip(eager_overloads, command_overloads, strict=True):
        eager_parameters = _signature_parameters(eager_fn)
        command_parameters = _signature_parameters(command_fn)
        assert tuple(parameter.name for parameter in eager_parameters) == expected_names
        assert tuple(parameter.name for parameter in command_parameters) == expected_names
        assert tuple(parameter.kind for parameter in eager_parameters) == tuple(
            parameter.kind for parameter in command_parameters
        )
        assert all(
            parameter.kind is not inspect.Parameter.VAR_KEYWORD for parameter in eager_parameters
        )
        assert all(
            parameter.kind is not inspect.Parameter.VAR_KEYWORD for parameter in command_parameters
        )
        for function in (eager_fn, command_fn):
            hints = typing.get_type_hints(function)
            assert "request" not in hints
            assert all("Request" not in str(annotation) for annotation in hints.values())
            assert hints["options"] == OperationOptions | None
            assert _signature_parameters(function)[-1].name == "options"

    assert not hasattr(Project, "set_status")


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
        "issues.move_after",
        "issues.move_before",
        "issues.move_to_bottom",
        "issues.move_to_top",
        "issues.metadata.set_typed",
        "issues.reorder",
        "issues.unassign",
        "cli.command",
        "issues.Issue.update",
        "issues.Issue.refresh",
        "issues.Issue.assign",
        "issues.Issue.unassign",
        "issues.Issue.set_status",
        "issues.Issue.move_to_top",
        "issues.Issue.move_to_bottom",
        "issues.Issue.move_before",
        "issues.Issue.move_after",
        "projects.Project.update",
        "projects.Project.refresh",
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
        if case.contract_operation_id is None:
            continue
        assert case.expected_response_id in responses, sdk_method
        annotation = typing.get_type_hints(_case_method(case))["return"]
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
    implemented_contract_keys = {
        (operation.operation_id, entrypoint.entrypoint_id)
        for operation in contract.operations
        for entrypoint in operation.entrypoints
        if _contract_entrypoint_is_implemented(entrypoint)
    }
    assert set(canonical_by_operation) == implemented_contract_keys
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
            case = canonical_by_operation[(operation.operation_id, entrypoint.entrypoint_id)]
            assert case.method == method_name


def _operation_payload(case: OperationCase) -> tuple[object, ...]:
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


def _assert_current_payload_fingerprint(case: OperationCase, fingerprints: dict[str, str]) -> None:
    actual = hashlib.sha256(repr(_operation_payload(case)).encode()).hexdigest()
    assert actual == fingerprints[case.id], case.id


def test_current_payload_fingerprint_guard() -> None:
    from tests.cases.legacy_payloads import CURRENT_PAYLOAD_FINGERPRINTS

    resolved = [case for case in OPERATION_CASES if case.id in CURRENT_PAYLOAD_FINGERPRINTS]
    assert len(CURRENT_PAYLOAD_FINGERPRINTS) == 142
    assert len(resolved) == len(CURRENT_PAYLOAD_FINGERPRINTS)
    assert len({case.id for case in resolved}) == len(resolved)
    assert {case.id for case in resolved} == set(CURRENT_PAYLOAD_FINGERPRINTS)
    assert all(case.id and not case.id.startswith("legacy:") for case in resolved)
    for case in resolved:
        _assert_current_payload_fingerprint(case, CURRENT_PAYLOAD_FINGERPRINTS)


def test_current_payload_fingerprint_detects_mutation() -> None:
    from tests.cases.legacy_payloads import CURRENT_PAYLOAD_FINGERPRINTS

    case = next(case for case in OPERATION_CASES if case.id == "manual:agents.list:canonical")
    mutated = replace(case, expected_argv=(*case.expected_argv, "--mutated"))
    with pytest.raises(AssertionError, match=case.id):
        _assert_current_payload_fingerprint(mutated, CURRENT_PAYLOAD_FINGERPRINTS)


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
