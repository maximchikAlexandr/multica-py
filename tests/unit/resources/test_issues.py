from __future__ import annotations

import datetime
import math
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from multica_py._internal.argv import build_global_args
from multica_py._internal.decoders import decode_json
from multica_py._internal.specs import RawCommandResult
from multica_py._internal.wire_models import (
    _issue_from_wire,
    _issue_list_page_from_wire,
    _IssueListPageWire,
    _IssueWire,
)
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus
from multica_py.models.issue_activity import (
    CommentListFlatRequest,
    MetadataSetRequest,
)
from multica_py.models.issues import (
    InlineDescription,
    IssueAssignmentRequest,
    IssueCreateRequest,
    IssueListFilter,
    IssueListPage,
    IssueMetadataItem,
    IssueReorderRequest,
    NoDescription,
)
from multica_py.models.system import AttachmentResult
from multica_py.resources.issue_comments import IssueCommentResource
from multica_py.resources.issue_labels import IssueLabelResource
from multica_py.resources.issue_metadata import IssueMetadataResource
from multica_py.resources.issue_subscribers import IssueSubscriberResource
from multica_py.resources.issues import Issue, IssueResource, TaskRun


@dataclass(frozen=True)
class _IssueListProjectionCase:
    payload: bytes
    expected_labels: tuple[str, ...]
    expected_metadata: tuple[IssueMetadataItem, ...]
    expected_match_source: str | None
    expected_has_more: bool
    expected_limit: int | None
    expected_offset: int | None
    expected_total: int | None


@dataclass(frozen=True)
class _MetadataValidationCase:
    predicates: tuple[IssueMetadataItem, ...]
    message: str


@dataclass(frozen=True)
class _IssueAttachmentCase:
    payload: bytes
    expected: tuple[AttachmentResult, ...]


_ISSUE_LIST_PROJECTION_CASES = (
    _IssueListProjectionCase(
        payload=(
            b'{"issues":[{"id":"i1","title":"Queue item","status":"todo",'
            b'"labels":[{"id":"l1","name":"queue"},{"id":"l2","name":"urgent"}],'
            b'"metadata":{"external_key":"42","ready":true}}],'
            b'"has_more":true,"limit":50,"offset":20,"total":137}'
        ),
        expected_labels=("queue", "urgent"),
        expected_metadata=(
            IssueMetadataItem(key="external_key", value="42"),
            IssueMetadataItem(key="ready", value=True),
        ),
        expected_match_source=None,
        expected_has_more=True,
        expected_limit=50,
        expected_offset=20,
        expected_total=137,
    ),
    _IssueListProjectionCase(
        payload=b'{"issues":[{"id":"i2","title":"Minimal","status":"todo"}]}',
        expected_labels=(),
        expected_metadata=(),
        expected_match_source=None,
        expected_has_more=False,
        expected_limit=None,
        expected_offset=None,
        expected_total=None,
    ),
)


