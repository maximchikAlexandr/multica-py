from __future__ import annotations

from multica_py.models.system import DaemonDiskUsageEntry, DaemonStatus
from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class DaemonResource(BaseResource):
    def start(self) -> ManagedProcess:
        return self._transport.spawn(("daemon", "start"))

    def status(self) -> DaemonStatus:
        return self._run_json_decode(("daemon", "status"), DaemonStatus)

    def stop(self) -> DaemonStatus:
        return self._run_json_decode(("daemon", "stop"), DaemonStatus)

    def restart(self) -> DaemonStatus:
        return self._run_json_decode(("daemon", "restart"), DaemonStatus)

    def disk_usage(self) -> tuple[DaemonDiskUsageEntry, ...]:
        return self._run_json_decode_list(("daemon", "disk-usage"), DaemonDiskUsageEntry)

    def logs(self, follow: bool = False) -> ManagedProcess:
        if follow:
            return self._transport.spawn(("daemon", "logs", "--follow"))
        return self._transport.spawn(("daemon", "logs"))
