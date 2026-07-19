from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.models.issues import (
    IssueAssignmentRequest,
    IssueCreateRequest,
    IssueUpdateRequest,
)
from multica_py.models.projects import ProjectCreateRequest
from multica_py.models.workspaces import Workspace
from tests.live.context import LiveContext
from tests.live.crud_descriptors import CRUD_DESCRIPTORS
from tests.live.settings import label_name

LiveExecReason = Literal[
    "destructive-irrecoverable",
    "requires-external-infra",
    "interactive-or-foreground",
    "process-or-daemon-control",
]


@dataclass(frozen=True)
class LiveOperation:
    sdk_method: str
    invoke: Callable[[LiveContext], object]


def _title(ctx: LiveContext, suffix: str) -> str:
    return f"live-op-{suffix}-{ctx.identity.user_id[:8]}"


def _create_issue(ctx: LiveContext, title: str) -> str:
    issue = ctx.client.issues.create(IssueCreateRequest(title=title))
    ctx.register_resource(
        key=f"issue-{issue.id}",
        cleanup=ctx.oracle.delete_callback(f"/api/issues/{issue.id}", "issue"),
    )
    return issue.id


def _create_label(ctx: LiveContext, suffix: str) -> str:
    name = label_name(f"live-op-{ctx.identity.user_id[:12]}", suffix)
    label = ctx.client.labels.create(name, color="#112233")
    ctx.register_resource(
        key=f"label-{label.id}",
        cleanup=ctx.oracle.delete_callback(f"/api/labels/{label.id}", "label"),
    )
    return label.id


def _client_list(ctx: LiveContext, resource: str) -> None:
    getattr(ctx.client, resource).list()


def _client_get_first(ctx: LiveContext, resource: str) -> None:
    client_resource = getattr(ctx.client, resource)
    items = client_resource.list()
    assert items, f"expected at least one {resource}"
    client_resource.get(items[0].id)


def _with_issue(
    ctx: LiveContext, suffix: str, action: Callable[[LiveContext, str], object]
) -> None:
    action(ctx, _create_issue(ctx, _title(ctx, suffix)))


def _first_workspace(ctx: LiveContext) -> Workspace:
    workspaces = ctx.client.workspaces.list()
    assert workspaces, "expected at least one workspace"
    return workspaces[0]


def _invoke_labels_remove(ctx: LiveContext) -> None:
    issue_id = _create_issue(ctx, _title(ctx, "lbl-rm"))
    label_id = _create_label(ctx, "remove")
    ctx.client.issues.labels.add(issue_id, label_id)
    ctx.client.issues.labels.remove(issue_id, label_id)


def _invoke_comments_add(ctx: LiveContext) -> None:
    issue_id = _create_issue(ctx, _title(ctx, "cmt-add"))
    comment = ctx.client.issues.comments.add(issue_id, "live-op comment")
    ctx.register_resource(
        key=f"comment-{comment.id}",
        cleanup=ctx.oracle.delete_callback(f"/api/comments/{comment.id}", "comment"),
    )


def _invoke_comments_delete(ctx: LiveContext) -> None:
    issue_id = _create_issue(ctx, _title(ctx, "cmt-del"))
    comment = ctx.client.issues.comments.add(issue_id, "live-op delete me")
    ctx.client.issues.comments.delete(comment.id)


def _invoke_deprioritize(ctx: LiveContext) -> None:
    issue_id = _create_issue(ctx, _title(ctx, "deprio"))
    ctx.client.issues.update(issue_id, IssueUpdateRequest(priority="high"))
    ctx.client.issues.deprioritize(issue_id)


def _invoke_labels_list(ctx: LiveContext) -> None:
    issue_id = _create_issue(ctx, _title(ctx, "lbl-list"))
    label_id = _create_label(ctx, "list")
    ctx.client.issues.labels.add(issue_id, label_id)
    ctx.client.issues.labels.list(issue_id)


def _invoke_subscribers_list(ctx: LiveContext) -> None:
    issue_id = _create_issue(ctx, _title(ctx, "sub-list"))
    ctx.client.issues.subscribers.add(issue_id, ctx.identity.user_id)
    ctx.client.issues.subscribers.list(issue_id)


def _invoke_subscribers_remove(ctx: LiveContext) -> None:
    issue_id = _create_issue(ctx, _title(ctx, "sub-rm"))
    ctx.client.issues.subscribers.add(issue_id, ctx.identity.user_id)
    ctx.client.issues.subscribers.remove(issue_id, ctx.identity.user_id)


def _invoke_projects_set_status(ctx: LiveContext) -> None:
    project = ctx.client.projects.create(
        ProjectCreateRequest(name=f"live-op-prj-{ctx.identity.user_id[:12]}")
    )
    ctx.register_resource(
        key=f"project-{project.id}",
        cleanup=ctx.oracle.delete_callback(f"/api/projects/{project.id}", "project"),
    )
    ctx.client.projects.set_status(project.id, ProjectStatus.in_progress)


