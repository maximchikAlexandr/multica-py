from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import pytest

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.exceptions import ConflictError, OutputShapeError
from multica_py.resources.autopilots import AutopilotResource
from multica_py.resources.chats import ChatResource
from multica_py.resources.issue_wakeups import IssueWakeupResource
from multica_py.resources.issues import IssueResource
from multica_py.resources.skill_files import SkillFileResource
from tests.unit.resources._factories import command_result


def transport() -> MagicMock:
    result = MagicMock(spec=CliTransport)
    result.build_full_argv.side_effect = lambda args: ("multica", *args)
    return result


def resource(resource_type: type[object], mock_transport: MagicMock) -> object:
    return resource_type(mock_transport, ClientConfig())  # type: ignore[call-arg]


def test_timeline_uses_exact_filters_and_decodes_native_page() -> None:
    mock_transport = transport()
    issue = resource(IssueResource, mock_transport)

    command = issue.timeline_command(
        "iss-1",
        activity_only=True,
        actions=("comment.created", "status.changed"),
        since="cursor-1",
        tail=2,
    )

    assert command.commands == (
        "multica issue timeline iss-1 --activity-only --action comment.created "
        "--action status.changed --since cursor-1 --tail 2 --output json",
    )
    mock_transport.run_bytes.return_value = command_result(
        b'{"events":[{"id":"e1","type":"comment","action":"created",'
        b'"created_at":"2026-09-27T10:00:00Z"}],"total":4,"limit":2,'
        b'"next_cursor":"cursor-2"}',
        "issue",
        "timeline",
        "iss-1",
    )
    page = command.run()
    assert page.total == 4
    assert page.next_cursor == "cursor-2"
    assert page.items[0].created_at == datetime.datetime(2026, 9, 27, 10, tzinfo=datetime.UTC)


def test_timeline_rejects_malformed_native_item() -> None:
    mock_transport = transport()
    mock_transport.run_bytes.return_value = command_result(b'{"events":["wrong"]}')
    command = resource(IssueResource, mock_transport).timeline_command("iss-1")

    with pytest.raises(OutputShapeError):
        command.run()


def test_chat_preserves_explicit_zero_limit_and_pagination() -> None:
    mock_transport = transport()
    chat = resource(ChatResource, mock_transport)
    command = chat.history_command(limit=0, before="cursor-1")

    assert command.commands == ("multica chat history --limit 0 --before cursor-1 --output json",)
    mock_transport.run_bytes.return_value = command_result(
        b'{"messages":[{"role":"agent","author":"a1","text":"ok"}],'
        b'"total":3,"limit":0,"next_cursor":"cursor-2"}'
    )
    page = command.run()
    assert page.limit == 0
    assert page.next_cursor == "cursor-2"
    assert page.items[0].text == "ok"


def test_chat_rejects_malformed_message_page() -> None:
    mock_transport = transport()
    mock_transport.run_bytes.return_value = command_result(b'{"messages":{}}')
    command = resource(ChatResource, mock_transport).thread_command("thread-1")

    with pytest.raises(TypeError, match="messages"):
        command.run()


def test_wakeup_events_preserve_loop_guard_and_native_event_catalog() -> None:
    mock_transport = transport()
    mock_transport.run_bytes.return_value = command_result(
        b'{"event_types":["comment.created"],"loop_protection":"same-source excluded"}'
    )
    wakeups = resource(IssueWakeupResource, mock_transport)

    assert wakeups.events_command().commands == ("multica issue wakeup events --output json",)
    events = wakeups.events()
    assert events.events[0].name == "comment.created"
    assert events.loop_protection == "same-source excluded"


def test_wakeup_update_is_complete_replacement_and_requires_instruction() -> None:
    mock_transport = transport()
    wakeups = resource(IssueWakeupResource, mock_transport)
    command = wakeups.update_command(
        "iss-1",
        "wake-1",
        instruction="Run checks",
        event_types=("comment.created",),
    )
    assert command.commands == (
        "multica issue wakeup update iss-1 wake-1 --instruction 'Run checks' "
        "--kind event --event comment.created --output json",
    )
    mock_transport.run_bytes.return_value = command_result(b'{"id":"wake-1","enabled":true}')
    assert command.run().enabled is True

    with pytest.raises(TypeError):
        wakeups.update_command("iss-1", "wake-1")  # type: ignore[call-arg]


