from __future__ import annotations

from collections.abc import Callable

import pytest

from multica_py.client import MulticaClient
from multica_py.enums import IssueStatus
from multica_py.models.issues import IssueCreateRequest, IssueListFilter
from tests.live.environment import label_name
from tests.live.oracle import DirectApiOracle

pytestmark = [pytest.mark.live, pytest.mark.live_extended, pytest.mark.serial]

PAGE_SIZE = 10
ISSUE_COUNT = 12


def _issue_id(entry: object) -> str:
    if isinstance(entry, dict) and isinstance(entry.get("id"), str):
        return entry["id"]
    msg = f"expected issue dict with id, got {entry!r}"
    raise AssertionError(msg)


def _collect_paginated_issue_ids(
    api_oracle: DirectApiOracle,
    *,
    limit: int,
    status: str | None = None,
    label_id: str | None = None,
) -> set[str]:
    collected: set[str] = set()
    cursor: str | None = None
    pages = 0
    while pages < 10:
        items, next_cursor = api_oracle.list_issues_page(
            limit=limit,
            cursor=cursor,
            status=status,
            label_id=label_id,
        )
        page_ids = {_issue_id(item) for item in items}
        overlap = collected & page_ids
        if overlap:
            msg = f"paginated issue ids must not repeat across pages: {sorted(overlap)}"
            raise AssertionError(msg)
        collected.update(page_ids)
        pages += 1
        if not next_cursor:
            break
        if len(items) == 0:
            msg = "pagination cursor returned an empty page before completion"
            raise AssertionError(msg)
        cursor = next_cursor
    else:
        msg = "pagination did not complete within the page budget"
        raise AssertionError(msg)
    return collected


def test_issue_pagination_collects_twelve_issues_without_duplicates(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    resource_name: str,
) -> None:
    """Create 12 issues and walk cursor pagination with page_size=10."""
    created_ids: list[str] = []
    for index in range(ISSUE_COUNT):
        issue = live_client.issues.create(
            IssueCreateRequest(title=f"{resource_name}-page-{index:02d}")
        )
        created_ids.append(issue.id)
        register_resource(
            key=f"issue-{issue.id}",
            cleanup=api_oracle.delete_callback(f"/api/issues/{issue.id}", "issue"),
        )
    collected = _collect_paginated_issue_ids(api_oracle, limit=PAGE_SIZE)
    missing = set(created_ids) - collected
    if missing:
        msg = f"pagination did not return all created issues: missing={sorted(missing)}"
        raise AssertionError(msg)


def test_issue_filter_status_and_label_id(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    resource_name: str,
) -> None:
    """Filter issues by status and attached label id."""
    target_label = live_client.labels.create(label_name(resource_name, "flt"), color="#445566")
    other_label = live_client.labels.create(label_name(resource_name, "oth"), color="#667788")
    for label in (target_label, other_label):
        register_resource(
            key=f"label-{label.id}",
            cleanup=api_oracle.delete_callback(f"/api/labels/{label.id}", "label"),
        )
    matching = live_client.issues.create(
        IssueCreateRequest(
            title=f"{resource_name}-match",
            label_ids=(target_label.id,),
        )
    )
    non_matching_status = live_client.issues.create(
        IssueCreateRequest(title=f"{resource_name}-wrong-status", label_ids=(target_label.id,))
    )
    non_matching_label = live_client.issues.create(
        IssueCreateRequest(title=f"{resource_name}-wrong-label", label_ids=(other_label.id,))
    )
    for issue in (matching, non_matching_status, non_matching_label):
        register_resource(
            key=f"issue-{issue.id}",
            cleanup=api_oracle.delete_callback(f"/api/issues/{issue.id}", "issue"),
        )
    live_client.issues.set_status(matching.id, IssueStatus.in_progress)
    filtered_oracle = _collect_paginated_issue_ids(
        api_oracle,
        limit=PAGE_SIZE,
        status=IssueStatus.in_progress.value,
        label_id=target_label.id,
    )
    assert matching.id in filtered_oracle
    assert non_matching_status.id not in filtered_oracle
    assert non_matching_label.id not in filtered_oracle
    sdk_filtered = live_client.issues.list(IssueListFilter(status=IssueStatus.in_progress))
    sdk_ids = {item.id for item in sdk_filtered}
    assert matching.id in sdk_ids
    assert non_matching_status.id not in sdk_ids
