from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Generic, TypeVar, overload

import msgspec

from multica_py.models.common import CommentCursor, Page

TAutopilot = TypeVar("TAutopilot")
TAutopilotRun = TypeVar("TAutopilotRun")


class AutopilotSubscriber(msgspec.Struct, frozen=True, kw_only=True):
    user_type: str
    user_id: str
    created_at: datetime.datetime | None = None


if TYPE_CHECKING:

    class _AutopilotListPageStatic(
        Page[TAutopilot], Generic[TAutopilot], frozen=True, kw_only=True
    ):
        total: int = 0

        @overload
        def __init__(
            self,
            *,
            items: tuple[TAutopilot, ...] = ...,
            limit: int | None = ...,
            offset: int | None = ...,
            total: int = ...,
            has_more: bool = ...,
            next_cursor: str | CommentCursor | None = ...,
        ) -> None: ...

        @overload
        def __init__(
            self,
            *,
            autopilots: tuple[TAutopilot, ...] = ...,
            limit: int | None = ...,
            offset: int | None = ...,
            total: int = ...,
            has_more: bool = ...,
            next_cursor: str | CommentCursor | None = ...,
        ) -> None: ...

        def __init__(self, **kwargs: object) -> None: ...

        @property
        def autopilots(self) -> tuple[TAutopilot, ...]:
            return self.items

    AutopilotListPage = _AutopilotListPageStatic

    class _AutopilotRunListPageStatic(
        Page[TAutopilotRun], Generic[TAutopilotRun], frozen=True, kw_only=True
    ):
        total: int = 0

        @overload
        def __init__(
            self,
            *,
            items: tuple[TAutopilotRun, ...] = ...,
            limit: int | None = ...,
            offset: int | None = ...,
            total: int = ...,
            has_more: bool = ...,
            next_cursor: str | CommentCursor | None = ...,
        ) -> None: ...

        @overload
        def __init__(
            self,
            *,
            runs: tuple[TAutopilotRun, ...] = ...,
            limit: int | None = ...,
            offset: int | None = ...,
            total: int = ...,
            has_more: bool = ...,
            next_cursor: str | CommentCursor | None = ...,
        ) -> None: ...

        def __init__(self, **kwargs: object) -> None: ...

        @property
        def runs(self) -> tuple[TAutopilotRun, ...]:
            return self.items

    AutopilotRunListPage = _AutopilotRunListPageStatic

else:

    class AutopilotListPage(Page[TAutopilot], Generic[TAutopilot], frozen=True, kw_only=True):
        total: int = 0

        @property
        def autopilots(self) -> tuple[TAutopilot, ...]:
            return self.items

    class AutopilotRunListPage(
        Page[TAutopilotRun], Generic[TAutopilotRun], frozen=True, kw_only=True
    ):
        total: int = 0

        @property
        def runs(self) -> tuple[TAutopilotRun, ...]:
            return self.items


class TriggerConfigItem(msgspec.Struct, frozen=True, kw_only=True):
    key: str
    value: str


class AutopilotTrigger(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    type: str
    config: tuple[TriggerConfigItem, ...] = ()