_ISSUE_ATTACHMENT_CASES = (
    _IssueAttachmentCase(
        payload=(
            b'{"id":"i1","title":"Issue","status":"todo",'
            b'"attachments":[{"id":"a1","filename":"first.txt","url":"/first"},'
            b'{"id":"a2","filename":"second.txt"}]}'
        ),
        expected=(
            AttachmentResult(id="a1", filename="first.txt", url="/first"),
            AttachmentResult(id="a2", filename="second.txt"),
        ),
    ),
    _IssueAttachmentCase(
        payload=b'{"id":"i2","title":"Empty","status":"todo","attachments":[]}',
        expected=(),
    ),
    _IssueAttachmentCase(
        payload=b'{"id":"i3","title":"Omitted","status":"todo"}',
        expected=(),
    ),
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


@pytest.mark.parametrize("case", _ISSUE_LIST_PROJECTION_CASES)
def test_issue_list_page_decodes_summary_collections(case: _IssueListProjectionCase) -> None:
    page = _issue_list_page_from_wire(decode_json(case.payload, _IssueListPageWire))
    assert isinstance(page, IssueListPage)
    assert page.has_more is case.expected_has_more
    assert page.limit == case.expected_limit
    assert page.offset == case.expected_offset
    assert page.total == case.expected_total
    assert page.issues[0].label_names == case.expected_labels
    assert page.issues[0].metadata_snapshot == case.expected_metadata
    assert page.issues[0].match_source is case.expected_match_source


def test_issue_resource_list_returns_issue_list_page(mock_transport: MagicMock) -> None:
    mock_transport.run_bytes.return_value.stdout = b'{"issues":[]}'
    page = IssueResource(mock_transport, ClientConfig()).list()
    assert type(page) is IssueListPage


def test_issue_entity_commands_route_relations_and_mutations_lazily(
    mock_transport: MagicMock,
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    client = MagicMock()
    resource = IssueResource(mock_transport, ClientConfig())
    resource._set_client(client)
    client.issues = resource
    issue = Issue(id="i1", title="Issue", status=IssueStatus.todo, _client=client)

    commands = (
        issue.comments.all_command(),
        issue.add_comment_command("body"),
        issue.reply_command("thread", "reply"),
        issue.add_subscriber_command("u1"),
        issue.remove_subscriber_command("u1"),
        issue.set_metadata_command("key", True),
        issue.delete_metadata_command("key"),
    )

    assert tuple(command.commands[0] for command in commands) == (
        "multica issue comment list i1 --output json",
        "multica issue comment add i1 --content body --output json",
        "multica issue comment add i1 --content reply --parent thread --output json",
        "multica issue subscriber add i1 --user-id u1",
        "multica issue subscriber remove i1 --user-id u1",
        "multica issue metadata set i1 --key key --value true --type boolean --output json",
        "multica issue metadata delete i1 --key key",
    )
    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()


def test_task_run_messages_command_delegates_to_issue_resource(
    mock_transport: MagicMock,
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    client = MagicMock()
    resource = IssueResource(mock_transport, ClientConfig())
    resource._set_client(client)
    client.issues = resource
    task_run = TaskRun(id="run1", status="completed", _client=client, _issue_id="i1")

    command = task_run.messages_command()

    assert command.commands == ("multica issue run-messages run1 --issue i1 --output json",)
    mock_transport.run_bytes.assert_not_called()


def test_task_run_messages_relation_command_delegates_to_issue_resource(
    mock_transport: MagicMock,
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    client = MagicMock()
    resource = IssueResource(mock_transport, ClientConfig())
    resource._set_client(client)
    client.issues = resource
    task_run = TaskRun(id="run1", status="completed", _client=client, _issue_id="i1")

    command = task_run.messages.all_command()

    assert command.commands == ("multica issue run-messages run1 --issue i1 --output json",)
    mock_transport.run_bytes.assert_not_called()


@pytest.mark.parametrize(
    "case",
    (
        _MetadataValidationCase(
            predicates=(IssueMetadataItem(key="", value="x"),),
            message="invalid metadata key",
        ),
        _MetadataValidationCase(
            predicates=(IssueMetadataItem(key=" ", value="x"),),
            message="invalid metadata key",
        ),
        _MetadataValidationCase(
            predicates=(IssueMetadataItem(key="bad=key", value="x"),),
            message="invalid metadata key",
        ),
        _MetadataValidationCase(
            predicates=(
                IssueMetadataItem(key="duplicate", value=1),
                IssueMetadataItem(key="duplicate", value=2),
            ),
            message="duplicate metadata key",
        ),
        _MetadataValidationCase(
            predicates=(IssueMetadataItem(key="non_finite", value=math.nan),),
            message="Out of range float values are not JSON compliant",
        ),
        _MetadataValidationCase(
            predicates=(IssueMetadataItem(key="non_finite", value=math.inf),),
            message="Out of range float values are not JSON compliant",
        ),
        _MetadataValidationCase(
            predicates=(IssueMetadataItem(key="non_finite", value=-math.inf),),
            message="Out of range float values are not JSON compliant",
        ),
    ),
    ids=("blank", "whitespace", "equals", "duplicate", "nan", "inf", "negative-inf"),
)
def test_issue_list_metadata_validation_before_transport(
    case: _MetadataValidationCase, mock_transport: MagicMock
) -> None:
    resource = IssueResource(mock_transport, ClientConfig())
    with pytest.raises(ValueError, match=case.message):
        resource.list(IssueListFilter(metadata=case.predicates))
    mock_transport.run_bytes.assert_not_called()


@pytest.mark.parametrize("case", _ISSUE_ATTACHMENT_CASES)
def test_issue_get_decodes_attachment_snapshots(case: _IssueAttachmentCase) -> None:
    wire = decode_json(case.payload, _IssueWire)
    issue = _issue_from_wire(wire)

    assert issue.attachments == case.expected
    assert all(isinstance(item, AttachmentResult) for item in issue.attachments)


def test_issue_polling_uses_attachment_id_from_later_get(mock_transport: MagicMock) -> None:
    first_payload = b'{"id":"i1","title":"Issue","status":"todo","attachments":[]}'
    second_payload = (
        b'{"id":"i1","title":"Issue","status":"todo",'
        b'"attachments":[{"id":"a1","filename":"result.txt"}]}'
    )
    mock_transport.run_bytes.side_effect = (
        RawCommandResult(
            argv=("issue", "get", "i1", "--output", "json"),
            exit_code=0,
            stdout=first_payload,
            stderr=b"",
            duration=datetime.timedelta(),
        ),
        RawCommandResult(
            argv=("issue", "get", "i1", "--output", "json"),
            exit_code=0,
            stdout=second_payload,
            stderr=b"",
            duration=datetime.timedelta(),
        ),
    )
    resource = IssueResource(mock_transport, ClientConfig())
    client = MagicMock()
    resource._set_client(client)

    first = resource.get("i1")
    later = resource.get("i1")

    assert first.attachments == ()
    assert later.attachments == (AttachmentResult(id="a1", filename="result.txt"),)
    client.attachments.download_bytes(later.attachments[0].id)
    client.attachments.download_bytes.assert_called_once_with("a1")
    assert mock_transport.run_bytes.call_count == 2


def test_invalid_value_rejected():
    with pytest.raises(TypeError):
        IssueCreateRequest(title="Test", description_input="some random string")  # type: ignore[arg-type]


def test_issue_assignment_request_rejects_multiple_targets():
    with pytest.raises(ValueError, match="Exactly one assignment target must be set"):
        IssueAssignmentRequest(issue_id="iss_001", member_id="usr_001", unassign=True)


def test_issue_reorder_request_rejects_multiple_targets():
    with pytest.raises(ValueError, match="Exactly one reorder target must be set"):
        IssueReorderRequest(issue_id="iss_001", before_id="iss_002", bottom=True)
