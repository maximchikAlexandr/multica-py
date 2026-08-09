from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py.models.common import Page
from multica_py.models.system import DaemonDiskUsageEntry, DaemonStatus
from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class DaemonResource(BaseResource):
    def start_command(self) -> Command[ManagedProcess]:
        return self._spawn_command(("daemon", "start"))

    def start(self) -> ManagedProcess:
        return self.start_command().run()

    def status_command(self) -> Command[DaemonStatus]:
        return self._decoded_command(("daemon", "status"), DaemonStatus)

    def status(self) -> DaemonStatus:
        return self.status_command().run()

    def stop_command(self) -> Command[DaemonStatus]:
        return self._decoded_command(("daemon", "stop"), DaemonStatus)

    def stop(self) -> DaemonStatus:
        return self.stop_command().run()

    def restart_command(self) -> Command[DaemonStatus]:
        return self._decoded_command(("daemon", "restart"), DaemonStatus)

    def restart(self) -> DaemonStatus:
        return self.restart_command().run()

    def disk_usage_command(self) -> Command[Page[DaemonDiskUsageEntry]]:
        return self._decoded_page_command(("daemon", "disk-usage"), DaemonDiskUsageEntry)

    def disk_usage(self) -> Page[DaemonDiskUsageEntry]:
        return self.disk_usage_command().run()

    def logs_command(self, follow: bool = False) -> Command[ManagedProcess]:
        args = ["daemon", "logs"]
        if follow:
            args.append("--follow")
        return self._spawn_command(tuple(args))

    def logs(self, follow: bool = False) -> ManagedProcess:
        return self.logs_command(follow).run()
