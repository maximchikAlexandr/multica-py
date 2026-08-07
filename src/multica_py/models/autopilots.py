from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Generic, TypeVar, overload

import msgspec

from multica_py.enums import AutopilotExecutionMode
from multica_py.models.common import CommentCursor, Page
from multica_py.sentinels import Unset, UnsetType

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


class AutopilotTriggerCreate(msgspec.Struct, frozen=True, kw_only=True):
    title: str
    kind: str


class AutopilotTriggerUpdate(msgspec.Struct, frozen=True, kw_only=True):
    title: str | UnsetType = Unset
    kind: str | UnsetType = Unset

    def __post_init__(self) -> None:
        if self.title is None:
            raise TypeError("title must be non-null")
        if self.kind is None:
            raise TypeError("kind must be non-null")


class AutopilotUpdateRequest(msgspec.Struct, frozen=True, kw_only=True):
    title: str | UnsetType = Unset
    agent: str | UnsetType = Unset
    priority: str | UnsetType = Unset
    status: str | UnsetType = Unset
    execution_mode: AutopilotExecutionMode | UnsetType = Unset
    description: str | None | UnsetType = Unset
    project_id: str | None | UnsetType = Unset
    issue_title_template: str | None | UnsetType = Unset
    subscribers: tuple[str, ...] | UnsetType = Unset

    def __post_init__(self) -> None:
        if self.title is None:
            raise TypeError("title must be non-null")
        if self.agent is None:
            raise TypeError("agent must be non-null")
        if self.priority is None:
            raise TypeError("priority must be non-null")
        if self.status is None:
            raise TypeError("status must be non-null")
        if self.execution_mode is None:
            raise TypeError("execution_mode must be non-null")
        if self.subscribers is None:
            raise TypeError("subscribers must be non-null")
