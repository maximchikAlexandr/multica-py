from __future__ import annotations

import datetime
import os
import pathlib
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, cast

import msgspec

from multica_py._internal.commands import Command, _CommandPlan, _Step, _TempProvider
from multica_py._internal.decoders import decode_json
from multica_py._internal.redaction import collect_secret_values, redact_text
from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions
from multica_py.models.common import ActionResult, Page
from multica_py.process import ManagedProcess
from multica_py.sentinels import Unset

if TYPE_CHECKING:
    from multica_py.client import MulticaClient
    from multica_py.resources.cli import CliResult

S = TypeVar("S", bound=msgspec.Struct)
T = TypeVar("T")


def _redacted_text(value: object, *, secret_values: tuple[str, ...] = ()) -> str | None:
    text = value.text if isinstance(value, TextResult) else value if isinstance(value, str) else ""
    return redact_text(text, secret_values=secret_values).strip() or None


def _page_items(value: Page[S] | tuple[S, ...]) -> tuple[S, ...]:
    return value.items if isinstance(value, Page) else value


def _validate_optional_string(value: object, field_name: str) -> None:
    if value is not None and value is not Unset and not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")


def _normalize_description_file(value: str | os.PathLike[str], *, cwd: pathlib.Path | None) -> str:
    try:
        raw_value = cast("str | bytes", os.fspath(value))
    except TypeError as error:
        raise TypeError("description_file must be a string or path-like value") from error
    if isinstance(raw_value, bytes):
        raise TypeError("description_file must be a text path, not bytes")
    if not raw_value.strip():
        raise ValueError("description_file must be nonblank when provided")
    if cwd is None:
        return os.path.abspath(raw_value)
    return os.path.abspath(os.path.join(os.fspath(cwd), raw_value))


def _is_transport(value: object) -> bool:
    return isinstance(value, CliTransport)


class BaseResource:
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        self._transport = transport
        self._config = config
        self._client: MulticaClient | None = None

    def _set_client(self, client: MulticaClient) -> None:
        self._client = client

    def _effective_config(self, options: OperationOptions | None = None) -> ClientConfig:
        if options is None:
            return msgspec.structs.replace(self._config)
        changes = {
            field_name: value
            for field_name, value in (
                ("profile", options.profile),
                ("workspace_id", options.workspace_id),
                ("timeout", options.timeout),
                ("cwd", options.cwd),
                ("environment", options.environment),
            )
            if value is not msgspec.UNSET
        }
        return msgspec.structs.replace(self._config, **changes)

    def _transport_snapshot(self, config: ClientConfig) -> CliTransport:
        transport_snapshot = self._transport._snapshot(config)
        if not _is_transport(transport_snapshot):
            return self._transport
        return transport_snapshot

    def _plan(
        self,
        *,
        steps: tuple[_Step, ...],
        finalize: Callable[[tuple[object, ...]], T],
        temp_provider: _TempProvider | None = None,
        options: OperationOptions | None = None,
    ) -> Command[T]:
        config_snapshot = self._effective_config(options)
        transport_snapshot = self._transport_snapshot(config_snapshot)
        return Command(
            _CommandPlan(
                config_snapshot=config_snapshot,
                transport=transport_snapshot,
                steps=steps,
                finalize=finalize,
                _temp_provider=temp_provider,
            )
        )

    def _plan_decode(
        self,
        args: tuple[str, ...],
        model_type: type[S],
    ) -> tuple[tuple[str, ...], Callable[[bytes, str], object]]:
        def decode(stdout: bytes, command: str) -> object:
            return decode_json(stdout, model_type, command=command)

        return (*args, "--output", "json"), decode

    def _plan_decode_list(
        self,
        args: tuple[str, ...],
        item_type: type[S],
    ) -> tuple[tuple[str, ...], Callable[[bytes, str], object]]:
        def decode(stdout: bytes, command: str) -> object:
            items = decode_json(stdout, list[item_type], command=command)  # type: ignore[valid-type]
            return tuple(items)

        return (*args, "--output", "json"), decode

    def _decoded_command(
        self,
        args: tuple[str, ...],
        model_type: type[S],
        *,
        options: OperationOptions | None = None,
    ) -> Command[S]:
        plan_args, decode = self._plan_decode(args, model_type)
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("S", results[0]),
            options=options,
        )

    def _decoded_list_command(
        self,
        args: tuple[str, ...],
        item_type: type[S],
        *,
        options: OperationOptions | None = None,
    ) -> Command[tuple[S, ...]]:
        plan_args, decode = self._plan_decode_list(args, item_type)
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("tuple[S, ...]", results[0]),
            options=options,
        )

    def _decoded_page_command(
        self,
        args: tuple[str, ...],
        item_type: type[S],
        *,
        options: OperationOptions | None = None,
    ) -> Command[Page[S]]:
        return self._decoded_list_command(args, item_type, options=options)._map(
            lambda items: Page(items=items, total=len(items))
        )

    def _text_command(
        self,
        args: tuple[str, ...],
        *,
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
        options: OperationOptions | None = None,
    ) -> Command[str]:
        return self._plan(
            steps=(_Step(args, "run_text", stdin=stdin, timeout=timeout),),
            finalize=lambda results: cast("TextResult", results[0]).text,
            options=options,
        )

    def _action_command(
        self,
        args: tuple[str, ...],
        *,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[None]]:
        secret_values = collect_secret_values(args)

        def finalize(results: tuple[object, ...]) -> ActionResult[None]:
            return ActionResult(
                value=None,
                message=_redacted_text(results[0], secret_values=secret_values),
            )

        return self._plan(
            steps=(_Step(args, "run_text"),),
            finalize=finalize,
            options=options,
        )

    def _action_text_command(
        self,
        args: tuple[str, ...],
        *,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[str]]:
        secret_values = collect_secret_values(args)

        def finalize(results: tuple[object, ...]) -> ActionResult[str]:
            return ActionResult(value=_redacted_text(results[0], secret_values=secret_values) or "")

        return self._plan(
            steps=(_Step(args, "run_text"),),
            finalize=finalize,
            options=options,
        )

    def _action_decoded_command(
        self,
        args: tuple[str, ...],
        model_type: type[S],
        *,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[S]]:
        return self._decoded_command(args, model_type, options=options)._map(
            lambda value: ActionResult(value=value)
        )

    def _raw_command(
        self,
        args: tuple[str, ...],
        *,
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
        options: OperationOptions | None = None,
    ) -> Command[CliResult]:
        from multica_py.resources.cli import decode_cli_result

        return self._plan(
            steps=(_Step(args, "run_bytes", stdin=stdin, timeout=timeout),),
            finalize=lambda results: decode_cli_result(cast("RawCommandResult", results[0])),
            options=options,
        )

    def _spawn_command(
        self,
        args: tuple[str, ...],
        *,
        options: OperationOptions | None = None,
    ) -> Command[ManagedProcess]:
        return self._plan(
            steps=(_Step(args, "spawn"),),
            finalize=lambda results: cast("ManagedProcess", results[0]),
            options=options,
        )
