from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.models.common import Page
from multica_py.models.system import DaemonDiskUsageEntry, DaemonStatus
from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class DaemonResource(BaseResource):
    def start_command(self, *, options: OperationOptions | None = None) -> Command[ManagedProcess]:
        return self._spawn_command(("daemon", "start"), options=options)

    def start(self, *, options: OperationOptions | None = None) -> ManagedProcess:
        return self.start_command(options=options).run()

    def status_command(self, *, options: OperationOptions | None = None) -> Command[DaemonStatus]:
        return self._decoded_command(("daemon", "status"), DaemonStatus, options=options)

    def status(self, *, options: OperationOptions | None = None) -> DaemonStatus:
        return self.status_command(options=options).run()

    def stop_command(self, *, options: OperationOptions | None = None) -> Command[DaemonStatus]:
        return self._decoded_command(("daemon", "stop"), DaemonStatus, options=options)

    def stop(self, *, options: OperationOptions | None = None) -> DaemonStatus:
        return self.stop_command(options=options).run()

    def restart_command(self, *, options: OperationOptions | None = None) -> Command[DaemonStatus]:
        return self._decoded_command(("daemon", "restart"), DaemonStatus, options=options)

    def restart(self, *, options: OperationOptions | None = None) -> DaemonStatus:
        return self.restart_command(options=options).run()

    def disk_usage_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[Page[DaemonDiskUsageEntry]]:
        return self._decoded_page_command(
            ("daemon", "disk-usage"), DaemonDiskUsageEntry, options=options
        )

    def disk_usage(self, *, options: OperationOptions | None = None) -> Page[DaemonDiskUsageEntry]:
        return self.disk_usage_command(options=options).run()

    def logs_command(
        self, follow: bool = False, *, options: OperationOptions | None = None
    ) -> Command[ManagedProcess]:
        args = ["daemon", "logs"]
        if follow:
            args.append("--follow")
        return self._spawn_command(tuple(args), options=options)

    def logs(
        self, follow: bool = False, *, options: OperationOptions | None = None
    ) -> ManagedProcess:
        return self.logs_command(follow, options=options).run()
