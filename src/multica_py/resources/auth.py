from __future__ import annotations

from typing import cast, overload

from multica_py._internal.commands import Command, _Step
from multica_py._internal.specs import TextResult
from multica_py.models.system import AuthenticationStatus
from multica_py.process import ManagedProcess
from multica_py.resources._base import BaseResource


class AuthResource(BaseResource):
    def status_command(self) -> Command[AuthenticationStatus]:
        args, decode = self._plan_decode(("auth", "status"), AuthenticationStatus)
        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("AuthenticationStatus", results[0]),
        )

    def status(self) -> AuthenticationStatus:
        return self.status_command().run()

    @overload
    def login_command(self, token: str) -> Command[str]: ...

    @overload
    def login_command(self, token: None = None) -> Command[ManagedProcess]: ...

    def login_command(self, token: str | None = None) -> Command[str] | Command[ManagedProcess]:
        if token is not None:
            return self._plan(
                steps=(_Step(("auth", "login", "--token", token), "run_text"),),
                finalize=lambda results: cast("TextResult", results[0]).text,
            )
        return self._plan(
            steps=(_Step(("auth", "login"), "spawn"),),
            finalize=lambda results: cast("ManagedProcess", results[0]),
        )

    @overload
    def login(self, token: str) -> str: ...

    @overload
    def login(self, token: None = None) -> ManagedProcess: ...

    def login(self, token: str | None = None) -> str | ManagedProcess:
        return self.login_command(token).run()

    def logout_command(self) -> Command[AuthenticationStatus]:
        args, decode = self._plan_decode(("auth", "logout"), AuthenticationStatus)
        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("AuthenticationStatus", results[0]),
        )

    def logout(self) -> AuthenticationStatus:
        return self.logout_command().run()
