from __future__ import annotations

import datetime
import pathlib
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import _CommentWire, comment_from_wire
from multica_py.config import ClientConfig, OperationOptions
from multica_py.exceptions import CommandExecutionError, OutputShapeError
from multica_py.execution import ExecutionRequest, ExecutionResult, LocalExecutor
from multica_py.models.issues import LinkedPullRequest
from multica_py.resources.agent_mcp import AgentMcpResource
from multica_py.resources.agents import AgentResource, _extract_task_cursor
from multica_py.resources.issues import IssueResource, _decode_issue_timeline
from multica_py.resources.workspace_mcp import WorkspaceMcpResource


def test_agent_tasks_maps_bounded_cursor_and_wakeup_fields() -> None:
    transport = MagicMock()
    transport.run_text.return_value = TextResult(
        '[{"id":"task-1","status":"done","issue_id":"issue-1",'
        '"wakeup_system_rule":"rule-1","wakeup_joined":false}]',
        'diagnostic\nMore runs available; use --before "opaque-cursor" to fetch the next page.\n',
        0,
    )
    page = AgentResource(transport, ClientConfig()).tasks("agent-1", limit=25, before="prior")

    assert page.next_cursor == "opaque-cursor"
    assert page.items[0].wakeup_system_rule == "rule-1"
    assert page.items[0].wakeup_joined is False
    transport.run_text.assert_called_once_with(
        (
            "agent",
            "tasks",
            "agent-1",
            "--limit",
            "25",
            "--before",
            "prior",
            "--output",
            "json",
        )
    )


@pytest.mark.parametrize("limit", (0, 201, True, "10"))
def test_agent_tasks_rejects_invalid_limit_before_io(limit: object) -> None:
    transport = MagicMock()
    with pytest.raises((TypeError, ValueError)):
        AgentResource(transport, ClientConfig()).tasks_command("agent-1", limit=limit)  # type: ignore[arg-type]
    transport.run_text.assert_not_called()


@pytest.mark.parametrize(
    ("payload", "expected", "presence"),
    (
        ('{"id":"task-1","status":"done","issue_id":"issue-1"}', None, "missing"),
        (
            '{"id":"task-1","status":"done","issue_id":"issue-1",'
            '"wakeup_system_rule":null,"wakeup_joined":null}',
            None,
            "null",
        ),
    ),
    ids=("omitted", "explicit-null"),
)
def test_agent_task_additive_fields_preserve_omission_and_null(
    payload: str, expected: None, presence: str
) -> None:
    transport = MagicMock()
    transport.run_text.return_value = TextResult(f"[{payload}]", "", 0)

    task = AgentResource(transport, ClientConfig()).tasks("agent-1").items[0]

    assert task.wakeup_system_rule is expected
    assert task.wakeup_joined is expected
    assert dict(task._wire_presence)["wakeup_system_rule"] == presence
    assert dict(task._wire_presence)["wakeup_joined"] == presence


@pytest.mark.parametrize(
    "payload",
    (
        b'[{"id":"task-1","status":"done","issue_id":"issue-1","wakeup_joined":"false"}]',
        b'[{"id":"task-1","status":"done","issue_id":"issue-1","wakeup_system_rule":7}]',
    ),
    ids=("joined-wrong-type", "rule-wrong-type"),
)
def test_agent_task_additive_fields_reject_malformed_values(payload: bytes) -> None:
    transport = MagicMock()
    transport.run_text.return_value = TextResult(payload.decode(), "", 0)

    with pytest.raises(OutputShapeError):
        AgentResource(transport, ClientConfig()).tasks("agent-1")


@pytest.mark.parametrize(
    ("stderr", "expected"),
    (
        ('More runs available; use --before "opaque" to fetch the next page.', "opaque"),
        ("warning: retry later", None),
        (
            'warning --before fake\nMore runs available; use --before "exact" to fetch the next page.\n',
            "exact",
        ),
    ),
    ids=("exact", "missing", "diagnostic-plus-exact"),
)
def test_agent_task_cursor_requires_exact_success_stderr_hint(
    stderr: str, expected: str | None
) -> None:
    transport = MagicMock()
    transport.run_text.return_value = TextResult(
        '[{"id":"task-1","status":"done","issue_id":"issue-1"}]', stderr, 0
    )

    assert AgentResource(transport, ClientConfig()).tasks("agent-1").next_cursor == expected


