from __future__ import annotations

from collections.abc import Iterator
from typing import Generic, TypeVar, cast, overload

import msgspec

T = TypeVar("T")


class CommentCursor(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    before: str
    before_id: str


class _PageSequence(Generic[T]):
    def _sequence_items(self) -> tuple[T, ...]:
        return cast("tuple[T, ...]", getattr(self, "items"))

    def __iter__(self) -> Iterator[T]:
        return iter(self._sequence_items())

    def __len__(self) -> int:
        return len(self._sequence_items())

    @overload
    def __getitem__(self, index: int) -> T: ...

    @overload
    def __getitem__(self, index: slice[int | None, int | None, int | None]) -> tuple[T, ...]: ...

    def __getitem__(
        self, index: int | slice[int | None, int | None, int | None]
    ) -> T | tuple[T, ...]:
        return self._sequence_items()[index]


class Page(_PageSequence[T], msgspec.Struct, Generic[T], frozen=True, kw_only=True):
    items: tuple[T, ...]
    limit: int | None = None
    offset: int | None = None
    total: int | None = None
    has_more: bool = False
    next_cursor: str | CommentCursor | None = None


class ActionResult(msgspec.Struct, Generic[T], frozen=True, kw_only=True):
    success: bool = True
    value: T | None = None
    message: str | None = None
