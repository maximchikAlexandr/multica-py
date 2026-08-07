from __future__ import annotations

import datetime
import shlex
from typing import cast
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.agents import AgentUpdateRequest
from multica_py.models.autopilots import (
    AutopilotTrigger,
    AutopilotTriggerUpdate,
    AutopilotUpdateRequest,
)
from multica_py.models.issues import IssueUpdateRequest
from multica_py.models.labels import LabelUpdateRequest
from multica_py.models.project_resources import ProjectResourceUpdateLocalDirectoryRequest
from multica_py.models.projects import ProjectUpdateRequest
from multica_py.models.skills import SkillUpdateRequest
from multica_py.models.system import RuntimeUpdate, UserProfile, UserProfileUpdate
from multica_py.resources.agents import Agent, AgentResource
from multica_py.resources.autopilots import Autopilot, AutopilotResource
from multica_py.resources.issues import Issue, IssueResource
from multica_py.resources.labels import Label, LabelResource
from multica_py.resources.project_resources import ProjectResourceCollection
from multica_py.resources.projects import Project, ProjectResource
from multica_py.resources.runtimes import RuntimeResource
from multica_py.resources.skills import Skill, SkillResource
from multica_py.resources.users import UserResource
from tests.cases.presence import (
    NO_OP_CASES,
    OPTIONAL_UPDATE_PRESENCE_CASES,
    PRESENCE_CASES,
    REQUIRED_UPDATE_BOUNDARY_CASES,
    NoOpCase,
    PresenceCase,
)

_MODELS: dict[str, type[msgspec.Struct]] = {
    "ProjectUpdateRequest": ProjectUpdateRequest,
    "AgentUpdateRequest": AgentUpdateRequest,
    "SkillUpdateRequest": SkillUpdateRequest,
    "IssueUpdateRequest": IssueUpdateRequest,
    "AutopilotUpdateRequest": AutopilotUpdateRequest,
    "LabelUpdateRequest": LabelUpdateRequest,
    "AutopilotTriggerUpdate": AutopilotTriggerUpdate,
    "UserProfileUpdate": UserProfileUpdate,
    "ProjectResourceUpdateLocalDirectoryRequest": ProjectResourceUpdateLocalDirectoryRequest,
    "RuntimeUpdate": RuntimeUpdate,
}

_UPDATE_MODELS = frozenset(_MODELS) - {
    "ProjectResourceUpdateLocalDirectoryRequest",
    "RuntimeUpdate",
}

_TARGETS = {
    "ProjectUpdateRequest": "p1",
    "AgentUpdateRequest": "a1",
    "SkillUpdateRequest": "s1",
    "IssueUpdateRequest": "i1",
    "AutopilotUpdateRequest": "ap1",
    "LabelUpdateRequest": "l1",
    "AutopilotTriggerUpdate": "ap1",
    "UserProfileUpdate": "profile",
}

_RESULT_TYPES: dict[str, type[object]] = {
    "ProjectUpdateRequest": Project,
    "AgentUpdateRequest": Agent,
    "SkillUpdateRequest": Skill,
    "IssueUpdateRequest": Issue,
    "AutopilotUpdateRequest": Autopilot,
    "LabelUpdateRequest": Label,
    "AutopilotTriggerUpdate": AutopilotTrigger,
    "UserProfileUpdate": UserProfile,
}


def _transport() -> MagicMock:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    return transport


def _resource(model_id: str, transport: MagicMock) -> object:
    config = ClientConfig()
    return {
        "ProjectUpdateRequest": ProjectResource(transport, config),
        "AgentUpdateRequest": AgentResource(transport, config),
        "SkillUpdateRequest": SkillResource(transport, config),
        "IssueUpdateRequest": IssueResource(transport, config),
        "AutopilotUpdateRequest": AutopilotResource(transport, config),
        "LabelUpdateRequest": LabelResource(transport, config),
        "AutopilotTriggerUpdate": AutopilotResource(transport, config),
        "UserProfileUpdate": UserResource(transport, config),
        "ProjectResourceUpdateLocalDirectoryRequest": ProjectResourceCollection(transport, config),
        "RuntimeUpdate": RuntimeResource(transport, config),
    }[model_id]


def _command(resource: object, model_id: str, target: str, request: object) -> object:
    if model_id == "AutopilotTriggerUpdate":
        return cast("AutopilotResource", resource).trigger_update_command(
            "ap1", "tr1", cast("AutopilotTriggerUpdate", request)
        )
    if model_id == "UserProfileUpdate":
        return cast("UserResource", resource).profile_update_command(
            cast("UserProfileUpdate", request)
        )
    if model_id == "ProjectResourceUpdateLocalDirectoryRequest":
        return cast("ProjectResourceCollection", resource).update_local_directory_command(
            "p1", "r1", cast("ProjectResourceUpdateLocalDirectoryRequest", request)
        )
    if model_id == "RuntimeUpdate":
        return cast("RuntimeResource", resource).update_command(
            "r1", cast("RuntimeUpdate", request)
        )
    return getattr(resource, "update_command")(target, request)


