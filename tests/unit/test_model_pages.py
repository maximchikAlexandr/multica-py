from __future__ import annotations

from typing import cast

import msgspec
import pytest

from multica_py import ActionResult, Page
from multica_py.models.autopilots import AutopilotListPage, AutopilotRunListPage
from multica_py.models.common import CommentCursor
from multica_py.models.issue_activity import MetadataEntry, MetadataPage
from multica_py.models.issues import (
    IssueChildrenResult,
    IssueListPage,
)
from multica_py.resources.issues import Issue


def test_page_is_frozen_typed_sequence_with_closed_cursor() -> None:
    cursor = CommentCursor(before="before", before_id="comment")
    page = Page(items=("one", "two"), limit=2, offset=4, total=8, has_more=True, next_cursor=cursor)

    assert page.items is page.items
    assert tuple(page) == ("one", "two")
    assert len(page) == 2
    assert page[0] == "one"
    assert page[1:] == ("two",)
    assert page.next_cursor is cursor
    with pytest.raises((AttributeError, TypeError)):
        page.items = ()  # type: ignore[misc]
    with pytest.raises(msgspec.ValidationError):
        msgspec.json.decode(b'{"before":"x","before_id":"y","unknown":true}', type=CommentCursor)


@pytest.mark.parametrize(
    ("page", "alias_name", "expected"),
    (
        (
            IssueListPage(items=cast("tuple[Issue, ...]", ("issue",)), total=1),
            "issues",
            ("issue",),
        ),
        (AutopilotListPage(items=("autopilot",), total=1), "autopilots", ("autopilot",)),
        (AutopilotRunListPage(items=("run",), total=1), "runs", ("run",)),
        (
            MetadataPage(items=cast("tuple[MetadataEntry, ...]", ("metadata",))),
            "items",
            ("metadata",),
        ),
        (
            IssueChildrenResult(items=cast("tuple[Issue, ...]", ("child",)), total=1),
            "children",
            ("child",),
        ),
    ),
)
def test_compatibility_pages_expose_identical_items_aliases(
    page: object, alias_name: str, expected: tuple[str, ...]
) -> None:
    items = getattr(page, "items")
    assert items is getattr(page, alias_name)
    assert items == expected
    sequence = cast("tuple[object, ...]", items)
    assert tuple(sequence) == expected
    assert list(sequence) == list(expected)


@pytest.mark.parametrize(
    ("page_type", "page", "alias_name"),
    (
        (
            IssueListPage,
            IssueListPage(items=cast("tuple[Issue, ...]", ("issue",)), total=1),
            "issues",
        ),
        (
            IssueChildrenResult,
            IssueChildrenResult(items=cast("tuple[Issue, ...]", ("child",))),
            "children",
        ),
        (AutopilotListPage, AutopilotListPage(items=("autopilot",), total=1), "autopilots"),
        (AutopilotRunListPage, AutopilotRunListPage(items=("run",), total=1), "runs"),
    ),
)
def test_compatibility_pages_are_frozen_page_subtypes(
    page_type: type[object], page: object, alias_name: str
) -> None:
    assert issubclass(page_type, Page)
    assert isinstance(page, Page)
    assert getattr(page, alias_name) is getattr(page, "items")
    assert all(hasattr(page, field) for field in ("limit", "offset", "total", "has_more"))
    assert hasattr(page, "next_cursor")

    with pytest.raises((AttributeError, TypeError)):
        setattr(page, "next_cursor", "cursor")


@pytest.mark.parametrize(
    ("page_type", "alias_name"),
    (
        (IssueListPage, "issues"),
        (IssueChildrenResult, "children"),
        (AutopilotListPage, "autopilots"),
        (AutopilotRunListPage, "runs"),
    ),
)
def test_compatibility_constructor_aliases_remain_supported(
    page_type: type[object], alias_name: str
) -> None:
    page = page_type(**{alias_name: ("item",)})

    assert getattr(page, "items") == ("item",)
    assert getattr(page, alias_name) is getattr(page, "items")


def test_issue_children_page_uses_neutral_metadata_by_default() -> None:
    page = IssueChildrenResult()

    assert page.items is page.children
    assert page.limit is None
    assert page.offset is None
    assert page.total == 0
    assert page.has_more is False
    assert page.next_cursor is None


def test_action_result_is_generic_and_serializable() -> None:
    result = ActionResult[int](value=7, success=True, message="completed")
    assert result.value == 7
    assert result.success is True
    assert result.message == "completed"
    decoded = msgspec.json.decode(msgspec.json.encode(result), type=ActionResult[int])
    assert decoded == result
    with pytest.raises(msgspec.ValidationError):
        msgspec.json.decode(b'{"success":"yes","value":7}', type=ActionResult[int])
