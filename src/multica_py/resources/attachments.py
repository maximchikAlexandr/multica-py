from __future__ import annotations

import pathlib
import tempfile

from multica_py.models.system import AttachmentResult
from multica_py.resources._base import BaseResource


def _safe_leaf(name: str, param: str) -> str:
    if not name:
        raise ValueError(f"{param} must not be empty")
    if name in (".", "..") or pathlib.PurePath(name).name != name or "/" in name or "\\" in name:
        raise ValueError(f"{param} must be a bare filename, not a path: {name!r}")
    return name


class AttachmentResource(BaseResource):
    def list(self, issue_id: str) -> tuple[AttachmentResult, ...]:
        return self._run_json_decode_list(("attachment", "list", issue_id), AttachmentResult)

    def upload(self, issue_id: str, file_path: str) -> AttachmentResult:
        return self._run_json_decode(
            ("attachment", "upload", issue_id, "--file", str(pathlib.Path(file_path).resolve())),
            AttachmentResult,
        )

    def upload_bytes(self, issue_id: str, filename: str, payload: bytes) -> AttachmentResult:
        _safe_leaf(filename, "filename")
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / filename
            path.write_bytes(payload)
            return self.upload(issue_id, str(path))

    def download(self, attachment_id: str, output_path: str) -> None:
        args = (
            "attachment",
            "download",
            attachment_id,
            "--output",
            str(pathlib.Path(output_path).resolve()),
        )
        self._transport.run_text(args)

    def download_bytes(self, attachment_id: str) -> bytes:
        _safe_leaf(attachment_id, "attachment_id")
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / attachment_id
            self.download(attachment_id, str(path))
            return path.read_bytes()
        # ponytail: assumes upstream `--output <file>` writes to that exact file path;
        # if upstream ever writes a server-named file into a directory, read the single
        # file in tmp instead. Covered by test_attachments.py::test_download_bytes_round_trip.
