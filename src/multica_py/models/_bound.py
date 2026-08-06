from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, ClassVar, Self, TypeGuard, cast

import msgspec

from multica_py.exceptions import DetachedEntityError

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


_RUNTIME_FIELDS = frozenset(
    {
        "_agents",
        "_autopilots",
        "_children",
        "_comments",
        "_files",
        "_issues",
        "_labels",
        "_members",
        "_messages",
        "_metadata",
        "_projects",
        "_pull_requests",
        "_repositories",
        "_resources",
        "_runtimes",
        "_runs",
        "_skills",
        "_squads",
        "_subscribers",
        "_tasks",
        "_triggers",
        "trigger_payload",
        "result",
    }
)


class _RuntimeHolder:
    """Slot-only base keeping runtime state outside the msgspec schema."""

    __slots__ = ("_runtime",)


# ``member_descriptor`` is supplied by CPython for the slot, but is not
# exposed by typeshed on the class object.
_RUNTIME_DESCRIPTOR = _RuntimeHolder._runtime  # type: ignore[attr-defined,misc]


def _runtime_state(obj: object) -> dict[str, object]:
    try:
        return cast("dict[str, object]", object.__getattribute__(obj, "_runtime"))
    except AttributeError:
        runtime: dict[str, object] = {}
        _RUNTIME_DESCRIPTOR.__set__(obj, runtime)  # type: ignore[misc]
        return runtime


def _get(obj: object, name: str) -> object:
    return cast("object", getattr(obj, name))


def _is_mapping(value: object) -> TypeGuard[Mapping[object, object]]:
    return isinstance(value, Mapping)


def _hashable(value: object) -> object:
    if _is_mapping(value):
        return tuple(sorted((key, _hashable(item)) for key, item in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_hashable(item) for item in value)
    return value


def _materialize_mappings(value: object) -> object:
    if _is_mapping(value):
        return {key: _materialize_mappings(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_materialize_mappings(item) for item in value)
    if isinstance(value, list):
        return [_materialize_mappings(item) for item in value]
    return value


class _BoundEntity(_RuntimeHolder, msgspec.Struct, frozen=True, kw_only=True, weakref=True):
    _client: object | None = msgspec.field(default=None, name="_client")

    _PUBLIC_FIELDS: ClassVar[tuple[str, ...]] = ()
    _RUNTIME_INIT_FIELDS: ClassVar[tuple[str, ...]] = ()

    def _require_client(
        self, *, entity_type: str, entity_id: str, relation_name: str
    ) -> MulticaClient:
        if self._client is None:
            raise DetachedEntityError(entity_type, entity_id, relation_name)
        return cast("MulticaClient", self._client)

    def detach(self) -> Self:
        return type(self).from_dict(self.to_dict())

    @classmethod
    def _normalize_from_dict(cls, data: dict[str, object]) -> dict[str, object]:
        return data

    @classmethod
    def _from_encoded_dict(cls, data: dict[str, object]) -> Self:
        return msgspec.convert(data, type=cls, strict=True)

    def _with_client(self, client: MulticaClient | None) -> Self:
        if client is None or client is self._client:
            return self
        result = msgspec.structs.replace(
            self,
            _client=client,
        )
        _runtime_state(result).update(_runtime_state(self))
        return result

    def _set_runtime(self, name: str, value: object) -> None:
        """Store relation state without mutating a frozen msgspec field.

        ``object.__setattr__`` happened to work for these private fields on
        some Python/msgspec combinations, but is rejected by Python 3.12.
        The slot-only private holder is used only for fixed runtime state;
        public model fields remain frozen and hashable.
        """
        if name not in _RUNTIME_FIELDS:
            raise AttributeError(f"unsupported runtime field: {name}")
        runtime = _runtime_state(self)
        runtime[name] = value

    def __getattribute__(self, name: str) -> object:
        if name in _RUNTIME_FIELDS:
            runtime = _runtime_state(self)
            sentinel = object()
            value = runtime.get(name, sentinel)
            if value is not sentinel:
                return value
        return cast("object", object.__getattribute__(self, name))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return all(_get(self, field) == _get(other, field) for field in self._PUBLIC_FIELDS)

    def __hash__(self) -> int:
        return hash(tuple(_hashable(_get(self, f)) for f in self._PUBLIC_FIELDS))

    def __repr__(self) -> str:
        fields = ", ".join(f"{f}={_get(self, f)!r}" for f in self._PUBLIC_FIELDS)
        return f"{type(self).__name__}({fields})"

    def to_dict(self) -> dict[str, object]:
        data = {f: _get(self, f) for f in self._PUBLIC_FIELDS}
        materialized = _materialize_mappings(data)
        return cast("dict[str, object]", msgspec.to_builtins(materialized))

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        unknown = set(data).difference(cls._PUBLIC_FIELDS)
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise ValueError(f"unknown bound-entity field(s): {names}")

        field_names = {field.name: field.encode_name for field in msgspec.structs.fields(cls)}
        normalized = cls._normalize_from_dict(data)
        encoded_data = {field_names[name]: value for name, value in normalized.items()}
        return cls._from_encoded_dict(encoded_data)

    def to_json(self) -> str:
        return msgspec.json.encode(self.to_dict()).decode()

    @classmethod
    def from_json(cls, payload: str | bytes) -> Self:
        data = msgspec.json.decode(payload, type=dict[str, object])
        return cls.from_dict(data)
