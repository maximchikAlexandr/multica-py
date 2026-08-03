from __future__ import annotations

import inspect
import typing
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.agents import AgentCreateRequest, AgentUpdateRequest
from multica_py.models.issues import (
    InlineDescription,
    IssueAssignmentRequest,
    IssueCreateRequest,
    IssueReorderRequest,
    IssueUpdateRequest,
    NoDescription,
)
from multica_py.models.project_resources import (
    ProjectResourceAddLocalDirectoryRequest,
    ProjectResourceUpdateLocalDirectoryRequest,
)
from multica_py.models.projects import ProjectCreateRequest, ProjectUpdateRequest
from multica_py.models.skills import SkillCreateRequest, SkillUpdateRequest
from multica_py.models.system import RuntimeUpdate, UserProfileUpdate
from multica_py.resources._base import _resolve_request
from multica_py.resources.agents import AgentResource
from multica_py.resources.issues import IssueResource
from multica_py.resources.project_resources import ProjectResourceCollection
from multica_py.resources.projects import ProjectResource
from multica_py.resources.runtimes import RuntimeResource
from multica_py.resources.skills import SkillResource
from multica_py.resources.users import UserResource
from multica_py.sentinels import Unset

_IN_SCOPE: list[tuple[str, type, type]] = [
    ("projects.create", ProjectResource, ProjectCreateRequest),
    ("projects.update", ProjectResource, ProjectUpdateRequest),
    ("agents.create", AgentResource, AgentCreateRequest),
    ("agents.update", AgentResource, AgentUpdateRequest),
    ("skills.create", SkillResource, SkillCreateRequest),
    ("skills.update", SkillResource, SkillUpdateRequest),
    ("issues.create", IssueResource, IssueCreateRequest),
    ("issues.update", IssueResource, IssueUpdateRequest),
    ("issues.assign", IssueResource, IssueAssignmentRequest),
    ("issues.reorder", IssueResource, IssueReorderRequest),
    ("runtimes.update", RuntimeResource, RuntimeUpdate),
    (
        "project_resources.add_local_directory",
        ProjectResourceCollection,
        ProjectResourceAddLocalDirectoryRequest,
    ),
    (
        "project_resources.update_local_directory",
        ProjectResourceCollection,
        ProjectResourceUpdateLocalDirectoryRequest,
    ),
    ("users.profile_update", UserResource, UserProfileUpdate),
]

_NODEFAULT = object()


class _DummyRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    value: int = 0


class TestResolveRequest:
    def test_request_only_returns_it(self) -> None:
        req = _DummyRequest(name="x")
        assert _resolve_request(req, {}, _DummyRequest) is req

    def test_kwargs_only_constructs(self) -> None:
        result = _resolve_request(None, {"name": "x", "value": 42}, _DummyRequest)
        assert result.name == "x"
        assert result.value == 42

    def test_mixed_raises_type_error(self) -> None:
        req = _DummyRequest(name="x")
        with pytest.raises(
            TypeError, match=r"Pass either a request object or keyword arguments, not both."
        ):
            _resolve_request(req, {"name": "y"}, _DummyRequest)

    def test_neither_raises_type_error(self) -> None:
        with pytest.raises(
            TypeError, match=r"Pass a _DummyRequest or its keyword arguments; got neither."
        ):
            _resolve_request(None, {}, _DummyRequest)

    def test_unknown_kwarg_re_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            _resolve_request(None, {"unknown": "x"}, _DummyRequest)


def _get_direct_overload(resource_cls: type, method_name: str) -> object | None:
    method = getattr(resource_cls, method_name)
    overloads = typing.get_overloads(method)
    for overload in overloads:
        sig = inspect.signature(overload)
        params = list(sig.parameters.values())
        if params and params[0].name == "self":
            params = params[1:]
        if any(p.kind == inspect.Parameter.KEYWORD_ONLY for p in params):
            return overload
    return None


def test_structural_parity_guard() -> None:
    for sdk_method, resource_cls, request_cls in _IN_SCOPE:
        method_name = sdk_method.rsplit(".", 1)[-1]
        overload = _get_direct_overload(resource_cls, method_name)
        assert overload is not None, f"no direct overload for {sdk_method}"
        sig = inspect.signature(overload)  # type: ignore[arg-type]
        params = [p for p in sig.parameters.values() if p.kind == inspect.Parameter.KEYWORD_ONLY]
        field_names = {p.name for p in params}
        request_fields = {f.name for f in msgspec.structs.fields(request_cls)}
        assert field_names == request_fields, (
            f"{sdk_method}: direct overload fields {field_names} != request fields {request_fields}"
        )
        overload_defaults = {
            p.name: _NODEFAULT if p.default is inspect.Parameter.empty else p.default
            for p in params
        }
        request_defaults = {
            f.name: _NODEFAULT if f.default is msgspec.NODEFAULT else f.default
            for f in msgspec.structs.fields(request_cls)
        }
        assert overload_defaults == request_defaults, (
            f"{sdk_method}: overload defaults {overload_defaults} != request defaults {request_defaults}"
        )


_SENTINEL_REQUEST: object = object()

_MIXED_NEITHER_CASES: list[tuple[str, type, str, tuple[object, ...], dict[str, object]]] = []

