from __future__ import annotations

import datetime
import pathlib
from collections.abc import Iterator
from contextlib import contextmanager

import msgspec

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.wire_models import _ProjectResourceRecordWire, project_resource_from_wire
from multica_py.config import ClientConfig
from multica_py.execution import LocalExecutor
from multica_py.models.project_resources import GithubRepoResourceRef
from multica_py.models.system import (
    AttachmentDownloadResult,
    AttachmentResult,
    DaemonAggregateDiskUsageReport,
    DaemonStatus,
    DaemonWorkspace,
    SquadMember,
    SquadMemberRemoval,
)
from multica_py.resources.attachments import AttachmentResource
from multica_py.resources.auth import AuthResource
from multica_py.resources.daemon import DaemonResource
from multica_py.resources.squad_members import SquadMemberResource
from tests.unit.resources._factories import make_transport


class _FixedStageExecutor(LocalExecutor):
    def __init__(self, path: pathlib.Path) -> None:
        self._path = path

    @contextmanager
    def stage(self, _label: str, content: bytes) -> Iterator[str]:
        self._path.write_bytes(content)
        try:
            yield str(self._path)
        finally:
            self._path.unlink(missing_ok=True)


def test_attachment_upload_and_download_use_source_argv(tmp_path: pathlib.Path) -> None:
    source = tmp_path / "file.txt"
    source.write_bytes(b"payload")
    staged_path = tmp_path / "staged-upload.bin"
    expected_upload_argv = ("attachment", "upload", str(staged_path))
    transport = make_transport(
        stdout={"id": "a1", "filename": "file.txt", "markdown_url": "url", "markdown": "md"}
    )
    transport.executor = _FixedStageExecutor(staged_path)

    def complete(argv: tuple[str, ...], **_kwargs: object) -> RawCommandResult:
        assert argv == expected_upload_argv
        assert staged_path.read_bytes() == source.read_bytes()
        return RawCommandResult(
            argv=expected_upload_argv,
            exit_code=0,
            stdout=msgspec.json.encode(
                {"id": "a1", "filename": "file.txt", "markdown_url": "url", "markdown": "md"}
            ),
            stderr=b"",
            duration=datetime.timedelta(),
        )

    transport.run_bytes.side_effect = complete
    resource = AttachmentResource(transport, ClientConfig())

    uploaded = resource.upload(source)

    assert uploaded == AttachmentResult(
        id="a1", filename="file.txt", markdown_url="url", markdown="md"
    )
    transport.run_bytes.assert_called_once_with(
        expected_upload_argv,
        stdin=None,
        timeout=None,
    )

    transport.run_bytes.side_effect = None
    transport.run_bytes.return_value = RawCommandResult(
        argv=(),
        exit_code=0,
        stdout=msgspec.json.encode(
            {"id": "a1", "filename": "file.txt", "path": str(tmp_path / "file.txt"), "size": "7"}
        ),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    transport.run_bytes.reset_mock()
    downloaded = resource.download("a1", output_dir=tmp_path)
    assert downloaded == AttachmentDownloadResult(
        id="a1", filename="file.txt", path=str(tmp_path / "file.txt"), size="7"
    )
    transport.run_bytes.assert_called_once_with(
        (
            "attachment",
            "download",
            "a1",
            "--output-dir",
            str(tmp_path.resolve()),
        ),
        stdin=None,
        timeout=None,
    )


def test_auth_status_is_text_and_logout_does_not_request_json() -> None:
    transport = make_transport(stdout={}, text="Authenticated as User (user@example.com)")
    resource = AuthResource(transport, ClientConfig())

    assert resource.status() == "Authenticated as User (user@example.com)"
    transport.run_text.assert_called_once_with(("auth", "status"))
    transport.run_text.reset_mock()

    result = resource.logout()
    assert result.success
    transport.run_text.assert_called_once_with(("auth", "logout"))


def test_daemon_health_and_disk_usage_shapes() -> None:
    transport = make_transport(
        stdout={
            "status": "running",
            "pid": 42,
            "uptime": "1m",
            "workspaces": [{"id": "ws1", "runtimes": ["rt1"]}],
        }
    )
    resource = DaemonResource(transport, ClientConfig())
    status = resource.status()
    assert status == DaemonStatus(
        status="running",
        pid=42,
        uptime="1m",
        workspaces=(DaemonWorkspace(id="ws1", runtimes=("rt1",)),),
    )
    transport.run_bytes.assert_called_once_with(
        ("daemon", "status", "--output", "json"),
        stdin=None,
        timeout=None,
    )
    transport.run_bytes.reset_mock()

    transport.run_bytes.return_value = RawCommandResult(
        argv=(),
        exit_code=0,
        stdout=msgspec.json.encode(
            {
                "generated_at": "2026-09-26T00:00:00Z",
                "artifact_patterns": [],
                "managed_artifact_subpaths": [],
                "roots": [],
            }
        ),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    report = resource.disk_usage(all_profiles=True)
    assert isinstance(report, DaemonAggregateDiskUsageReport)
    transport.run_bytes.assert_called_once_with(
        (
            "daemon",
            "disk-usage",
            "--all-profiles",
            "--output",
            "json",
        ),
        stdin=None,
        timeout=None,
    )


def test_squad_member_add_remove_use_flagged_request_fields() -> None:
    transport = make_transport(stdout={"member_id": "a1", "member_type": "agent", "role": "worker"})
    resource = SquadMemberResource(transport, ClientConfig())

    member = resource.add("s1", member_id="a1", member_type="agent", role="worker")
    assert member == SquadMember(member_id="a1", member_type="agent", role="worker")
    transport.run_bytes.assert_called_once_with(
        (
            "squad",
            "member",
            "add",
            "s1",
            "--member-id",
            "a1",
            "--type",
            "agent",
            "--role",
            "worker",
            "--output",
            "json",
        ),
        stdin=None,
        timeout=None,
    )
    transport.run_bytes.reset_mock()

    transport.run_bytes.return_value = RawCommandResult(
        argv=(),
        exit_code=0,
        stdout=msgspec.json.encode({"squad_id": "s1", "member_id": "a1", "removed": True}),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    removed = resource.remove("s1", member_id="a1", member_type="agent")
    assert removed == SquadMemberRemoval(squad_id="s1", member_id="a1", removed=True)
    transport.run_bytes.assert_called_once_with(
        (
            "squad",
            "member",
            "remove",
            "s1",
            "--member-id",
            "a1",
            "--type",
            "agent",
            "--output",
            "json",
        ),
        stdin=None,
        timeout=None,
    )


def test_project_resource_conversion_preserves_supported_variants() -> None:
    github = project_resource_from_wire(
        _ProjectResourceRecordWire(
            id="r1",
            project_id="p1",
            resource_type="github_repo",
            resource_ref={"url": "https://github.com/acme/repo", "ref": "main"},
        )
    )
    assert github.resource_ref == GithubRepoResourceRef(
        url="https://github.com/acme/repo", ref="main"
    )

    custom = project_resource_from_wire(
        _ProjectResourceRecordWire(
            id="r2",
            project_id="p1",
            resource_type="custom",
            resource_ref={"endpoint": "https://example.test", "options": {"x": True}},
        )
    )
    assert custom.resource_ref == {
        "endpoint": "https://example.test",
        "options": {"x": True},
    }
