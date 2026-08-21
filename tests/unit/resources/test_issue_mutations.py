from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, cast
from unittest.mock import MagicMock

import pytest

from multica_py._internal.decoders import decode_json
from multica_py._internal.specs import RawCommandResult
from multica_py._internal.wire_models import _issue_from_wire, _IssueWire
from multica_py.client import MulticaClient
from multica_py.entities.issues import Issue
from multica_py.entities.workspaces import WorkspaceMember
from multica_py.exceptions import UnsupportedReferenceTargetError
from multica_py.models.issues import IssueAssignee
from multica_py.models.relations import LazyRef

_OLD_PARENT = "parent-old"
_OLD_PROJECT = "project-old"
_OLD_AGENT = "agent-old"


def _issue_payload(
    *, parent_id: str | None, project_id: str | None, assignee: IssueAssignee | None
) -> bytes:
    return json.dumps(
        {
            "id": "issue-1",
            "title": "Issue snapshot",
            "status": "todo",
            "parent_issue_id": parent_id,
            "project_id": project_id,
            "assignee": None
            if assignee is None
            else {"id": assignee.id, "name": assignee.name, "type": assignee.type},
        }
    ).encode()


_OLD_ASSIGNEE = IssueAssignee(id=_OLD_AGENT, name="Old agent", type="agent")


def _issue(payload: bytes, client: MulticaClient) -> Issue:
    return _issue_from_wire(decode_json(payload, _IssueWire))._with_client(client)


def _transport_response(
    argv: tuple[str, ...], issue_payload: bytes, raw_result: Callable[..., RawCommandResult]
) -> RawCommandResult:
    if argv == ("issue", "get", _OLD_PARENT, "--output", "json"):
        return raw_result(argv, stdout=b'{"id":"parent-old","title":"Parent","status":"todo"}')
    if argv == ("project", "get", _OLD_PROJECT, "--output", "json"):
        return raw_result(argv, stdout=b'{"id":"project-old","title":"Project","status":"planned"}')
    if argv == ("agent", "get", _OLD_AGENT, "--output", "json"):
        return raw_result(argv, stdout=b'{"id":"agent-old","name":"Old agent"}')
    return raw_result(argv, stdout=issue_payload)


MutationName = Literal["update-parent", "update-project", "update-assignee", "assign", "unassign"]


@dataclass(frozen=True)
class MutationSuccessCase:
    name: str
    operation: MutationName
    reference: Literal["parent", "project", "assignee_ref"]
    response_parent: str | None
    response_project: str | None
    response_assignee: IssueAssignee | None
    invoke: Callable[[Issue], Issue]
    expected_seed: Literal["missing", "null", "value"]


def _update_parent_changed(issue: Issue) -> Issue:
    return issue.update(parent_id="parent-new")


def _update_parent_cleared(issue: Issue) -> Issue:
    return issue.update(parent_id=None)


def _update_parent_same(issue: Issue) -> Issue:
    return issue.update(parent_id=_OLD_PARENT)


def _update_project_changed(issue: Issue) -> Issue:
    return issue.update(project_id="project-new")


def _update_project_cleared(issue: Issue) -> Issue:
    return issue.update(project_id=None)


def _update_project_same(issue: Issue) -> Issue:
    return issue.update(project_id=_OLD_PROJECT)


def _update_assignee_changed(issue: Issue) -> Issue:
    return issue.update(assignee_id="agent-new")


def _update_assignee_cleared(issue: Issue) -> Issue:
    return issue.update(assignee_id=None)


def _update_assignee_same(issue: Issue) -> Issue:
    return issue.update(assignee_id=_OLD_AGENT)


def _assign_changed(issue: Issue) -> Issue:
    return issue.assign("agent-new")


def _assign_same(issue: Issue) -> Issue:
    return issue.assign(_OLD_AGENT)


def _unassign_cleared(issue: Issue) -> Issue:
    return issue.unassign()


def _unassign_same(issue: Issue) -> Issue:
    return issue.unassign()


