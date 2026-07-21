from __future__ import annotations

from collections.abc import Callable

import pytest

from multica_py.client import MulticaClient
from multica_py.enums import IssueStatus
from multica_py.models.issues import (
    InlineDescription,
    IssueCreateRequest,
    IssueUpdateRequest,
)
from tests.live.environment import label_name
from tests.live.oracle import DirectApiOracle
from tests.live.resources import ResourceRegistry

pytestmark = [pytest.mark.live, pytest.mark.live_smoke, pytest.mark.serial]

UNICODE_DESCRIPTION = 'Unicode: 日本語\n"quotes" \\ backslash\r\nemoji: 🚀'


def test_issue_create_get_list_filter_with_project_and_labels(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    resource_name: str,
) -> None:
    """Create project, labels, and Unicode issue; verify get, list, filter, and project link."""
    project = api_oracle.create_project(
        f"{resource_name}-project",
        description="workflow project",
    )
    project_id = str(project["id"])
    register_resource(
        key=f"project-{project_id}",
        cleanup=api_oracle.delete_callback(f"/api/projects/{project_id}", "project"),
    )
    label_a = live_client.labels.create(label_name(resource_name, "a"), color="#112233")
    label_b = live_client.labels.create(label_name(resource_name, "b"), color="#332211")
    register_resource(
        key=f"label-{label_a.id}",
        cleanup=api_oracle.delete_callback(f"/api/labels/{label_a.id}", "label"),
    )
    register_resource(
        key=f"label-{label_b.id}",
        cleanup=api_oracle.delete_callback(f"/api/labels/{label_b.id}", "label"),
    )
    created = api_oracle.create_issue(
        f"{resource_name}-issue",
        description=UNICODE_DESCRIPTION,
        project_id=project_id,
    )
    issue_id = str(created["id"])
    register_resource(
        key=f"issue-{issue_id}",
        cleanup=api_oracle.delete_callback(f"/api/issues/{issue_id}", "issue"),
    )
    live_client.issues.labels.add(issue_id, label_a.id)
    live_client.issues.labels.add(issue_id, label_b.id)
    oracle_issue = api_oracle.get_issue(issue_id)
    assert oracle_issue["title"] == f"{resource_name}-issue"
    assert oracle_issue["description"] == UNICODE_DESCRIPTION
    assert api_oracle.issue_project_id(oracle_issue) == project_id
    fetched = live_client.issues.get(issue_id)
    assert fetched.description == UNICODE_DESCRIPTION
    assert label_a.name in fetched.labels
    assert label_b.name in fetched.labels
    listed_ids = {item.id for item in live_client.issues.list()}
    assert issue_id in listed_ids
    oracle_page, _ = api_oracle.list_issues_page(label_id=label_a.id)
    assert issue_id in {str(item["id"]) for item in oracle_page}


def test_issue_update_status_priority_title_attach_detach_label_and_comment_round_trip(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    resource_name: str,
) -> None:
    """Update issue fields, attach/detach labels, and round-trip one comment."""
    label_keep = live_client.labels.create(label_name(resource_name, "keep"), color="#abcdef")
    label_swap = live_client.labels.create(label_name(resource_name, "swap"), color="#fedcba")
    label_extra = live_client.labels.create(label_name(resource_name, "extra"), color="#0f0f0f")
    for label in (label_keep, label_swap, label_extra):
        register_resource(
            key=f"label-{label.id}",
            cleanup=api_oracle.delete_callback(f"/api/labels/{label.id}", "label"),
        )
    issue = live_client.issues.create(
        IssueCreateRequest(
            title=f"{resource_name}-mutable",
            description_input=InlineDescription(text="initial"),
            label_ids=(label_keep.id, label_swap.id),
        )
    )
    register_resource(
        key=f"issue-{issue.id}",
        cleanup=api_oracle.delete_callback(f"/api/issues/{issue.id}", "issue"),
    )
    live_client.issues.set_status(issue.id, IssueStatus.in_progress)
    live_client.issues.update(
        issue.id,
        IssueUpdateRequest(title=f"{resource_name}-renamed", priority="high"),
    )
    live_client.issues.labels.remove(issue.id, label_swap.id)
    live_client.issues.labels.add(issue.id, label_extra.id)
    oracle_labels = api_oracle.list_issue_labels(issue.id)
    attached_names = {
        entry["name"] if isinstance(entry, dict) else str(entry) for entry in oracle_labels
    }
    assert label_keep.name in attached_names
    assert label_extra.name in attached_names
    assert label_swap.name not in attached_names
    comment_body = f"{resource_name} comment 📝"
    comment = live_client.issues.comments.add(issue.id, comment_body)
    register_resource(
        key=f"comment-{comment.id}",
        cleanup=api_oracle.delete_callback(f"/api/comments/{comment.id}", "comment"),
    )
    oracle_comments = api_oracle.list_comments(issue.id)
    assert any(
        isinstance(entry, dict) and entry.get("content") == comment_body
        for entry in oracle_comments
    )
    listed = live_client.issues.comments.list(issue.id)
    assert any(item.id == comment.id and item.body == comment_body for item in listed)
    updated_issue = live_client.issues.get(issue.id)
    assert updated_issue.title == f"{resource_name}-renamed"
    assert updated_issue.priority == "high"
    assert updated_issue.status == IssueStatus.in_progress
    live_client.issues.comments.delete(comment.id)
    api_oracle.assert_comment_removed_from_issue(issue.id, comment.id)


