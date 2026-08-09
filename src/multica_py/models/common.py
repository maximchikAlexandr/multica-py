from __future__ import annotations

from collections.abc import Iterator
from typing import Generic, TypeVar, cast, overload

import msgspec

T = TypeVar("T")


class CommentCursor(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    before: str
    before_id: str


_PAGE_ITEM_ALIASES = {
    "IssueListPage": "issues",
    "IssueChildrenResult": "children",
    "AutopilotListPage": "autopilots",
    "AutopilotRunListPage": "runs",
}


class _PageMeta(msgspec.StructMeta):
    def __call__(cls, *args: object, **kwargs: object) -> object:
        alias = _PAGE_ITEM_ALIASES.get(cls.__name__)
        if alias is not None and alias in kwargs:
            if "items" in kwargs:
                raise TypeError("Pass either items or its compatibility alias, not both.")
            normalized = dict(kwargs)
            normalized["items"] = normalized.pop(alias)
            return cast("object", super().__call__(*args, **normalized))
        return cast("object", super().__call__(*args, **kwargs))


class Page(msgspec.Struct, Generic[T], frozen=True, kw_only=True, metaclass=_PageMeta):
    items: tuple[T, ...] = ()
    limit: int | None = None
    offset: int | None = None
    total: int | None = None
    has_more: bool = False
    next_cursor: str | CommentCursor | None = None

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    @overload
    def __getitem__(self, index: int) -> T: ...

    @overload
    def __getitem__(self, index: slice[int | None, int | None, int | None]) -> tuple[T, ...]: ...

    def __getitem__(
        self, index: int | slice[int | None, int | None, int | None]
    ) -> T | tuple[T, ...]:
        return self.items[index]


class ActionResult(msgspec.Struct, Generic[T], frozen=True, kw_only=True):
    success: bool = True
    value: T | None = None
    message: str | None = None
