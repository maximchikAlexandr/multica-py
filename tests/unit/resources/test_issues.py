from __future__ import annotations

import datetime
import json
import math
from dataclasses import dataclass
from typing import Any, cast
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.argv import build_global_args
from multica_py._internal.decoders import decode_json
from multica_py._internal.specs import RawCommandResult
from multica_py._internal.wire_models import (
    _issue_children_result_from_wire,
    _issue_from_wire,
    _issue_list_page_from_wire,
    _IssueChildrenResultWire,
    _IssueListPageWire,
    _IssueWire,
)
from multica_py.config import ClientConfig
from multica_py.entities.agents import Agent
from multica_py.entities.issues import Issue, TaskRun
from multica_py.enums import IssueStatus
from multica_py.exceptions import DetachedEntityError, OutputShapeError
from multica_py.models.issues import (
    InlineDescription,
    IssueChildrenResult,
    IssueDescriptionInput,
    IssueListFilter,
    IssueListPage,
    IssueMetadataItem,
    NoDescription,
)
from multica_py.models.properties import PropertyValue
from multica_py.models.system import AttachmentResult
from multica_py.resources.issue_comments import IssueCommentResource
from multica_py.resources.issue_labels import IssueLabelResource
from multica_py.resources.issue_metadata import IssueMetadataResource
from multica_py.resources.issue_subscribers import IssueSubscriberResource
from multica_py.resources.issues import IssueResource, _decode_issue_search

_DESCRIPTION_INPUT_IMPOSTORS = (
    type("NoDescription", (), {})(),
    type("StdinDescription", (), {})(),
)
_ISSUE_LIST_FILTER_IMPOSTOR = type("IssueListFilter", (), {})()


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


@dataclass(frozen=True)
class _IssueCreateArgvCase:
    name: str
    description_input: IssueDescriptionInput
    label_ids: tuple[str, ...]
    expected_steps: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class _IssueQueryValidationCase:
    kwargs: dict[str, object]
    message: str


@dataclass(frozen=True)
class _IssuePropertyProjectionCase:
    name: str
    payload: bytes
    expected: tuple[PropertyValue, ...]
    partial: bool = False


@dataclass(frozen=True)
class _IssuePartialSerializationCase:
    name: str
    payload: bytes
    expected: dict[str, object]
    fields: tuple[str, ...] = ()


_ISSUE_CREATE_ARGV_CASES = (
    _IssueCreateArgvCase(
        name="without description",
        description_input=NoDescription(),
        label_ids=(),
        expected_steps=(("issue", "create", "--title", "Test", "--output", "json"),),
    ),
    _IssueCreateArgvCase(
        name="with description",
        description_input=InlineDescription(text="Description text"),
        label_ids=(),
        expected_steps=(
            (
                "issue",
                "create",
                "--title",
                "Test",
                "--description",
                "Description text",
                "--output",
                "json",
            ),
        ),
    ),
    _IssueCreateArgvCase(
        name="with labels",
        description_input=NoDescription(),
        label_ids=("bug", "urgent"),
        expected_steps=(
            ("issue", "create", "--title", "Test", "--output", "json"),
            ("issue", "label", "add", "", "bug", "--output", "json"),
            ("issue", "label", "add", "", "urgent", "--output", "json"),
            ("issue", "get", "", "--output", "json"),
        ),
    ),
)


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


@pytest.mark.parametrize("case", _ISSUE_CREATE_ARGV_CASES, ids=lambda case: case.name)
def test_issue_create_direct_uses_full_expected_argv(case: _IssueCreateArgvCase) -> None:
    resource = IssueResource(MagicMock(), ClientConfig())
    command = resource.create_command(
        title="Test", description_input=case.description_input, label_ids=case.label_ids
    )

    assert tuple(step.argv for step in command._plan.steps) == case.expected_steps


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


def test_issue_children_wire_finalizer_returns_page_with_neutral_metadata() -> None:
    page = _issue_children_result_from_wire(_IssueChildrenResultWire())

    assert isinstance(page, IssueChildrenResult)
    assert page.items is page.children
    assert page.limit is None
    assert page.offset is None
    assert page.total == 0
    assert page.has_more is False
    assert page.next_cursor is None