_MUTATION_SUCCESS_CASES = (
    MutationSuccessCase(
        "update parent changed",
        "update-parent",
        "parent",
        "parent-new",
        _OLD_PROJECT,
        _OLD_ASSIGNEE,
        _update_parent_changed,
        "value",
    ),
    MutationSuccessCase(
        "update parent cleared",
        "update-parent",
        "parent",
        None,
        _OLD_PROJECT,
        _OLD_ASSIGNEE,
        _update_parent_cleared,
        "null",
    ),
    MutationSuccessCase(
        "update parent no change",
        "update-parent",
        "parent",
        _OLD_PARENT,
        _OLD_PROJECT,
        _OLD_ASSIGNEE,
        _update_parent_same,
        "value",
    ),
    MutationSuccessCase(
        "update project changed",
        "update-project",
        "project",
        _OLD_PARENT,
        "project-new",
        _OLD_ASSIGNEE,
        _update_project_changed,
        "value",
    ),
    MutationSuccessCase(
        "update project cleared",
        "update-project",
        "project",
        _OLD_PARENT,
        None,
        _OLD_ASSIGNEE,
        _update_project_cleared,
        "null",
    ),
    MutationSuccessCase(
        "update project no change",
        "update-project",
        "project",
        _OLD_PARENT,
        _OLD_PROJECT,
        _OLD_ASSIGNEE,
        _update_project_same,
        "value",
    ),
    MutationSuccessCase(
        "update assignee changed",
        "update-assignee",
        "assignee_ref",
        _OLD_PARENT,
        _OLD_PROJECT,
        IssueAssignee(id="agent-new", name="New agent", type="agent"),
        _update_assignee_changed,
        "value",
    ),
    MutationSuccessCase(
        "update assignee cleared",
        "update-assignee",
        "assignee_ref",
        _OLD_PARENT,
        _OLD_PROJECT,
        None,
        _update_assignee_cleared,
        "null",
    ),
    MutationSuccessCase(
        "update assignee no change",
        "update-assignee",
        "assignee_ref",
        _OLD_PARENT,
        _OLD_PROJECT,
        _OLD_ASSIGNEE,
        _update_assignee_same,
        "value",
    ),
    MutationSuccessCase(
        "assign changed",
        "assign",
        "assignee_ref",
        _OLD_PARENT,
        _OLD_PROJECT,
        IssueAssignee(id="agent-new", name="New agent", type="agent"),
        _assign_changed,
        "value",
    ),
    MutationSuccessCase(
        "assign no change",
        "assign",
        "assignee_ref",
        _OLD_PARENT,
        _OLD_PROJECT,
        _OLD_ASSIGNEE,
        _assign_same,
        "value",
    ),
    MutationSuccessCase(
        "unassign cleared",
        "unassign",
        "assignee_ref",
        _OLD_PARENT,
        _OLD_PROJECT,
        None,
        _unassign_cleared,
        "null",
    ),
    MutationSuccessCase(
        "unassign no change",
        "unassign",
        "assignee_ref",
        _OLD_PARENT,
        _OLD_PROJECT,
        None,
        _unassign_same,
        "null",
    ),
)


def _load_original_handles(
    issue: Issue,
    transport: MagicMock,
    raw_result: Callable[..., RawCommandResult],
) -> dict[str, LazyRef[object]]:
    transport.run_bytes.side_effect = lambda argv, **_kwargs: _transport_response(
        argv,
        _issue_payload(parent_id=_OLD_PARENT, project_id=_OLD_PROJECT, assignee=_OLD_ASSIGNEE),
        raw_result,
    )
    handles: dict[str, LazyRef[object]] = {
        "parent": cast("LazyRef[object]", issue.parent),
        "project": cast("LazyRef[object]", issue.project),
        "assignee_ref": cast("LazyRef[object]", issue.assignee_ref),
    }
    for handle in handles.values():
        handle.get()
    return handles


@dataclass(frozen=True)
class ResponseHandleCase:
    name: str
    field_name: str
    value: str | IssueAssignee | None


@pytest.mark.parametrize("case", _MUTATION_SUCCESS_CASES, ids=lambda case: case.name)
def test_issue_mutations_publish_fresh_response_state_and_preserve_original(
    case: MutationSuccessCase,
    client_with_transport: tuple[MulticaClient, MagicMock],
    raw_result: Callable[..., RawCommandResult],
) -> None:
    client, transport = client_with_transport
    source = _issue(
        _issue_payload(parent_id=_OLD_PARENT, project_id=_OLD_PROJECT, assignee=_OLD_ASSIGNEE),
        client,
    )
    old_handles = _load_original_handles(source, transport, raw_result)
    response = _issue_payload(
        parent_id=case.response_parent,
        project_id=case.response_project,
        assignee=case.response_assignee,
    )
    transport.run_bytes.side_effect = lambda argv, **_kwargs: _transport_response(
        argv, response, raw_result
    )

    replacement = case.invoke(source)

    assert replacement is not source
    assert replacement.id == source.id
    assert replacement.parent_id == case.response_parent
    assert replacement.project_id == case.response_project
    assert replacement.assignee == case.response_assignee
    assert replacement._client is client

    response_handles = (
        ResponseHandleCase("parent", "parent_id", case.response_parent),
        ResponseHandleCase("project", "project_id", case.response_project),
        ResponseHandleCase("assignee_ref", "assignee", case.response_assignee),
    )
    for response_handle in response_handles:
        new_handle = getattr(replacement, response_handle.name)
        assert new_handle is not old_handles[response_handle.name]
        expected_seed = "null" if response_handle.value is None else "value"
        assert (response_handle.field_name, expected_seed) in replacement._wire_presence
        if response_handle.value is None:
            assert new_handle.loaded is True
            assert new_handle.value is None
        else:
            assert new_handle.loaded is False

    assert (
        "assignee" if case.reference == "assignee_ref" else f"{case.reference}_id",
        case.expected_seed,
    ) in replacement._wire_presence

    assert source.parent_id == _OLD_PARENT
    assert source.project_id == _OLD_PROJECT
    assert source.assignee == _OLD_ASSIGNEE
    for name, handle in old_handles.items():
        assert getattr(source, name) is handle
        assert handle.loaded is True
    assert transport.run_bytes.call_count >= 4


