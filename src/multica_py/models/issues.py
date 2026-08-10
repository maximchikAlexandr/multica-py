from __future__ import annotations

from typing import TYPE_CHECKING, cast, overload

import msgspec

from multica_py.enums import IssueSort, IssueStatus, SortDirection
from multica_py.models.common import CommentCursor, Page
from multica_py.types import MetadataValue

if TYPE_CHECKING:
    from multica_py.resources.agents import Agent
    from multica_py.resources.issues import Issue
    from multica_py.resources.squads import Squad
    from multica_py.resources.workspaces import WorkspaceMember

    type AssignmentTarget = str | Agent | Squad | WorkspaceMember
    type IssueReference = str | Issue
else:
    # The runtime validator uses an explicit allow-list; this fallback keeps
    # the aliases importable without importing resource modules cyclically.
    from multica_py.models._bound import _BoundEntity

    type AssignmentTarget = str | _BoundEntity
    type IssueReference = str | _BoundEntity


class IssueMetadataItem(msgspec.Struct, frozen=True, kw_only=True):
    key: str
    value: MetadataValue


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
        unstaged: tuple[object, ...] = ()

        @property
        def children(self) -> tuple[Issue, ...]:
            return cast("tuple[Issue, ...]", self.items)


class IssueListFilter(msgspec.Struct, frozen=True, kw_only=True):
    status: IssueStatus | None = None
    priority: str | None = None
    assignee_id: str | None = None
    limit: int | None = None
    offset: int | None = None
    project_id: str | None = None
    sort: IssueSort | None = None
    direction: SortDirection | None = None
    metadata: tuple[IssueMetadataItem, ...] = ()


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