def _direct_command(
    resource: object, model_id: str, target: str, kwargs: dict[str, object]
) -> object:
    if model_id == "AutopilotTriggerUpdate":
        return getattr(resource, "trigger_update_command")("ap1", "tr1", **kwargs)
    if model_id == "UserProfileUpdate":
        return getattr(resource, "profile_update_command")(**kwargs)
    if model_id == "ProjectResourceUpdateLocalDirectoryRequest":
        return getattr(resource, "update_local_directory_command")("p1", "r1", **kwargs)
    if model_id == "RuntimeUpdate":
        return getattr(resource, "update_command")("r1", **kwargs)
    return getattr(resource, "update_command")(target, **kwargs)


def _request(model_id: str, kwargs: dict[str, object]) -> msgspec.Struct:
    return _MODELS[model_id](**kwargs)


def _render(expected_argv: tuple[str, ...]) -> str:
    return shlex.join(("multica", *expected_argv))


@pytest.mark.parametrize("case", OPTIONAL_UPDATE_PRESENCE_CASES, ids=lambda case: case.id)
def test_approved_presence_vectors_have_exact_plan_or_pre_io_error(case: PresenceCase) -> None:
    kwargs = {} if case.state == "omitted" else {case.field: case.value}

    object_transport = _transport()
    object_resource = _resource(case.model_id, object_transport)
    if case.error_match is not None:
        with pytest.raises((TypeError, ValueError), match=case.error_match):
            request = _request(case.model_id, kwargs)
            _command(object_resource, case.model_id, "p1", request)
        object_transport.run_bytes.assert_not_called()
        object_transport.run_text.assert_not_called()

        direct_transport = _transport()
        direct_resource = _resource(case.model_id, direct_transport)
        with pytest.raises((TypeError, ValueError), match=case.error_match):
            _direct_command(direct_resource, case.model_id, "p1", kwargs)
        direct_transport.run_bytes.assert_not_called()
        direct_transport.run_text.assert_not_called()
        return

    request = _request(case.model_id, kwargs)
    target = _TARGETS[case.model_id]
    object_command = _command(object_resource, case.model_id, target, request)
    direct_command = _direct_command(object_resource, case.model_id, target, kwargs)
    expected = tuple(
        _render(argv) for argv in cast("tuple[tuple[str, ...], ...]", case.expected_argv)
    )
    assert object_command.commands == direct_command.commands == expected  # type: ignore[attr-defined]
    object_transport.run_bytes.assert_not_called()
    object_transport.run_text.assert_not_called()


@pytest.mark.parametrize("case", NO_OP_CASES, ids=lambda case: case.id)
def test_all_optional_no_op_reads_once_and_returns_current_entity(case: NoOpCase) -> None:
    transport = _transport()
    resource = _resource(case.model_id, transport)
    command = _command(resource, case.model_id, case.target_id, _request(case.model_id, {}))

    expected_command = _render((*case.expected_argv, "--output", "json"))
    assert command.commands == (expected_command,)  # type: ignore[attr-defined]

    transport.run_bytes.return_value = RawCommandResult(
        argv=("multica", *case.expected_argv, "--output", "json"),
        exit_code=0,
        stdout=case.stdout,
        stderr=b"",
        duration=datetime.timedelta(),
    )
    result = command.run()  # type: ignore[attr-defined]
    assert isinstance(result, _RESULT_TYPES[case.model_id])
    assert result.id == case.expected_entity_id  # type: ignore[attr-defined]
    transport.run_bytes.assert_called_once_with(
        (*case.expected_argv, "--output", "json"), stdin=None, timeout=None
    )
    transport.run_text.assert_not_called()


def test_presence_table_is_field_complete_and_frozen() -> None:
    assert isinstance(PRESENCE_CASES, tuple)
    by_model: dict[str, set[str]] = {model_id: set() for model_id in _UPDATE_MODELS}
    for case in PRESENCE_CASES:
        if case.model_id in by_model:
            by_model[case.model_id].add(case.field)
    for model_id in _UPDATE_MODELS:
        assert by_model[model_id] == {
            field.name for field in msgspec.structs.fields(_MODELS[model_id])
        }


@pytest.mark.parametrize("case", REQUIRED_UPDATE_BOUNDARY_CASES, ids=lambda case: case.id)
def test_required_update_boundaries_never_construct_a_no_op(case: PresenceCase) -> None:
    kwargs = {} if case.state == "omitted" else {case.field: case.value}
    transport = _transport()
    resource = _resource(case.model_id, transport)
    if case.error_match is not None:
        with pytest.raises((TypeError, ValueError), match=case.error_match):
            request = _request(case.model_id, kwargs)
            _command(resource, case.model_id, "p1", request)
        transport.run_bytes.assert_not_called()
        transport.run_text.assert_not_called()
        return

    request = _request(case.model_id, {"target_version": "v1", **kwargs})
    command = _command(resource, case.model_id, "p1", request)
    expected = tuple(
        _render(argv) for argv in cast("tuple[tuple[str, ...], ...]", case.expected_argv)
    )
    assert command.commands == expected  # type: ignore[attr-defined]
    transport.run_bytes.assert_not_called()
