from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import Protocol, cast

from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py.client import MulticaClient
from multica_py.exceptions import CommandExecutionError, OutputShapeError
from tests.cases.models import ErrorCase, OperationCase


class _MutableAttr(Protocol):
    side_effect: object


class _SideEffectTransport(Protocol):
    run_bytes: _MutableAttr
    run_text: _MutableAttr
    spawn: _MutableAttr


def _walk_attr(client: MulticaClient, parts: tuple[str, ...]) -> object:
    current: object = client
    for part in parts:
        current = getattr(current, part)
    return current


def _default_stdout(case: OperationCase) -> bytes:
    if case.response is not None and case.response.stdout:
        return case.response.stdout
    sdk = case.sdk_method
    if sdk.endswith((".list", ".members", ".children")) or ".list." in sdk:
        return b"[]"
    return b"{}"


def invoke_client_operation(
    client: MulticaClient, sdk_method: str, *args: object, **kwargs: object
) -> object:
    parts = tuple(sdk_method.split("."))
    target = _walk_attr(client, parts[:-1])
    method = getattr(target, parts[-1])
    return method(*args, **kwargs)


def configure_mock_transport(
    transport: _SideEffectTransport, case: OperationCase | ErrorCase
) -> None:
    if isinstance(case, ErrorCase):
        _configure_error_transport(transport, case)
    else:
        _configure_success_transport(transport, case)


def _configure_success_transport(transport: _SideEffectTransport, case: OperationCase) -> None:
    transport_call = case.expected_call
    if transport_call is None:
        return
    method_name = transport_call.method
    stdout_bytes = _default_stdout(case)
    stdout_text = stdout_bytes.decode("utf-8")

    def run_bytes(
        argv: tuple[str, ...],
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
    ) -> RawCommandResult:
        return RawCommandResult(
            argv=argv,
            exit_code=0,
            stdout=stdout_bytes,
            stderr=b"",
            duration=datetime.timedelta(),
        )

    def run_text(
        argv: tuple[str, ...],
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
    ) -> TextResult:
        return TextResult(text=stdout_text, stderr="", exit_code=0)

    def spawn(argv: tuple[str, ...]) -> object:
        return object()

    if method_name == "run_bytes":
        transport.run_bytes.side_effect = run_bytes
        transport.run_text.side_effect = run_text
    elif method_name == "run_text":
        transport.run_text.side_effect = run_text
        transport.run_bytes.side_effect = run_bytes
    else:
        transport.spawn.side_effect = spawn


def _configure_error_transport(transport: _SideEffectTransport, case: ErrorCase) -> None:
    exc_type = case.exception_type
    is_summable = isinstance(exc_type, type) and issubclass(exc_type, CommandExecutionError)
    if not is_summable:
        err = OutputShapeError(f"output shape mismatch for {case.operation.sdk_method}")
        transport.run_bytes.side_effect = _raise_bytes_shape(err)
        transport.run_text.side_effect = _raise_text_shape(err)
        return
    exc_class = cast("type[CommandExecutionError]", exc_type)
    exit_code = case.response.exit_code
    message = case.response.stderr.decode("utf-8") or f"exit {exit_code}"
    transport.run_bytes.side_effect = _raise_bytes(exc_class, message, exit_code)
    transport.run_text.side_effect = _raise_text(exc_class, message, exit_code)


def _raise_bytes_shape(
    err: OutputShapeError,
) -> Callable[..., RawCommandResult]:
    def raise_bytes(
        argv: tuple[str, ...],
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
    ) -> RawCommandResult:
        raise err

    return raise_bytes


def _raise_text_shape(
    err: OutputShapeError,
) -> Callable[..., TextResult]:
    def raise_text(
        argv: tuple[str, ...],
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
    ) -> TextResult:
        raise err

    return raise_text


def _raise_bytes(
    exc_class: type[CommandExecutionError], message: str, exit_code: int
) -> Callable[..., RawCommandResult]:
    def raise_bytes(
        argv: tuple[str, ...],
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
    ) -> RawCommandResult:
        raise exc_class(
            message,
            exit_code=exit_code,
            stdout="",
            stderr="",
            argv=argv,
        )

    return raise_bytes


def _raise_text(
    exc_class: type[CommandExecutionError], message: str, exit_code: int
) -> Callable[..., TextResult]:
    def raise_text(
        argv: tuple[str, ...],
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
    ) -> TextResult:
        raise exc_class(
            message,
            exit_code=exit_code,
            stdout="",
            stderr="",
            argv=argv,
        )

    return raise_text


__all__ = [
    "configure_mock_transport",
    "invoke_client_operation",
]
