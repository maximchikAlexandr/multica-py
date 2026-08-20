from __future__ import annotations

import datetime
import os
from dataclasses import dataclass
from typing import Literal

import msgspec

from multica_py._internal.argv import normalize_global_args
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
        stdout=redact_bytes(
            result.stdout,
            secret_values=result.secret_values,
            secret_bytes=result.secret_bytes,
        ),
        stderr=redact_bytes(
            result.stderr,
            secret_values=result.secret_values,
            secret_bytes=result.secret_bytes,
        ),
        duration=result.duration,
    )


@dataclass(frozen=True, slots=True)
class _RawExecutionModeRule:
    path: tuple[str, ...]
    replacement: str
    kind: Literal["managed", "auth"]


_RAW_EXECUTION_MODE_REGISTRY: tuple[_RawExecutionModeRule, ...] = (
    _RawExecutionModeRule(
        ("login",),
        "client.auth.login(token=...)",
        "auth",
    ),
    _RawExecutionModeRule(
        ("setup", "cloud"),
        "client.setup.cloud() / ManagedProcess",
        "managed",
    ),
    _RawExecutionModeRule(
        ("setup", "self-host"),
        "client.setup.self_host(...) / ManagedProcess",
        "managed",
    ),
    _RawExecutionModeRule(
        ("daemon", "start"),
        "client.daemon.start() / ManagedProcess",
        "managed",
    ),
    _RawExecutionModeRule(
        ("daemon", "logs"),
        "client.daemon.logs(...) / ManagedProcess",
        "managed",
    ),
    _RawExecutionModeRule(
        ("update",),
        "client.maintenance.update() / ManagedProcess",
        "managed",
    ),
)

# Reviewed bounded command paths intentionally remain outside the deny registry.
_RAW_EXECUTION_MODE_REVIEWED_EXCEPTIONS: frozenset[tuple[str, ...]] = frozenset()


def _matching_execution_mode_rule(argv: tuple[str, ...]) -> _RawExecutionModeRule | None:
    for rule in _RAW_EXECUTION_MODE_REGISTRY:
        if argv[: len(rule.path)] == rule.path:
            return rule
    return None


def _reject_raw_execution_mode(rule: _RawExecutionModeRule) -> None:
    raise ValueError(
        f"raw command is not a bounded {rule.path!r} execution form; use {rule.replacement}"
    )


def _validate_auth_login_argv(argv: tuple[str, ...], rule: _RawExecutionModeRule) -> None:
    token_option = len(rule.path)
    if len(argv) <= token_option or not (
        argv[token_option] == "--token" or argv[token_option].startswith("--token=")
    ):
        raise ValueError(
            "raw login without --token is interactive; use client.auth.login() / ManagedProcess"
        )
    if (
        len(argv) > token_option + 1
        and argv[token_option] == "--token"
        and argv[token_option + 1]
        and not argv[token_option + 1].startswith("-")
    ):
        return
    raise ValueError(f"raw login requires bounded --token <token>; use {rule.replacement}")


def _validate_execution_mode(argv: tuple[str, ...]) -> None:
    normalized_argv = normalize_global_args(argv)
    rule = _matching_execution_mode_rule(normalized_argv)
    if rule is None:
        return
    if rule.kind == "auth":
        _validate_auth_login_argv(normalized_argv, rule)
        return
    _reject_raw_execution_mode(rule)


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
    _validate_execution_mode(string_argv)


class CliResource(BaseResource):
    def command_command(
        self, *argv: str, options: OperationOptions | None = None
    ) -> Command[CliResult]:
        _validate_argv(argv, self._config.executable)
        return self._raw_command(tuple(argv), options=options)

    def command(self, *argv: str, options: OperationOptions | None = None) -> Command[CliResult]:
        return self.command_command(*argv, options=options)
