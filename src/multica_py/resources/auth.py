from __future__ import annotations

from typing import overload

from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.models.common import ActionResult
from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class AuthResource(BaseResource):
    def status_command(self, *, options: OperationOptions | None = None) -> Command[str]:
        return self._text_command(("auth", "status"), options=options)

    def status(self, *, options: OperationOptions | None = None) -> str:
        return self.status_command(options=options).run()

    @overload
    def login_command(
        self, token: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[str]]: ...

    @overload
    def login_command(
        self, token: None = None, *, options: OperationOptions | None = None
    ) -> Command[ManagedProcess]: ...

    def login_command(
        self, token: str | None = None, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[str]] | Command[ManagedProcess]:
        if token is not None:
            return self._action_text_command(("login", "--token", token), options=options)
        return self._spawn_command(("login",), options=options)

    @overload
    def login(
        self, token: str, *, options: OperationOptions | None = None
    ) -> ActionResult[str]: ...

    @overload
    def login(
        self, token: None = None, *, options: OperationOptions | None = None
    ) -> ManagedProcess: ...

    def login(
        self, token: str | None = None, *, options: OperationOptions | None = None
    ) -> ActionResult[str] | ManagedProcess:
        return self.login_command(token, options=options).run()

    def logout_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("auth", "logout"), options=options)

    def logout(self, *, options: OperationOptions | None = None) -> ActionResult[None]:
        return self.logout_command(options=options).run()
