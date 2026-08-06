from __future__ import annotations

from typing import cast

from multica_py._internal.commands import Command, _Step
from multica_py.models.system import DaemonDiskUsageEntry, DaemonStatus
from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class DaemonResource(BaseResource):
    def start_command(self) -> Command[ManagedProcess]:
        return self._plan(
            steps=(_Step(("daemon", "start"), "spawn"),),
            finalize=lambda results: cast("ManagedProcess", results[0]),
        )

    def start(self) -> ManagedProcess:
        return self.start_command().run()

    def status_command(self) -> Command[DaemonStatus]:
        args, decode = self._plan_decode(("daemon", "status"), DaemonStatus)
        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("DaemonStatus", results[0]),
        )

    def status(self) -> DaemonStatus:
        return self.status_command().run()

    def stop_command(self) -> Command[DaemonStatus]:
        args, decode = self._plan_decode(("daemon", "stop"), DaemonStatus)
        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("DaemonStatus", results[0]),
        )

    def stop(self) -> DaemonStatus:
        return self.stop_command().run()

    def restart_command(self) -> Command[DaemonStatus]:
        args, decode = self._plan_decode(("daemon", "restart"), DaemonStatus)
        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("DaemonStatus", results[0]),
        )

    def restart(self) -> DaemonStatus:
        return self.restart_command().run()

    def disk_usage_command(self) -> Command[tuple[DaemonDiskUsageEntry, ...]]:
        args, decode = self._plan_decode_list(("daemon", "disk-usage"), DaemonDiskUsageEntry)

        def finalize(results: tuple[object, ...]) -> tuple[DaemonDiskUsageEntry, ...]:
            return cast("tuple[DaemonDiskUsageEntry, ...]", results[0])

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def disk_usage(self) -> tuple[DaemonDiskUsageEntry, ...]:
        return self.disk_usage_command().run()

    def logs_command(self, follow: bool = False) -> Command[ManagedProcess]:
        args = ["daemon", "logs"]
        if follow:
            args.append("--follow")
        return self._plan(
            steps=(_Step(tuple(args), "spawn"),),
            finalize=lambda results: cast("ManagedProcess", results[0]),
        )

    def logs(self, follow: bool = False) -> ManagedProcess:
        return self.logs_command(follow).run()
