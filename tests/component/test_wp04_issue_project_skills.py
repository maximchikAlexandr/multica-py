from __future__ import annotations

import datetime
import json
import pathlib
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.exceptions import CommandExecutionError, ValidationError
from multica_py.models.common import Page
from multica_py.models.project_resources import LocalDirectoryResourceRef
from multica_py.resources.project_resources import ProjectResourceCollection
from tests.fixtures.fake_multica import FakeMultica

pytestmark = pytest.mark.component


def test_workflow_resolved_issue_update_keeps_returned_assignee(
    client_factory: Callable[..., MulticaClient], tmp_path: pathlib.Path
) -> None:
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    response = FakeMultica(responses_dir=responses_dir).build_response(
        stdout=(
            '{"id":"issue-1","title":"Resolved","status":"todo",'
            '"assignee":{"id":"agent-7","name":"Agent Seven","type":"agent"}}'
        ),
        argv=(
            "fake_multica",
            "issue",
            "update",
            "issue-1",
            "--title",
            "Resolved",
            "--output",
            "json",
        ),
    )
    (responses_dir / "issue.json").write_text(json.dumps(response.to_dict()), encoding="utf-8")
    client = client_factory(environment=(("MULTICA_FAKE_RESPONSES", str(responses_dir)),))

    updated = client.issues.update("issue-1", title="Resolved")

    assert updated.assignee is not None
    assert (updated.assignee.id, updated.assignee.type) == ("agent-7", "agent")


def test_concurrent_project_resource_updates_decode_merged_state_and_keep_presence() -> None:
    merged_response = msgspec.json.encode(
        {
            "id": "resource-1",
            "project_id": "project-1",
            "resource_type": "local_directory",
            "resource_ref": {
                "local_path": "/work/project",
                "daemon_id": "daemon-new",
                "execution_mode": "workspace",
            },
            "label": None,
            "position": 4,
        }
    )
    transport = MagicMock(spec=CliTransport)
    transport._snapshot.return_value = transport
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    calls: list[tuple[str, ...]] = []
    interleave = threading.Barrier(2)

    def execute(argv: tuple[str, ...], **_: object) -> RawCommandResult:
        calls.append(argv)
        interleave.wait(timeout=5)
        return RawCommandResult(
            argv=("multica", *argv),
            exit_code=0,
            stdout=merged_response,
            stderr=b"",
            duration=datetime.timedelta(),
        )

    transport.run_bytes.side_effect = execute
    resources = ProjectResourceCollection(transport, ClientConfig())

    with ThreadPoolExecutor(max_workers=2) as executor:
        clear_label = executor.submit(
            resources.update,
            "project-1",
            "resource-1",
            clear_label=True,
        )
        update_daemon = executor.submit(
            resources.update,
            "project-1",
            "resource-1",
            daemon_id="daemon-new",
        )
        results = (clear_label.result(timeout=8), update_daemon.result(timeout=8))

    assert len(results) == 2
    for result in results:
        assert result.label is None
        assert result.position == 4
        assert isinstance(result.resource_ref, LocalDirectoryResourceRef)
        assert result.resource_ref.daemon_id == "daemon-new"
        assert result.resource_ref.execution_mode == "workspace"
    assert sorted(calls) == sorted(
        (
            (
                "project",
                "resource",
                "update",
                "project-1",
                "resource-1",
                "--clear-label",
                "--output",
                "json",
            ),
            (
                "project",
                "resource",
                "update",
                "project-1",
                "resource-1",
                "--daemon-id",
                "daemon-new",
                "--output",
                "json",
            ),
        )
    )


def _write_skill_response(
    fake: FakeMultica,
    responses_dir: pathlib.Path,
    *,
    stdout: str = "",
    stderr: str = "",
    exit_code: int = 0,
) -> None:
    response = fake.build_response(
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        argv=("fake_multica", "skill"),
    )
    (responses_dir / "skill.json").write_text(json.dumps(response.to_dict()), encoding="utf-8")


