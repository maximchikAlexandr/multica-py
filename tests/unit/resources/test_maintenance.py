from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import msgspec

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.system import MaintenanceVersion
from multica_py.resources.maintenance import MaintenanceResource


def _t() -> MagicMock:
    return MagicMock(spec=CliTransport)


def _r(stdout: bytes = b"") -> RawCommandResult:
    return RawCommandResult(
        argv=(), exit_code=0, stdout=stdout, stderr=b"", duration=datetime.timedelta()
    )


class TestMaintenanceCommands:
    def test_version_sends_version_json(self):
        t = _t()
        v = msgspec.json.encode(MaintenanceVersion(version="1.0.0", commit="abc"))
        t.run_bytes.return_value = _r(stdout=v)
        MaintenanceResource(t, ClientConfig()).version()
        t.run_bytes.assert_called_once_with(("version", "--output", "json"))

    def test_update_sends_update_text(self):
        t = _t()
        t.spawn.return_value = MagicMock()
        MaintenanceResource(t, ClientConfig()).update()
        t.spawn.assert_called_once_with(("update",))


class TestMaintenanceDecode:
    def test_version_decodes(self):
        t = _t()
        v = MaintenanceVersion(version="1.0.0", commit="abc", build_date="2026-01-01")
        t.run_bytes.return_value = _r(stdout=msgspec.json.encode(v))
        result = MaintenanceResource(t, ClientConfig()).version()
        assert result.version == "1.0.0"
        assert result.commit == "abc"
