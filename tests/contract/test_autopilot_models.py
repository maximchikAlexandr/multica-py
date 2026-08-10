from __future__ import annotations

import datetime
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.enums import AutopilotExecutionMode
from multica_py.exceptions import JsonOutputError, OutputShapeError
from multica_py.models.autopilots import (
    AutopilotListPage,
    AutopilotRunListPage,
    AutopilotSubscriber,
)
from multica_py.resources.autopilots import Autopilot, AutopilotResource, AutopilotRun


def test_autopilot_list_rejects_legacy_fields() -> None:
    ap = Autopilot(
        id="a1",
        workspace_id="w1",
        title="T",
        assignee_type="member",
        assignee_id="u1",
        status="active",
        execution_mode="create_issue",
        created_by_type="member",
        created_by_id="u1",
    )
    assert not hasattr(ap, "name")
    assert not hasattr(ap, "enabled")
    r = AutopilotRun(id="r1", autopilot_id="a1", source="web", status="running")
    assert not hasattr(r, "started_at")


_FULL_AP_JSON = (
    b'{"id":"a1","workspace_id":"w1","title":"My AP","description":"desc",'
    b'"project_id":"p1","assignee_type":"member","assignee_id":"u1",'
    b'"status":"active","execution_mode":"create_issue",'
    b'"issue_title_template":"{{title}}",'
    b'"created_by_type":"member","created_by_id":"creator",'
    b'"last_run_at":"2026-07-28T11:47:17Z",'
    b'"created_at":"2026-07-28T10:00:00Z","updated_at":"2026-07-28T11:00:00Z",'
    b'"trigger_kinds":["cron","webhook"],"next_run_at":"2026-07-29T00:00:00Z",'
    b'"last_run_status":"success",'
    b'"subscribers":[{"user_type":"member","user_id":"s1","created_at":"2026-07-28T09:00:00Z"}],'
    b'"can_write":true,"can_manage_access":false}'
)
_MINIMAL_AP_JSON = (
    b'{"id":"a1","workspace_id":"w1","title":"My AP",'
    b'"assignee_type":"member","assignee_id":"u1",'
    b'"status":"active","execution_mode":"create_issue",'
    b'"created_by_type":"member","created_by_id":"creator"}'
)
_SUBSCRIBERS = (
    AutopilotSubscriber(
        user_type="member",
        user_id="s1",
        created_at=datetime.datetime(2026, 7, 28, 9, 0, tzinfo=datetime.UTC),
    ),
)


@pytest.mark.parametrize(
    ("json_bytes", "expected_fields"),
    [
        (
            _FULL_AP_JSON,
            {
                "id": "a1",
                "workspace_id": "w1",
                "title": "My AP",
                "description": "desc",
                "project_id": "p1",
                "issue_title_template": "{{title}}",
                "trigger_kinds": ("cron", "webhook"),
                "last_run_status": "success",
                "can_write": True,
                "can_manage_access": False,
                "subscriber_snapshot": _SUBSCRIBERS,
                "next_run_at": datetime.datetime(2026, 7, 29, 0, 0, tzinfo=datetime.UTC),
                "last_run_at": datetime.datetime(2026, 7, 28, 11, 47, 17, tzinfo=datetime.UTC),
            },
        ),
        (
            _MINIMAL_AP_JSON,
            {
                "id": "a1",
                "title": "My AP",
                "description": None,
                "project_id": None,
                "issue_title_template": None,
                "trigger_kinds": (),
                "last_run_status": None,
                "can_write": None,
                "can_manage_access": None,
                "subscriber_snapshot": (),
                "next_run_at": None,
                "last_run_at": None,
            },
        ),
    ],
)
def test_autopilot_decoding(json_bytes: bytes, expected_fields: dict[str, object]) -> None:
    ap = decode_json(json_bytes, Autopilot, command="test")
    for field, expected in expected_fields.items():
        assert getattr(ap, field) == expected, f"{field} mismatch"


_FULL_RUN_JSON = (
    b'{"id":"r1","autopilot_id":"a1","trigger_id":"tr_1",'
    b'"source":"webhook","status":"completed",'
    b'"issue_id":"iss_1","task_id":"tk_1",'
    b'"triggered_at":"2026-07-28T11:47:17Z",'
    b'"completed_at":"2026-07-28T12:00:00Z",'
    b'"failure_reason":null,"reason_code":null,'
    b'"trigger_payload":{"event":"push"},"result":{"ok":true},'
    b'"created_at":"2026-07-28T11:47:00Z"}'
)
_MINIMAL_RUN_JSON = b'{"id":"r1","autopilot_id":"a1","source":"manual","status":"running"}'


