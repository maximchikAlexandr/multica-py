from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast, overload

import msgspec

from multica_py.enums import IssueStatus
from multica_py.models.common import CommentCursor, Page
from multica_py.models.properties import PropertyListValue
from multica_py.types import MetadataValue

if TYPE_CHECKING:
    from multica_py.entities.agents import Agent
    from multica_py.entities.issues import Issue
    from multica_py.entities.projects import Project
    from multica_py.entities.squads import Squad
    from multica_py.entities.workspaces import WorkspaceMember

    type AssignmentTarget = str | Agent | Squad | WorkspaceMember
    type IssueReference = str | Issue
    type ProjectReference = str | Project
else:
    # The runtime validator uses an explicit allow-list; this fallback keeps
    # the aliases importable without importing resource modules cyclically.
    from multica_py.entities._base import _BoundEntity

    type AssignmentTarget = str | _BoundEntity
    type IssueReference = str | _BoundEntity
    type ProjectReference = str | _BoundEntity


class IssueMetadataItem(msgspec.Struct, frozen=True, kw_only=True):
    key: str
    value: MetadataValue


class IssueAssignee(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str | None = None
    type: str | None = None


class DuplicateIssueReference(msgspec.Struct, frozen=True, kw_only=True):
    """Read-only snapshot of the issue that caused a duplicate."""

    id: str
    identifier: str
    title: str
    status: str


class IssuePropertyAssignment(msgspec.Struct, frozen=True, kw_only=True):
    """One ordered, atomic property assignment for issue creation."""

    reference: str
    value: str | PropertyListValue

    def __post_init__(self) -> None:
        if type(self.reference) is not str:
            raise TypeError("reference must be a string")
        if not self.reference.strip():
            raise ValueError("reference must be nonblank")
        if type(self.value) is str:
            return
        if type(self.value) is not tuple:
            raise TypeError("value must be a string")
        if not self.value:
            raise ValueError("value must contain at least one string")
        if any(type(item) is not str for item in self.value):
            raise TypeError("value tuple must contain only strings")
        if any(not item.strip() for item in self.value):
            raise ValueError("value tuple cannot contain blank strings")
        if len(set(self.value)) > 20:
            raise ValueError("value cannot contain more than 20 unique strings")

    @property
    def encoded_value(self) -> str:
        if type(self.value) is str:
            return self.value
        unique: list[str] = []
        for item in self.value:
            if item not in unique:
                unique.append(item)
        return json.dumps(unique, ensure_ascii=False, separators=(",", ":"))


class PullRequestAutoComplete(msgspec.Struct, frozen=True, kw_only=True):
    target_status: str
    state: str | None = None


class LinkedPullRequest(msgspec.Struct, frozen=True, kw_only=True):
    url: str
    title: str | None = None
    state: str | None = None
    pr_auto_complete: PullRequestAutoComplete | None = None


class IssueChildStageGroup(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    count: int


if TYPE_CHECKING:

    class _IssueChildrenResultStatic(Page[Issue], frozen=True, kw_only=True):
        total: int = 0
        child_stages: tuple[IssueChildStageGroup, ...] = ()
        unstaged: tuple[Issue, ...] = ()

        @overload
        def __init__(
            self,
            *,
            items: tuple[Issue, ...] = ...,
            limit: int | None = ...,
            offset: int | None = ...,
            total: int = ...,
            has_more: bool = ...,
            next_cursor: str | CommentCursor | None = ...,
            child_stages: tuple[IssueChildStageGroup, ...] = ...,
            unstaged: tuple[Issue, ...] = ...,
        ) -> None: ...

        @overload
        def __init__(
            self,
            *,
            children: tuple[Issue, ...] = ...,
            limit: int | None = ...,
            offset: int | None = ...,
            total: int = ...,
            has_more: bool = ...,
            next_cursor: str | CommentCursor | None = ...,
            child_stages: tuple[IssueChildStageGroup, ...] = ...,
            unstaged: tuple[Issue, ...] = ...,
        ) -> None: ...

        def __init__(self, **kwargs: object) -> None: ...

        @property
        def children(self) -> tuple[Issue, ...]:
            return self.items

    IssueChildrenResult = _IssueChildrenResultStatic

else:

    class IssueChildrenResult(Page["Issue"], frozen=True, kw_only=True):
        total: int = 0
        child_stages: tuple[IssueChildStageGroup, ...] = ()
        unstaged: tuple[Issue, ...] = ()

        @property
        def children(self) -> tuple[Issue, ...]:
            return cast("tuple[Issue, ...]", self.items)


class IssueListFilter(msgspec.Struct, frozen=True, kw_only=True):
    status: IssueStatus | str | None = None
    priority: str | None = None
    assignee_id: str | None = None
    limit: int | None = None
    offset: int | None = None
    project_id: str | None = None
    sort: str | None = None
    direction: str | None = None
    metadata: tuple[IssueMetadataItem, ...] = ()
    fields: tuple[str, ...] = ()
    property_filters: tuple[str, ...] = ()
    resolve_properties: bool = False


if TYPE_CHECKING:

    class _IssueListPageStatic(Page[Issue], frozen=True, kw_only=True):
        @overload
        def __init__(
            self,
            *,
            items: tuple[Issue, ...] = ...,
            limit: int | None = ...,
            offset: int | None = ...,
            total: int | None = ...,
            has_more: bool = ...,
            next_cursor: str | CommentCursor | None = ...,
        ) -> None: ...

        @overload
        def __init__(
            self,
            *,
            issues: tuple[Issue, ...] = ...,
            limit: int | None = ...,
            offset: int | None = ...,
            total: int | None = ...,
            has_more: bool = ...,
            next_cursor: str | CommentCursor | None = ...,
        ) -> None: ...

        def __init__(self, **kwargs: object) -> None: ...

        @property
        def issues(self) -> tuple[Issue, ...]:
            return self.items

    IssueListPage = _IssueListPageStatic

else:

    class IssueListPage(Page["Issue"], frozen=True, kw_only=True):
        @property
        def issues(self) -> tuple[Issue, ...]:
            return self.items


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