@pytest.mark.parametrize(
    "status, expected_error, expected_exit",
    (
        (400, ValidationError, 5),
        (413, CommandExecutionError, 1),
        (502, CommandExecutionError, 1),
        (503, CommandExecutionError, 1),
        (504, CommandExecutionError, 1),
    ),
    ids=("bad-request", "too-large", "bad-gateway", "unavailable", "timeout"),
)
def test_skill_refresh_remote_failures_keep_typed_error_and_existing_portable_files(
    client_factory: Callable[..., MulticaClient],
    tmp_path: pathlib.Path,
    status: int,
    expected_error: type[CommandExecutionError],
    expected_exit: int,
) -> None:
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    fake = FakeMultica(responses_dir=responses_dir)
    existing_bundle = [
        {"id": "file-1", "path": "SKILL.md", "content": "old instructions"},
        {"id": "file-2", "path": "references/guide.md", "content": "old guide"},
    ]
    _write_skill_response(
        fake,
        responses_dir,
        stdout=json.dumps({"id": "skill-1", "name": "example", "file_count": 2}),
    )
    client = client_factory(environment=(("MULTICA_FAKE_RESPONSES", str(responses_dir)),))
    imported = client.skills.import_from_url("https://example.test/skill")
    assert imported.id == "skill-1"
    _write_skill_response(fake, responses_dir, stdout=json.dumps(existing_bundle))
    before = client.skills.files.list("skill-1", with_content=True)

    _write_skill_response(
        fake,
        responses_dir,
        stderr=f"Error: GET /api/skills/skill-1/refresh returned {status}: remote failure",
        exit_code=1,
    )
    with pytest.raises(expected_error) as excinfo:
        client.skills.refresh("skill-1")
    assert excinfo.value.exit_code == expected_exit
    assert str(status) in excinfo.value.stderr
    assert tuple((file.path, file.content) for file in before.items) == (
        ("SKILL.md", "old instructions"),
        ("references/guide.md", "old guide"),
    )


@pytest.mark.parametrize(
    "path",
    ("../escape.md", "/absolute/escape.md", "C:\\escape.md", "\\\\server\\share\\escape.md"),
    ids=("traversal", "absolute", "drive-path", "unc-path"),
)
def test_skill_refresh_path_rejection_preserves_existing_readable_snapshot(
    client_factory: Callable[..., MulticaClient],
    tmp_path: pathlib.Path,
    path: str,
) -> None:
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    fake = FakeMultica(responses_dir=responses_dir)
    old_bundle = [
        {"id": "file-1", "path": "SKILL.md", "content": "stable instructions"},
    ]
    _write_skill_response(fake, responses_dir, stdout=json.dumps(old_bundle))
    client = client_factory(environment=(("MULTICA_FAKE_RESPONSES", str(responses_dir)),))
    existing = client.skills.files.list("skill-1", with_content=True)

    _write_skill_response(
        fake,
        responses_dir,
        stderr=(
            "Error: GET /api/skills/skill-1/refresh returned 400: "
            f'{{"error":"non-portable path: {path}"}}'
        ),
        exit_code=1,
    )
    with pytest.raises(ValidationError) as excinfo:
        client.skills.refresh("skill-1")
    assert "400" in excinfo.value.stderr

    assert tuple((file.path, file.content) for file in existing.items) == (
        ("SKILL.md", "stable instructions"),
    )


def test_skill_bundle_decodes_complete_portable_text_files_without_binary_payload(
    client_factory: Callable[..., MulticaClient], tmp_path: pathlib.Path
) -> None:
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    bundle = [
        {"id": "file-1", "path": "SKILL.md", "content": "instructions"},
        {"id": "file-2", "path": "references/guide.md", "content": "guide"},
        {"id": "file-3", "path": "scripts/run.py", "content": "print('ok')"},
    ]
    fake = FakeMultica(responses_dir=responses_dir)
    _write_skill_response(
        fake,
        responses_dir,
        stdout=json.dumps({"id": "skill-1", "name": "portable", "file_count": 3}),
    )
    client = client_factory(environment=(("MULTICA_FAKE_RESPONSES", str(responses_dir)),))

    imported = client.skills.import_from_url("https://example.test/portable-skill")
    assert imported.id == "skill-1"
    _write_skill_response(fake, responses_dir, stdout=json.dumps(bundle))
    files = client.skills.files.list("skill-1", with_content=True)

    assert isinstance(files, Page)
    assert tuple(file.path for file in files.items) == (
        "SKILL.md",
        "references/guide.md",
        "scripts/run.py",
    )
    assert tuple(file.content for file in files.items) == ("instructions", "guide", "print('ok')")
    assert all(not file.path.endswith(".bin") for file in files.items)
