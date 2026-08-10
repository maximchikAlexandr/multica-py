from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class SetupResource(BaseResource):
    def cloud_command(self, *, options: OperationOptions | None = None) -> Command[ManagedProcess]:
        return self._spawn_command(("setup", "cloud"), options=options)

    def cloud(self, *, options: OperationOptions | None = None) -> ManagedProcess:
        return self.cloud_command(options=options).run()

    def self_host_command(
        self, url: str, *, options: OperationOptions | None = None
    ) -> Command[ManagedProcess]:
        return self._spawn_command(("setup", "self-host", "--url", url), options=options)

    def self_host(self, url: str, *, options: OperationOptions | None = None) -> ManagedProcess:
        return self.self_host_command(url, options=options).run()
