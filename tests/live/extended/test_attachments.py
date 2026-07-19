from __future__ import annotations

import pathlib
from collections.abc import Callable

import pytest

from multica_py.client import MulticaClient
from multica_py.models.issues import IssueCreateRequest
from tests.live.oracle import DirectApiOracle

pytestmark = [pytest.mark.live, pytest.mark.live_extended]

ATTACHMENT_PAYLOAD = b"\x00\xff" * 512
EDGE_FILENAMES = ("empty.bin", "file name.bin", "файл.bin")


def test_attachment_round_trip_for_pinned_payload(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    resource_name: str,
    tmp_path: pathlib.Path,
) -> None:
    """Upload, verify metadata, download SHA-256, and delete a 1024-byte attachment."""
    issue = live_client.issues.create(IssueCreateRequest(title=f"{resource_name}-attachment"))
    register_resource(
        key=f"issue-{issue.id}",
        cleanup=api_oracle.delete_callback(f"/api/issues/{issue.id}", "issue"),
    )
    payload_path = tmp_path / "payload.bin"
    payload_path.write_bytes(ATTACHMENT_PAYLOAD)
    uploaded = live_client.attachments.upload(issue.id, str(payload_path))
    register_resource(
        key=f"attachment-{uploaded.id}",
        cleanup=api_oracle.delete_callback(f"/api/attachments/{uploaded.id}", "attachment"),
    )
    metadata = api_oracle.get_attachment(uploaded.id)
    assert metadata.get("id") == uploaded.id
    downloaded = api_oracle.download_attachment_content(uploaded.id)
    assert DirectApiOracle.sha256_hex(downloaded) == DirectApiOracle.sha256_hex(ATTACHMENT_PAYLOAD)
    listed = api_oracle.list_issue_attachments(issue.id)
    listed_ids = {
        entry.get("id")
        for entry in listed
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    assert uploaded.id in listed_ids
    api_oracle.delete(f"/api/attachments/{uploaded.id}")
    api_oracle.assert_absent(f"/api/attachments/{uploaded.id}", "attachment")


@pytest.mark.parametrize("filename", EDGE_FILENAMES)
def test_attachment_edge_filenames_are_supported(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    resource_name: str,
    tmp_path: pathlib.Path,
    filename: str,
) -> None:
    """Upload edge-case filenames and fail when attachments are unsupported on the pinned target."""
    issue = live_client.issues.create(IssueCreateRequest(title=f"{resource_name}-edge-{filename}"))
    register_resource(
        key=f"issue-{issue.id}",
        cleanup=api_oracle.delete_callback(f"/api/issues/{issue.id}", "issue"),
    )
    content = b"" if filename == "empty.bin" else ATTACHMENT_PAYLOAD
    file_path = tmp_path / filename
    file_path.write_bytes(content)
    uploaded = api_oracle.upload_attachment(issue.id, filename=filename, content=content)
    attachment_id = str(uploaded["id"])
    register_resource(
        key=f"attachment-{attachment_id}",
        cleanup=api_oracle.delete_callback(f"/api/attachments/{attachment_id}", "attachment"),
    )
    metadata = api_oracle.get_attachment(attachment_id)
    assert metadata.get("filename") == filename or metadata.get("name") == filename
    downloaded = api_oracle.download_attachment_content(attachment_id)
    assert DirectApiOracle.sha256_hex(downloaded) == DirectApiOracle.sha256_hex(content)
