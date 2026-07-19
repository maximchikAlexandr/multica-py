from __future__ import annotations

from multica_py._internal.argv import build_global_args
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus
from multica_py.models.issues import (
    InlineDescription,
    IssueCreateRequest,
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
    args = build_global_args(config)
    assert "--server-url" in args
    assert "--workspace-id" in args


def test_global_args_with_debug():
    config = ClientConfig(debug=True)
    args = build_global_args(config)
    assert "--debug" in args


def test_issue_status_enum_values():
    assert IssueStatus.todo.value == "todo"
    assert IssueStatus.done.value == "done"
    assert IssueStatus.cancelled.value == "cancelled"
