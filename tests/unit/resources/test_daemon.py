from __future__ import annotations

from multica_py.models.system import DaemonStatus


class TestDaemonModels:
    def test_daemon_status_defaults(self):
        ds = DaemonStatus()
        assert ds.running is False
        assert ds.pid is None
