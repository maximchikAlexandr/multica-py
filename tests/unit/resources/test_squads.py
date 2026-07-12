from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import msgspec

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.system import Squad
from multica_py.resources.squads import SquadResource


def _t() -> MagicMock:
    return MagicMock(spec=CliTransport)


def _r(stdout: bytes = b"") -> RawCommandResult:
    return RawCommandResult(
        argv=(), exit_code=0, stdout=stdout, stderr=b"", duration=datetime.timedelta()
    )


class TestSquadCommands:
    def test_list_sends_squad_list(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=b"[]")
        SquadResource(t, ClientConfig()).list()
        t.run_bytes.assert_called_once_with(
            ("squad", "list", "--output", "json"), stdin=None, timeout=None
        )

    def test_get_sends_squad_get(self):
        t = _t()
        t.run_bytes.return_value = _r(msgspec.json.encode(Squad(id="s1", name="S")))
        SquadResource(t, ClientConfig()).get("s1")
        t.run_bytes.assert_called_once_with(
            ("squad", "get", "s1", "--output", "json"), stdin=None, timeout=None
        )


class TestSquadDecode:
    def test_list_decodes(self):
        t = _t()
        t.run_bytes.return_value = _r(
            msgspec.json.encode([Squad(id="s1", name="S1", member_count=3)])
        )
        result = SquadResource(t, ClientConfig()).list()
        assert result[0].member_count == 3
