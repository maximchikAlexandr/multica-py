from __future__ import annotations

import hashlib
import json

import msgspec
import msgspec.structs

from .models import (
    JsonScalar,
    SemanticCLIContract,
    UpstreamContractDiff,
    UpstreamState,
)


def canonical_bytes(
    obj: msgspec.Struct | dict[str, object] | list[object] | JsonScalar,
) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_default,
    ).encode("utf-8")


def _default(
    value: msgspec.Struct | tuple[object, ...] | object,
) -> str | int | float | bool | None | list[object] | dict[str, object]:
    if isinstance(value, msgspec.Struct):  # type: ignore[misc]
        raw: dict[str, object] = msgspec.structs.asdict(value)
        return raw
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"cannot canonicalize {type(value).__name__}")


def semantic_hash(
    obj: msgspec.Struct | dict[str, object] | list[object] | JsonScalar,
) -> str:
    payload: msgspec.Struct | dict[str, object] | list[object] | JsonScalar
    if isinstance(obj, SemanticCLIContract):
        payload = _strip_volatile_contract(obj)
    elif isinstance(obj, (UpstreamState, UpstreamContractDiff)):
        built: object = msgspec.to_builtins(obj)
        if not isinstance(built, dict):
            raise TypeError("msgspec.to_builtins did not return a dict")
        payload = built
    else:
        payload = obj
    digest = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    return f"sha256:{digest}"


def _strip_volatile_contract(contract: SemanticCLIContract) -> dict[str, object]:
    state: object = msgspec.to_builtins(contract)
    if not isinstance(state, dict):
        raise TypeError("SemanticCLIContract must canonicalize to a JSON object")
    state.pop("observation", None)
    artifact = state.get("artifact")
    if isinstance(artifact, dict):
        artifact.pop("semantic_hash", None)
    return state
