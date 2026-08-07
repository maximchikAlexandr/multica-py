from __future__ import annotations

import inspect
import typing
from dataclasses import dataclass
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


@dataclass(frozen=True)
class DirectKeywordCase:
    sdk_method: str
    resource_cls: type
    request_cls: type


_IN_SCOPE = (
    DirectKeywordCase("projects.create", ProjectResource, ProjectCreateRequest),
    DirectKeywordCase("projects.update", ProjectResource, ProjectUpdateRequest),
    DirectKeywordCase("agents.create", AgentResource, AgentCreateRequest),
    DirectKeywordCase("agents.update", AgentResource, AgentUpdateRequest),
    DirectKeywordCase("skills.create", SkillResource, SkillCreateRequest),
    DirectKeywordCase("skills.update", SkillResource, SkillUpdateRequest),
    DirectKeywordCase("issues.create", IssueResource, IssueCreateRequest),
    DirectKeywordCase("issues.update", IssueResource, IssueUpdateRequest),
    DirectKeywordCase("issues.assign", IssueResource, IssueAssignmentRequest),
    DirectKeywordCase("issues.reorder", IssueResource, IssueReorderRequest),
    DirectKeywordCase("runtimes.update", RuntimeResource, RuntimeUpdate),
    DirectKeywordCase(
        "project_resources.add_local_directory",
        ProjectResourceCollection,
        ProjectResourceAddLocalDirectoryRequest,
    ),
    DirectKeywordCase(
        "project_resources.update_local_directory",
        ProjectResourceCollection,
        ProjectResourceUpdateLocalDirectoryRequest,
    ),
    DirectKeywordCase("users.profile_update", UserResource, UserProfileUpdate),
)

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
    for case in _IN_SCOPE:
        method_name = case.sdk_method.rsplit(".", 1)[-1]
        overload = _get_direct_overload(case.resource_cls, method_name)
        assert overload is not None, f"no direct overload for {case.sdk_method}"
        sig = inspect.signature(overload)  # type: ignore[arg-type]
        params = [p for p in sig.parameters.values() if p.kind == inspect.Parameter.KEYWORD_ONLY]
        field_names = {p.name for p in params}
        request_fields = {f.name for f in msgspec.structs.fields(case.request_cls)}
        assert field_names == request_fields, (
            f"{case.sdk_method}: direct overload fields {field_names} != request fields {request_fields}"
        )
        overload_hints = typing.get_type_hints(overload)
        overload_types = {name: overload_hints[name] for name in field_names}
        request_types = {f.name: f.type for f in msgspec.structs.fields(case.request_cls)}
        assert overload_types == request_types, (
            f"{case.sdk_method}: direct overload types {overload_types} != request types {request_types}"
        )
        overload_defaults = {
            p.name: _NODEFAULT if p.default is inspect.Parameter.empty else p.default
            for p in params
        }
        request_defaults = {
            f.name: _NODEFAULT if f.default is msgspec.NODEFAULT else f.default
            for f in msgspec.structs.fields(case.request_cls)
        }
        assert overload_defaults == request_defaults, (
            f"{case.sdk_method}: overload defaults {overload_defaults} != request defaults {request_defaults}"
        )


_SENTINEL_REQUEST: object = object()


def _required_positional_args(resource_cls: type, method_name: str) -> tuple[str, ...]:
    sig = inspect.signature(getattr(resource_cls, method_name))
    params = list(sig.parameters.values())
    if params and params[0].name == "self":
        params = params[1:]
    return tuple(
        p.name
        for p in params
        if p.kind == inspect.Parameter.POSITIONAL_ONLY
        and p.default is inspect.Parameter.empty
        and p.name != "request"
    )


@dataclass(frozen=True)
class MixedNeitherCase:
    sdk_method: str
    resource_cls: type
    method_name: str
    args: tuple[object, ...]
    kwargs: tuple[tuple[str, object], ...]


_MIXED_NEITHER_CASES = tuple(
    MixedNeitherCase(
        case.sdk_method,
        case.resource_cls,
        method_name,
        tuple("test" for _ in _required_positional_args(case.resource_cls, method_name))
        + (_SENTINEL_REQUEST,),
        (("name", "extra"),),
    )
    for case in _IN_SCOPE
    for method_name in (case.sdk_method.rsplit(".", 1)[-1],)
)


@pytest.mark.parametrize(
    "case",
    _MIXED_NEITHER_CASES,
    ids=lambda case: case.sdk_method,
)
def test_mixed_input_type_error(
    case: MixedNeitherCase,
    mock_transport: MagicMock,
) -> None:
    transport: CliTransport = mock_transport
    config = ClientConfig()
    resource = case.resource_cls(transport, config)
    method = getattr(resource, case.method_name)
    with pytest.raises(
        TypeError, match=r"Pass either a request object or keyword arguments, not both."
    ):
        method(*case.args, **dict(case.kwargs))
    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()
    mock_transport.spawn.assert_not_called()


@dataclass(frozen=True)
class NeitherCase:
    sdk_method: str
    resource_cls: type
    method_name: str
    positional_args: tuple[object, ...]


_NEITHER_CASES = tuple(
    NeitherCase(
        case.sdk_method,
        case.resource_cls,
        method_name,
        _required_positional_args(case.resource_cls, method_name),
    )
    for case in _IN_SCOPE
    for method_name in (case.sdk_method.rsplit(".", 1)[-1],)
)


@pytest.mark.parametrize(
    "case",
    _NEITHER_CASES,
    ids=lambda case: case.sdk_method,
)
def test_neither_input_type_error(
    case: NeitherCase,
    mock_transport: MagicMock,
) -> None:
    transport: CliTransport = mock_transport
    config = ClientConfig()
    resource = case.resource_cls(transport, config)
    method = getattr(resource, case.method_name)
    with pytest.raises(TypeError, match=r"Pass a .* or its keyword arguments; got neither."):
        method(*case.positional_args)
    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()
    mock_transport.spawn.assert_not_called()


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
        (("issue_id", "iss_1"),),
        "Exactly one assignment target must be set",
    ),
    PostInitCase(
        "issues.assign:multiple-targets",
        "issues.assign",
        IssueResource,
        "assign",
        (),
        (("issue_id", "iss_1"), ("member_id", "u1"), ("agent_id", "a1")),
        "Exactly one assignment target must be set",
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
    PostInitCase(
        "users.profile_update:unset-description",
        "users.profile_update",
        UserResource,
        "profile_update",
        (),
        (("description", msgspec.UNSET),),
        "description must be provided",
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
