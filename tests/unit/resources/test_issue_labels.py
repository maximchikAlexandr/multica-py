from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import msgspec

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.issues import IssueCreateRequest
from multica_py.resources.issue_labels import IssueLabelResource
from multica_py.resources.issues import IssueResource


def _result(stdout: bytes = b"[]", exit_code: int = 0) -> RawCommandResult:
    return RawCommandResult(
        argv=(), exit_code=exit_code, stdout=stdout, stderr=b"", duration=datetime.timedelta()
    )


def test_issue_label_add_uses_positional_label_id() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.run_bytes.return_value = _result(
        msgspec.json.encode([{"id": "lbl_1", "name": "bug", "color": "#ff0000"}])
    )
    IssueLabelResource(transport, ClientConfig()).add("iss_1", "lbl_1")
    transport.run_bytes.assert_called_once_with(
        ("issue", "label", "add", "iss_1", "lbl_1", "--output", "json"),
        stdin=None,
        timeout=None,
    )


def test_issue_label_remove_uses_positional_label_id() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.run_bytes.return_value = _result(b"[]")
    IssueLabelResource(transport, ClientConfig()).remove("iss_1", "lbl_1")
    transport.run_bytes.assert_called_once_with(
        ("issue", "label", "remove", "iss_1", "lbl_1", "--output", "json"),
        stdin=None,
        timeout=None,
    )


def test_issue_create_attaches_labels_after_create() -> None:
    transport = MagicMock(spec=CliTransport)
    created = {
        "id": "iss_1",
        "title": "Test",
        "status": "todo",
        "labels": [],
    }
    with_labels = {
        "id": "iss_1",
        "title": "Test",
        "status": "todo",
        "labels": [
            {"id": "lbl_1", "name": "bug"},
            {"id": "lbl_2", "name": "urgent"},
        ],
    }
    transport.run_bytes.side_effect = [
        _result(msgspec.json.encode(created)),
        _result(msgspec.json.encode([{"id": "lbl_1", "name": "bug"}])),
        _result(
            msgspec.json.encode([{"id": "lbl_1", "name": "bug"}, {"id": "lbl_2", "name": "urgent"}])
        ),
        _result(msgspec.json.encode(with_labels)),
    ]
    issue = IssueResource(transport, ClientConfig()).create(
        IssueCreateRequest(title="Test", label_ids=("lbl_1", "lbl_2"))
    )
    assert issue.labels == ("bug", "urgent")
    calls = [call.args[0] for call in transport.run_bytes.call_args_list]
    assert calls[0] == ("issue", "create", "--title", "Test", "--output", "json")
    assert "--label" not in calls[0]
    assert calls[1] == ("issue", "label", "add", "iss_1", "lbl_1", "--output", "json")
    assert calls[2] == ("issue", "label", "add", "iss_1", "lbl_2", "--output", "json")
    assert calls[3] == ("issue", "get", "iss_1", "--output", "json")
