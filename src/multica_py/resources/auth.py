from __future__ import annotations

from typing import overload

from multica_py.models.system import AuthenticationStatus
from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class AuthResource(BaseResource):
    def status(self) -> AuthenticationStatus:
        return self._run_json_decode(("auth", "status"), AuthenticationStatus)

    @overload
    def login(self, token: str) -> str: ...

    @overload
    def login(self, token: None = None) -> ManagedProcess: ...

    def login(self, token: str | None = None) -> str | ManagedProcess:
        if token is not None:
            return self._transport.run_text(("auth", "login", "--token", token)).text
        return self._transport.spawn(("auth", "login"))

    def logout(self) -> AuthenticationStatus:
        return self._run_json_decode(("auth", "logout"), AuthenticationStatus)