def test_issue_runs_preserve_envelope_and_never_leak_task_cursor() -> None:
    transport = MagicMock()
    transport.run_bytes.return_value = RawCommandResult(
        argv=("issue", "runs", "issue-1", "--output", "json"),
        exit_code=0,
        stdout=b'[{"id":"run-1","status":"done","wakeup_joined":false}]',
        stderr=b'More runs available; use --before "must-not-leak" to fetch the next page.',
        duration=datetime.timedelta(),
    )

    page = IssueResource(transport, ClientConfig()).runs("issue-1")

    assert page.next_cursor is None
    assert page.items[0].wakeup_joined is False
    assert page.items[0].issue_id == "issue-1"


@pytest.mark.parametrize(
    ("payload", "expected", "presence"),
    (
        (b'[{"id":"run-1","status":"done"}]', None, "missing"),
        (
            b'[{"id":"run-1","status":"done","wakeup_system_rule":null,"wakeup_joined":null}]',
            None,
            "null",
        ),
    ),
    ids=("omitted", "explicit-null"),
)
def test_issue_run_additive_fields_preserve_omission_and_null(
    payload: bytes, expected: None, presence: str
) -> None:
    transport = MagicMock()
    transport.run_bytes.return_value = RawCommandResult(
        argv=("issue", "runs", "issue-1", "--output", "json"),
        exit_code=0,
        stdout=payload,
        stderr=b"",
        duration=datetime.timedelta(),
    )

    run = IssueResource(transport, ClientConfig()).runs("issue-1").items[0]

    assert run.wakeup_system_rule is expected
    assert run.wakeup_joined is expected
    assert dict(run._wire_presence)["wakeup_system_rule"] == presence
    assert dict(run._wire_presence)["wakeup_joined"] == presence


def test_issue_run_additive_fields_reject_malformed_values() -> None:
    transport = MagicMock()
    transport.run_bytes.return_value = RawCommandResult(
        argv=("issue", "runs", "issue-1", "--output", "json"),
        exit_code=0,
        stdout=b'[{"id":"run-1","status":"done","wakeup_joined":"false"}]',
        stderr=b"",
        duration=datetime.timedelta(),
    )

    with pytest.raises(OutputShapeError):
        IssueResource(transport, ClientConfig()).runs("issue-1")


def test_update_attachments_are_prevalidated_and_use_single_cli_step(
    tmp_path: pathlib.Path,
) -> None:
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    first = workdir / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")
    resource = IssueResource(MagicMock(), ClientConfig(cwd=workdir))

    command = resource.update_command(
        "issue-1",
        attachments=(str(first), str(second)),
        allow_external_file=True,
        options=OperationOptions(timeout=120),
    )

    assert len(command._plan.steps) == 1
    assert command._plan.steps[0].argv == (
        "issue",
        "update",
        "issue-1",
        "--attachment",
        str(first),
        "--attachment",
        str(second),
        "--allow-external-file",
        "--output",
        "json",
    )
    assert command._plan.steps[0].timeout == datetime.timedelta(seconds=120)


def test_update_rejects_missing_attachment_before_io(tmp_path: pathlib.Path) -> None:
    transport = MagicMock()
    resource = IssueResource(transport, ClientConfig(cwd=tmp_path))
    with pytest.raises(ValueError, match="existing local file"):
        resource.update_command("issue-1", attachments=(str(tmp_path / "missing.txt"),))
    transport.run_bytes.assert_not_called()


@pytest.mark.parametrize(
    ("attachments", "allow_external_file", "message"),
    (
        (["file.txt"], False, "tuple"),
        ((1,), False, "path-like"),
        (("https://example.test/file.txt",), False, "URLs"),
    ),
    ids=("container", "element", "url"),
)
def test_update_attachment_shape_fails_before_io(
    tmp_path: pathlib.Path, attachments: object, allow_external_file: bool, message: str
) -> None:
    transport = MagicMock()
    resource = IssueResource(transport, ClientConfig(cwd=tmp_path))

    with pytest.raises((TypeError, ValueError), match=message):
        resource.update_command(
            "issue-1",
            attachments=attachments,  # type: ignore[arg-type]
            allow_external_file=allow_external_file,
        )

    transport.run_bytes.assert_not_called()