# fmt: off
LIVE_OPERATIONS: tuple[LiveOperation, ...] = (
    LiveOperation("workspaces.list", lambda ctx: _client_list(ctx, "workspaces")),
    LiveOperation("labels.list", lambda ctx: _client_list(ctx, "labels")),
    LiveOperation("agents.list", lambda ctx: _client_list(ctx, "agents")),
    LiveOperation("skills.list", lambda ctx: _client_list(ctx, "skills")),
    LiveOperation("projects.list", lambda ctx: _client_list(ctx, "projects")),
    LiveOperation("repositories.list", lambda ctx: _client_list(ctx, "repositories")),
    LiveOperation("runtimes.list", lambda ctx: _client_list(ctx, "runtimes")),
    LiveOperation("squads.list", lambda ctx: _client_list(ctx, "squads")),
    LiveOperation("issues.create", lambda ctx: _create_issue(ctx, _title(ctx, "create"))),
    LiveOperation("issues.get", lambda ctx: _with_issue(ctx, "get", lambda c, i: c.client.issues.get(i))),
    LiveOperation("issues.list", lambda ctx: ctx.client.issues.list()),
    LiveOperation("issues.update", lambda ctx: _with_issue(ctx, "update", lambda c, i: c.client.issues.update(i, IssueUpdateRequest(title=f"live-op-updated-{c.identity.user_id[:8]}")))),
    LiveOperation("issues.set_status", lambda ctx: _with_issue(ctx, "status", lambda c, i: c.client.issues.set_status(i, IssueStatus.in_progress))),
    LiveOperation("issues.labels.add", lambda ctx: ctx.client.issues.labels.add(_create_issue(ctx, _title(ctx, "lbl-add")), _create_label(ctx, "add"))),
    LiveOperation("issues.labels.remove", _invoke_labels_remove),
    LiveOperation("issues.comments.add", _invoke_comments_add),
    LiveOperation("issues.comments.list", lambda ctx: _with_issue(ctx, "cmt-list", lambda c, i: c.client.issues.comments.list(i))),
    LiveOperation("issues.comments.delete", _invoke_comments_delete),
    LiveOperation("issues.assign", lambda ctx: ctx.client.issues.assign(IssueAssignmentRequest(issue_id=_create_issue(ctx, _title(ctx, "assign")), member_id=ctx.identity.user_id))),
    LiveOperation("issues.deprioritize", _invoke_deprioritize),
    LiveOperation("issues.labels.list", _invoke_labels_list),
    LiveOperation("issues.subscribers.add", lambda ctx: _with_issue(ctx, "sub-add", lambda c, i: c.client.issues.subscribers.add(i, c.identity.user_id))),
    LiveOperation("issues.subscribers.list", _invoke_subscribers_list),
    LiveOperation("issues.subscribers.remove", _invoke_subscribers_remove),
    LiveOperation("projects.set_status", _invoke_projects_set_status),
    LiveOperation("workspaces.get", lambda ctx: _client_get_first(ctx, "workspaces")),
    LiveOperation("workspaces.members", lambda ctx: ctx.client.workspaces.members(_first_workspace(ctx).id)),
)
# fmt: on


def _exc(reason: LiveExecReason, *methods: str) -> dict[str, LiveExecReason]:
    return dict.fromkeys(methods, reason)


LIVE_EXEC_EXCEPTIONS: Mapping[str, LiveExecReason] = {
    **_exc(
        "destructive-irrecoverable",
        "agents.archive",
        "agents.create",
        "agents.restore",
        "maintenance.update",
    ),
    **_exc(
        "interactive-or-foreground",
        "auth.login",
        "auth.logout",
        "auth.status",
        "daemon.logs",
        "setup.cloud",
        "setup.self_host",
        "workspaces.switch",
    ),
    **_exc(
        "process-or-daemon-control",
        "daemon.disk_usage",
        "daemon.restart",
        "daemon.start",
        "daemon.status",
        "daemon.stop",
    ),
    **_exc(
        "requires-external-infra",
        "agents.skills.set",
        "agents.skills.list",
        "agents.get",
        "agents.tasks",
        "agents.update",
        "agents.upload_avatar",
        "attachments.download",
        "attachments.list",
        "attachments.upload",
        "autopilots.create",
        "autopilots.delete",
        "autopilots.get",
        "autopilots.get_run",
        "autopilots.history",
        "autopilots.list",
        "autopilots.run",
        "autopilots.triggers.create",
        "autopilots.triggers.delete",
        "autopilots.triggers.list",
        "autopilots.update",
        "configuration.get",
        "configuration.set",
        "configuration.show",
        "issues.cancel_task",
        "issues.children",
        "issues.comments.reply",
        "issues.comments.resolve",
        "issues.comments.unresolve",
        "issues.metadata.delete",
        "issues.metadata.get",
        "issues.metadata.list",
        "issues.metadata.set",
        "issues.pull_requests",
        "issues.rerun",
        "issues.reorder",
        "issues.run_messages",
        "issues.runs",
        "issues.search",
        "issues.usage",
        "maintenance.version",
        "repositories.checkout",
        "repositories.get",
        "runtimes.get",
        "skills.create",
        "skills.delete",
        "skills.files.delete",
        "skills.files.list",
        "skills.files.upsert",
        "skills.get",
        "skills.import_from_url",
        "skills.update",
        "squads.get",
        "users.get",
        "users.list",
        "workspaces.unwatch",
        "workspaces.watch",
    ),
}


def crud_sdk_methods() -> frozenset[str]:
    methods: set[str] = set()
    for desc in CRUD_DESCRIPTORS:
        base = desc.id
        for verb in ("create", "get", "update", "delete"):
            methods.add(f"{base}.{verb}")
    return frozenset(methods)


KNOWN_LIVE_GAPS: frozenset[str] = frozenset()
