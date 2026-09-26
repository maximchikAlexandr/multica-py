from __future__ import annotations

import datetime
import pathlib
from unittest.mock import MagicMock

import msgspec

from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.wire_models import _ProjectResourceRecordWire, project_resource_from_wire
from multica_py.config import ClientConfig
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


def _transport(stdout: object, *, text: str = "") -> MagicMock:
    transport = MagicMock()
    payload = stdout if isinstance(stdout, bytes) else msgspec.json.encode(stdout)
    transport.run_bytes.return_value = RawCommandResult(
        argv=(), exit_code=0, stdout=payload, stderr=b"", duration=datetime.timedelta()
    )
    transport.run_text.return_value = TextResult(text=text, stderr="", exit_code=0)
    return transport


def test_attachment_upload_and_download_use_source_argv(tmp_path: pathlib.Path) -> None:
    source = tmp_path / "file.txt"
    source.write_bytes(b"payload")
    transport = _transport(
        {"id": "a1", "filename": "file.txt", "markdown_url": "url", "markdown": "md"}
    )
    resource = AttachmentResource(transport, ClientConfig())

    uploaded = resource.upload(source)

    assert uploaded == AttachmentResult(
        id="a1", filename="file.txt", markdown_url="url", markdown="md"
    )
    upload_argv = transport.run_bytes.call_args.args[0]
    assert upload_argv[:2] == ("attachment", "upload")
    assert upload_argv[2]
    assert "--output" not in upload_argv

    transport.run_bytes.return_value = RawCommandResult(
        argv=(),
        exit_code=0,
        stdout=msgspec.json.encode(
            {"id": "a1", "filename": "file.txt", "path": str(tmp_path / "file.txt"), "size": "7"}
        ),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    downloaded = resource.download("a1", output_dir=tmp_path)
    assert downloaded == AttachmentDownloadResult(
        id="a1", filename="file.txt", path=str(tmp_path / "file.txt"), size="7"
    )
    assert transport.run_bytes.call_args.args[0] == (
        "attachment",
        "download",
        "a1",
        "--output-dir",
        str(tmp_path.resolve()),
    )


def test_auth_status_is_text_and_logout_does_not_request_json() -> None:
    transport = _transport({}, text="Authenticated as User (user@example.com)")
    resource = AuthResource(transport, ClientConfig())

    assert resource.status() == "Authenticated as User (user@example.com)"
    assert transport.run_text.call_args.args[0] == ("auth", "status")

    result = resource.logout()
    assert result.success
    assert transport.run_text.call_args.args[0] == ("auth", "logout")


def test_daemon_health_and_disk_usage_shapes() -> None:
    transport = _transport(
        {
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
    assert transport.run_bytes.call_args.args[0] == (
        "daemon",
        "disk-usage",
        "--all-profiles",
        "--output",
        "json",
    )


def test_squad_member_add_remove_use_flagged_request_fields() -> None:
    transport = _transport({"member_id": "a1", "member_type": "agent", "role": "worker"})
    resource = SquadMemberResource(transport, ClientConfig())

    member = resource.add("s1", member_id="a1", member_type="agent", role="worker")
    assert member == SquadMember(member_id="a1", member_type="agent", role="worker")
    assert transport.run_bytes.call_args.args[0] == (
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
    )

    transport.run_bytes.return_value = RawCommandResult(
        argv=(),
        exit_code=0,
        stdout=msgspec.json.encode({"squad_id": "s1", "member_id": "a1", "removed": True}),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    removed = resource.remove("s1", member_id="a1", member_type="agent")
    assert removed == SquadMemberRemoval(squad_id="s1", member_id="a1", removed=True)


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