def test_c_empty_issue_labels_detach_all_returns_empty_oracle_list(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    resource_name: str,
) -> None:
    """Case C-EMPTY: detaching all labels leaves an empty oracle label collection."""
    label_a = live_client.labels.create(label_name(resource_name, "ea"), color="#111111")
    label_b = live_client.labels.create(label_name(resource_name, "eb"), color="#222222")
    for label in (label_a, label_b):
        register_resource(
            key=f"label-{label.id}",
            cleanup=api_oracle.delete_callback(f"/api/labels/{label.id}", "label"),
        )
    issue = live_client.issues.create(
        IssueCreateRequest(
            title=f"{resource_name}-empty-labels", label_ids=(label_a.id, label_b.id)
        )
    )
    register_resource(
        key=f"issue-{issue.id}",
        cleanup=api_oracle.delete_callback(f"/api/issues/{issue.id}", "issue"),
    )
    live_client.issues.labels.remove(issue.id, label_a.id)
    live_client.issues.labels.remove(issue.id, label_b.id)
    assert api_oracle.list_issue_labels(issue.id) == []


def test_workflow_dependency_safe_cleanup_and_oracle_absence(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    resource_registry: ResourceRegistry,
    resource_name: str,
) -> None:
    """Cleanup issue, comment, labels, and project in dependency-safe order."""
    project = api_oracle.create_project(f"{resource_name}-cleanup")
    project_id = str(project["id"])
    label_a = live_client.labels.create(label_name(resource_name, "ca"), color="#121212")
    label_b = live_client.labels.create(label_name(resource_name, "cb"), color="#343434")
    issue = live_client.issues.create(
        IssueCreateRequest(
            title=f"{resource_name}-cleanup-issue",
            description_input=InlineDescription(text="cleanup"),
            label_ids=(label_a.id, label_b.id),
        )
    )
    comment = live_client.issues.comments.add(issue.id, "cleanup comment")
    resource_registry.defer(
        key=f"project-{project_id}",
        cleanup=api_oracle.delete_callback(f"/api/projects/{project_id}", "project"),
    )
    for label in (label_a, label_b):
        resource_registry.defer(
            key=f"label-{label.id}",
            cleanup=api_oracle.delete_callback(f"/api/labels/{label.id}", "label"),
        )
    resource_registry.defer(
        key=f"issue-{issue.id}",
        cleanup=api_oracle.delete_callback(f"/api/issues/{issue.id}", "issue"),
    )
    resource_registry.defer(
        key=f"comment-{comment.id}",
        cleanup=api_oracle.delete_callback(f"/api/comments/{comment.id}", "comment"),
    )
    report = resource_registry.cleanup_all()
    assert report == []
    api_oracle.assert_absent(f"/api/issues/{issue.id}", "issue")
    api_oracle.assert_absent(f"/api/labels/{label_a.id}", "label")
    api_oracle.assert_absent(f"/api/labels/{label_b.id}", "label")
    api_oracle.assert_absent(f"/api/projects/{project_id}", "project")
