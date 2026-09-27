from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Generic, TypeVar, overload

import msgspec

from multica_py._internal.redaction import REDACTED
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


class AutopilotTrigger(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    autopilot_id: str
    kind: str
    enabled: bool
    cron_expression: str | None = None
    timezone: str | None = None
    next_run_at: datetime.datetime | None = None
    label: str | None = None
    last_fired_at: datetime.datetime | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


class AutopilotTriggerRotateURL(msgspec.Struct, frozen=True, kw_only=True):
    autopilot_id: str | None = None
    trigger_id: str | None = None
    url: str | None = None
    path: str | None = None
    token: str | None = None
    warning: str | None = None

    def __repr__(self) -> str:
        return (
            "AutopilotTriggerRotateURL("
            f"autopilot_id={self.autopilot_id!r}, "
            f"trigger_id={self.trigger_id!r}, "
            f"url={REDACTED if self.url is not None else None!r}, "
            f"path={REDACTED if self.path is not None else None!r}, "
            f"token={REDACTED if self.token is not None else None!r}, "
            f"warning={self.warning!r})"
        )

    def to_dict(self) -> dict[str, object]:
        """Return the ordinary redacted projection of a rotation result."""
        return {
            "autopilot_id": self.autopilot_id,
            "trigger_id": self.trigger_id,
            "url": REDACTED if self.url is not None else None,
            "path": REDACTED if self.path is not None else None,
            "token": REDACTED if self.token is not None else None,
            "warning": self.warning,
        }
