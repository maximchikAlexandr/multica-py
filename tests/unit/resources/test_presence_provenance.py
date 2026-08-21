from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.decoders import decode_json
from multica_py._internal.wire_models import (
    _autopilot_from_wire,
    _autopilot_run_from_wire,
    _AutopilotRunWire,
    _AutopilotWire,
    _issue_from_wire,
    _IssueWire,
    _task_run_from_wire,
    _TaskRunWire,
)
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.entities._base import _BoundEntity
from multica_py.entities.autopilots import Autopilot, AutopilotRun
from multica_py.entities.issues import Issue, TaskRun
from multica_py.enums import IssueStatus
from multica_py.exceptions import DetachedEntityError, MissingRelationContextError
from multica_py.models.issues import IssueAssignee
from multica_py.models.relations import LazyRef


def _issue_payload(**fields: object) -> bytes:
    return json.dumps({"id": "issue-1", "title": "Issue", "status": "todo", **fields}).encode()


@dataclass(frozen=True)
class WirePresenceCase:
    field: str
    wire_value: object
    seed: str


ISSUE_WIRE_PRESENCE_CASES = (
    WirePresenceCase("parent_issue_id", msgspec.UNSET, "missing"),
    WirePresenceCase("parent_issue_id", None, "null"),
    WirePresenceCase("parent_issue_id", "parent-1", "value"),
    WirePresenceCase("project_id", msgspec.UNSET, "missing"),
    WirePresenceCase("project_id", None, "null"),
    WirePresenceCase("project_id", "project-1", "value"),
    WirePresenceCase("assignee", msgspec.UNSET, "missing"),
    WirePresenceCase("assignee", None, "null"),
    WirePresenceCase("assignee", {"id": "agent-1", "name": "Agent", "type": "agent"}, "value"),
)


@pytest.mark.parametrize(
    "case", ISSUE_WIRE_PRESENCE_CASES, ids=lambda case: f"{case.field}-{case.seed}"
)
def test_issue_wire_presence_preserves_public_values(case: WirePresenceCase) -> None:
    encoded = {} if case.wire_value is msgspec.UNSET else {case.field: case.wire_value}
    issue = _issue_from_wire(decode_json(_issue_payload(**encoded), _IssueWire))

    public_field = "parent_id" if case.field == "parent_issue_id" else case.field
    expected = None if case.wire_value is msgspec.UNSET else case.wire_value
    if case.field == "assignee" and isinstance(expected, dict):
        expected = IssueAssignee(**expected)
    assert getattr(issue, public_field) == expected
    presence_field = "parent_id" if case.field == "parent_issue_id" else case.field
    assert (presence_field, case.seed) in issue._wire_presence


AUTOPILOT_PROJECT_PRESENCE_CASES = (
    WirePresenceCase("project_id", msgspec.UNSET, "missing"),
    WirePresenceCase("project_id", None, "null"),
    WirePresenceCase("project_id", "project-1", "value"),
)


@pytest.mark.parametrize(
    "case", AUTOPILOT_PROJECT_PRESENCE_CASES, ids=lambda case: f"{case.field}-{case.seed}"
)
def test_autopilot_project_presence_preserves_public_value(
    case: WirePresenceCase,
) -> None:
    fields = {} if case.wire_value is msgspec.UNSET else {case.field: case.wire_value}
    wire = decode_json(
        json.dumps(
            {
                "id": "autopilot-1",
                "workspace_id": "workspace-1",
                "title": "Autopilot",
                "assignee_type": "agent",
                "assignee_id": "agent-1",
                "status": "active",
                "execution_mode": "manual",
                "created_by_type": "member",
                "created_by_id": "member-1",
                **fields,
            }
        ).encode(),
        _AutopilotWire,
    )
    autopilot = _autopilot_from_wire(wire)

    assert autopilot.project_id == (None if case.wire_value is msgspec.UNSET else case.wire_value)
    assert ("project_id", case.seed) in autopilot._wire_presence


AUTOPILOT_RUN_ISSUE_PRESENCE_CASES = (
    WirePresenceCase("issue_id", msgspec.UNSET, "missing"),
    WirePresenceCase("issue_id", None, "null"),
    WirePresenceCase("issue_id", "issue-1", "value"),
)


