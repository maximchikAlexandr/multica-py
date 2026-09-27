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
        self,
        token: str,
        *,
        callback_host: str | None = None,
        prompt_token: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[str]]: ...

    @overload
    def login_command(
        self,
        token: None = None,
        *,
        callback_host: str | None = None,
        prompt_token: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[ManagedProcess]: ...

    def login_command(
        self,
        token: str | None = None,
        *,
        callback_host: str | None = None,
        prompt_token: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[str]] | Command[ManagedProcess]:
        if callback_host is not None and not callback_host.strip():
            raise ValueError("callback_host must be nonblank when provided")
        if token is not None and not token.strip():
            raise ValueError("token must be nonblank")
        if token is not None and callback_host is not None:
            raise ValueError("callback_host is only valid for browser login")
        if token is not None and prompt_token:
            raise ValueError("prompt_token cannot be combined with token")
        if token is not None:
            return self._action_text_command(("login", "--token", token), options=options)
        args = ["login"]
        if prompt_token:
            args.append("--token")
        if callback_host is not None:
            args.extend(("--callback-host", callback_host))
        return self._spawn_command(tuple(args), options=options)

    @overload
    def login(
        self,
        token: str,
        *,
        callback_host: str | None = None,
        prompt_token: bool = False,
        options: OperationOptions | None = None,
    ) -> ActionResult[str]: ...

    @overload
    def login(
        self,
        token: None = None,
        *,
        callback_host: str | None = None,
        prompt_token: bool = False,
        options: OperationOptions | None = None,
    ) -> ManagedProcess: ...

    def login(
        self,
        token: str | None = None,
        *,
        callback_host: str | None = None,
        prompt_token: bool = False,
        options: OperationOptions | None = None,
    ) -> ActionResult[str] | ManagedProcess:
        return self.login_command(
            token, callback_host=callback_host, prompt_token=prompt_token, options=options
        ).run()

    def logout_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("auth", "logout"), options=options)

    def logout(self, *, options: OperationOptions | None = None) -> ActionResult[None]:
        return self.logout_command(options=options).run()