def test_update_rejects_external_path_without_opt_in_before_io(tmp_path: pathlib.Path) -> None:
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    external = tmp_path / "outside.txt"
    external.write_text("outside", encoding="utf-8")
    transport = MagicMock()

    with pytest.raises(ValueError, match="outside the working directory"):
        IssueResource(transport, ClientConfig(cwd=workdir)).update_command(
            "issue-1", attachments=(str(external),)
        )

    transport.run_bytes.assert_not_called()


@pytest.mark.parametrize(
    ("configured", "expected"),
    (
        (datetime.timedelta(seconds=30), datetime.timedelta(seconds=60)),
        (datetime.timedelta(seconds=120), datetime.timedelta(seconds=120)),
    ),
    ids=("minimum", "preserve-larger"),
)
def test_attach_only_update_uses_single_step_and_effective_timeout(
    tmp_path: pathlib.Path, configured: datetime.timedelta, expected: datetime.timedelta
) -> None:
    attachment = tmp_path / "file.txt"
    attachment.write_text("payload", encoding="utf-8")
    resource = IssueResource(MagicMock(), ClientConfig(cwd=tmp_path, timeout=configured))

    command = resource.update_command(
        "issue-1", attachments=(str(attachment),), assignee_id="agent-1"
    )

    assert len(command._plan.steps) == 1
    assert command._plan.steps[0].timeout == expected


class _PartialUploadExecutor(LocalExecutor):
    def __init__(self) -> None:
        self.requests: list[ExecutionRequest] = []

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        self.requests.append(request)
        return ExecutionResult(
            1,
            b"",
            b"partial upload; uploaded attachment IDs: [att-1]; token=secret-token",
        )


def test_attach_only_update_propagates_one_redacted_partial_upload_error(
    tmp_path: pathlib.Path,
) -> None:
    attachment = tmp_path / "file.txt"
    attachment.write_text("payload", encoding="utf-8")
    executor = _PartialUploadExecutor()
    config = ClientConfig(
        cwd=tmp_path,
        environment=(("UPLOAD_TOKEN", "secret-token"),),
    )
    resource = IssueResource(CliTransport(config, executor=executor), config)

    with pytest.raises(CommandExecutionError) as excinfo:
        resource.update("issue-1", attachments=(str(attachment),), assignee_id="agent-1")

    assert "partial upload" in excinfo.value.stderr
    assert "att-1" in excinfo.value.stderr
    assert "secret-token" not in excinfo.value.stderr
    assert len(executor.requests) == 1


def test_comment_supplements_are_immutable_and_independent() -> None:
    wire = msgspec.json.decode(
        b'{"id":"comment-1","content":"body","supplement":{"legacy":true},'
        b'"supplements":[{"task_id":"task-1","status":"delivered",'
        b'"delivered_at":"2026-09-29T12:00:00Z"}]}',
        type=_CommentWire,
    )
    comment = comment_from_wire(wire)

    assert comment.supplement == {"legacy": True}
    assert comment.supplements[0].task_id == "task-1"
    assert isinstance(comment.supplements, tuple)
    assert comment.supplements[0].delivered_at == datetime.datetime(
        2026, 9, 29, 12, tzinfo=datetime.UTC
    )


def test_comment_supplement_requires_task_and_status() -> None:
    wire = msgspec.json.decode(
        b'{"id":"comment-1","content":"body","supplements":[{"task_id":"","status":"delivered"}]}',
        type=_CommentWire,
    )
    with pytest.raises(OutputShapeError, match="task_id"):
        comment_from_wire(wire)


def test_comment_supplements_omitted_preserve_legacy_projection() -> None:
    wire = msgspec.json.decode(
        b'{"id":"comment-1","content":"body","supplement":{"legacy":true}}',
        type=_CommentWire,
    )

    comment = comment_from_wire(wire)

    assert comment.supplements == ()
    assert comment.supplement == {"legacy": True}


