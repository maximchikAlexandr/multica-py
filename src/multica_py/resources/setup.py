from __future__ import annotations

from typing import cast

from multica_py._internal.commands import Command, _Step
from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class SetupResource(BaseResource):
    def cloud_command(self) -> Command[ManagedProcess]:
        return self._plan(
            steps=(_Step(("setup", "cloud"), "spawn"),),
            finalize=lambda results: cast("ManagedProcess", results[0]),
        )

    def cloud(self) -> ManagedProcess:
        return self.cloud_command().run()

    def self_host_command(self, url: str) -> Command[ManagedProcess]:
        return self._plan(
            steps=(_Step(("setup", "self-host", "--url", url), "spawn"),),
            finalize=lambda results: cast("ManagedProcess", results[0]),
        )

    def self_host(self, url: str) -> ManagedProcess:
        return self.self_host_command(url).run()