MutationFailure = Callable[[Issue], Issue]


@dataclass(frozen=True)
class MutationFailureCase:
    name: str
    invoke: MutationFailure


MUTATION_FAILURE_CASES = (
    MutationFailureCase("update parent", _update_parent_changed),
    MutationFailureCase("update project", _update_project_changed),
    MutationFailureCase("update assignee", _update_assignee_changed),
    MutationFailureCase("assign", _assign_changed),
    MutationFailureCase("unassign", _unassign_cleared),
)


@pytest.mark.parametrize("case", MUTATION_FAILURE_CASES, ids=lambda case: case.name)
def test_failed_issue_mutation_does_not_publish_or_change_original(
    case: MutationFailureCase,
    client_with_transport: tuple[MulticaClient, MagicMock],
) -> None:
    client, transport = client_with_transport
    name = case.name
    source = _issue(
        _issue_payload(parent_id=_OLD_PARENT, project_id=_OLD_PROJECT, assignee=_OLD_ASSIGNEE),
        client,
    )
    old_handles: dict[str, LazyRef[object]] = {
        "parent": cast("LazyRef[object]", source.parent),
        "project": cast("LazyRef[object]", source.project),
        "assignee_ref": cast("LazyRef[object]", source.assignee_ref),
    }
    transport.run_bytes.side_effect = RuntimeError(f"{name} failed")

    with pytest.raises(RuntimeError, match="failed"):
        case.invoke(source)

    assert source.parent_id == _OLD_PARENT
    assert source.project_id == _OLD_PROJECT
    assert source.assignee == _OLD_ASSIGNEE
    assert source.parent is old_handles["parent"]
    assert source.project is old_handles["project"]
    assert source.assignee_ref is old_handles["assignee_ref"]
    assert all(not handle.loaded for handle in old_handles.values())


@dataclass(frozen=True)
class AssignmentCase:
    name: str
    target: str | WorkspaceMember
    expected_argv: tuple[str, ...]


ASSIGNMENT_CASES = (
    AssignmentCase(
        "workspace member",
        WorkspaceMember(id="member-1", name="Member"),
        ("issue", "assign", "issue-1", "--to-id", "member-1", "--output", "json"),
    ),
    AssignmentCase(
        "email",
        "member@example.com",
        ("issue", "assign", "issue-1", "--assignee", "member@example.com", "--output", "json"),
    ),
)


@pytest.mark.parametrize("case", ASSIGNMENT_CASES, ids=lambda case: case.name)
def test_assignment_keeps_member_snapshot_and_rejects_lazy_load_before_io(
    case: AssignmentCase,
    client_with_transport: tuple[MulticaClient, MagicMock],
    raw_result: Callable[..., RawCommandResult],
) -> None:
    client, transport = client_with_transport
    source = _issue(
        _issue_payload(parent_id=_OLD_PARENT, project_id=_OLD_PROJECT, assignee=_OLD_ASSIGNEE),
        client,
    )
    member_snapshot = IssueAssignee(id="member-1", name="Member", type="member")
    response = _issue_payload(
        parent_id=_OLD_PARENT, project_id=_OLD_PROJECT, assignee=member_snapshot
    )
    transport.run_bytes.return_value = raw_result(case.expected_argv, stdout=response)

    replacement = source.assign(case.target)

    assert replacement.assignee == member_snapshot
    assert replacement.assignee_ref.loaded is False
    assert transport.run_bytes.call_count == 1
    with pytest.raises(UnsupportedReferenceTargetError):
        replacement.assignee_ref.get()
    assert transport.run_bytes.call_count == 1