@pytest.mark.parametrize(
    "case", AUTOPILOT_RUN_ISSUE_PRESENCE_CASES, ids=lambda case: f"{case.field}-{case.seed}"
)
def test_autopilot_run_issue_presence_preserves_public_value(case: WirePresenceCase) -> None:
    fields = {} if case.wire_value is msgspec.UNSET else {case.field: case.wire_value}
    wire = decode_json(
        json.dumps(
            {
                "id": "run-1",
                "autopilot_id": "autopilot-1",
                "source": "manual",
                "status": "completed",
                **fields,
            }
        ).encode(),
        _AutopilotRunWire,
    )
    run = _autopilot_run_from_wire(wire)

    assert run.issue_id == (None if case.wire_value is msgspec.UNSET else case.wire_value)
    assert ("issue_id", case.seed) in run._wire_presence


TASK_RUN_AGENT_PRESENCE_CASES = (
    WirePresenceCase("agent_id", msgspec.UNSET, "missing"),
    WirePresenceCase("agent_id", None, "null"),
    WirePresenceCase("agent_id", "agent-1", "value"),
)


@pytest.mark.parametrize(
    "case", TASK_RUN_AGENT_PRESENCE_CASES, ids=lambda case: f"{case.field}-{case.seed}"
)
def test_task_run_agent_presence_preserves_inherited_issue_context(
    case: WirePresenceCase,
) -> None:
    fields = {} if case.wire_value is msgspec.UNSET else {case.field: case.wire_value}
    wire = decode_json(
        json.dumps({"id": "task-1", "status": "completed", **fields}).encode(),
        _TaskRunWire,
    )
    task_run = _task_run_from_wire(wire, issue_id="issue-1")

    assert isinstance(task_run, TaskRun)
    assert task_run.agent_id == (None if case.wire_value is msgspec.UNSET else case.wire_value)
    assert task_run.issue_id == "issue-1"
    assert ("agent_id", case.seed) in task_run._wire_presence


def test_detach_preserves_presence_and_freshens_runtime_state() -> None:
    issue = _issue_from_wire(
        decode_json(
            _issue_payload(parent_issue_id=None, project_id="project-1"),
            _IssueWire,
        )
    )._with_client(MagicMock())
    _ = issue.comments

    detached = issue.detach()

    assert detached._client is None
    assert detached._wire_presence == issue._wire_presence
    assert detached._comments is None
    assert detached == issue
    assert hash(detached) == hash(issue)
    assert "_wire_presence" not in detached.to_dict()
    assert "_wire_presence" not in detached.to_json()
    assert "_wire_presence" not in repr(detached)
    assert issue._comments is not None

    serialized = Issue.from_dict(detached.to_dict())
    assert serialized._wire_presence == ()


def test_detach_preserves_run_context_and_manual_none_has_no_seed() -> None:
    run = _autopilot_run_from_wire(
        decode_json(
            b'{"id":"run-1","autopilot_id":"a1","source":"manual",'
            b'"status":"completed","issue_id":"issue-1"}',
            _AutopilotRunWire,
        )
    )
    detached = run._with_client(MagicMock()).detach()

    assert detached.issue_id == "issue-1"
    assert detached._wire_presence == run._wire_presence
    assert detached._client is None

    direct = Issue(id="issue-1", title="Issue", status=IssueStatus.todo)
    assert direct._wire_presence == ()
    assert direct.to_dict()["parent_id"] is None
    assert "_wire_presence" not in direct.to_json()


@dataclass(frozen=True)
class OptionalReferenceCase:
    name: str
    relation: str
    build: Callable[[object], _BoundEntity]


def _build_issue_optional(field: str, value: object) -> _BoundEntity:
    fields = {} if value is msgspec.UNSET else {field: value}
    return _issue_from_wire(decode_json(_issue_payload(**fields), _IssueWire))


def _build_issue_assignee_optional(value: object) -> _BoundEntity:
    if value not in (msgspec.UNSET, None):
        value = {"id": "agent-1", "name": "Agent", "type": "agent"}
    return _build_issue_optional("assignee", value)


def _build_autopilot_optional(value: object) -> _BoundEntity:
    fields = {} if value is msgspec.UNSET else {"project_id": value}
    payload = {
        "id": "autopilot-1",
        "workspace_id": "workspace-1",
        "title": "Autopilot",
        "assignee_type": "agent",
        "assignee_id": "agent-1",
        "status": "active",
        "execution_mode": "manual",
        "created_by_type": "member",
        "created_by_id": "member-1",
        **fields,
    }
    return _autopilot_from_wire(decode_json(json.dumps(payload).encode(), _AutopilotWire))


