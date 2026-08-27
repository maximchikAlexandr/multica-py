from __future__ import annotations

import datetime
from collections.abc import Mapping

import msgspec

from multica_py.enums import MetadataValueType
from multica_py.models.common import CommentCursor, Page
from multica_py.types import JsonValue, MetadataValue

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
    task_id: str
    seq: int
    type: str
    issue_id: str | None = None
    tool: str | None = None
    content: str | None = None
    input: Mapping[str, JsonValue] | None = None
    output: str | None = None
    created_at: datetime.datetime | None = None


class IssueUsage(msgspec.Struct, frozen=True, kw_only=True):
    total_runs: int = 0
    total_tokens: int | None = None
    cost_usd: float | None = None
    period_start: datetime.datetime | None = None
    period_end: datetime.datetime | None = None
    task_count: int | None = None
    total_input_tokens: int | None = None
    total_output_tokens: int | None = None
    total_cache_read_tokens: int | None = None
    total_cache_write_tokens: int | None = None
    cost_usd_ticks: int | None = None
    uncosted_input_tokens: int | None = None
    uncosted_output_tokens: int | None = None
    uncosted_cache_read_tokens: int | None = None
    uncosted_cache_write_tokens: int | None = None
