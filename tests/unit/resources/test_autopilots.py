from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import msgspec

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.autopilots import Autopilot, AutopilotRun
from multica_py.resources.autopilots import AutopilotResource


def _transport() -> MagicMock:
    return MagicMock(spec=CliTransport)


def _result(stdout: bytes = b"") -> RawCommandResult:
    return RawCommandResult(
        argv=(), exit_code=0, stdout=stdout, stderr=b"", duration=datetime.timedelta()
    )


_A = msgspec.json.encode(Autopilot(id="a1", name="AP"))
_AR = msgspec.json.encode(AutopilotRun(id="r1", status="running"))


class TestAutopilotCommands:
    def test_list_sends_autopilot_list(self):
        t = _transport()
        t.run_bytes.return_value = _result(stdout=b"[]")
        AutopilotResource(t, ClientConfig()).list()
        t.run_bytes.assert_called_once_with(
            ("autopilot", "list", "--output", "json"), stdin=None, timeout=None
        )

    def test_get_sends_autopilot_get(self):
        t = _transport()
        t.run_bytes.return_value = _result(stdout=_A)
        AutopilotResource(t, ClientConfig()).get("a1")
        t.run_bytes.assert_called_once_with(
            ("autopilot", "get", "a1", "--output", "json"), stdin=None, timeout=None
        )

    def test_create_sends_name(self):
        t = _transport()
        t.run_bytes.return_value = _result(stdout=_A)
        AutopilotResource(t, ClientConfig()).create("my-ap")
        t.run_bytes.assert_called_once_with(
            ("autopilot", "create", "--name", "my-ap", "--output", "json"), stdin=None, timeout=None
        )

    def test_update_name_only(self):
        t = _transport()
        t.run_bytes.return_value = _result(stdout=_A)
        AutopilotResource(t, ClientConfig()).update("a1", name="new")
        args = t.run_bytes.call_args[0][0]
        assert "--name" in args and "--enabled" not in args

    def test_update_enabled_only(self):
        t = _transport()
        t.run_bytes.return_value = _result(stdout=_A)
        AutopilotResource(t, ClientConfig()).update("a1", enabled=True)
        args = t.run_bytes.call_args[0][0]
        assert "--name" not in args and "--enabled" in args

    def test_update_both_name_and_enabled(self):
        t = _transport()
        t.run_bytes.return_value = _result(stdout=_A)
        AutopilotResource(t, ClientConfig()).update("a1", name="n", enabled=False)
        args = t.run_bytes.call_args[0][0]
        assert "--name" in args and "--enabled" in args

    def test_delete_uses_text(self):
        t = _transport()
        AutopilotResource(t, ClientConfig()).delete("a1")
        t.run_text.assert_called_once_with(("autopilot", "delete", "a1"))

    def test_run_sends_autopilot_run(self):
        t = _transport()
        t.run_bytes.return_value = _result(stdout=_AR)
        AutopilotResource(t, ClientConfig()).run("a1")
        t.run_bytes.assert_called_once_with(
            ("autopilot", "run", "a1", "--output", "json"), stdin=None, timeout=None
        )

    def test_history_sends_autopilot_history(self):
        t = _transport()
        t.run_bytes.return_value = _result(stdout=b"[]")
        AutopilotResource(t, ClientConfig()).history("a1")
        t.run_bytes.assert_called_once_with(
            ("autopilot", "history", "a1", "--output", "json"), stdin=None, timeout=None
        )

    def test_get_run_sends_run_get(self):
        t = _transport()
        t.run_bytes.return_value = _result(stdout=_AR)
        AutopilotResource(t, ClientConfig()).get_run("r1")
        t.run_bytes.assert_called_once_with(
            ("autopilot", "run", "get", "r1", "--output", "json"), stdin=None, timeout=None
        )


class TestAutopilotDecode:
    def test_list_decodes_autopilots(self):
        t = _transport()
        t.run_bytes.return_value = _result(
            msgspec.json.encode([Autopilot(id="a1", name="X"), Autopilot(id="a2", name="Y")])
        )
        result = AutopilotResource(t, ClientConfig()).list()
        assert len(result) == 2
        assert result[0].name == "X"

    def test_get_run_decodes(self):
        t = _transport()
        t.run_bytes.return_value = _result(stdout=_AR)
        result = AutopilotResource(t, ClientConfig()).get_run("r1")
        assert result.id == "r1"
        assert result.status == "running"
