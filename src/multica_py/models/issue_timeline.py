from __future__ import annotations

import datetime

import msgspec

from multica_py.models.common import Page
from multica_py.types import JsonValue

__all__ = ["IssueTimelineEvent", "IssueTimelinePage"]


class IssueTimelineEvent(msgspec.Struct, frozen=True, kw_only=True):
    id: str = ""
    type: str = ""
    action: str | None = None
    actor_type: str | None = None
    actor_id: str | None = None
    summary: str | None = None
    created_at: datetime.datetime | None = None
    data: JsonValue | None = None
    metadata: JsonValue | None = None


IssueTimelinePage = Page[IssueTimelineEvent]
