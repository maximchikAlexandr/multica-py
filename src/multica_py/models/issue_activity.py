from __future__ import annotations

import datetime

import msgspec

from multica_py.enums import MetadataValueType
from multica_py.models.common import CommentCursor, Page
from multica_py.types import MetadataValue

__all__ = [
    "CommentCursor",
    "IssueUsage",
    "MetadataEntry",
    "MetadataPage",
    "MetadataPredicate",
    "Page",
    "RunMessage",
    "Subscriber",
]


class Subscriber(msgspec.Struct, frozen=True, kw_only=True):
    user_type: str
    user_id: str
    issue_id: str | None = None
    reason: str | None = None
    created_at: str | None = None


class MetadataEntry(msgspec.Struct, frozen=True, kw_only=True):
    key: str
    value: MetadataValue


MetadataPage = Page[MetadataEntry]


class MetadataPredicate(msgspec.Struct, frozen=True, kw_only=True):
    key: str
    value: MetadataValue
    value_type: MetadataValueType | None = None


class RunMessage(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    run_id: str
    role: str
    content: str
    created_at: datetime.datetime | None = None


class IssueUsage(msgspec.Struct, frozen=True, kw_only=True):
    total_runs: int = 0
    total_tokens: int | None = None
    cost_usd: float | None = None
    period_start: datetime.datetime | None = None
    period_end: datetime.datetime | None = None
