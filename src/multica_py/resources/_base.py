from __future__ import annotations

import datetime
from typing import TypeVar

import msgspec

from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig

T = TypeVar("T", bound=msgspec.Struct)


class BaseResource:
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        self._transport = transport
        self._config = config

    def _run_json_decode(
        self,
        args: tuple[str, ...],
        model_type: type[T],
        *,
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
    ) -> T:
        result = self._transport.run_bytes(
            (*args, "--output", "json"),
            stdin=stdin,
            timeout=timeout,
        )
        return decode_json(result.stdout, model_type, command=" ".join(result.argv))

    def _run_json_decode_list(
        self,
        args: tuple[str, ...],
        item_type: type[T],
        *,
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
    ) -> tuple[T, ...]:
        result = self._transport.run_bytes(
            (*args, "--output", "json"),
            stdin=stdin,
            timeout=timeout,
        )
        items = decode_json(result.stdout, list[item_type], command=" ".join(result.argv))  # type: ignore[valid-type]
        return tuple(items)
