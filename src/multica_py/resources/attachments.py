from __future__ import annotations

from multica_py.models.system import AttachmentResult
from multica_py.resources._base import BaseResource


class AttachmentResource(BaseResource):
    def list(self, issue_id: str) -> tuple[AttachmentResult, ...]:
        return self._run_json_decode_list(("attachment", "list", issue_id), AttachmentResult)

    def upload(self, issue_id: str, file_path: str) -> AttachmentResult:
        return self._run_json_decode(
            ("attachment", "upload", issue_id, "--file", file_path), AttachmentResult
        )

    def download(self, attachment_id: str, output_path: str) -> None:
        args = ("attachment", "download", attachment_id, "--output", output_path)
        self._transport.run_text(args)