def test_issue_children_wire_decoder_does_not_bind_a_client() -> None:
    page = _issue_children_result_from_wire(
        _IssueChildrenResultWire(
            children=(_IssueWire(id="child", title="Child", status=IssueStatus.todo),),
            unstaged=(_IssueWire(id="unstaged", title="Unstaged", status=IssueStatus.done),),
        )
    )

    assert page.items[0]._client is None
    assert page.unstaged[0]._client is None


def test_issue_resource_list_returns_issue_list_page(mock_transport: MagicMock) -> None:
    mock_transport.run_bytes.return_value.stdout = b'{"issues":[]}'
    page = IssueResource(mock_transport, ClientConfig()).list()
    assert type(page) is IssueListPage


def test_issue_list_finalizer_binds_partial_rows_without_extra_get(
    mock_transport: MagicMock,
) -> None:
    mock_transport.run_bytes.return_value = RawCommandResult(
        argv=("issue", "list", "--output", "json"),
        exit_code=0,
        stdout=(
            b'{"issues":[{"id":"i1","title":"Partial","status":"todo",'
            b'"parent_issue_id":"p1","match_source":"future-index"}]}'
        ),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    client = MagicMock()
    resource = IssueResource(mock_transport, ClientConfig())
    resource._set_client(client)

    page = resource.list()
    issue = page.items[0]

    assert page.issues is page.items
    assert isinstance(issue, Issue)
    assert issue._client is client
    assert issue.description is None
    assert issue.parent_id == "p1"
    assert issue.match_source == "future-index"
    assert issue.to_dict()["match_source"] == "future-index"
    assert issue == Issue.from_dict(issue.to_dict())
    assert issue.to_json() == Issue.from_dict(issue.to_dict()).to_json()
    mock_transport.run_bytes.assert_called_once()
    client.issues.get.assert_not_called()


def test_issue_list_projection_preserves_absence_and_properties_without_get(
    mock_transport: MagicMock,
) -> None:
    mock_transport.run_bytes.return_value = RawCommandResult(
        argv=(),
        exit_code=0,
        stdout=b'{"issues":[{"id":"i1","properties":{"prop-1":"raw",'
        b'"prop-2":{"value":1}}}],"has_more":true,"total":0}',
        stderr=b"",
        duration=datetime.timedelta(),
    )
    client = MagicMock()
    resource = IssueResource(mock_transport, ClientConfig())
    resource._set_client(client)

    row = resource.list(fields=("id", "properties")).items[0]

    assert row.id == "i1"
    assert cast("object", row.title) is msgspec.UNSET
    assert cast("object", row.status) is msgspec.UNSET
    assert cast("object", row.properties) == {"prop-1": "raw", "prop-2": {"value": 1}}
    assert client.issues.get.call_count == 0


def test_issue_list_fields_preserve_core_and_dynamic_projection_without_get(
    mock_transport: MagicMock,
) -> None:
    mock_transport.run_bytes.return_value = RawCommandResult(
        argv=(),
        exit_code=0,
        stdout=(
            b'{"issues":[{"id":"i1","title":"Title","status":"todo",'
            b'"identifier":"ABC-1","revision":0,"workspace_id":"ws",'
            b'"number":1,"status_name":"Todo","position":3}]}'
        ),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    client = MagicMock()
    resource = IssueResource(mock_transport, ClientConfig())
    resource._set_client(client)

    page = resource.list(
        fields=(
            "id",
            "title",
            "status",
            "identifier",
            "revision",
            "workspace_id",
            "number",
            "status_name",
            "position",
        )
    )
    issue = page.items[0]

    assert issue.to_dict() == {
        "id": "i1",
        "title": "Title",
        "status": "todo",
        "identifier": "ABC-1",
        "revision": 0,
        "workspace_id": "ws",
        "number": 1,
        "status_name": "Todo",
        "position": 3,
    }
    assert issue.detach().to_dict() == issue.to_dict()
    assert Issue.from_dict(issue.to_dict()).to_dict() == issue.to_dict()
    client.issues.get.assert_not_called()


_ISSUE_PROPERTY_PROJECTION_CASES = (
    _IssuePropertyProjectionCase(
        name="full-resolved-rows",
        payload=(
            b'{"issues":[{"id":"i1","title":"Issue","status":"todo",'
            b'"properties":[{"property_id":"p1","name":"Impact",'
            b'"type":"select","value":"high","display":"High",'
            b'"archived":false}]}]}'
        ),
        expected=(
            PropertyValue(
                property_id="p1",
                name="Impact",
                type="select",
                value="high",
                display="High",
                archived=False,
            ),
        ),
    ),
    _IssuePropertyProjectionCase(
        name="partial-resolved-rows",
        payload=(
            b'{"issues":[{"id":"i1","properties":[{"property_id":"p1",'
            b'"name":"Impact","type":"select","value":"high",'
            b'"display":"High"}]}]}'
        ),
        expected=(
            PropertyValue(
                property_id="p1",
                name="Impact",
                type="select",
                value="high",
                display="High",
            ),
        ),
        partial=True,
    ),
    _IssuePropertyProjectionCase(
        name="raw-uuid-map",
        payload=b'{"issues":[{"id":"i1","title":"Issue","status":"todo",'
        b'"properties":{"p1":"high"}}]}',
        expected=(),
    ),
)


@pytest.mark.parametrize("case", _ISSUE_PROPERTY_PROJECTION_CASES, ids=lambda case: case.name)
def test_issue_property_projection_decodes_full_and_partial_target_rows(
    case: _IssuePropertyProjectionCase,
) -> None:
    page = _issue_list_page_from_wire(decode_json(case.payload, _IssueListPageWire))
    issue = page.items[0]._with_client(MagicMock())

    assert isinstance(issue, Issue)
    if case.partial:
        assert cast("object", issue.title) is msgspec.UNSET
        assert cast("object", issue.status) is msgspec.UNSET
    if case.expected:
        assert tuple(issue.properties.all().values()) == case.expected
    else:
        assert cast("object", dict(issue.properties.all())) == {"p1": "high"}


def test_issue_projection_preserves_full_allowlist_and_omitted_vs_null() -> None:
    payload = (
        b'{"issues":[{"id":"i1","workspace_id":"ws","number":7,'
        b'"identifier":"ABC-7","description":null,"status_category":"started",'
        b'"status_name":"Todo","priority":"high","assignee_type":null,'
        b'"assignee_id":null,"creator_type":"member","creator_id":"u1",'
        b'"parent_issue_id":null,"project_id":"p1","position":3,"stage":0,'
        b'"start_date":null,"due_date":"2026-02-01","created_at":null,'
        b'"updated_at":"2026-01-02T00:00:00Z","revision":0,'
        b'"last_activity_at":null,"metadata":{},"properties":{},'
        b'"labels":[{"id":"l1","name":"bug","color":"red"}]}]}'
    )
    issue = _issue_list_page_from_wire(decode_json(payload, _IssueListPageWire)).items[0]

    assert isinstance(issue, Issue)
    assert issue.id == "i1"
    assert issue.workspace_id == "ws"
    assert issue.number == 7
    assert issue.identifier == "ABC-7"
    assert issue.description is None
    assert issue.status_category == "started"
    assert issue.status_name == "Todo"
    assert issue.priority == "high"
    assert issue.assignee_type is None
    assert issue.assignee_id is None
    assert issue.creator_type == "member"
    assert issue.creator_id == "u1"
    assert issue.parent_id is None
    assert issue.project_id == "p1"
    assert issue.position == 3
    assert issue.stage == 0
    assert issue.start_date is None
    assert issue.due_date == "2026-02-01"
    assert issue.created_at is None
    assert issue.updated_at == datetime.datetime(2026, 1, 2, tzinfo=datetime.UTC)
    assert issue.revision == 0
    assert issue.last_activity_at is None
    assert tuple(label.name for label in issue.labels.all()) == ("bug",)
    serialized = issue.to_dict()
    assert serialized["workspace_id"] == "ws"
    assert serialized["number"] == 7
    assert serialized["identifier"] == "ABC-7"
    assert serialized["description"] is None
    assert serialized["parent_id"] is None
    assert serialized["revision"] == 0

    detached = issue.detach()
    restored = Issue.from_dict(issue.to_dict())
    assert detached.identifier == "ABC-7"
    assert detached.revision == 0
    assert restored.identifier == "ABC-7"
    assert restored.revision == 0

    omitted = _issue_list_page_from_wire(
        decode_json(b'{"issues":[{"id":"i2"}]}', _IssueListPageWire)
    ).items[0]
    for field in (
        "workspace_id",
        "number",
        "identifier",
        "status_category",
        "status_name",
        "revision",
        "last_activity_at",
    ):
        assert cast("object", getattr(omitted, field)) is msgspec.UNSET
    assert cast("object", omitted.description) is msgspec.UNSET
    assert cast("object", omitted.parent_id) is msgspec.UNSET
    assert cast("object", omitted.created_at) is msgspec.UNSET
    assert "description" not in omitted.to_dict()


_ISSUE_PARTIAL_SERIALIZATION_CASES = (
    _IssuePartialSerializationCase(
        name="id-only",
        payload=b'{"issues":[{"id":"i1"}]}',
        expected={"id": "i1"},
    ),
    _IssuePartialSerializationCase(
        name="title-with-identity",
        payload=b'{"issues":[{"id":"i2","title":"Title"}]}',
        expected={"id": "i2", "title": "Title"},
    ),
    _IssuePartialSerializationCase(
        name="explicit-null-description",
        payload=b'{"issues":[{"id":"i3","description":null}]}',
        expected={"id": "i3", "description": None},
    ),
    _IssuePartialSerializationCase(
        name="explicit-null-parent",
        payload=b'{"issues":[{"id":"i4","parent_issue_id":null}]}',
        expected={"id": "i4", "parent_id": None},
    ),
    _IssuePartialSerializationCase(
        name="explicit-null-created-at",
        payload=b'{"issues":[{"id":"i5","created_at":null}]}',
        expected={"id": "i5", "created_at": None},
    ),
    _IssuePartialSerializationCase(
        name="priority",
        payload=b'{"issues":[{"id":"i6","priority":"high"}]}',
        expected={"id": "i6", "priority": "high"},
    ),
    _IssuePartialSerializationCase(
        name="creator-id",
        payload=b'{"issues":[{"id":"i7","creator_id":"u1"}]}',
        expected={"id": "i7", "creator_id": "u1"},
    ),
    _IssuePartialSerializationCase(
        name="creator-type",
        payload=b'{"issues":[{"id":"i8","creator_type":"member"}]}',
        expected={"id": "i8", "creator_type": "member"},
    ),
    _IssuePartialSerializationCase(
        name="assignee-id-only",
        payload=b'{"issues":[{"id":"i9","assignee_id":"a1"}]}',
        expected={"id": "i9", "assignee_id": "a1"},
    ),
    _IssuePartialSerializationCase(
        name="assignee-type-only",
        payload=b'{"issues":[{"id":"i10","assignee_type":"agent"}]}',
        expected={"id": "i10", "assignee_type": "agent"},
    ),
    _IssuePartialSerializationCase(
        name="core-triple",
        payload=b'{"issues":[{"id":"i11","title":"Title","status":"todo"}]}',
        expected={"id": "i11", "title": "Title", "status": "todo"},
        fields=("id", "title", "status"),
    ),
    _IssuePartialSerializationCase(
        name="core-and-dynamic-allowlist",
        payload=(
            b'{"issues":[{"id":"i12","title":"Title","status":"todo",'
            b'"identifier":"ABC-12","revision":0,"workspace_id":"ws",'
            b'"number":12,"status_name":"Todo","position":3}]}'
        ),
        expected={
            "id": "i12",
            "title": "Title",
            "status": "todo",
            "identifier": "ABC-12",
            "revision": 0,
            "workspace_id": "ws",
            "number": 12,
            "status_name": "Todo",
            "position": 3,
        },
        fields=(
            "id",
            "title",
            "status",
            "identifier",
            "revision",
            "workspace_id",
            "number",
            "status_name",
            "position",
        ),
    ),
)


@pytest.mark.parametrize("case", _ISSUE_PARTIAL_SERIALIZATION_CASES, ids=lambda case: case.name)
def test_issue_partial_projection_serialization_preserves_exact_presence(
    case: _IssuePartialSerializationCase,
) -> None:
    issue = _issue_list_page_from_wire(
        decode_json(case.payload, _IssueListPageWire), fields=case.fields or None
    ).items[0]

    assert issue.to_dict() == case.expected
    for field in case.fields:
        public_name = "parent_id" if field == "parent_issue_id" else field
        assert getattr(issue, public_name) == case.expected[public_name]
    assert issue.detach().to_dict() == case.expected
    assert issue._clone_for_client(MagicMock()).to_dict() == case.expected
    assert Issue.from_dict(issue.to_dict()).to_dict() == case.expected
    assert Issue.from_json(issue.to_json()).to_dict() == case.expected


@pytest.mark.parametrize(
    ("field", "value"),
    (("assignee_id", "agent-1"), ("assignee_type", "agent")),
    ids=("id-only", "type-only"),
)
def test_issue_partial_assignee_scalars_do_not_fabricate_relation(field: str, value: str) -> None:
    payload = json.dumps({"issues": [{"id": "i1", field: value}]}).encode()
    issue = _issue_list_page_from_wire(decode_json(payload, _IssueListPageWire)).items[0]

    assert getattr(issue, field) == value
    assert issue.assignee is None


@pytest.mark.parametrize(
    "case",
    (
        _IssueQueryValidationCase({"limit": 0}, "between 1 and 100"),
        _IssueQueryValidationCase({"limit": 101}, "between 1 and 100"),
        _IssueQueryValidationCase({"fields": ("unknown",)}, "invalid field"),
        _IssueQueryValidationCase({"fields": ("id", "id")}, "duplicate field"),
        _IssueQueryValidationCase({"fields": ("title",)}, "identity_required"),
        _IssueQueryValidationCase({"property_filters": ("Owner>=me",)}, ">="),
        _IssueQueryValidationCase({"property_filters": ("Owner<=me",)}, "<="),
        _IssueQueryValidationCase({"property_filters": ("Owner!=me",)}, "!="),
        _IssueQueryValidationCase({"property_filters": ("Owner",)}, "Name=Value"),
        _IssueQueryValidationCase({"sort": "property:"}, "invalid sort"),
        _IssueQueryValidationCase(
            {"fields": ("id",), "resolve_properties": True}, "requires properties"
        ),
    ),
    ids=lambda case: next(iter(case.kwargs)),
)
def test_issue_query_validation_table_is_zero_io(
    case: _IssueQueryValidationCase,
) -> None:
    transport = MagicMock()
    resource = IssueResource(transport, ClientConfig())

    with pytest.raises((TypeError, ValueError), match=case.message):
        resource.list_command(**cast("Any", case.kwargs))

    transport.run_bytes.assert_not_called()


def test_issue_query_accepts_none_property_sentinel() -> None:
    resource = IssueResource(MagicMock(), ClientConfig())

    command = resource.list_command(property_filters=("Name=__none__",))

    assert command._plan.steps[0].argv == (
        "issue",
        "list",
        "--property",
        "Name=__none__",
        "--output",
        "json",
    )


def test_issue_search_envelope_preserves_unavailable_total() -> None:
    page = _decode_issue_search(
        b'{"issues":[{"id":"i1","title":"t","status":"todo"}],"has_more":true,"total":0}',
        "issue search",
    )

    assert page.total is None
    assert page.has_more is True


@pytest.mark.parametrize(
    "payload",
    (
        b"{}",
        b'{"issues":[],"has_more":true}',
        b'{"issues":[],"total":-1}',
    ),
    ids=("missing-items", "empty-continuation", "negative-total"),
)
def test_issue_page_decoder_rejects_bounded_malformed_pages(payload: bytes) -> None:
    with pytest.raises((OutputShapeError, msgspec.DecodeError, msgspec.ValidationError)):
        _issue_list_page_from_wire(decode_json(payload, _IssueListPageWire))


def test_deferred_issue_query_surfaces_remain_absent() -> None:
    import inspect

    assert not hasattr(IssueResource, "timeline")
    assert "active" not in inspect.signature(IssueResource.runs).parameters
    assert "siblings" not in inspect.signature(IssueResource.runs).parameters


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


def test_issue_continuation_commands_forward_fixed_id_and_entities(
    mock_transport: MagicMock,
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    client = MagicMock()
    resource = IssueResource(mock_transport, ClientConfig())
    resource._set_client(client)
    client.issues = resource
    issue = Issue(id="i1", title="Issue", status=IssueStatus.todo, _client=client)
    other = Issue(id="i2", title="Other", status=IssueStatus.todo)
    agent = Agent(id="a1", name="Agent")

    commands = (
        issue.refresh_command(),
        issue.update_command(title="Updated"),
        issue.assign_command(agent),
        issue.unassign_command(),
        issue.set_status_command(IssueStatus.done),
        issue.move_to_top_command(),
        issue.move_to_bottom_command(),
        issue.move_before_command(other),
        issue.move_after_command("i3"),
    )

    assert tuple(command.commands[0] for command in commands) == (
        "multica issue get i1 --output json",
        "multica issue update i1 --title Updated --output json",
        "multica issue assign i1 --to-id a1 --output json",
        "multica issue assign i1 --unassign --output json",
        "multica issue status i1 done --output json",
        "multica issue reorder i1 --top --output json",
        "multica issue reorder i1 --bottom --output json",
        "multica issue reorder i1 --before i2 --output json",
        "multica issue reorder i1 --after i3 --output json",
    )
    mock_transport.run_bytes.assert_not_called()


def test_issue_continuations_require_client_before_command_construction() -> None:
    issue = Issue(id="i1", title="Issue", status=IssueStatus.todo)
    with pytest.raises(DetachedEntityError):
        issue.refresh_command()
    with pytest.raises(DetachedEntityError):
        issue.assign_command("a1")


def test_task_run_messages_command_delegates_to_issue_resource(
    mock_transport: MagicMock,
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    client = MagicMock()
    resource = IssueResource(mock_transport, ClientConfig())
    resource._set_client(client)
    client.issues = resource
    task_run = TaskRun(id="run1", status="completed", _client=client, issue_id="i1")

    command = task_run.messages_command()

    assert command.commands == (
        "multica issue run-messages run1 --issue i1 --since 0 --output json",
    )
    mock_transport.run_bytes.assert_not_called()


def test_task_run_messages_relation_command_delegates_to_issue_resource(
    mock_transport: MagicMock,
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    client = MagicMock()
    resource = IssueResource(mock_transport, ClientConfig())
    resource._set_client(client)
    client.issues = resource
    task_run = TaskRun(id="run1", status="completed", _client=client, issue_id="i1")

    command = task_run.messages.all_command()

    assert command.commands == (
        "multica issue run-messages run1 --issue i1 --since 0 --output json",
    )
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
        IssueResource(MagicMock(), ClientConfig()).create_command(
            title="Test",
            description_input="some random string",  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "description_input", _DESCRIPTION_INPUT_IMPOSTORS, ids=lambda value: type(value).__name__
)
def test_description_input_rejects_same_name_impostors(description_input: object) -> None:
    with pytest.raises(TypeError, match="supported issue description"):
        IssueResource(MagicMock(), ClientConfig()).create_command(
            title="Test",
            description_input=cast("IssueDescriptionInput", description_input),
        )


def test_issue_list_rejects_same_name_filter_impostor() -> None:
    with pytest.raises(TypeError, match="Expected IssueListFilter"):
        IssueResource(MagicMock(), ClientConfig()).list_command(
            _ISSUE_LIST_FILTER_IMPOSTOR,
        )


def test_issue_assignment_rejects_blank_or_structural_targets_before_io():
    resource = IssueResource(MagicMock(), ClientConfig())
    with pytest.raises(ValueError, match="assignee must be non-empty"):
        resource.assign_command("iss_001", " ")
    with pytest.raises(TypeError, match="non-empty ID"):
        resource.assign_command("iss_001", object())  # type: ignore[arg-type]


def test_issue_reorder_request_rejects_multiple_targets():
    with pytest.raises(ValueError, match="Exactly one reorder target must be set"):
        IssueResource(MagicMock(), ClientConfig()).reorder_command(
            "iss_001", before_id="iss_002", bottom=True
        )
