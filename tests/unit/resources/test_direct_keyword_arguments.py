from __future__ import annotations

import inspect
import shlex
import typing
from dataclasses import dataclass
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.issues import (
    IssueListFilter,
)
from multica_py.resources.agents import AgentResource
from multica_py.resources.issues import IssueResource
from multica_py.resources.project_resources import ProjectResourceCollection
from multica_py.resources.projects import ProjectResource
from multica_py.resources.skills import SkillResource

_OPTIONAL_DIRECT_CASES = (
    (IssueResource, "list", IssueListFilter),
    (IssueResource, "list_command", IssueListFilter),
)


@pytest.mark.parametrize("resource_cls, method_name, request_cls", _OPTIONAL_DIRECT_CASES)
def test_optional_direct_overloads_match_request_fields(
    resource_cls: type, method_name: str, request_cls: type
) -> None:
    overload = _get_direct_overload(resource_cls, method_name)
    assert overload is not None
    signature = inspect.signature(overload)  # type: ignore[arg-type]
    params = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind == inspect.Parameter.KEYWORD_ONLY and parameter.name != "options"
    ]
    assert {parameter.name for parameter in params} == {
        field.name for field in msgspec.structs.fields(request_cls)
    }
    hints = typing.get_type_hints(overload)
    assert {name: hints[name] for name in (parameter.name for parameter in params)} == {
        field.name: field.type for field in msgspec.structs.fields(request_cls)
    }