@dataclass(frozen=True)
class DecodeErrorCase:
    name: str
    json_bytes: bytes
    model_type: type[object]


@pytest.mark.parametrize(
    ("json_bytes", "expected_fields"),
    [
        (
            _FULL_RUN_JSON,
            {
                "id": "r1",
                "autopilot_id": "a1",
                "trigger_id": "tr_1",
                "source": "webhook",
                "status": "completed",
                "issue_id": "iss_1",
                "task_id": "tk_1",
                "failure_reason": None,
                "reason_code": None,
                "trigger_payload": {"event": "push"},
                "result": {"ok": True},
            },
        ),
        (
            _MINIMAL_RUN_JSON,
            {
                "id": "r1",
                "autopilot_id": "a1",
                "source": "manual",
                "status": "running",
                "trigger_id": None,
                "issue_id": None,
                "task_id": None,
                "failure_reason": None,
                "reason_code": None,
                "trigger_payload": None,
                "result": None,
                "completed_at": None,
            },
        ),
    ],
)
def test_autopilot_run_decoding(json_bytes: bytes, expected_fields: dict[str, object]) -> None:
    run = decode_json(json_bytes, AutopilotRun, command="test")
    for field, expected in expected_fields.items():
        assert getattr(run, field) == expected, f"{field} mismatch"


_DECODE_ERROR_CASES: tuple[DecodeErrorCase, ...] = (
    DecodeErrorCase(name="single-shape", json_bytes=b'{"id":"r1"}', model_type=AutopilotRun),
    DecodeErrorCase(
        name="list-shape",
        json_bytes=b'{"runs":[{"id":"r1"}]}',
        model_type=AutopilotRunListPage[AutopilotRun],
    ),
    DecodeErrorCase(name="single-json", json_bytes=b"{bad", model_type=AutopilotRun),
    DecodeErrorCase(
        name="list-json",
        json_bytes=b'{"runs":[bad]}',
        model_type=AutopilotRunListPage[AutopilotRun],
    ),
)


@pytest.mark.parametrize("case", _DECODE_ERROR_CASES, ids=lambda case: case.name)
def test_autopilot_run_decode_errors_preserve_command(case: DecodeErrorCase) -> None:
    with pytest.raises(
        (JsonOutputError, OutputShapeError), match=r"\[command: autopilot runs --output json\]"
    ):
        decode_json(case.json_bytes, case.model_type, command="autopilot runs --output json")


def test_autopilot_list_page_decoding() -> None:
    page = decode_json(
        b'{"autopilots":[{"id":"a1","workspace_id":"w1","title":"T",'
        b'"assignee_type":"member","assignee_id":"u1","status":"active",'
        b'"execution_mode":"create_issue","created_by_type":"member",'
        b'"created_by_id":"creator"}],"total":1}',
        AutopilotListPage[Autopilot],
        command="test",
    )
    assert len(page.autopilots) == 1
    assert page.autopilots[0].id == "a1"
    assert page.total == 1


def test_autopilot_list_page_empty() -> None:
    page = decode_json(
        b'{"autopilots":[],"total":0}',
        AutopilotListPage[Autopilot],
        command="test",
    )
    assert page.autopilots == ()
    assert page.total == 0


def test_autopilot_run_list_page_decoding() -> None:
    page = decode_json(
        b'{"runs":[{"id":"r1","autopilot_id":"a1","source":"web","status":"running"}],"total":5}',
        AutopilotRunListPage[AutopilotRun],
        command="test",
    )
    assert len(page.runs) == 1
    assert page.runs[0].id == "r1"
    assert page.total == 5
    assert not page.has_more


@pytest.mark.parametrize(
    ("offset", "total", "runs_count", "expected_has_more"),
    [
        (None, 5, 1, True),
        (0, 5, 1, True),
        (3, 5, 2, False),
        (5, 5, 0, False),
        (0, 3, 3, False),
    ],
)
def test_autopilot_run_list_page_has_more(
    offset: int | None,
    total: int,
    runs_count: int,
    expected_has_more: bool,
) -> None:
    from multica_py._internal.wire_models import (
        _autopilot_run_list_page_from_wire,
        _AutopilotRunListPageWire,
        _AutopilotRunWire,
    )

    runs = tuple(
        _AutopilotRunWire(id=f"r{i}", autopilot_id="a1", source="web", status="running")
        for i in range(runs_count)
    )
    wire = _AutopilotRunListPageWire(runs=runs, total=total)
    page = _autopilot_run_list_page_from_wire(wire, limit=10, offset=offset)
    assert page.has_more is expected_has_more