for sdk_method, resource_cls, _ in _IN_SCOPE:
    method_name = sdk_method.rsplit(".", 1)[-1]
    sig = inspect.signature(getattr(resource_cls, method_name))
    params = list(sig.parameters.values())
    if params and params[0].name == "self":
        params = params[1:]
    required_positional = tuple(
        p.name
        for p in params
        if p.kind == inspect.Parameter.POSITIONAL_ONLY
        and p.default is inspect.Parameter.empty
        and p.name != "request"
    )
    args = tuple("test" for _ in required_positional) + (_SENTINEL_REQUEST,)
    _MIXED_NEITHER_CASES.append((sdk_method, resource_cls, method_name, args, {"name": "extra"}))


@pytest.mark.parametrize(
    "sdk_method,resource_cls,method_name,args,kwargs",
    _MIXED_NEITHER_CASES,
    ids=[c[0] for c in _MIXED_NEITHER_CASES],
)
def test_mixed_input_type_error(
    sdk_method: str,
    resource_cls: type,
    method_name: str,
    args: tuple[object, ...],
    kwargs: dict[str, object],
    mock_transport: MagicMock,
) -> None:
    transport: CliTransport = mock_transport
    config = ClientConfig()
    resource = resource_cls(transport, config)
    method = getattr(resource, method_name)
    with pytest.raises(
        TypeError, match=r"Pass either a request object or keyword arguments, not both."
    ):
        method(*args, **kwargs)
    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()
    mock_transport.spawn.assert_not_called()


_NEITHER_CASES: list[tuple[str, type, str, tuple[object, ...]]] = []

for sdk_method, resource_cls, _ in _IN_SCOPE:
    method_name = sdk_method.rsplit(".", 1)[-1]
    sig = inspect.signature(getattr(resource_cls, method_name))
    params = list(sig.parameters.values())
    if params and params[0].name == "self":
        params = params[1:]
    required_positional = tuple(
        p.name
        for p in params
        if p.kind == inspect.Parameter.POSITIONAL_ONLY
        and p.default is inspect.Parameter.empty
        and p.name != "request"
    )
    _NEITHER_CASES.append((sdk_method, resource_cls, method_name, required_positional))


@pytest.mark.parametrize(
    "sdk_method,resource_cls,method_name,positional_args",
    _NEITHER_CASES,
    ids=[c[0] for c in _NEITHER_CASES],
)
def test_neither_input_type_error(
    sdk_method: str,
    resource_cls: type,
    method_name: str,
    positional_args: tuple[object, ...],
    mock_transport: MagicMock,
) -> None:
    transport: CliTransport = mock_transport
    config = ClientConfig()
    resource = resource_cls(transport, config)
    method = getattr(resource, method_name)
    with pytest.raises(TypeError, match=r"Pass a .* or its keyword arguments; got neither."):
        method(*positional_args)
    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()
    mock_transport.spawn.assert_not_called()


_POST_INIT_CASES: list[tuple[str, type, str, tuple[object, ...], dict[str, object], str]] = [
    (
        "issues.create",
        IssueResource,
        "create",
        (),
        {"title": "Test", "project_id": ""},
        "project_id must be non-empty",
    ),
    (
        "issues.create",
        IssueResource,
        "create",
        (),
        {"title": "Test", "parent_id": ""},
        "parent_id must be non-empty",
    ),
    (
        "issues.update",
        IssueResource,
        "update",
        ("iss_1",),
        {"project_id": ""},
        "project_id must be non-empty",
    ),
    (
        "issues.update",
        IssueResource,
        "update",
        ("iss_1",),
        {"parent_id": ""},
        "parent_id must be non-empty",
    ),
    (
        "issues.assign",
        IssueResource,
        "assign",
        (),
        {"issue_id": "iss_1"},
        "Exactly one assignment target must be set",
    ),
    (
        "issues.assign",
        IssueResource,
        "assign",
        (),
        {"issue_id": "iss_1", "member_id": "u1", "agent_id": "a1"},
        "Exactly one assignment target must be set",
    ),
    (
        "issues.reorder",
        IssueResource,
        "reorder",
        (),
        {"issue_id": "iss_1"},
        "Exactly one reorder target must be set",
    ),
    (
        "issues.reorder",
        IssueResource,
        "reorder",
        (),
        {"issue_id": "iss_1", "top": True, "bottom": True},
        "Exactly one reorder target must be set",
    ),
    (
        "project_resources.add_local_directory",
        ProjectResourceCollection,
        "add_local_directory",
        ("pr_1",),
        {"local_path": "/tmp", "daemon_id": ""},
        "daemon_id must be non-empty",
    ),
    (
        "project_resources.update_local_directory",
        ProjectResourceCollection,
        "update_local_directory",
        ("pr_1", "res_1"),
        {"local_path": ""},
        "local_path must be non-empty",
    ),
    (
        "users.profile_update",
        UserResource,
        "profile_update",
        (),
        {"description": msgspec.UNSET},
        "description must be provided",
    ),
]


@pytest.mark.parametrize(
    "sdk_method,resource_cls,method_name,args,kwargs,expected_msg",
    _POST_INIT_CASES,
    ids=[c[0] + ":" + str(i) for i, c in enumerate(_POST_INIT_CASES)],
)
def test_post_init_value_error(
    sdk_method: str,
    resource_cls: type,
    method_name: str,
    args: tuple[object, ...],
    kwargs: dict[str, object],
    expected_msg: str,
    mock_transport: MagicMock,
) -> None:
    transport: CliTransport = mock_transport
    config = ClientConfig()
    resource = resource_cls(transport, config)
    method = getattr(resource, method_name)
    with pytest.raises(ValueError, match=expected_msg):
        method(*args, **kwargs)
    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()
    mock_transport.spawn.assert_not_called()
