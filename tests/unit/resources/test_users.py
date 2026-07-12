from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import msgspec

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.system import User
from multica_py.resources.users import UserResource


def _t() -> MagicMock:
    return MagicMock(spec=CliTransport)


def _r(stdout: bytes = b"") -> RawCommandResult:
    return RawCommandResult(
        argv=(), exit_code=0, stdout=stdout, stderr=b"", duration=datetime.timedelta()
    )


class TestUserCommands:
    def test_list_sends_user_list(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=b"[]")
        UserResource(t, ClientConfig()).list()
        t.run_bytes.assert_called_once_with(
            ("user", "list", "--output", "json"), stdin=None, timeout=None
        )

    def test_get_sends_user_get(self):
        t = _t()
        t.run_bytes.return_value = _r(msgspec.json.encode(User(id="u1", name="Alice")))
        UserResource(t, ClientConfig()).get("u1")
        t.run_bytes.assert_called_once_with(
            ("user", "get", "u1", "--output", "json"), stdin=None, timeout=None
        )


class TestUserDecode:
    def test_list_decodes(self):
        t = _t()
        t.run_bytes.return_value = _r(
            msgspec.json.encode([User(id="u1", name="Alice"), User(id="u2", name="Bob")])
        )
        result = UserResource(t, ClientConfig()).list()
        assert len(result) == 2
