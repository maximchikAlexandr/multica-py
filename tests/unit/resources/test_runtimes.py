from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import msgspec

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.system import RuntimeDefinition
from multica_py.resources.runtimes import RuntimeResource


def _t() -> MagicMock:
    return MagicMock(spec=CliTransport)


def _r(stdout: bytes = b"") -> RawCommandResult:
    return RawCommandResult(
        argv=(), exit_code=0, stdout=stdout, stderr=b"", duration=datetime.timedelta()
    )


_RD = msgspec.json.encode(RuntimeDefinition(id="r1", name="py3"))


class TestRuntimeCommands:
    def test_list_sends_runtime_list(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=b"[]")
        RuntimeResource(t, ClientConfig()).list()
        t.run_bytes.assert_called_once_with(
            ("runtime", "list", "--output", "json"), stdin=None, timeout=None
        )

    def test_get_sends_runtime_get(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=_RD)
        RuntimeResource(t, ClientConfig()).get("r1")
        t.run_bytes.assert_called_once_with(
            ("runtime", "get", "r1", "--output", "json"), stdin=None, timeout=None
        )


class TestRuntimeDecode:
    def test_list_decodes(self):
        t = _t()
        t.run_bytes.return_value = _r(msgspec.json.encode([RuntimeDefinition(id="r1", name="py3")]))
        result = RuntimeResource(t, ClientConfig()).list()
        assert result[0].name == "py3"
