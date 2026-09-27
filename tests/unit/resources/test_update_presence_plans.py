from __future__ import annotations

from multica_py.config import ClientConfig
from multica_py.resources.autopilots import AutopilotResource
from multica_py.resources.issues import IssueResource
from tests.unit.resources._factories import make_transport


def test_issue_composite_clear_is_ordered_and_authoritative() -> None:
    resource = IssueResource(make_transport(), ClientConfig())
    command = resource.update_command(
        "i1", description=None, assignee_id=None, project_id=None, parent_id=None
    )

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
    resource = AutopilotResource(make_transport(), ClientConfig())

    omitted = resource.update_command("ap1")
    empty = resource.update_command("ap1", subscribers=())

    assert omitted.commands == ("multica autopilot get ap1 --output json",)
    assert empty.commands == ("multica autopilot update ap1 --clear-subscribers --output json",)
