from __future__ import annotations

import datetime
import json
import ntpath
import pathlib
import threading
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.exceptions import CommandExecutionError, OutputShapeError, ValidationError
from multica_py.models.common import Page
from multica_py.models.project_resources import LocalDirectoryResourceRef
from multica_py.resources.project_resources import ProjectResourceCollection
from tests.component.conftest import patch_client_transport
from tests.fixtures.fake_multica import FakeMultica

pytestmark = pytest.mark.component


@dataclass(frozen=True)
class SkillRefreshFailureCase:
    id: str
    status: int
    expected_error: type[CommandExecutionError]
    expected_exit: int


_SKILL_REFRESH_FAILURE_CASES = (
    SkillRefreshFailureCase("bad-request", 400, ValidationError, 5),
    SkillRefreshFailureCase("too-large", 413, CommandExecutionError, 1),
    SkillRefreshFailureCase("bad-gateway", 502, CommandExecutionError, 1),
    SkillRefreshFailureCase("unavailable", 503, CommandExecutionError, 1),
    SkillRefreshFailureCase("timeout", 504, CommandExecutionError, 1),
)


@dataclass(frozen=True)
class UnsafeSkillPathCase:
    id: str
    path: str


_UNSAFE_SKILL_PATH_CASES = (
    UnsafeSkillPathCase("traversal", "../escape.md"),
    UnsafeSkillPathCase("absolute", "/absolute/escape.md"),
    UnsafeSkillPathCase("drive-path", "C:\\escape.md"),
    UnsafeSkillPathCase("unc-path", "\\\\server\\share\\escape.md"),
)


class ControlledSkillStore:
    """In-memory remote bundle state reached through public SDK calls."""

    def __init__(self, files: Sequence[Mapping[str, object]]) -> None:
        self.files = {str(item["path"]): dict(item) for item in files}
        self.refresh_candidate: Sequence[Mapping[str, object]] | None = None
        self.refresh_attempts = 0
        self.refresh_error: CommandExecutionError | None = None

    def run_bytes(self, argv: tuple[str, ...], **_: object) -> RawCommandResult:
        stdout: bytes
        if argv[:3] == ("skill", "files", "list"):
            stdout = json.dumps(tuple(self.files.values())).encode()
        elif argv[:2] == ("skill", "refresh"):
            self.refresh_attempts += 1
            if self.refresh_error is not None:
                raise self.refresh_error
            if self.refresh_candidate is not None:
                candidate = {str(item["path"]): dict(item) for item in self.refresh_candidate}
                if any(
                    pathlib.PurePosixPath(path).is_absolute()
                    or ntpath.isabs(path)
                    or ".." in pathlib.PurePosixPath(path).parts
                    for path in candidate
                ):
                    raise ValidationError(
                        "unsafe skill path",
                        exit_code=5,
                        stderr="Error: GET /api/skills/skill-1/refresh returned 400: non-portable path",
                    )
                self.files = candidate
            stdout = json.dumps(
                {"id": "skill-1", "name": "refreshed", "file_count": len(self.files)}
            ).encode()
        else:
            raise AssertionError(f"unexpected SDK command: {argv!r}")
        return RawCommandResult(
            argv=("multica", *argv),
            exit_code=0,
            stdout=stdout,
            stderr=b"",
            duration=datetime.timedelta(),
        )


def _client_with_skill_store(
    client_factory: Callable[..., MulticaClient], store: ControlledSkillStore
) -> tuple[MulticaClient, MagicMock]:
    client = client_factory()
    transport = MagicMock(spec=CliTransport)
    transport.run_bytes.side_effect = store.run_bytes
    patch_client_transport(client, transport)
    return client, transport


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


@pytest.mark.parametrize("case", _SKILL_REFRESH_FAILURE_CASES, ids=lambda case: case.id)
def test_skill_refresh_remote_failures_keep_typed_error(
    client_factory: Callable[..., MulticaClient],
    tmp_path: pathlib.Path,
    case: SkillRefreshFailureCase,
) -> None:
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    fake = FakeMultica(responses_dir=responses_dir)
    _write_skill_response(
        fake,
        responses_dir,
        stdout=json.dumps({"id": "skill-1", "name": "example", "file_count": 2}),
    )
    client = client_factory(environment=(("MULTICA_FAKE_RESPONSES", str(responses_dir)),))
    imported = client.skills.import_from_url("https://example.test/skill")
    assert imported.id == "skill-1"

    _write_skill_response(
        fake,
        responses_dir,
        stderr=f"Error: GET /api/skills/skill-1/refresh returned {case.status}: remote failure",
        exit_code=1,
    )
    with pytest.raises(case.expected_error) as excinfo:
        client.skills.refresh("skill-1")
    assert excinfo.value.exit_code == case.expected_exit
    assert str(case.status) in excinfo.value.stderr