def test_wakeup_create_retries_only_explicit_busy_once(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_transport = transport()
    mock_transport.run_bytes.side_effect = [
        ConflictError("source is busy", code="wakeup_source_busy"),
        command_result(b'{"id":"wake-1","enabled":true}'),
    ]
    sleeps: list[float] = []
    monkeypatch.setattr("multica_py.resources.issue_wakeups.time.sleep", sleeps.append)
    command = resource(IssueWakeupResource, mock_transport).create_command(
        "iss-1", instruction="Run checks"
    )

    assert command.run().id == "wake-1"
    assert mock_transport.run_bytes.call_count == 2
    assert sleeps == [0.25]


def test_wakeup_busy_retry_is_bounded_and_does_not_retry_other_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_transport = transport()
    busy = ConflictError("source is busy", code="wakeup_source_busy")
    mock_transport.run_bytes.side_effect = [busy, busy]
    monkeypatch.setattr("multica_py.resources.issue_wakeups.time.sleep", lambda _seconds: None)
    command = resource(IssueWakeupResource, mock_transport).create_command(
        "iss-1", instruction="Run checks"
    )

    with pytest.raises(ConflictError):
        command.run()
    assert mock_transport.run_bytes.call_count == 2


def test_wakeup_list_decodes_pagination_and_rejects_bad_rows() -> None:
    mock_transport = transport()
    mock_transport.run_bytes.return_value = command_result(
        b'{"wakeups":[{"id":"wake-1","next_fire_at":"2026-09-27T10:00:00Z"}],'
        b'"total":5,"limit":1,"offset":2,"has_more":true,"next_cursor":"c2"}'
    )
    page = resource(IssueWakeupResource, mock_transport).list("iss-1")
    assert page.total == 5
    assert page.offset == 2
    assert page.has_more is True
    assert page.items[0].next_run_at == datetime.datetime(2026, 9, 27, 10, tzinfo=datetime.UTC)

    mock_transport.run_bytes.return_value = command_result(b'{"wakeups":[null]}')
    with pytest.raises(TypeError, match="items"):
        resource(IssueWakeupResource, mock_transport).list("iss-1")


def test_wakeup_update_rejects_response_that_was_not_reenabled() -> None:
    mock_transport = transport()
    mock_transport.run_bytes.return_value = command_result(b'{"id":"wake-1","enabled":false}')
    command = resource(IssueWakeupResource, mock_transport).update_command(
        "iss-1", "wake-1", instruction="Run checks"
    )

    with pytest.raises(OutputShapeError, match="enabled"):
        command.run()


def test_rotation_requires_confirmation_and_has_exact_argv() -> None:
    mock_transport = transport()
    autopilots = resource(AutopilotResource, mock_transport)
    with pytest.raises(ValueError):
        autopilots.trigger_rotate_url_command("ap-1", "tr-1")
    command = autopilots.trigger_rotate_url_command("ap-1", "tr-1", yes=True)
    assert command.commands == (
        "multica autopilot trigger-rotate-url ap-1 tr-1 --yes --output json",
    )


def test_autopilot_secrets_are_opt_in_on_the_wire() -> None:
    mock_transport = transport()
    autopilots = resource(AutopilotResource, mock_transport)
    assert autopilots.get_command("ap-1").commands == ("multica autopilot get ap-1 --output json",)
    assert autopilots.get_command("ap-1", show_secrets=True).commands == (
        "multica autopilot get ap-1 --show-secrets --output json",
    )


def test_skill_file_content_channels_are_exact_and_mutually_exclusive(tmp_path) -> None:
    mock_transport = transport()
    files = resource(SkillFileResource, mock_transport)
    from_file = files.upsert_command("sk-1", "README.md", content_file=tmp_path / "README.md")
    assert from_file.commands == (
        f"multica skill files upsert sk-1 --path README.md --content-file {tmp_path}/README.md "
        "--output json",
    )
    assert from_file._plan.steps[0].stdin is None
    from_stdin = files.upsert_command("sk-1", "README.md", content_stdin=b"body")
    assert from_stdin.commands == (
        "multica skill files upsert sk-1 --path README.md --content-stdin --output json",
    )
    assert from_stdin._plan.steps[0].stdin == b"body"
    with pytest.raises(TypeError, match="exactly one"):
        files.upsert_command("sk-1", "README.md")
