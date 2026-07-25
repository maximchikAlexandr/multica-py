from __future__ import annotations

import enum

from multica_py._generated.approved_sdk import IssueSort, SortDirection

__all__ = [
    "CompatibilityPolicy",
    "IssueSort",
    "IssueStatus",
    "MetadataValueType",
    "OutputMode",
    "ProjectStatus",
    "SortDirection",
]


class IssueStatus(enum.StrEnum):
    backlog = "backlog"
    todo = "todo"
    in_progress = "in_progress"
    in_review = "in_review"
    done = "done"
    blocked = "blocked"
    cancelled = "cancelled"


class ProjectStatus(enum.StrEnum):
    planned = "planned"
    in_progress = "in_progress"
    paused = "paused"
    completed = "completed"
    cancelled = "cancelled"


class OutputMode(enum.StrEnum):
    json = "json"
    table = "table"
    text = "text"


class CompatibilityPolicy(enum.StrEnum):
    strict = "strict"
    warn = "warn"
    ignore = "ignore"


class MetadataValueType(enum.StrEnum):
    string = "string"
    integer = "integer"
    number = "number"
    boolean = "boolean"
    null = "null"
