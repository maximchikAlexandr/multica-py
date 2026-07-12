from __future__ import annotations

from typing import Generic, TypeVar

import msgspec

T = TypeVar("T")


class Page(msgspec.Struct, Generic[T], frozen=True, kw_only=True):
    items: tuple[T, ...]
    next_cursor: str | None = None


class ActionResult(msgspec.Struct, frozen=True, kw_only=True):
    success: bool = True
    message: str | None = None
