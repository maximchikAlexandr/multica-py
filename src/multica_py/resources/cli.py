from __future__ import annotations

import datetime
import os

import msgspec

from multica_py._internal.commands import Command
from multica_py._internal.redaction import redact_bytes
from multica_py._internal.specs import RawCommandResult
from multica_py.config import OperationOptions
from multica_py.resources._base import BaseResource

__all__ = ["CliResource", "CliResult"]


class CliResult(msgspec.Struct, frozen=True, kw_only=True):
    """Redaction-safe result for a successful bounded raw CLI command."""

    stdout: bytes
    stderr: bytes
    duration: datetime.timedelta


def decode_cli_result(result: RawCommandResult) -> CliResult:
    return CliResult(
        stdout=redact_bytes(result.stdout, secret_values=result.secret_values),
        stderr=redact_bytes(result.stderr, secret_values=result.secret_values),
        duration=result.duration,
    )


def _validate_argv(argv: tuple[object, ...], executable: str | os.PathLike[str]) -> None:
    if not argv:
        raise ValueError("argv must contain at least one command argument")
    if any(not isinstance(argument, str) for argument in argv):
        raise TypeError("argv components must be strings")
    string_argv = tuple(argument for argument in argv if isinstance(argument, str))
    if not string_argv[0].strip():
        raise ValueError("argv executable must not be blank")
    configured_executable = str(executable)
    if string_argv[0] == configured_executable:
        raise ValueError("argv must not duplicate the configured executable")
    if any("\x00" in argument for argument in string_argv):
        raise ValueError("argv components must not contain NUL")


class CliResource(BaseResource):
    def command_command(
        self, *argv: str, options: OperationOptions | None = None
    ) -> Command[CliResult]:
        _validate_argv(argv, self._config.executable)
        return self._raw_command(tuple(argv), options=options)

    def command(self, *argv: str, options: OperationOptions | None = None) -> Command[CliResult]:
        return self.command_command(*argv, options=options)