@pytest.mark.parametrize(
    "payload",
    (
        b'{"id":"comment-1","content":"body","supplements":null}',
        b'{"id":"comment-1","content":"body","supplements":[null]}',
        b'{"id":"comment-1","content":"body","supplements":[{"task_id":"task-1","status":3}]}',
    ),
    ids=("explicit-null", "null-item", "malformed-item"),
)
def test_comment_supplements_reject_null_and_malformed_values(payload: bytes) -> None:
    with pytest.raises(msgspec.ValidationError):
        msgspec.json.decode(payload, type=_CommentWire)


def test_pull_request_and_timeline_keep_open_future_values() -> None:
    pr = msgspec.json.decode(
        b'{"url":"https://example.test/pr/1","state":"at_target",'
        b'"pr_auto_complete":{"target_status":"future-status","state":"new-open"}}',
        type=LinkedPullRequest,
    )
    timeline = _decode_issue_timeline(
        b'{"items":[{"id":"e1","action":"wakeup_created",'
        b'"details":{"rule":"r1"}}],"next_cursor":"next"}',
        "issue timeline",
    )

    assert pr.state == "at_target"
    assert pr.pr_auto_complete is not None
    assert pr.pr_auto_complete.target_status == "future-status"
    assert timeline.items[0].action == "wakeup_created"
    assert timeline.items[0].details == {"rule": "r1"}
    assert timeline.next_cursor == "next"


def test_pull_request_requires_target_status_and_accepts_no_close_intent() -> None:
    pr = msgspec.json.decode(
        b'{"url":"https://example.test/pr/1","pr_auto_complete":'
        b'{"target_status":"target","state":"no_close_intent"}}',
        type=LinkedPullRequest,
    )

    assert pr.pr_auto_complete is not None
    assert pr.pr_auto_complete.target_status == "target"
    assert pr.pr_auto_complete.state == "no_close_intent"
    with pytest.raises(msgspec.ValidationError):
        msgspec.json.decode(
            b'{"url":"https://example.test/pr/1","pr_auto_complete":{"state":"open"}}',
            type=LinkedPullRequest,
        )


def test_timeline_preserves_unknown_action_and_structured_details() -> None:
    timeline = _decode_issue_timeline(
        b'{"items":[{"id":"e1","action":"future_action","details":[{"key":"value"}]}]}',
        "issue timeline",
    )

    assert timeline.items[0].action == "future_action"
    assert timeline.items[0].details == ({"key": "value"},)


def test_workspace_mcp_only_list_exposes_zero_agent_count() -> None:
    payload = b'[{"id":"mcp-1","name":"server","transport":"stdio","agent_count":0}]'
    omitted = WorkspaceMcpResource._decode_mcp_servers(
        b'[{"id":"mcp-1","name":"server","transport":"stdio"}]',
        "workspace mcp list",
        include_agent_count=True,
    )
    listed = WorkspaceMcpResource._decode_mcp_servers(
        payload, "workspace mcp list", include_agent_count=True
    )
    other = WorkspaceMcpResource._decode_mcp_servers(payload, "agent mcp list")

    assert omitted.items[0].agent_count is None
    assert listed.items[0].agent_count == 0
    assert other.items[0].agent_count is None


def test_agent_mcp_entrypoint_does_not_leak_workspace_agent_count() -> None:
    payload = b'[{"id":"mcp-1","name":"server","transport":"stdio","agent_count":0}]'
    transport = MagicMock()
    transport.run_bytes.return_value = RawCommandResult(
        argv=("agent", "mcp", "list", "agent-1", "--output", "json"),
        exit_code=0,
        stdout=payload,
        stderr=b"",
        duration=datetime.timedelta(),
    )

    page = AgentMcpResource(transport, ClientConfig()).list("agent-1")

    assert page.items[0].agent_count is None


def test_mcp_rejects_malformed_agent_count() -> None:
    with pytest.raises(OutputShapeError):
        WorkspaceMcpResource._decode_mcp_servers(
            b'[{"id":"mcp-1","name":"server","transport":"stdio","agent_count":"zero"}]',
            "workspace mcp list",
            include_agent_count=True,
        )


def test_task_cursor_parser_ignores_unrelated_stderr() -> None:
    assert _extract_task_cursor("warning --before fake") is None
