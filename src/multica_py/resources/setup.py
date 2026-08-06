from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class SetupResource(BaseResource):
    def cloud_command(self) -> Command[ManagedProcess]:
        return self._spawn_command(("setup", "cloud"))

    def cloud(self) -> ManagedProcess:
        return self.cloud_command().run()

    def self_host_command(self, url: str) -> Command[ManagedProcess]:
        return self._spawn_command(("setup", "self-host", "--url", url))

    def self_host(self, url: str) -> ManagedProcess:
        return self.self_host_command(url).run()
