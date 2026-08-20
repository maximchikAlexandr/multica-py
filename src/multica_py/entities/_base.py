from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING, Protocol, Self, TypeGuard, cast

import msgspec

from multica_py.exceptions import DetachedEntityError

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


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


def _reference_presence(entity: _BoundEntity, field_name: str, value: object) -> str:
    """Return decoded presence, conservatively classifying manual values."""
    try:
        seeds = cast(
            "tuple[tuple[str, str], ...]", object.__getattribute__(entity, "_wire_presence")
        )
    except AttributeError:
        seeds = ()
    for name, seed in seeds:
        if name == field_name:
            return seed
    return "missing" if value is None else "value"


@dataclass(frozen=True)
class _EntityPolicy:
    """Schema-derived names used by all bound-entity value operations."""

    public_fields: tuple[str, ...]
    private_fields: frozenset[str]
    constructor_seeds: tuple[str, ...]
    encoded_names: tuple[tuple[str, str], ...]
    runtime_overlays: frozenset[str]

    @property
    def runtime_fields(self) -> frozenset[str]:
        return self.private_fields | self.runtime_overlays

    def encoded_name(self, field_name: str) -> str:
        for python_name, encoded_name in self.encoded_names:
            if python_name == field_name:
                return encoded_name
        raise KeyError(field_name)


class _DetachField(Protocol):
    name: str
    encode_name: str
    default: object
    default_factory: object


_AUTOPILOT_RUN_RUNTIME_OVERLAYS = frozenset(("trigger_payload", "result"))


def _overlay_names(entity_type: type[object]) -> frozenset[str]:
    """Return overlays for the one concrete entity with runtime JSON fields."""
    from multica_py.entities.autopilots import AutopilotRun

    return _AUTOPILOT_RUN_RUNTIME_OVERLAYS if entity_type is AutopilotRun else frozenset()


class _BoundEntity(_RuntimeHolder, msgspec.Struct, frozen=True, kw_only=True, weakref=True):
    _client: object | None = msgspec.field(default=None, name="_client")

    def _require_client(
        self, *, entity_type: str, entity_id: str, relation_name: str
    ) -> MulticaClient:
        if self._client is None:
            raise DetachedEntityError(entity_type, entity_id, relation_name)
        return cast("MulticaClient", self._client)

    def detach(self) -> Self:
        replacements: dict[str, object] = {"_client": None}
        fields = cast("tuple[_DetachField, ...]", msgspec.structs.fields(type(self)))
        for field in fields:
            if field.name in {"_client", "_wire_presence"}:
                continue
            if not field.name.startswith("_"):
                if field.encode_name.startswith("_") and field.name in {"triggers", "subscribers"}:
                    replacements[field.name] = msgspec.UNSET
                continue
            if field.default is not msgspec.NODEFAULT:
                replacements[field.name] = field.default
            elif callable(field.default_factory):
                factory = cast("Callable[[], object]", field.default_factory)
                replacements[field.name] = factory()
        return msgspec.structs.replace(self, **replacements)

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

    def _clone_for_client(self, client: MulticaClient | None) -> Self:
        """Clone immutable target data with fresh destination-local runtime state."""
        return msgspec.structs.replace(self, _client=client)

    def _set_runtime(self, name: str, value: object) -> None:
        """Store relation state without mutating a frozen msgspec field.

        ``object.__setattr__`` happened to work for these private fields on
        some Python/msgspec combinations, but is rejected by Python 3.12.
        The slot-only private holder is used only for fixed runtime state;
        public model fields remain frozen and hashable.
        """
        if name not in _entity_policy(type(self)).runtime_fields:
            raise AttributeError(f"unsupported runtime field: {name}")
        runtime = _runtime_state(self)
        runtime[name] = value

    def __getattribute__(self, name: str) -> object:
        if name in _entity_policy(type(self)).runtime_fields:
            runtime = _runtime_state(self)
            sentinel = object()
            value = runtime.get(name, sentinel)
            if value is not sentinel:
                return value
        return cast("object", object.__getattribute__(self, name))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        policy = _entity_policy(type(self))
        return all(_get(self, field) == _get(other, field) for field in policy.public_fields)

    def __hash__(self) -> int:
        policy = _entity_policy(type(self))
        return hash(tuple(_hashable(_get(self, field)) for field in policy.public_fields))

    def __repr__(self) -> str:
        policy = _entity_policy(type(self))
        fields = ", ".join(f"{field}={_get(self, field)!r}" for field in policy.public_fields)
        return f"{type(self).__name__}({fields})"

    def to_dict(self) -> dict[str, object]:
        policy = _entity_policy(type(self))
        data = {field: _get(self, field) for field in policy.public_fields}
        materialized = _materialize_mappings(data)
        return cast("dict[str, object]", msgspec.to_builtins(materialized))

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        policy = _entity_policy(cls)
        unknown = set(data).difference(policy.public_fields)
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise ValueError(f"unknown bound-entity field(s): {names}")

        normalized = cls._normalize_from_dict(data)
        encoded_data = {policy.encoded_name(name): value for name, value in normalized.items()}
        return cls._from_encoded_dict(encoded_data)

    def to_json(self) -> str:
        return msgspec.json.encode(self.to_dict()).decode()

    @classmethod
    def from_json(cls, payload: str | bytes) -> Self:
        data = msgspec.json.decode(payload, type=dict[str, object])
        return cls.from_dict(data)


@cache  # type: ignore[misc]
def _entity_policy(entity_type: type[_BoundEntity]) -> _EntityPolicy:
    fields = msgspec.structs.fields(entity_type)
    encoded_names = tuple((field.name, field.encode_name) for field in fields)
    runtime_overlays = _overlay_names(entity_type)
    public_fields = tuple(
        field.name
        for field in fields
        if not field.name.startswith("_") and not field.encode_name.startswith("_")
    )
    private_fields = frozenset(field.name for field in fields if field.name.startswith("_"))
    constructor_seeds = tuple(
        field.name
        for field in fields
        if not field.name.startswith("_") and field.encode_name.startswith("_")
    )
    return _EntityPolicy(
        public_fields=public_fields,
        private_fields=private_fields,
        constructor_seeds=constructor_seeds,
        encoded_names=encoded_names,
        runtime_overlays=runtime_overlays,
    )


def _normalize_entity_id(
    value: str | _BoundEntity,
    *,
    field_name: str,
    allowed_types: tuple[type[_BoundEntity], ...],
) -> str:
    """Return an ID from a supported ID/entity input.

    The allow-list is deliberately supplied by the caller.  Merely exposing an
    ``id`` attribute is not enough: accepting arbitrary structural objects here
    would make a typo in a public reference silently turn into a CLI request.
    """
    if isinstance(value, str):
        if not value.strip():
            raise ValueError(f"{field_name} must be non-empty")
        return value
    if not isinstance(value, allowed_types):
        names = ", ".join(entity.__name__ for entity in allowed_types)
        raise TypeError(f"{field_name} must be a non-empty ID or one of: {names}")
    entity_id = value.id
    if not isinstance(entity_id, str) or not entity_id.strip():
        raise ValueError(f"{field_name} entity has an invalid ID")
    return entity_id