@pytest.mark.parametrize("case", _SKILL_REFRESH_FAILURE_CASES, ids=lambda case: case.id)
def test_failed_remote_refresh_keeps_the_same_bundle_readable(
    client_factory: Callable[..., MulticaClient],
    case: SkillRefreshFailureCase,
) -> None:
    original = (
        {"id": "file-1", "path": "SKILL.md", "content": "persisted instructions"},
        {"id": "file-2", "path": "references/guide.md", "content": "persisted guide"},
    )
    store = ControlledSkillStore(original)
    store.refresh_error = case.expected_error(
        "remote failure",
        exit_code=case.expected_exit,
        stderr=f"Error: GET /api/skills/skill-1/refresh returned {case.status}: unavailable",
    )
    client, transport = _client_with_skill_store(client_factory, store)

    before = client.skills.files.list("skill-1", with_content=True)
    with pytest.raises(case.expected_error, match="remote failure") as excinfo:
        client.skills.refresh("skill-1")
    after = client.skills.files.list("skill-1", with_content=True)

    assert tuple((file.path, file.content) for file in before.items) == (
        ("SKILL.md", "persisted instructions"),
        ("references/guide.md", "persisted guide"),
    )
    assert tuple((file.path, file.content) for file in after.items) == (
        ("SKILL.md", "persisted instructions"),
        ("references/guide.md", "persisted guide"),
    )
    assert store.refresh_attempts == 1
    assert excinfo.value.exit_code == case.expected_exit
    assert str(case.status) in excinfo.value.stderr
    assert transport.run_bytes.call_args_list[1].args[0] == (
        "skill",
        "refresh",
        "skill-1",
        "--output",
        "json",
    )


@pytest.mark.parametrize("case", _UNSAFE_SKILL_PATH_CASES, ids=lambda case: case.id)
def test_skill_refresh_path_rejection_preserves_existing_readable_snapshot(
    client_factory: Callable[..., MulticaClient],
    case: UnsafeSkillPathCase,
) -> None:
    store = ControlledSkillStore(
        ({"id": "file-1", "path": "SKILL.md", "content": "stable instructions"},)
    )
    store.refresh_candidate = (
        {"id": "file-2", "path": "references/new.md", "content": "new file"},
        {"id": "file-bad", "path": case.path, "content": "unsafe"},
    )
    client, transport = _client_with_skill_store(client_factory, store)

    with pytest.raises(ValidationError) as excinfo:
        client.skills.refresh("skill-1")
    assert "400" in excinfo.value.stderr
    assert store.refresh_attempts == 1
    assert transport.run_bytes.call_args_list[0].args[0] == (
        "skill",
        "refresh",
        "skill-1",
        "--output",
        "json",
    )
    after = client.skills.files.list("skill-1", with_content=True)
    assert tuple((file.path, file.content) for file in after.items) == (
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
    returned_paths = {file.path for file in files.items}
    assert returned_paths == {"SKILL.md", "references/guide.md", "scripts/run.py"}


def test_skill_file_list_rejects_binary_content_at_public_boundary(
    client_factory: Callable[..., MulticaClient],
) -> None:
    store = ControlledSkillStore(
        (
            {
                "id": "binary-1",
                "path": "assets/logo.png",
                "kind": "binary",
                "content": {"encoding": "base64", "data": "iVBORw0KGgo="},
            },
        )
    )
    client, transport = _client_with_skill_store(client_factory, store)

    with pytest.raises(OutputShapeError):
        client.skills.files.list("skill-1", with_content=True)

    assert transport.run_bytes.call_args.args[0] == (
        "skill",
        "files",
        "list",
        "skill-1",
        "--with-content",
        "--output",
        "json",
    )


def test_successful_skill_refresh_replaces_the_entire_bundle(
    client_factory: Callable[..., MulticaClient],
) -> None:
    old_bundle = (
        {"id": "old-1", "path": "SKILL.md", "content": "old instructions"},
        {"id": "old-2", "path": "references/old.md", "content": "old reference"},
    )
    new_bundle = (
        {"id": "new-1", "path": "SKILL.md", "content": "new instructions"},
        {"id": "new-2", "path": "references/new.md", "content": "new reference"},
        {"id": "new-3", "path": "scripts/new.py", "content": "print('new')"},
    )
    store = ControlledSkillStore(old_bundle)
    store.refresh_candidate = new_bundle
    client, transport = _client_with_skill_store(client_factory, store)
    before = client.skills.files.list("skill-1", with_content=True)
    assert tuple(file.path for file in before.items) == ("SKILL.md", "references/old.md")

    refreshed = client.skills.refresh("skill-1")
    assert refreshed.name == "refreshed"

    after = client.skills.files.list("skill-1", with_content=True)
    assert tuple((file.path, file.content) for file in after.items) == (
        ("SKILL.md", "new instructions"),
        ("references/new.md", "new reference"),
        ("scripts/new.py", "print('new')"),
    )
    assert {file.path for file in after.items}.isdisjoint({"references/old.md"})
    assert store.refresh_attempts == 1
    assert transport.run_bytes.call_args_list[1].args[0] == (
        "skill",
        "refresh",
        "skill-1",
        "--output",
        "json",
    )
