from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

from multica_py import MulticaClient
from multica_py.entities.issues import TaskRun
from scripts.retro_collect import collect, completed_in_window, local_session, plain_json


def test_completed_run_window_is_half_open() -> None:
    start = dt.datetime(2026, 10, 5, tzinfo=dt.UTC)
    end = start + dt.timedelta(days=3)
    assert completed_in_window(
        TaskRun(id="run-1", status="completed", completed_at=start), start, end
    )
    assert not completed_in_window(
        TaskRun(id="run-2", status="completed", completed_at=end), start, end
    )
    assert completed_in_window(TaskRun(id="run-3", status="failed", completed_at=start), start, end)
    assert not completed_in_window(TaskRun(id="run-4", status="running"), start, end)


def test_local_session_matches_codex_metadata(tmp_path: Path) -> None:
    session_id = "01a10ccf-ee9f-7ef0-99c4-56fbffe04e6b"
    root = tmp_path / "task"
    sessions = root / "codex-home" / "sessions" / "2026" / "10" / "05"
    sessions.mkdir(parents=True)
    rollout = sessions / f"rollout-2026-10-05T19-05-16-{session_id}.jsonl"
    rollout.write_text(
        json.dumps({"type": "session_meta", "payload": {"id": session_id}}) + "\n",
        encoding="utf-8",
    )
    run = TaskRun(
        id="run-1",
        status="completed",
        work_dir=str(root / "workdir"),
        result={"session_id": session_id},
    )
    assert local_session(run)["status"] == "found"
    rollout.write_text(
        json.dumps({"type": "session_meta", "payload": {"id": "other"}}) + "\n",
        encoding="utf-8",
    )
    assert local_session(run) == {"status": "missing"}


def test_collect_uses_run_completion_and_preserves_messages() -> None:
    client = MagicMock()
    issue = SimpleNamespace(id="issue-1", identifier="MYL-1", title="Example")
    client.issues.list.return_value = SimpleNamespace(items=(issue,), has_more=False)
    start = dt.datetime(2026, 10, 5, tzinfo=dt.UTC)
    end = start + dt.timedelta(days=3)
    old = TaskRun(id="old", status="completed", completed_at=start - dt.timedelta(seconds=1))
    recent = TaskRun(id="new", status="completed", completed_at=start, result={})
    client.issues.runs.return_value = SimpleNamespace(items=(old, recent), has_more=False)
    client.issues.run_messages.return_value = SimpleNamespace(
        items=(
            SimpleNamespace(
                seq=1,
                type="tool_use",
                tool="exec",
                content=None,
                input=MappingProxyType({"nested": MappingProxyType({"ok": True})}),
                output=None,
                output_truncated=False,
            ),
        )
    )

    result = collect(cast("MulticaClient", client), ["project-1"], start, end)

    project = cast("list[dict[str, object]]", result["projects"])[0]
    runs = cast("list[dict[str, object]]", project["runs"])
    assert [run["run_id"] for run in runs] == ["new"]
    assert cast("list[dict[str, object]]", runs[0]["messages"])[0]["input"] == {
        "nested": {"ok": True}
    }
    client.issues.run_messages.assert_called_once_with("new", issue_id="issue-1")
    assert plain_json(MappingProxyType({"x": (1, 2)})) == {"x": [1, 2]}
