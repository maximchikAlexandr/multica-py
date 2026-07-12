from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import msgspec

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.system import AttachmentResult
from multica_py.resources.attachments import AttachmentResource


def _t() -> MagicMock:
    return MagicMock(spec=CliTransport)


def _r(stdout: bytes = b"") -> RawCommandResult:
    return RawCommandResult(
        argv=(), exit_code=0, stdout=stdout, stderr=b"", duration=datetime.timedelta()
    )


_AR = msgspec.json.encode(AttachmentResult(id="a1", filename="f.txt"))


class TestAttachmentCommands:
    def test_list_sends_attachment_list(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=b"[]")
        AttachmentResource(t, ClientConfig()).list("i1")
        t.run_bytes.assert_called_once_with(
            ("attachment", "list", "i1", "--output", "json"), stdin=None, timeout=None
        )

    def test_upload_sends_attachment_upload(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=_AR)
        AttachmentResource(t, ClientConfig()).upload("i1", "/p/f.txt")
        t.run_bytes.assert_called_once_with(
            ("attachment", "upload", "i1", "--file", "/p/f.txt", "--output", "json"),
            stdin=None,
            timeout=None,
        )

    def test_download_uses_text(self):
        t = _t()
        AttachmentResource(t, ClientConfig()).download("a1", "/out")
        t.run_text.assert_called_once_with(("attachment", "download", "a1", "--output", "/out"))


class TestAttachmentDecode:
    def test_list_decodes(self):
        t = _t()
        t.run_bytes.return_value = _r(
            msgspec.json.encode([AttachmentResult(id="a1", filename="x")])
        )
        result = AttachmentResource(t, ClientConfig()).list("i1")
        assert len(result) == 1
        assert result[0].filename == "x"

    def test_upload_decodes(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=_AR)
        result = AttachmentResource(t, ClientConfig()).upload("i1", "/f")
        assert result.id == "a1"
