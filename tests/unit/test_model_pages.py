from __future__ import annotations

from typing import cast

import msgspec
import pytest

from multica_py import ActionResult, Page
from multica_py.models.autopilots import AutopilotListPage, AutopilotRunListPage
from multica_py.models.common import CommentCursor
from multica_py.models.issue_activity import MetadataEntry, MetadataPage
from multica_py.models.issues import IssueChildrenResult, IssueListPage, IssueSummary
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
            IssueListPage(issues=cast("tuple[IssueSummary, ...]", ("issue",)), total=1),
            "issues",
            ("issue",),
        ),
        (AutopilotListPage(autopilots=("autopilot",), total=1), "autopilots", ("autopilot",)),
        (AutopilotRunListPage(runs=("run",), total=1), "runs", ("run",)),
        (
            MetadataPage(items=cast("tuple[MetadataEntry, ...]", ("metadata",))),
            "items",
            ("metadata",),
        ),
        (
            IssueChildrenResult(children=cast("tuple[Issue, ...]", ("child",)), total=1),
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


def test_action_result_is_generic_and_serializable() -> None:
    result = ActionResult[int](value=7, success=True, message="completed")
    assert result.value == 7
    assert result.success is True
    assert result.message == "completed"
    decoded = msgspec.json.decode(msgspec.json.encode(result), type=ActionResult[int])
    assert decoded == result
    with pytest.raises(msgspec.ValidationError):
        msgspec.json.decode(b'{"success":"yes","value":7}', type=ActionResult[int])
