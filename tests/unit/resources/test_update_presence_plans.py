from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.enums import AutopilotExecutionMode
from multica_py.models.agents import AgentUpdateRequest
from multica_py.models.autopilots import AutopilotUpdateRequest
from multica_py.models.issues import IssueUpdateRequest
from multica_py.models.projects import ProjectUpdateRequest
from multica_py.models.skills import SkillUpdateRequest
from multica_py.resources.agents import AgentResource
from multica_py.resources.autopilots import AutopilotResource
from multica_py.resources.issues import IssueResource
from multica_py.resources.projects import ProjectResource
from multica_py.resources.skills import SkillResource


def _transport() -> MagicMock:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    return transport


@pytest.mark.parametrize(
    ("resource_cls", "request_cls", "target", "read_argv"),
    (
        (ProjectResource, ProjectUpdateRequest, "p1", ("project", "get", "p1")),
        (AgentResource, AgentUpdateRequest, "a1", ("agent", "get", "a1")),
        (SkillResource, SkillUpdateRequest, "s1", ("skill", "get", "s1")),
        (IssueResource, IssueUpdateRequest, "i1", ("issue", "get", "i1")),
        (AutopilotResource, AutopilotUpdateRequest, "ap1", ("autopilot", "get", "ap1")),
    ),
)
def test_all_unset_update_is_matching_read_without_transport(
    resource_cls: type[object],
    request_cls: type[object],
    target: str,
    read_argv: tuple[str, ...],
) -> None:
    transport = _transport()
    resource = resource_cls(transport, ClientConfig())  # type: ignore[call-arg]

    command = resource.update_command(target, request_cls())  # type: ignore[attr-defined]

    assert command.commands == (f"multica {' '.join(read_argv)} --output json",)
    assert command.commands == resource.get_command(target).commands  # type: ignore[attr-defined]
    transport.run_bytes.assert_not_called()


@pytest.mark.parametrize(
    ("resource_cls", "target", "request_value", "direct", "expected"),
    (
        (
            ProjectResource,
            "p1",
            ProjectUpdateRequest(description=None),
            {"description": None},
            "multica project update p1 --description '' --output json",
        ),
        (
            AgentResource,
            "a1",
            AgentUpdateRequest(description=None),
            {"description": None},
            "multica agent update a1 --description '' --output json",
        ),
        (
            SkillResource,
            "s1",
            SkillUpdateRequest(description=None),
            {"description": None},
            "multica skill update s1 --description '' --output json",
        ),
        (
            IssueResource,
            "i1",
            IssueUpdateRequest(description=None),
            {"description": None},
            "multica issue update i1 --description '' --output json",
        ),
        (
            IssueResource,
            "i1",
            IssueUpdateRequest(project_id=None, parent_id=None),
            {"project_id": None, "parent_id": None},
            "multica issue update i1 --project '' --parent '' --output json",
        ),
        (
            AutopilotResource,
            "ap1",
            AutopilotUpdateRequest(description=None, project_id=None, issue_title_template=None),
            {"description": None, "project_id": None, "issue_title_template": None},
            "multica autopilot update ap1 --description '' --project '' --issue-title-template '' --output json",
        ),
    ),
)
def test_nullable_clear_object_and_direct_plans_are_identical(
    resource_cls: type[object],
    target: str,
    request_value: object,
    direct: dict[str, object],
    expected: str,
) -> None:
    resource = resource_cls(_transport(), ClientConfig())  # type: ignore[call-arg]

    object_command = resource.update_command(target, request_value)  # type: ignore[attr-defined]
    direct_command = resource.update_command(target, **direct)  # type: ignore[attr-defined]

    assert object_command.commands == direct_command.commands == (expected,)


@pytest.mark.parametrize(
    ("resource_cls", "target", "request_value", "expected"),
    (
        (
            ProjectResource,
            "p1",
            ProjectUpdateRequest(name=""),
            "multica project update p1 --title '' --output json",
        ),
        (
            AgentResource,
            "a1",
            AgentUpdateRequest(name=""),
            "multica agent update a1 --name '' --output json",
        ),
        (
            SkillResource,
            "s1",
            SkillUpdateRequest(name=""),
            "multica skill update s1 --name '' --output json",
        ),
        (
            IssueResource,
            "i1",
            IssueUpdateRequest(priority=""),
            "multica issue update i1 --priority '' --output json",
        ),
        (
            AutopilotResource,
            "ap1",
            AutopilotUpdateRequest(priority="", execution_mode=AutopilotExecutionMode.create_issue),
            "multica autopilot update ap1 --priority '' --mode create_issue --output json",
        ),
    ),
)
def test_approved_falsey_values_remain_present(
    resource_cls: type[object], target: str, request_value: object, expected: str
) -> None:
    resource = resource_cls(_transport(), ClientConfig())  # type: ignore[call-arg]
    assert resource.update_command(target, request_value).commands == (expected,)  # type: ignore[attr-defined]


def test_issue_composite_clear_is_ordered_and_authoritative() -> None:
    resource = IssueResource(_transport(), ClientConfig())
    request = IssueUpdateRequest(
        description=None,
        assignee_id=None,
        project_id=None,
        parent_id=None,
    )

    command = resource.update_command("i1", request)

    assert command.commands == (
        "multica issue update i1 --description '' --project '' --parent '' --output json",
        "multica issue assign i1 --unassign --output json",
        "multica issue get i1 --output json",
    )
    assert tuple(step.result_alias for step in command._plan.steps) == (
        "update",
        "assign",
        "authoritative",
    )


def test_autopilot_subscriber_omission_is_distinct_from_empty_clear() -> None:
    resource = AutopilotResource(_transport(), ClientConfig())

    omitted = resource.update_command("ap1")
    empty = resource.update_command("ap1", subscribers=())

    assert omitted.commands == ("multica autopilot get ap1 --output json",)
    assert empty.commands == ("multica autopilot update ap1 --clear-subscribers --output json",)