def test_issue_list_object_and_direct_forms_have_identical_empty_and_filtered_plans(
    mock_transport: MagicMock,
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    resource = IssueResource(mock_transport, ClientConfig())
    request = IssueListFilter(limit=10, offset=2)

    assert (
        resource.list_command(request).commands
        == resource.list_command(limit=10, offset=2).commands
    )
    assert resource.list_command().commands == resource.list_command(IssueListFilter()).commands
    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()


@pytest.mark.parametrize(
    ("resource_cls", "method_name", "expected_names"),
    (
        (
            AgentResource,
            "create_command",
            ("self", "name", "description", "runtime_id", "model", "options"),
        ),
        (
            AgentResource,
            "update_command",
            ("self", "agent_id", "name", "description", "options"),
        ),
        (ProjectResource, "create_command", ("self", "name", "description", "options")),
        (
            ProjectResource,
            "update_command",
            ("self", "project_id", "name", "description", "options"),
        ),
        (SkillResource, "create_command", ("self", "name", "description", "options")),
        (
            SkillResource,
            "update_command",
            ("self", "skill_id", "name", "description", "options"),
        ),
    ),
)
def test_migrated_operations_have_one_explicit_signature(
    resource_cls: type, method_name: str, expected_names: tuple[str, ...]
) -> None:
    signature = inspect.signature(getattr(resource_cls, method_name))
    assert tuple(signature.parameters) == expected_names
    assert all(
        parameter.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        for parameter in signature.parameters.values()
    )
    assert all(
        parameter.name not in {"request", "kwargs"} for parameter in signature.parameters.values()
    )


@pytest.mark.parametrize(
    ("resource_cls", "method_name", "target"),
    (
        (AgentResource, "create_command", ()),
        (AgentResource, "update_command", ("a1",)),
        (ProjectResource, "create_command", ()),
        (ProjectResource, "update_command", ("p1",)),
        (SkillResource, "create_command", ()),
        (SkillResource, "update_command", ("s1",)),
    ),
)
def test_migrated_invalid_values_fail_before_io(
    resource_cls: type, method_name: str, target: tuple[str, ...]
) -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    resource = resource_cls(transport, ClientConfig())
    method = getattr(resource, method_name)
    with pytest.raises((TypeError, ValueError)):
        if method_name.endswith("create_command"):
            method(name=" ")
        else:
            method(*target, name=None)
    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


@pytest.mark.parametrize(
    ("resource_cls", "command_name", "target", "name_flag"),
    (
        (AgentResource, "agent", "a1", "--name"),
        (ProjectResource, "project", "p1", "--title"),
        (SkillResource, "skill", "s1", "--name"),
    ),
)
def test_migrated_updates_preserve_unset_empty_and_nullable_presence(
    resource_cls: type, command_name: str, target: str, name_flag: str
) -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    resource = resource_cls(transport, ClientConfig())

    assert resource.update_command(target).commands == (
        shlex.join(("multica", command_name, "get", target, "--output", "json")),
    )
    assert resource.update_command(target, name="").commands == (
        shlex.join(("multica", command_name, "update", target, name_flag, "", "--output", "json")),
    )
    assert resource.update_command(target, description=None).commands == (
        shlex.join(
            ("multica", command_name, "update", target, "--description", "", "--output", "json")
        ),
    )
    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


def _get_direct_overload(resource_cls: type, method_name: str) -> object | None:
    method = getattr(resource_cls, method_name)
    overloads = typing.get_overloads(method)
    for overload in overloads:
        sig = inspect.signature(overload)
        params = list(sig.parameters.values())
        if params and params[0].name == "self":
            params = params[1:]
        if any(p.kind == inspect.Parameter.KEYWORD_ONLY and p.name != "options" for p in params):
            return overload
    return None


@dataclass(frozen=True)
class PostInitCase:
    name: str
    sdk_method: str
    resource_cls: type
    method_name: str
    args: tuple[object, ...]
    kwargs: tuple[tuple[str, object], ...]
    expected_msg: str


_POST_INIT_CASES = (
    PostInitCase(
        "issues.create:blank-project-id",
        "issues.create",
        IssueResource,
        "create",
        (),
        (("title", "Test"), ("project_id", "")),
        "project_id must be non-empty",
    ),
    PostInitCase(
        "issues.create:blank-parent-id",
        "issues.create",
        IssueResource,
        "create",
        (),
        (("title", "Test"), ("parent_id", "")),
        "parent_id must be non-empty",
    ),
    PostInitCase(
        "issues.update:blank-project-id",
        "issues.update",
        IssueResource,
        "update",
        ("iss_1",),
        (("project_id", ""),),
        "project_id must be non-empty",
    ),
    PostInitCase(
        "issues.update:blank-parent-id",
        "issues.update",
        IssueResource,
        "update",
        ("iss_1",),
        (("parent_id", ""),),
        "parent_id must be non-empty",
    ),
    PostInitCase(
        "issues.assign:missing-target",
        "issues.assign",
        IssueResource,
        "assign",
        (),
        (("issue_id", "iss_1"), ("assignee", "")),
        "assignee must be non-empty",
    ),
    PostInitCase(
        "issues.assign:multiple-targets",
        "issues.assign",
        IssueResource,
        "assign",
        (),
        (("issue_id", "iss_1"), ("assignee", " ")),
        "assignee must be non-empty",
    ),
    PostInitCase(
        "issues.reorder:missing-target",
        "issues.reorder",
        IssueResource,
        "reorder",
        (),
        (("issue_id", "iss_1"),),
        "Exactly one reorder target must be set",
    ),
    PostInitCase(
        "issues.reorder:multiple-targets",
        "issues.reorder",
        IssueResource,
        "reorder",
        (),
        (("issue_id", "iss_1"), ("top", True), ("bottom", True)),
        "Exactly one reorder target must be set",
    ),
    PostInitCase(
        "project_resources.add_local_directory:blank-daemon-id",
        "project_resources.add_local_directory",
        ProjectResourceCollection,
        "add_local_directory",
        ("pr_1",),
        (("local_path", "/tmp"), ("daemon_id", "")),
        "daemon_id must be non-empty",
    ),
    PostInitCase(
        "project_resources.update_local_directory:blank-local-path",
        "project_resources.update_local_directory",
        ProjectResourceCollection,
        "update_local_directory",
        ("pr_1", "res_1"),
        (("local_path", ""),),
        "local_path must be non-empty",
    ),
)


@pytest.mark.parametrize(
    "case",
    _POST_INIT_CASES,
    ids=lambda case: case.name,
)
def test_post_init_value_error(
    case: PostInitCase,
    mock_transport: MagicMock,
) -> None:
    transport: CliTransport = mock_transport
    config = ClientConfig()
    resource = case.resource_cls(transport, config)
    method = getattr(resource, case.method_name)
    with pytest.raises(ValueError, match=case.expected_msg):
        method(*case.args, **dict(case.kwargs))
    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()
    mock_transport.spawn.assert_not_called()
