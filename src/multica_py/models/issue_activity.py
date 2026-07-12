from __future__ import annotations

import datetime

import msgspec

from multica_py.enums import MetadataValueType
from multica_py.types import MetadataValue


class Comment(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    body: str
    thread_id: str | None = None
    author_id: str | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


class CommentThread(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    comments: tuple[Comment, ...] = ()
    resolved: bool = False
    updated_at: datetime.datetime | None = None


class CommentListFlatRequest(msgspec.Struct, frozen=True, kw_only=True):
    issue_id: str
    cursor: str | None = None
    limit: int | None = None
    since: datetime.datetime | None = None


class CommentListThreadRequest(msgspec.Struct, frozen=True, kw_only=True):
    issue_id: str
    thread_id: str
    cursor: str | None = None
    limit: int | None = None
    since: datetime.datetime | None = None


class CommentListRecentRequest(msgspec.Struct, frozen=True, kw_only=True):
    issue_id: str
    cursor: str | None = None
    limit: int | None = None
    since: datetime.datetime | None = None


class Subscriber(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str | None = None
    type: str | None = None


class MetadataEntry(msgspec.Struct, frozen=True, kw_only=True):
    key: str
    value: MetadataValue


class MetadataPredicate(msgspec.Struct, frozen=True, kw_only=True):
    key: str
    value: MetadataValue
    value_type: MetadataValueType | None = None


class MetadataListRequest(msgspec.Struct, frozen=True, kw_only=True):
    issue_id: str
    predicates: tuple[MetadataPredicate, ...] = ()
    cursor: str | None = None
    limit: int | None = None


class MetadataSetRequest(msgspec.Struct, frozen=True, kw_only=True):
    issue_id: str
    key: str
    value: MetadataValue
    value_type: MetadataValueType | None = None


class TaskRun(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    status: str
    agent_id: str | None = None
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None


class RunMessage(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    run_id: str
    role: str
    content: str
    created_at: datetime.datetime | None = None


class IssueUsage(msgspec.Struct, frozen=True, kw_only=True):
    total_runs: int = 0
    total_tokens: int | None = None
    period_start: datetime.datetime | None = None
    period_end: datetime.datetime | None = None
