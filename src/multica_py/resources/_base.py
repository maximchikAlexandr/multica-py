from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, cast

import msgspec

from multica_py._internal.commands import Command, _CommandPlan, _Step, _TempProvider
from multica_py._internal.decoders import decode_json
from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.process import ManagedProcess

if TYPE_CHECKING:
    from multica_py.client import MulticaClient

S = TypeVar("S", bound=msgspec.Struct)
R = TypeVar("R", bound=msgspec.Struct)
T = TypeVar("T")


def _is_transport(value: object) -> bool:
    return isinstance(value, CliTransport)


def _resolve_request(
    request: R | None,
    kwargs: dict[str, object],
    cls: type[R],
    *,
    allow_empty: bool = False,
) -> R:
    if request is not None and kwargs:
        raise TypeError("Pass either a request object or keyword arguments, not both.")
    if request is not None:
        if not isinstance(request, cls):
            raise TypeError(f"Expected {cls.__name__}, got {type(request).__name__}.")
        return request
    if not kwargs:
        if allow_empty:
            return cls()
        raise TypeError(f"Pass a {cls.__name__} or its keyword arguments; got neither.")
    return cls(**kwargs)


class BaseResource:
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        self._transport = transport
        self._config = config
        self._client: MulticaClient | None = None

    def _set_client(self, client: MulticaClient) -> None:
        self._client = client

    def _plan(
        self,
        *,
        steps: tuple[_Step, ...],
        finalize: Callable[[tuple[object, ...]], T],
        temp_provider: _TempProvider | None = None,
    ) -> Command[T]:
        config_snapshot = msgspec.structs.replace(self._config)
        transport_snapshot = self._transport._snapshot(config_snapshot)
        if not _is_transport(transport_snapshot):
            transport_snapshot = self._transport
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

    def _decoded_command(self, args: tuple[str, ...], model_type: type[S]) -> Command[S]:
        plan_args, decode = self._plan_decode(args, model_type)
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("S", results[0]),
        )

    def _decoded_list_command(
        self, args: tuple[str, ...], item_type: type[S]
    ) -> Command[tuple[S, ...]]:
        plan_args, decode = self._plan_decode_list(args, item_type)
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("tuple[S, ...]", results[0]),
        )

    def _text_command(
        self,
        args: tuple[str, ...],
        *,
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
    ) -> Command[str]:
        return self._plan(
            steps=(_Step(args, "run_text", stdin=stdin, timeout=timeout),),
            finalize=lambda results: cast("TextResult", results[0]).text,
        )

    def _none_command(self, args: tuple[str, ...]) -> Command[None]:
        return self._plan(
            steps=(_Step(args, "run_text"),),
            finalize=lambda results: None,
        )

    def _raw_command(
        self,
        args: tuple[str, ...],
        *,
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
    ) -> Command[RawCommandResult]:
        return self._plan(
            steps=(_Step(args, "run_bytes", stdin=stdin, timeout=timeout),),
            finalize=lambda results: cast("RawCommandResult", results[0]),
        )

    def _spawn_command(self, args: tuple[str, ...]) -> Command[ManagedProcess]:
        return self._plan(
            steps=(_Step(args, "spawn"),),
            finalize=lambda results: cast("ManagedProcess", results[0]),
        )

    def _run_json_decode(
        self,
        args: tuple[str, ...],
        model_type: type[S],
        *,
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
    ) -> S:
        result = self._transport.run_bytes(
            (*args, "--output", "json"),
            stdin=stdin,
            timeout=timeout,
        )
        return decode_json(result.stdout, model_type, command=" ".join(result.argv))

    def _run_json_decode_list(
        self,
        args: tuple[str, ...],
        item_type: type[S],
        *,
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
    ) -> tuple[S, ...]:
        result = self._transport.run_bytes(
            (*args, "--output", "json"),
            stdin=stdin,
            timeout=timeout,
        )
        items = decode_json(result.stdout, list[item_type], command=" ".join(result.argv))  # type: ignore[valid-type]
        return tuple(items)