@pytest.fixture
def mock_transport() -> MagicMock:
    transport = MagicMock(spec=CliTransport)
    _MOCK_AP = (
        b'{"id":"a1","workspace_id":"w1","title":"T","assignee_type":"member",'
        b'"assignee_id":"u1","status":"active","execution_mode":"create_issue",'
        b'"created_by_type":"member","created_by_id":"u1"}'
    )
    _MOCK_RUN = b'{"id":"r1","autopilot_id":"a1","source":"manual","status":"running"}'
    transport.run_bytes.return_value = MagicMock(stdout=_MOCK_AP, argv=("test",))
    transport.run_text.return_value = MagicMock()
    return transport


def _make_resource(transport: MagicMock) -> AutopilotResource:
    return AutopilotResource(transport, ClientConfig())


@pytest.mark.parametrize("negative", [-1, -5])
def test_history_rejects_negative_limit(negative: int, mock_transport: MagicMock) -> None:
    resource = _make_resource(mock_transport)
    with pytest.raises(ValueError, match="limit"):
        resource.history("a1", limit=negative)
    mock_transport.run_bytes.assert_not_called()


def test_history_limit_zero(mock_transport: MagicMock) -> None:
    resource = _make_resource(mock_transport)
    resource.history("a1", limit=0)
    args = mock_transport.run_bytes.call_args[0][0]
    assert args == ("autopilot", "runs", "a1", "--limit", "0", "--output", "json")


@pytest.mark.parametrize("negative", [-1, -5])
def test_history_rejects_negative_offset(negative: int, mock_transport: MagicMock) -> None:
    resource = _make_resource(mock_transport)
    with pytest.raises(ValueError, match="offset"):
        resource.history("a1", offset=negative)
    mock_transport.run_bytes.assert_not_called()


def test_history_offset_zero(mock_transport: MagicMock) -> None:
    resource = _make_resource(mock_transport)
    resource.history("a1", offset=0)
    args = mock_transport.run_bytes.call_args[0][0]
    assert args == ("autopilot", "runs", "a1", "--offset", "0", "--output", "json")


def test_update_rejects_clear_subscribers_with_subscribers(mock_transport: MagicMock) -> None:
    resource = _make_resource(mock_transport)
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        resource.update("a1", clear_subscribers=True, subscribers=("u1",))  # type: ignore[call-arg]
    mock_transport.run_bytes.assert_not_called()


def test_create_emits_repeatable_subscribers(mock_transport: MagicMock) -> None:
    resource = _make_resource(mock_transport)
    resource.create(
        "T",
        agent="ag1",
        execution_mode=AutopilotExecutionMode.create_issue,
        subscribers=("u1", "u2"),
    )
    args = mock_transport.run_bytes.call_args[0][0]
    idx = args.index("--subscriber")
    assert idx >= 0
    assert args[idx + 1] == "u1"
    assert args[idx + 2] == "--subscriber"
    assert args[idx + 3] == "u2"


def test_update_emits_repeatable_subscribers(mock_transport: MagicMock) -> None:
    resource = _make_resource(mock_transport)
    resource.update("a1", subscribers=("u1", "u2"))
    args = mock_transport.run_bytes.call_args[0][0]
    idx = args.index("--subscriber")
    assert idx >= 0
    assert args[idx + 1] == "u1"
    assert args[idx + 2] == "--subscriber"
    assert args[idx + 3] == "u2"


@pytest.mark.parametrize("bad", ["", "  "])
def test_create_rejects_blank_subscriber(bad: str, mock_transport: MagicMock) -> None:
    resource = _make_resource(mock_transport)
    with pytest.raises(ValueError, match="subscribers"):
        resource.create(
            "T", agent="ag1", execution_mode=AutopilotExecutionMode.create_issue, subscribers=(bad,)
        )
    mock_transport.run_bytes.assert_not_called()


@pytest.mark.parametrize("bad", ["", "  "])
def test_update_rejects_blank_subscriber(bad: str, mock_transport: MagicMock) -> None:
    resource = _make_resource(mock_transport)
    with pytest.raises(ValueError, match="subscribers"):
        resource.update("a1", subscribers=(bad,))
    mock_transport.run_bytes.assert_not_called()


def test_update_clears_project_id_with_empty_string(mock_transport: MagicMock) -> None:
    resource = _make_resource(mock_transport)
    resource.update("a1", project_id="")
    args = mock_transport.run_bytes.call_args[0][0]
    assert "--project" in args
    assert args[args.index("--project") + 1] == ""


def test_update_omits_project_id_when_none(mock_transport: MagicMock) -> None:
    resource = _make_resource(mock_transport)
    resource.update("a1", title="x")
    args = mock_transport.run_bytes.call_args[0][0]
    assert "--project" not in args