def _build_autopilot_run_optional(value: object) -> _BoundEntity:
    fields = {} if value is msgspec.UNSET else {"issue_id": value}
    payload = {
        "id": "run-1",
        "autopilot_id": "autopilot-1",
        "source": "manual",
        "status": "completed",
        **fields,
    }
    return _autopilot_run_from_wire(decode_json(json.dumps(payload).encode(), _AutopilotRunWire))


def _build_task_run_optional(value: object) -> _BoundEntity:
    fields = {} if value is msgspec.UNSET else {"agent_id": value}
    payload = {"id": "task-1", "status": "completed", **fields}
    return _task_run_from_wire(
        decode_json(json.dumps(payload).encode(), _TaskRunWire), issue_id="issue-1"
    )


OPTIONAL_REFERENCE_CASES = (
    OptionalReferenceCase(
        "issue parent", "parent", lambda value: _build_issue_optional("parent_issue_id", value)
    ),
    OptionalReferenceCase(
        "issue project", "project", lambda value: _build_issue_optional("project_id", value)
    ),
    OptionalReferenceCase("issue assignee", "assignee_ref", _build_issue_assignee_optional),
    OptionalReferenceCase("autopilot project", "project", _build_autopilot_optional),
    OptionalReferenceCase("autopilot run issue", "issue", _build_autopilot_run_optional),
    OptionalReferenceCase("task run agent", "agent", _build_task_run_optional),
)


@dataclass(frozen=True)
class OptionalReferenceValueCase:
    name: str
    value: object


OPTIONAL_REFERENCE_VALUES = (
    OptionalReferenceValueCase("omitted", msgspec.UNSET),
    OptionalReferenceValueCase("explicit-null", None),
    OptionalReferenceValueCase("value", "target-1"),
)


@pytest.mark.parametrize("case", OPTIONAL_REFERENCE_CASES, ids=lambda case: case.name)
@pytest.mark.parametrize("value_case", OPTIONAL_REFERENCE_VALUES, ids=lambda case: case.name)
def test_optional_reference_shapes_classify_before_and_after_detach(
    case: OptionalReferenceCase, value_case: OptionalReferenceValueCase
) -> None:
    wire_value = value_case.value
    entity = case.build(wire_value)

    if wire_value is msgspec.UNSET:
        reference = cast("LazyRef[object | None]", getattr(entity, case.relation))
        assert reference.loaded is False
        with pytest.raises(MissingRelationContextError):
            reference.get()
        detached = entity.detach()
    elif wire_value is None:
        reference = cast("LazyRef[object | None]", getattr(entity, case.relation))
        assert reference.loaded is True
        assert reference.value is None
        assert reference.get() is None
        detached = entity.detach()
    else:
        client = MulticaClient(ClientConfig())
        try:
            bound = entity._with_client(client)
            bound_reference = cast("LazyRef[object | None]", getattr(bound, case.relation))
            assert bound_reference.loaded is False
            assert bound_reference.get_command().commands
            detached = bound.detach()
        finally:
            client.close()

    detached_reference = cast("LazyRef[object | None]", getattr(detached, case.relation))
    if wire_value is None:
        assert detached_reference.loaded is True
        assert detached_reference.get() is None
    elif wire_value is msgspec.UNSET:
        with pytest.raises(MissingRelationContextError):
            detached_reference.get()
    else:
        with pytest.raises(DetachedEntityError):
            detached_reference.get()


@pytest.mark.parametrize("case", OPTIONAL_REFERENCE_CASES, ids=lambda case: case.name)
def test_public_serialization_and_manual_none_do_not_seed_absence(
    case: OptionalReferenceCase,
) -> None:
    decoded = case.build(None)
    reconstructed = type(decoded).from_dict(decoded.to_dict())
    reconstructed_reference = cast("LazyRef[object | None]", getattr(reconstructed, case.relation))
    assert reconstructed_reference.loaded is False
    with pytest.raises(MissingRelationContextError):
        reconstructed_reference.get()


def test_manual_non_null_reference_is_loadable_after_binding() -> None:
    issue = Issue(id="issue-1", title="Issue", status=IssueStatus.todo, project_id="project-1")
    client = MulticaClient(ClientConfig())
    try:
        bound = issue._with_client(client)
        assert bound.project.loaded is False
        assert bound.project.get_command().commands == (
            "multica project get project-1 --output json",
        )
    finally:
        client.close()
