from __future__ import annotations

import os
from typing import cast

import msgspec

from multica_py._internal.commands import Command, _Step
from multica_py.config import OperationOptions
from multica_py.models.system import UserProfile
from multica_py.resources._base import BaseResource, _normalize_description_file
from multica_py.sentinels import Unset


class UserResource(BaseResource):
    def profile_get_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[UserProfile]:
        return self._decoded_command(("user", "profile", "get"), UserProfile, options=options)

    def profile_get(self, *, options: OperationOptions | None = None) -> UserProfile:
        return self.profile_get_command(options=options).run()

    def profile_update_command(
        self,
        *,
        description: str | None | msgspec.UnsetType = msgspec.UNSET,
        description_stdin: str | bytes | None = None,
        description_file: str | os.PathLike[str] | None = None,
        allow_external_file: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[UserProfile]:
        if sum(value is not None for value in (description_stdin, description_file)) > 1:
            raise TypeError("description_stdin and description_file are mutually exclusive")
        if description is not Unset and (
            description_stdin is not None or description_file is not None
        ):
            raise TypeError("description cannot be combined with a file or stdin")
        if description is Unset and description_stdin is None and description_file is None:
            return self._decoded_command(("user", "profile", "get"), UserProfile, options=options)
        if description is None:
            return self._decoded_command(
                ("user", "profile", "update", "--clear"), UserProfile, options=options
            )
        if description_stdin is not None:
            stdin = (
                description_stdin.encode()
                if isinstance(description_stdin, str)
                else description_stdin
            )
            args, decode = self._plan_decode(
                ("user", "profile", "update", "--description-stdin"), UserProfile
            )
            return self._plan(
                steps=(_Step(args, "run_bytes", stdin=stdin, decode=decode),),
                finalize=lambda results: cast("UserProfile", results[0]),
                options=options,
            )
        if description_file is not None:
            path = _normalize_description_file(
                description_file, cwd=self._effective_config(options).cwd
            )
            file_args: list[str] = ["user", "profile", "update", "--description-file", path]
            if allow_external_file:
                file_args.append("--allow-external-file")
            return self._decoded_command(tuple(file_args), UserProfile, options=options)
        if not isinstance(description, str):
            raise TypeError("description must be a string, None, or Unset")
        description_args = ("user", "profile", "update", "--description", description)
        return self._decoded_command(description_args, UserProfile, options=options)

    def profile_update(
        self,
        *,
        description: str | None | msgspec.UnsetType = msgspec.UNSET,
        description_stdin: str | bytes | None = None,
        description_file: str | os.PathLike[str] | None = None,
        allow_external_file: bool = False,
        options: OperationOptions | None = None,
    ) -> UserProfile:
        return self.profile_update_command(
            description=description,
            description_stdin=description_stdin,
            description_file=description_file,
            allow_external_file=allow_external_file,
            options=options,
        ).run()
