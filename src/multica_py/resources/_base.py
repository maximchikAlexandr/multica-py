from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, TypeVar

import msgspec

from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig

if TYPE_CHECKING:
    from multica_py.client import MulticaClient

S = TypeVar("S", bound=msgspec.Struct)
R = TypeVar("R", bound=msgspec.Struct)


def _resolve_request(request: R | None, kwargs: dict[str, object], cls: type[R]) -> R:
    if request is not None and kwargs:
        raise TypeError("Pass either a request object or keyword arguments, not both.")
    if request is not None:
        return request
    if not kwargs:
        raise TypeError(f"Pass a {cls.__name__} or its keyword arguments; got neither.")
    return cls(**kwargs)


class BaseResource:
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        self._transport = transport
        self._config = config
        self._client: MulticaClient | None = None

    def _set_client(self, client: MulticaClient) -> None:
        self._client = client

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
