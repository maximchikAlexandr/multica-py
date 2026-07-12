from __future__ import annotations

from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class SetupResource(BaseResource):
    def cloud(self) -> ManagedProcess:
        return self._transport.spawn(("setup", "cloud"))

    def self_host(self, url: str) -> ManagedProcess:
        return self._transport.spawn(("setup", "self-host", "--url", url))
