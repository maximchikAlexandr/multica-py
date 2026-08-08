from __future__ import annotations

from typing import overload

from multica_py._internal.commands import Command
from multica_py.models.common import ActionResult
from multica_py.models.system import AuthenticationStatus
from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class AuthResource(BaseResource):
    def status_command(self) -> Command[AuthenticationStatus]:
        return self._decoded_command(("auth", "status"), AuthenticationStatus)

    def status(self) -> AuthenticationStatus:
        return self.status_command().run()

    @overload
    def login_command(self, token: str) -> Command[ActionResult[str]]: ...

    @overload
    def login_command(self, token: None = None) -> Command[ManagedProcess]: ...

    def login_command(
        self, token: str | None = None
    ) -> Command[ActionResult[str]] | Command[ManagedProcess]:
        if token is not None:
            return self._action_text_command(("auth", "login", "--token", token))
        return self._spawn_command(("auth", "login"))

    @overload
    def login(self, token: str) -> ActionResult[str]: ...

    @overload
    def login(self, token: None = None) -> ManagedProcess: ...

    def login(self, token: str | None = None) -> ActionResult[str] | ManagedProcess:
        return self.login_command(token).run()

    def logout_command(self) -> Command[AuthenticationStatus]:
        return self._decoded_command(("auth", "logout"), AuthenticationStatus)

    def logout(self) -> AuthenticationStatus:
        return self.logout_command().run()
