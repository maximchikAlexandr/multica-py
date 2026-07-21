from __future__ import annotations

import datetime

import msgspec

from multica_py.enums import IssueStatus
from multica_py.types import MetadataValue


class IssueSummary(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    title: str
    status: IssueStatus
    priority: str | None = None


class IssueAssignee(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str | None = None
    type: str | None = None


class LinkedPullRequest(msgspec.Struct, frozen=True, kw_only=True):
    url: str
    title: str | None = None
    state: str | None = None


class IssueChildStageGroup(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    count: int


class IssueMetadataItem(msgspec.Struct, frozen=True, kw_only=True):
    key: str
    value: MetadataValue


class Issue(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    title: str
    description: str | None = None
    status: IssueStatus
    priority: str | None = None
    assignee: IssueAssignee | None = None
    pull_requests: tuple[LinkedPullRequest, ...] = ()
    children: tuple[IssueChildStageGroup, ...] = ()
    labels: tuple[str, ...] = ()
    metadata: tuple[IssueMetadataItem, ...] = ()
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


class IssueListFilter(msgspec.Struct, frozen=True, kw_only=True):
    status: IssueStatus | None = None
    priority: str | None = None
    assignee_id: str | None = None
    limit: int | None = None


class InlineDescription(msgspec.Struct, frozen=True, kw_only=True):
    text: str


class FileDescription(msgspec.Struct, frozen=True, kw_only=True):
    path: str


class StdinDescription(msgspec.Struct, frozen=True, kw_only=True):
    pass


class NoDescription(msgspec.Struct, frozen=True, kw_only=True):
    pass


IssueDescriptionInput = InlineDescription | FileDescription | StdinDescription | NoDescription


_VALID_DESC_TYPES = (InlineDescription, FileDescription, StdinDescription, NoDescription)  # type: ignore[misc]


class IssueCreateRequest(msgspec.Struct, frozen=True, kw_only=True):
    """Request to create an issue via the CLI.

    ``label_ids`` are label UUIDs attached after creation. ``Issue.labels`` on
    the returned issue are label names from the wire response, not these IDs.
    """

    title: str
    description_input: IssueDescriptionInput = NoDescription()
    priority: str | None = None
    assignee_id: str | None = None
    label_ids: tuple[str, ...] = ()
    project_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.description_input, _VALID_DESC_TYPES):  # type: ignore[misc]
            raise TypeError(
                f"description_input must be one of {_VALID_DESC_TYPES}, "
                f"got {type(self.description_input).__name__}"
            )
        if self.project_id is not None and not self.project_id.strip():
            raise ValueError("project_id must be non-empty when set")


class IssueUpdateRequest(msgspec.Struct, frozen=True, kw_only=True):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    assignee_id: str | None = None
    project_id: str | None = None

    def __post_init__(self) -> None:
        if self.project_id is not None and not self.project_id.strip():
            raise ValueError("project_id must be non-empty when set")


class IssueReorderRequest(msgspec.Struct, frozen=True, kw_only=True):
    issue_id: str
    before_id: str | None = None
    after_id: str | None = None
    top: bool = False
    bottom: bool = False

    def __post_init__(self) -> None:
        selected = sum(
            (
                self.before_id is not None,
                self.after_id is not None,
                self.top,
                self.bottom,
            )
        )
        if selected != 1:
            raise ValueError("Exactly one reorder target must be set")


class IssueAssignmentRequest(msgspec.Struct, frozen=True, kw_only=True):
    issue_id: str
    member_id: str | None = None
    agent_id: str | None = None
    squad_id: str | None = None
    unassign: bool = False

    def __post_init__(self) -> None:
        selected = sum(
            (
                self.member_id is not None,
                self.agent_id is not None,
                self.squad_id is not None,
                self.unassign,
            )
        )
        if selected != 1:
            raise ValueError("Exactly one assignment target must be set")
