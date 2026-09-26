from __future__ import annotations

import os

from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.models.common import ActionResult
from multica_py.models.system import (
    DaemonAggregateDiskUsageReport,
    DaemonDiskUsageReport,
    DaemonStatus,
)
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

    def stop_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("daemon", "stop"), options=options)

    def stop(self, *, options: OperationOptions | None = None) -> ActionResult[None]:
        return self.stop_command(options=options).run()

    def restart_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("daemon", "restart"), options=options)

    def restart(self, *, options: OperationOptions | None = None) -> ActionResult[None]:
        return self.restart_command(options=options).run()

    def disk_usage_command(
        self,
        *,
        by_workspace: bool = False,
        by_task: bool = False,
        top: int | None = None,
        workspaces_root: str | os.PathLike[str] | None = None,
        all_profiles: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[DaemonDiskUsageReport | DaemonAggregateDiskUsageReport]:
        if by_workspace and by_task:
            raise ValueError("by_workspace and by_task are mutually exclusive")
        if top is not None and top < 0:
            raise ValueError("top must be non-negative")
        if all_profiles and workspaces_root is not None:
            raise ValueError("all_profiles and workspaces_root are mutually exclusive")

        args = ["daemon", "disk-usage"]
        if by_workspace:
            args.append("--by-workspace")
        if by_task:
            args.append("--by-task")
        if top is not None:
            args.extend(("--top", str(top)))
        if workspaces_root is not None:
            root = os.fspath(workspaces_root)
            if not root.strip():
                raise ValueError("workspaces_root must be nonblank")
            args.extend(("--workspaces-root", os.path.abspath(root)))
        if all_profiles:
            args.append("--all-profiles")
        model = DaemonAggregateDiskUsageReport if all_profiles else DaemonDiskUsageReport
        return self._decoded_command(tuple(args), model, options=options)

    def disk_usage(
        self,
        *,
        by_workspace: bool = False,
        by_task: bool = False,
        top: int | None = None,
        workspaces_root: str | os.PathLike[str] | None = None,
        all_profiles: bool = False,
        options: OperationOptions | None = None,
    ) -> DaemonDiskUsageReport | DaemonAggregateDiskUsageReport:
        return self.disk_usage_command(
            by_workspace=by_workspace,
            by_task=by_task,
            top=top,
            workspaces_root=workspaces_root,
            all_profiles=all_profiles,
            options=options,
        ).run()

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
