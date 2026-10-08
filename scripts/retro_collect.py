"""Collect issue-bound Multica runs for a read-only coding-session retrospective.

The output can contain secrets from tool calls. Keep it local and private.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

from multica_py import MulticaClient

if TYPE_CHECKING:
    from collections.abc import Iterator

    from multica_py.entities.issues import Issue, TaskRun

UTC = dt.UTC


def parse_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("time must include a UTC offset")
    return parsed.astimezone(UTC)


def plain_json(value: object) -> object:
    """Turn the SDK's immutable JSON snapshots into standard JSON containers."""
    if isinstance(value, Mapping):
        return {str(key): plain_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain_json(item) for item in value]
    return value


def issues_in_project(client: MulticaClient, project_id: str) -> Iterator[Issue]:
    offset = 0
    while True:
        page = client.issues.list(
            project_id=project_id,
            limit=100,
            offset=offset,
            fields=("id", "identifier", "title", "project_id"),
        )
        yield from page.items
        if not page.has_more:
            return
        if not page.items:
            raise RuntimeError(f"issue pagination stalled for project {project_id}")
        offset += len(page.items)


def completed_in_window(run: TaskRun, since: dt.datetime, until: dt.datetime) -> bool:
    completed = run.completed_at
    return completed is not None and since <= completed.astimezone(UTC) < until


def local_session(run: TaskRun) -> dict[str, str | int]:
    """Find the primary Codex rollout beside this run's workdir, if retained."""
    result = run.result if isinstance(run.result, Mapping) else {}
    session_id = result.get("session_id")
    work_dir = run.work_dir or result.get("work_dir")
    if not isinstance(session_id, str) or not isinstance(work_dir, str):
        return {"status": "unavailable"}
    try:
        uuid.UUID(session_id)
    except ValueError:
        return {"status": "invalid_session_id"}
    sessions = Path(work_dir).parent / "codex-home" / "sessions"
    matches = list(sessions.glob(f"*/*/*/*-{session_id}.jsonl"))
    verified: list[Path] = []
    for path in matches:
        try:
            with path.open(encoding="utf-8") as stream:
                header = json.loads(stream.readline())
            if (
                header.get("type") == "session_meta"
                and header.get("payload", {}).get("id") == session_id
            ):
                verified.append(path)
        except (OSError, ValueError, AttributeError):
            continue
    if len(verified) != 1:
        return {"status": "missing" if not verified else "ambiguous"}
    return {"status": "found", "path": str(verified[0]), "bytes": verified[0].stat().st_size}


def collect(
    client: MulticaClient,
    project_ids: list[str],
    since: dt.datetime,
    until: dt.datetime,
    *,
    issue_key: str | None = None,
) -> dict[str, object]:
    if since >= until:
        raise ValueError("since must be earlier than until")
    projects: list[dict[str, object]] = []
    seen_runs: set[str] = set()
    matched_issues = 0
    for project_id in dict.fromkeys(project_ids):
        selected: list[dict[str, object]] = []
        issue_count = 0
        for issue in issues_in_project(client, project_id):
            if issue_key and issue.identifier != issue_key:
                continue
            issue_count += 1
            matched_issues += 1
            page = client.issues.runs(issue.id)
            if page.has_more:
                raise RuntimeError(f"run history was truncated for {issue.identifier}")
            for run in page.items:
                if run.id in seen_runs or not completed_in_window(run, since, until):
                    continue
                seen_runs.add(run.id)
                messages = client.issues.run_messages(run.id, issue_id=issue.id).items
                selected.append(
                    {
                        "run_id": run.id,
                        "issue_id": issue.id,
                        "issue_key": issue.identifier,
                        "issue_title": issue.title,
                        "agent_id": run.agent_id,
                        "status": run.status,
                        "started_at": run.started_at.isoformat() if run.started_at else None,
                        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                        "session_id": (
                            run.result.get("session_id")
                            if isinstance(run.result, Mapping)
                            else None
                        ),
                        "local_session": local_session(run),
                        "messages": [
                            {
                                "seq": message.seq,
                                "type": message.type,
                                "tool": message.tool,
                                "content": message.content,
                                "input": plain_json(message.input),
                                "output": message.output,
                                "output_truncated": message.output_truncated,
                            }
                            for message in messages
                        ],
                    }
                )
        selected.sort(key=lambda item: (parse_time(str(item["completed_at"])), str(item["run_id"])))
        projects.append({"project_id": project_id, "issues_scanned": issue_count, "runs": selected})
    if issue_key and not matched_issues:
        raise ValueError(f"issue {issue_key} was not found in the selected projects")
    return {"since": since.isoformat(), "until": until.isoformat(), "projects": projects}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-id", action="append", required=True, help="Repeat for each project"
    )
    parser.add_argument("--days", type=int, default=3, help="Completed-run window (default: 3)")
    parser.add_argument("--until", type=parse_time, help="Exclusive UTC end; default: now")
    parser.add_argument("--issue", help="Limit a smoke test to one issue key")
    parser.add_argument("--output", type=Path, required=True, help="New private JSON file")
    args = parser.parse_args()
    if args.days < 1:
        parser.error("--days must be positive")
    until = args.until or dt.datetime.now(UTC)
    data = collect(
        MulticaClient(),
        args.project_id,
        until - dt.timedelta(days=args.days),
        until,
        issue_key=args.issue,
    )
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
