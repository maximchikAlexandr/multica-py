from __future__ import annotations

import pytest

from multica_py.enums import IssueStatus
from multica_py.models.issues import (
    InlineDescription,
    IssueCreateRequest,
    IssueUpdateRequest,
)
from tests.live._live_helpers import label_name
from tests.live.session import LiveCase, LiveSession

pytestmark = [pytest.mark.live, pytest.mark.live_smoke, pytest.mark.serial]

UNICODE_DESCRIPTION = 'Unicode: 日本語\n"quotes" \\ backslash\r\nemoji: 🚀'


def test_issue_create_get_list_filter_with_project_and_labels(
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """Create project, labels, and Unicode issue; verify get, list, filter, and project link."""
    project = live_session.oracle.create_project(
        f"{live_case.unique_name}-project",
        description="workflow project",
    )
    project_id = str(project["id"])
    live_case.defer_cleanup(
        live_session.oracle.delete_callback(f"/api/projects/{project_id}", "project"),
    )
    label_a = live_session.client.labels.create(
        label_name(live_case.unique_name, "a"), color="#112233"
    )
    label_b = live_session.client.labels.create(
        label_name(live_case.unique_name, "b"), color="#332211"
    )
    live_case.defer_cleanup(
        live_session.oracle.delete_callback(f"/api/labels/{label_a.id}", "label"),
    )
    live_case.defer_cleanup(
        live_session.oracle.delete_callback(f"/api/labels/{label_b.id}", "label"),
    )
    created = live_session.oracle.create_issue(
        f"{live_case.unique_name}-issue",
        description=UNICODE_DESCRIPTION,
        project_id=project_id,
    )
    issue_id = str(created["id"])
    live_case.defer_cleanup(live_session.oracle.delete_callback(f"/api/issues/{issue_id}", "issue"))
    live_session.client.issues.labels.add(issue_id, label_a.id)
    live_session.client.issues.labels.add(issue_id, label_b.id)
    oracle_issue = live_session.oracle.get_issue(issue_id)
    assert oracle_issue["title"] == f"{live_case.unique_name}-issue"
    assert oracle_issue["description"] == UNICODE_DESCRIPTION
    assert live_session.oracle.issue_project_id(oracle_issue) == project_id
    fetched = live_session.client.issues.get(issue_id)
    assert fetched.description == UNICODE_DESCRIPTION
    assert label_a.name in fetched.labels
    assert label_b.name in fetched.labels
    listed_ids = {item.id for item in live_session.client.issues.list()}
    assert issue_id in listed_ids
    oracle_page, _ = live_session.oracle.list_issues_page(label_id=label_a.id)
    assert issue_id in {str(item["id"]) for item in oracle_page}


def test_issue_update_status_priority_title_attach_detach_label_and_comment_round_trip(
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """Update issue fields, attach/detach labels, and round-trip one comment."""
    label_keep = live_session.client.labels.create(
        label_name(live_case.unique_name, "keep"), color="#abcdef"
    )
    label_swap = live_session.client.labels.create(
        label_name(live_case.unique_name, "swap"), color="#fedcba"
    )
    label_extra = live_session.client.labels.create(
        label_name(live_case.unique_name, "extra"), color="#0f0f0f"
    )
    for label in (label_keep, label_swap, label_extra):
        live_case.defer_cleanup(
            live_session.oracle.delete_callback(f"/api/labels/{label.id}", "label"),
        )
    issue = live_session.client.issues.create(
        IssueCreateRequest(
            title=f"{live_case.unique_name}-mutable",
            description_input=InlineDescription(text="initial"),
            label_ids=(label_keep.id, label_swap.id),
        )
    )
    live_case.defer_cleanup(live_session.oracle.delete_callback(f"/api/issues/{issue.id}", "issue"))
    live_session.client.issues.set_status(issue.id, IssueStatus.in_progress)
    live_session.client.issues.update(
        issue.id,
        IssueUpdateRequest(title=f"{live_case.unique_name}-renamed", priority="high"),
    )
    live_session.client.issues.labels.remove(issue.id, label_swap.id)
    live_session.client.issues.labels.add(issue.id, label_extra.id)
    oracle_labels = live_session.oracle.list_issue_labels(issue.id)
    attached_names = {
        entry["name"] if isinstance(entry, dict) else str(entry) for entry in oracle_labels
    }
    assert label_keep.name in attached_names
    assert label_extra.name in attached_names
    assert label_swap.name not in attached_names
    comment_body = f"{live_case.unique_name} comment 📝"
    comment = live_session.client.issues.comments.add(issue.id, comment_body)
    live_case.defer_cleanup(
        live_session.oracle.delete_callback(f"/api/comments/{comment.id}", "comment"),
    )
    oracle_comments = live_session.oracle.list_comments(issue.id)
    assert any(
        isinstance(entry, dict) and entry.get("content") == comment_body
        for entry in oracle_comments
    )
    listed = live_session.client.issues.comments.list(issue.id)
    assert any(item.id == comment.id and item.body == comment_body for item in listed)
    updated_issue = live_session.client.issues.get(issue.id)
    assert updated_issue.title == f"{live_case.unique_name}-renamed"
    assert updated_issue.priority == "high"
    assert updated_issue.status == IssueStatus.in_progress
    live_session.client.issues.comments.delete(comment.id)
    live_session.oracle.assert_comment_removed_from_issue(issue.id, comment.id)


def test_c_empty_issue_labels_detach_all_returns_empty_oracle_list(
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """Case C-EMPTY: detaching all labels leaves an empty oracle label collection."""
    label_a = live_session.client.labels.create(
        label_name(live_case.unique_name, "ea"), color="#111111"
    )
    label_b = live_session.client.labels.create(
        label_name(live_case.unique_name, "eb"), color="#222222"
    )
    for label in (label_a, label_b):
        live_case.defer_cleanup(
            live_session.oracle.delete_callback(f"/api/labels/{label.id}", "label"),
        )
    issue = live_session.client.issues.create(
        IssueCreateRequest(
            title=f"{live_case.unique_name}-empty-labels",
            label_ids=(label_a.id, label_b.id),
        )
    )
    live_case.defer_cleanup(live_session.oracle.delete_callback(f"/api/issues/{issue.id}", "issue"))
    live_session.client.issues.labels.remove(issue.id, label_a.id)
    live_session.client.issues.labels.remove(issue.id, label_b.id)
    assert live_session.oracle.list_issue_labels(issue.id) == []


def test_workflow_dependency_safe_cleanup_and_oracle_absence(
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """Cleanup issue, comment, labels, and project in dependency-safe order."""
    project = live_session.oracle.create_project(f"{live_case.unique_name}-cleanup")
    project_id = str(project["id"])
    label_a = live_session.client.labels.create(
        label_name(live_case.unique_name, "ca"), color="#121212"
    )
    label_b = live_session.client.labels.create(
        label_name(live_case.unique_name, "cb"), color="#343434"
    )
    issue = live_session.client.issues.create(
        IssueCreateRequest(
            title=f"{live_case.unique_name}-cleanup-issue",
            description_input=InlineDescription(text="cleanup"),
            label_ids=(label_a.id, label_b.id),
        )
    )
    comment = live_session.client.issues.comments.add(issue.id, "cleanup comment")
    live_session.resource_registry.defer(
        key=f"project-{project_id}",
        cleanup=live_session.oracle.delete_callback(f"/api/projects/{project_id}", "project"),
    )
    for label in (label_a, label_b):
        live_session.resource_registry.defer(
            key=f"label-{label.id}",
            cleanup=live_session.oracle.delete_callback(f"/api/labels/{label.id}", "label"),
        )
    live_session.resource_registry.defer(
        key=f"issue-{issue.id}",
        cleanup=live_session.oracle.delete_callback(f"/api/issues/{issue.id}", "issue"),
    )
    live_session.resource_registry.defer(
        key=f"comment-{comment.id}",
        cleanup=live_session.oracle.delete_callback(f"/api/comments/{comment.id}", "comment"),
    )
    report = live_session.resource_registry.cleanup_all()
    assert report == []
    live_session.oracle.assert_absent(f"/api/issues/{issue.id}", "issue")
    live_session.oracle.assert_absent(f"/api/labels/{label_a.id}", "label")
    live_session.oracle.assert_absent(f"/api/labels/{label_b.id}", "label")
    live_session.oracle.assert_absent(f"/api/projects/{project_id}", "project")
