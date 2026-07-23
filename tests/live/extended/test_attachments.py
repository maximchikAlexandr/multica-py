from __future__ import annotations

import hashlib
import pathlib

import pytest

from multica_py.models.issues import IssueCreateRequest
from tests.live.session import LiveCase, LiveSession
from tools.live_support.oracle import DirectApiOracle

pytestmark = [pytest.mark.live, pytest.mark.live_extended, pytest.mark.serial]

ATTACHMENT_PAYLOAD = b"\x00\xff" * 512
EDGE_FILENAMES = ("empty.bin", "file name.bin", "файл.bin")


def test_attachment_round_trip_for_pinned_payload(
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """Upload, verify metadata, download SHA-256, and delete a 1024-byte attachment."""
    issue = live_session.client.issues.create(
        IssueCreateRequest(title=f"{live_case.unique_name}-attachment")
    )
    live_case.defer_cleanup(live_session.oracle.delete_callback(f"/api/issues/{issue.id}", "issue"))
    uploaded = live_session.oracle.upload_attachment(
        issue.id,
        filename="payload.bin",
        content=ATTACHMENT_PAYLOAD,
    )
    attachment_id = str(uploaded["id"])
    live_case.defer_cleanup(
        live_session.oracle.delete_callback(f"/api/attachments/{attachment_id}", "attachment"),
    )
    metadata = live_session.oracle.get_attachment(attachment_id)
    assert metadata.get("id") == attachment_id
    downloaded = live_session.oracle.download_attachment_content(attachment_id)
    assert hashlib.sha256(downloaded).hexdigest() == hashlib.sha256(ATTACHMENT_PAYLOAD).hexdigest()
    listed = live_session.oracle.list_issue_attachments(issue.id)
    listed_ids = {
        entry.get("id")
        for entry in listed
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    assert attachment_id in listed_ids
    live_session.oracle.delete(f"/api/attachments/{attachment_id}")
    live_session.oracle.assert_absent(f"/api/attachments/{attachment_id}", "attachment")


@pytest.mark.parametrize("filename", EDGE_FILENAMES)
def test_attachment_edge_filenames_are_supported(
    live_session: LiveSession,
    live_case: LiveCase,
    tmp_path: pathlib.Path,
    filename: str,
) -> None:
    """Upload edge-case filenames and fail when attachments are unsupported on the pinned target."""
    issue = live_session.client.issues.create(
        IssueCreateRequest(title=f"{live_case.unique_name}-edge-{filename}")
    )
    live_case.defer_cleanup(live_session.oracle.delete_callback(f"/api/issues/{issue.id}", "issue"))
    content = b"" if filename == "empty.bin" else ATTACHMENT_PAYLOAD
    file_path = tmp_path / filename
    file_path.write_bytes(content)
    uploaded = live_session.oracle.upload_attachment(issue.id, filename=filename, content=content)
    attachment_id = str(uploaded["id"])
    live_case.defer_cleanup(
        live_session.oracle.delete_callback(f"/api/attachments/{attachment_id}", "attachment"),
    )
    metadata = live_session.oracle.get_attachment(attachment_id)
    assert metadata.get("filename") == filename or metadata.get("name") == filename
    downloaded = live_session.oracle.download_attachment_content(attachment_id)
    assert hashlib.sha256(downloaded).hexdigest() == hashlib.sha256(content).hexdigest()
