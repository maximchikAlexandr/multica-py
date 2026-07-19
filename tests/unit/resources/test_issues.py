from __future__ import annotations

import pytest

from multica_py._internal.argv import build_global_args
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus
from multica_py.models.issues import (
    InlineDescription,
    IssueAssignmentRequest,
    IssueCreateRequest,
    IssueReorderRequest,
    NoDescription,
)


def test_issue_create_request_with_description():
    req = IssueCreateRequest(
        title="Test", description_input=InlineDescription(text="Description text")
    )
    assert req.title == "Test"
    assert isinstance(req.description_input, InlineDescription)
    assert req.description_input.text == "Description text"


def test_issue_create_request_no_description():
    req = IssueCreateRequest(title="Test")
    assert isinstance(req.description_input, NoDescription)


def test_issue_create_request_with_labels():
    req = IssueCreateRequest(title="Test", label_ids=("bug", "urgent"))
    assert req.label_ids == ("bug", "urgent")


def test_global_args_with_server_and_workspace():
    config = ClientConfig(server_url="https://example.com", workspace_id="ws_001")
    assert build_global_args(config) == (
        "--server-url",
        "https://example.com",
        "--workspace-id",
        "ws_001",
    )


def test_global_args_with_debug():
    config = ClientConfig(debug=True)
    assert build_global_args(config) == ("--debug",)


def test_issue_status_enum_values():
    assert IssueStatus.todo.value == "todo"
    assert IssueStatus.done.value == "done"
    assert IssueStatus.cancelled.value == "cancelled"


def test_invalid_value_rejected():
    with pytest.raises(TypeError):
        IssueCreateRequest(title="Test", description_input="some random string")  # type: ignore[arg-type]


def test_issue_assignment_request_rejects_multiple_targets():
    with pytest.raises(ValueError, match="Exactly one assignment target must be set"):
        IssueAssignmentRequest(issue_id="iss_001", member_id="usr_001", unassign=True)


def test_issue_reorder_request_rejects_multiple_targets():
    with pytest.raises(ValueError, match="Exactly one reorder target must be set"):
        IssueReorderRequest(issue_id="iss_001", before_id="iss_002", bottom=True)
