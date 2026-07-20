from __future__ import annotations

import difflib
import hashlib
import json
import os
import pathlib
import subprocess
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from typing import Literal

from multica_py.client import MulticaClient
from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.exceptions import NotFoundError
from multica_py.models.agents import AgentCreateRequest
from multica_py.models.issue_activity import TaskRun
from multica_py.models.issues import (
    InlineDescription,
    IssueAssignmentRequest,
    IssueCreateRequest,
    IssueUpdateRequest,
)
from multica_py.models.project_resources import ProjectResourceAddLocalDirectoryRequest
from multica_py.models.projects import ProjectCreateRequest
from multica_py.models.workspaces import Workspace
from tests.live.backend import (
    TERMINAL_RUN_STATUSES,
    BootstrapApiClient,
    DaemonLifecycle,
    poll_runtime_deregistered,
    poll_runtime_online,
    setup_sandbox_session,
)
from tests.live.diagnostics import DiagnosticCollector, LiveDiagnosticsBundle
from tests.live.environment import (
    CANARY_COST_CEILING_USD,
    AgentSandboxSettings,
    LiveContext,
    LiveRunContext,
    LiveSetupError,
    LiveTestEnvironment,
    OpenCodeCanarySettings,
    ResourceAbsentError,
    TestIdentity,
    label_name,
    remove_live_run_context,
)
from tests.live.oracle import DirectApiOracle


class ResourceRegistry:
    """LIFO registry for live test resource cleanup."""

    def __init__(self) -> None:
        self._cleanups: list[tuple[str, Callable[[], None]]] = []

    def defer(self, *, key: str, cleanup: Callable[[], None]) -> None:
        """Register one cleanup callback invoked in reverse creation order.

        Args:
            key: Unique registry key.
            cleanup: Callback invoked during cleanup.
        """
        self._cleanups.append((key, cleanup))

    def cleanup_all(self) -> list[dict[str, str]]:
        """Delete registered resources in reverse registration order.

        Returns:
            Cleanup failure records for any resources that could not be removed.
        """
        failures: list[dict[str, str]] = []
        for key, cleanup in reversed(self._cleanups):
            try:
                cleanup()
            except (ResourceAbsentError, NotFoundError):
                continue
            except Exception as exc:
                failures.append({"key": key, "message": str(exc)})
        return failures


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
    from tests.live.crud_descriptors import CRUD_DESCRIPTORS

    methods: set[str] = set()
    for desc in CRUD_DESCRIPTORS:
        base = desc.resource_id
        for verb in ("create", "get", "update", "delete"):
            methods.add(f"{base}.{verb}")
    return frozenset(methods)


KNOWN_LIVE_GAPS: frozenset[str] = frozenset()


class LiveCleanupError(RuntimeError):
    """Raised when an injected cleanup step fails deterministically."""

    def __init__(self, step: str) -> None:
        super().__init__(step)
        self.step = step


FileKind = Literal["file", "directory", "symlink"]


@dataclass(frozen=True, slots=True)
class FileManifestEntry:
    """One filesystem entry in a sandbox manifest."""

    kind: FileKind
    size: int
    sha256: str | None = None
    symlink_target: str | None = None


FileManifest = dict[str, FileManifestEntry]
ALLOWLIST_FILES = frozenset({"AGENTS.md"})
ALLOWLIST_PREFIXES = (".multica/",)
USER_FILES = frozenset({"target.txt", "control.txt"})
RUN_ASSIGNMENT_TIMEOUT_SECONDS = 120.0
CANCEL_WAIT_TIMEOUT_SECONDS = 10.0


class CleanupRegistry:
    """Fixed-order cleanup registry for agent sandbox runs."""

    _ORDER: tuple[str, ...] = (
        "cancel-run",
        "remove-resource",
        "archive-agent",
        "delete-project",
        "stop-daemon",
        "wait-runtime-deregister",
        "delete-workspace",
        "remove-temp-paths",
        "postcondition-audit",
    )

    def __init__(self) -> None:
        self._actions: list[tuple[str, Callable[[], None]]] = []
        self._primary_failure: BaseException | None = None

    def register(self, name: str, execute: Callable[[], None]) -> None:
        """Register one cleanup action keyed by its stable name."""
        self._actions.append((name, execute))

    def set_primary_failure(self, exc: BaseException | None) -> None:
        """Record the primary workflow failure without overwriting an existing one."""
        if self._primary_failure is None and exc is not None:
            self._primary_failure = exc

    @property
    def primary_failure(self) -> BaseException | None:
        """Return the preserved primary failure when present."""
        return self._primary_failure

    def execute_all(self) -> list[dict[str, str]]:
        """Execute cleanup actions in the fixed contract order."""
        failures: list[dict[str, str]] = []
        order = {name: index for index, name in enumerate(self._ORDER)}
        for name, execute in sorted(
            self._actions,
            key=lambda item: order.get(item[0], len(self._ORDER)),
        ):
            try:
                execute()
            except (ResourceAbsentError, NotFoundError):
                continue
            except Exception as exc:
                failures.append({"name": name, "message": str(exc)})
        return failures


def build_file_manifest(root: pathlib.Path) -> FileManifest:
    """Build a recursive manifest for files under a sandbox root."""
    manifest: FileManifest = {}
    if not root.is_dir():
        return manifest
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            target = os.readlink(path)
            manifest[relative] = FileManifestEntry(
                kind="symlink",
                size=0,
                symlink_target=target,
            )
            continue
        if path.is_dir():
            manifest[relative] = FileManifestEntry(kind="directory", size=0)
            continue
        if path.is_file():
            content = path.read_bytes()
            manifest[relative] = FileManifestEntry(
                kind="file",
                size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
            )
    return manifest


def manifest_to_json(manifest: FileManifest) -> dict[str, object]:
    """Serialize a file manifest for diagnostic output."""
    return {
        path: {
            "kind": entry.kind,
            "size": entry.size,
            "sha256": entry.sha256,
            "symlink_target": entry.symlink_target,
        }
        for path, entry in sorted(manifest.items())
    }


def unified_target_control_diff(
    before: FileManifest,
    after: FileManifest,
    *,
    sandbox_dir: pathlib.Path,
) -> str:
    """Return a unified diff for target.txt and control.txt only."""
    chunks: list[str] = []
    for name in ("target.txt", "control.txt"):
        before_entry = before.get(name)
        after_entry = after.get(name)
        before_text = ""
        after_text = ""
        file_path = sandbox_dir / name
        if before_entry is not None and file_path.is_file():
            before_text = (sandbox_dir / name).read_text(encoding="utf-8")
        if after_entry is not None and file_path.is_file():
            after_text = file_path.read_text(encoding="utf-8")
        diff = difflib.unified_diff(
            before_text.splitlines(keepends=True),
            after_text.splitlines(keepends=True),
            fromfile=f"before/{name}",
            tofile=f"after/{name}",
        )
        chunks.extend(diff)
    return "".join(chunks)


def _path_allowed_to_change(relative: str) -> bool:
    if relative in ALLOWLIST_FILES:
        return True
    return relative == ".multica" or relative.startswith(".multica/")


def assert_manifest_policy(
    before: FileManifest,
    after: FileManifest,
    run_id: str,
    *,
    expect_target_change: bool,
) -> None:
    """Assert sandbox filesystem policy against before and after manifests."""
    expected_target = f"after:{run_id}\n"
    expected_control = f"control:{run_id}\n"
    target_path = "target.txt"
    control_path = "control.txt"
    if expect_target_change:
        after_target = after.get(target_path)
        if after_target is None:
            msg = "target.txt missing after run"
            raise AssertionError(msg)
        expected_hash = hashlib.sha256(expected_target.encode()).hexdigest()
        if after_target.sha256 != expected_hash:
            msg = f"target.txt bytes mismatch: expected {expected_target!r}"
            raise AssertionError(msg)
    else:
        if before.get(target_path) != after.get(target_path):
            msg = "target.txt changed unexpectedly"
            raise AssertionError(msg)
    before_control = before.get(control_path)
    after_control = after.get(control_path)
    if before_control != after_control:
        msg = "control.txt changed"
        raise AssertionError(msg)
    if after_control is not None:
        expected_hash = hashlib.sha256(expected_control.encode()).hexdigest()
        if after_control.sha256 != expected_hash:
            msg = "control.txt bytes mismatch"
            raise AssertionError(msg)
    all_paths = set(before) | set(after)
    for relative in sorted(all_paths):
        if relative in USER_FILES or _path_allowed_to_change(relative):
            continue
        if before.get(relative) != after.get(relative):
            msg = f"unexpected filesystem change at {relative}"
            raise AssertionError(msg)


def write_initial_sandbox_files(sandbox_dir: pathlib.Path, run_id: str) -> None:
    """Write exact initial target and control files for one sandbox run."""
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    (sandbox_dir / "target.txt").write_text(f"before:{run_id}\n", encoding="utf-8")
    (sandbox_dir / "control.txt").write_text(f"control:{run_id}\n", encoding="utf-8")


def issue_description_for_run(run_id: str) -> str:
    """Build the deterministic issue description for one sandbox run."""
    action = json.dumps(
        {
            "schema": 1,
            "path": "target.txt",
            "before": f"before:{run_id}\n",
            "after": f"after:{run_id}\n",
        },
        separators=(",", ":"),
    )
    return (
        "Edit target.txt in the attached local directory.\n"
        "Replace the exact current content with the exact replacement below.\n"
        "Do not modify control.txt or any other user file.\n"
        f"MULTICA_TEST_ACTION={action}"
    )


def canary_issue_title_for_run(run_id: str) -> str:
    """Build the canary issue title for one sandbox run."""
    return f"Agent canary edit {run_id}"


def canary_issue_description_for_run(run_id: str) -> str:
    """Build the real OpenCode canary issue description for one sandbox run."""
    return (
        "Replace the entire contents of target.txt with exactly:\n"
        f"after:{run_id}\n"
        "(with trailing newline)\n"
        "Do not modify control.txt or any other file.\n"
        "Initial content of target.txt is exactly:\n"
        f"before:{run_id}\n"
        "(with trailing newline)"
    )


def _assert_canary_usage_cost(client: MulticaClient, issue_id: str) -> float:
    try:
        usage = client.issues.usage(issue_id)
    except Exception as exc:
        msg = f"issues.usage failed: {exc}"
        raise LiveSetupError("usage", msg) from exc
    if usage.cost_usd is None:
        raise LiveSetupError("usage", "cost_usd missing from issues.usage payload")
    if usage.cost_usd > CANARY_COST_CEILING_USD:
        msg = f"cost_usd {usage.cost_usd} exceeds ceiling {CANARY_COST_CEILING_USD}"
        raise LiveSetupError("usage", msg)
    return usage.cost_usd


@dataclass(frozen=True, slots=True)
class AgentSandboxOutcome:
    """Observed outcome from one agent sandbox workflow execution."""

    run_status: str
    run_id: str
    file_assertion_failed: bool
    primary_error: str | None
    cleanup_errors: tuple[str, ...]
    cancelled: bool = False
    cost_usd: float | None = None


def _select_post_assignment_run(
    runs: tuple[TaskRun, ...],
    *,
    assigned_at: float,
    first_seen: dict[str, float],
    previous_selected: str | None,
) -> tuple[TaskRun | None, str | None]:
    candidates: list[TaskRun] = []
    for run in runs:
        seen_at = first_seen.setdefault(run.id, time.monotonic())
        if seen_at + 0.001 < assigned_at:
            continue
        candidates.append(run)
    if not candidates:
        return None, previous_selected
    with_started = [run for run in candidates if run.started_at is not None]
    if not with_started:
        return None, previous_selected
    selected = max(
        with_started,
        key=lambda run: run.started_at.timestamp() if run.started_at is not None else float("-inf"),
    )
    if previous_selected is not None and selected.id != previous_selected:
        msg = f"multiple post-assignment runs detected: {previous_selected} vs {selected.id}"
        raise LiveSetupError("run", msg)
    return selected, selected.id


def _refresh_run_until_terminal(
    client: MulticaClient,
    issue_id: str,
    run_id: str,
    selected: TaskRun,
    *,
    timeout_seconds: float,
) -> tuple[TaskRun, str]:
    deadline = time.monotonic() + timeout_seconds
    run_status = selected.status.lower()
    refreshed = selected
    while time.monotonic() < deadline:
        refreshed = next(
            (run for run in client.issues.runs(issue_id) if run.id == run_id),
            selected,
        )
        run_status = refreshed.status.lower()
        if run_status in TERMINAL_RUN_STATUSES:
            return refreshed, run_status
        time.sleep(1.0)
    return refreshed, run_status


def _poll_issue_run(
    client: MulticaClient,
    issue_id: str,
    *,
    assigned_at: float,
    deadline_seconds: float = RUN_ASSIGNMENT_TIMEOUT_SECONDS,
) -> tuple[TaskRun, bool]:
    deadline = time.monotonic() + deadline_seconds
    first_seen: dict[str, float] = {}
    previous_selected: str | None = None
    selected: TaskRun | None = None
    while time.monotonic() < deadline:
        runs = client.issues.runs(issue_id)
        for run in runs:
            first_seen.setdefault(run.id, time.monotonic())
        selected, previous_selected = _select_post_assignment_run(
            runs,
            assigned_at=assigned_at,
            first_seen=first_seen,
            previous_selected=previous_selected,
        )
        if selected is not None and selected.status.lower() in TERMINAL_RUN_STATUSES:
            return selected, False
        time.sleep(1.0)
    if selected is None:
        raise LiveSetupError("run", "no post-assignment run selected before deadline")
    return selected, True


@dataclass(frozen=True, slots=True)
class SandboxExpectation:
    """Expected sandbox workflow outcome for one agent mode."""

    expected_run_status: str | None
    expect_target_change: bool
    expect_cancelled: bool
    expect_file_assertion_failure: bool
    record_canary_cost: bool = False


def _sandbox_expectation(
    *,
    is_canary: bool,
    agent_mode: str,
    expect_success: bool,
) -> SandboxExpectation:
    if is_canary:
        return SandboxExpectation(
            expected_run_status="completed",
            expect_target_change=True,
            expect_cancelled=False,
            expect_file_assertion_failure=False,
            record_canary_cost=True,
        )
    if agent_mode == "success" and expect_success:
        return SandboxExpectation("completed", True, False, False)
    if agent_mode == "error":
        return SandboxExpectation("failed", False, False, False)
    if agent_mode == "timeout":
        return SandboxExpectation(None, False, True, False)
    if agent_mode == "wrong-edit":
        return SandboxExpectation("completed", True, False, True)
    return SandboxExpectation(None, False, False, False)


def _apply_sandbox_expectation(
    expectation: SandboxExpectation,
    *,
    run_status: str,
    cancelled: bool,
    manifest_before: FileManifest,
    manifest_after: FileManifest,
    run_id: str,
    cleanup: CleanupRegistry,
    client: MulticaClient,
    issue_id: str,
    diagnostics: DiagnosticCollector,
) -> tuple[bool, str | None, float | None]:
    file_assertion_failed = False
    primary_error: str | None = None
    cost_usd: float | None = None
    if expectation.expected_run_status is not None:
        assert run_status == expectation.expected_run_status, (
            f"expected {expectation.expected_run_status} run, got {run_status}"
        )
    if expectation.expect_cancelled:
        assert cancelled, "expected timeout cancellation"
    if expectation.expect_file_assertion_failure:
        try:
            assert_manifest_policy(
                manifest_before,
                manifest_after,
                run_id,
                expect_target_change=True,
            )
            assert False, "expected file assertion failure for wrong-edit mode"
        except AssertionError as exc:
            file_assertion_failed = True
            primary_error = str(exc)
            cleanup.set_primary_failure(exc)
    else:
        try:
            assert_manifest_policy(
                manifest_before,
                manifest_after,
                run_id,
                expect_target_change=expectation.expect_target_change,
            )
        except AssertionError as exc:
            file_assertion_failed = True
            primary_error = str(exc)
            cleanup.set_primary_failure(exc)
        else:
            if expectation.record_canary_cost:
                cost_usd = _assert_canary_usage_cost(client, issue_id)
                diagnostics.write_json(
                    "canary-usage.json",
                    {"issue_id": issue_id, "cost_usd": cost_usd},
                )
    return file_assertion_failed, primary_error, cost_usd


@dataclass(slots=True)
class _WorkflowIds:
    workspace_id: str | None = None
    runtime_id: str | None = None
    agent_id: str | None = None
    project_id: str | None = None
    issue_id: str | None = None
    resource_id: str | None = None
    run_execution_id: str | None = None

    def merge(self, run_context: LiveRunContext) -> LiveRunContext:
        return replace(
            run_context,
            workspace_id=self.workspace_id,
            runtime_id=self.runtime_id,
            agent_id=self.agent_id,
            project_id=self.project_id,
            issue_id=self.issue_id,
            resource_id=self.resource_id,
            run_execution_id=self.run_execution_id,
        )


def execute_agent_sandbox_workflow(
    *,
    live_environment: LiveTestEnvironment,
    run_context: LiveRunContext,
    sandbox_settings: AgentSandboxSettings,
    diagnostics: DiagnosticCollector,
    target_report: dict[str, object],
    compose_project: str,
    compose_files: tuple[pathlib.Path, ...],
    inject_cleanup_failure: str | None = None,
    expect_success: bool = True,
    canary_settings: OpenCodeCanarySettings | None = None,
) -> AgentSandboxOutcome:
    """Execute the agent sandbox workflow end to end."""
    is_canary = canary_settings is not None
    resolved_canary = canary_settings
    if is_canary:
        assert resolved_canary is not None
        sandbox_settings = resolved_canary.to_sandbox_settings()
    ids = _WorkflowIds()
    cleanup = CleanupRegistry()
    daemon: DaemonLifecycle | None = None
    client: MulticaClient | None = None
    oracle: DirectApiOracle | None = None
    identity: TestIdentity | None = None
    manifest_before: FileManifest = {}
    manifest_after: FileManifest = {}
    run_status = "unknown"
    file_assertion_failed = False
    primary_error: str | None = None
    cancelled = False
    cost_usd: float | None = None
    cleanup_errors: list[dict[str, str]] = []
    outcome: AgentSandboxOutcome
    try:
        write_initial_sandbox_files(run_context.sandbox_dir, run_context.run_id)
        secret_values: list[str] = []
        if resolved_canary is not None:
            secret_values.extend(resolved_canary.secret_values().values())
        session = setup_sandbox_session(
            server_url=live_environment.server_url,
            run_id=run_context.run_id,
            cli_executable=live_environment.cli_executable,
            home_dir=run_context.home,
            profile_name=run_context.profile_name,
            secret_values=secret_values,
            sandbox_bootstrap=True,
        )
        diagnostics.register_secrets(secret_values)
        identity = session.identity
        bootstrap_client = session.bootstrap_client
        client = session.client
        oracle = session.oracle
        ids.workspace_id = session.workspace.id
        daemon = DaemonLifecycle(
            cli_executable=live_environment.cli_executable,
            home_dir=run_context.home,
            profile_name=run_context.profile_name,
            daemon_id=run_context.daemon_id,
            workspaces_root=run_context.workspaces_root,
            opencode_path=sandbox_settings.opencode_path,
            opencode_model=sandbox_settings.opencode_model,
            agent_mode=sandbox_settings.agent_mode,
            diagnostics=diagnostics,
        )
        daemon.start()
        ids.runtime_id = poll_runtime_online(oracle, daemon_id=run_context.daemon_id)
        agent = client.agents.create(AgentCreateRequest(name=f"{run_context.prefix}-agent"))
        ids.agent_id = agent.id
        project = client.projects.create(ProjectCreateRequest(name=f"{run_context.prefix}-project"))
        ids.project_id = project.id
        issue_title = (
            canary_issue_title_for_run(run_context.run_id)
            if is_canary
            else f"Agent sandbox edit {run_context.run_id}"
        )
        issue_description = (
            canary_issue_description_for_run(run_context.run_id)
            if is_canary
            else issue_description_for_run(run_context.run_id)
        )
        issue = client.issues.create(
            IssueCreateRequest(
                title=issue_title,
                description_input=InlineDescription(text=issue_description),
                project_id=project.id,
            )
        )
        ids.issue_id = issue.id
        resource = client.projects.resources.add_local_directory(
            project.id,
            ProjectResourceAddLocalDirectoryRequest(
                local_path=run_context.sandbox_dir,
                daemon_id=run_context.daemon_id,
            ),
        )
        ids.resource_id = resource.id
        listed = client.projects.resources.list(project.id)
        assert len(listed) == 1
        assert listed[0].resource_ref.local_path == str(run_context.sandbox_dir)
        assert listed[0].resource_ref.daemon_id == run_context.daemon_id
        manifest_before = build_file_manifest(run_context.sandbox_dir)
        assigned_at = time.monotonic()
        client.issues.assign(IssueAssignmentRequest(issue_id=issue.id, agent_id=agent.id))
        selected_run, timed_out = _poll_issue_run(
            client,
            issue.id,
            assigned_at=assigned_at,
        )
        ids.run_execution_id = selected_run.id
        run_status = selected_run.status.lower()
        if timed_out and run_status not in TERMINAL_RUN_STATUSES:
            client.issues.cancel_task(issue.id, selected_run.id)
            cancelled = True
            selected_run, run_status = _refresh_run_until_terminal(
                client,
                issue.id,
                selected_run.id,
                selected_run,
                timeout_seconds=CANCEL_WAIT_TIMEOUT_SECONDS,
            )
        manifest_after = build_file_manifest(run_context.sandbox_dir)
        expectation = _sandbox_expectation(
            is_canary=is_canary,
            agent_mode=sandbox_settings.agent_mode,
            expect_success=expect_success,
        )
        file_assertion_failed, primary_error, cost_usd = _apply_sandbox_expectation(
            expectation,
            run_status=run_status,
            cancelled=cancelled,
            manifest_before=manifest_before,
            manifest_after=manifest_after,
            run_id=run_context.run_id,
            cleanup=cleanup,
            client=client,
            issue_id=issue.id,
            diagnostics=diagnostics,
        )
        if oracle is not None and ids.issue_id and ids.agent_id:
            issue_raw = oracle.get_issue(ids.issue_id)
            assert oracle.issue_project_id(issue_raw) == ids.project_id
            assert oracle.issue_assignee_id(issue_raw) == ids.agent_id
        outcome = AgentSandboxOutcome(
            run_status=run_status,
            run_id=run_context.run_id,
            file_assertion_failed=file_assertion_failed,
            primary_error=primary_error,
            cleanup_errors=(),
            cancelled=cancelled,
            cost_usd=cost_usd,
        )
    except BaseException as exc:
        cleanup.set_primary_failure(exc)
        if primary_error is None and not isinstance(exc, LiveSetupError):
            primary_error = str(exc)
        active_context = ids.merge(run_context)
        bundle = LiveDiagnosticsBundle(diagnostics, run_context.run_id)
        bundle.write_failure_bundle(
            target_report=target_report,
            run_context=active_context,
            entities=_collect_entities_snapshot(client, oracle, active_context),
            runtime_state=_collect_runtime_snapshot(client, oracle, active_context),
            run_messages=_collect_run_messages(client, active_context),
            filesystem_before=manifest_before,
            filesystem_after=manifest_after,
            sandbox_dir=run_context.sandbox_dir,
            daemon=daemon,
            compose_project=compose_project,
            compose_files=compose_files,
            primary_failure=exc,
        )
        raise
    finally:
        if (
            client is not None
            and oracle is not None
            and identity is not None
            and daemon is not None
        ):
            _register_sandbox_cleanup(
                cleanup,
                client=client,
                oracle=oracle,
                identity=identity,
                daemon=daemon,
                bootstrap_client=bootstrap_client,
                run_context=ids.merge(run_context),
                live_environment=live_environment,
                compose_project=compose_project,
                inject_cleanup_failure=inject_cleanup_failure,
            )
            cleanup_errors = cleanup.execute_all()
            diagnostics.record_cleanup(
                {
                    "failures": cleanup_errors,
                    "primary_failure": None
                    if cleanup.primary_failure is None
                    else str(cleanup.primary_failure),
                }
            )
            oracle.close()
    return AgentSandboxOutcome(
        run_status=outcome.run_status,
        run_id=outcome.run_id,
        file_assertion_failed=outcome.file_assertion_failed,
        primary_error=outcome.primary_error,
        cleanup_errors=tuple(item["message"] for item in cleanup_errors),
        cancelled=outcome.cancelled,
        cost_usd=outcome.cost_usd,
    )


def _collect_entities_snapshot(
    client: MulticaClient | None,
    oracle: DirectApiOracle | None,
    run_context: LiveRunContext,
) -> dict[str, object]:
    if client is None or oracle is None:
        return {}
    payload: dict[str, object] = {"run_context": run_context.diagnostics_payload()}
    if run_context.workspace_id:
        payload["workspace_id"] = run_context.workspace_id
    if run_context.project_id:
        payload["project"] = oracle.get_project(run_context.project_id)
    if run_context.issue_id:
        payload["issue"] = oracle.get_issue(run_context.issue_id)
    if run_context.agent_id:
        payload["agent"] = oracle.get_agent_raw(run_context.agent_id)
    if run_context.project_id and run_context.resource_id:
        payload["resources"] = oracle.list_project_resources_raw(run_context.project_id)
    return payload


def _collect_runtime_snapshot(
    client: MulticaClient | None,
    oracle: DirectApiOracle | None,
    run_context: LiveRunContext,
) -> dict[str, object]:
    if client is None or oracle is None:
        return {}
    runtimes = oracle.list_runtimes_raw()
    selected = None
    if run_context.runtime_id:
        selected = oracle.get_runtime_raw(run_context.runtime_id)
    return {"list": runtimes, "selected": selected}


def _collect_run_messages(
    client: MulticaClient | None,
    run_context: LiveRunContext,
) -> list[dict[str, object]]:
    if client is None or run_context.issue_id is None or run_context.run_execution_id is None:
        return []
    messages = client.issues.run_messages(run_context.issue_id, run_context.run_execution_id)
    return [
        {
            "id": message.id,
            "run_id": message.run_id,
            "role": message.role,
            "content": message.content,
        }
        for message in messages
    ]


def _register_sandbox_cleanup(
    cleanup: CleanupRegistry,
    *,
    client: MulticaClient,
    oracle: DirectApiOracle,
    identity: TestIdentity,
    daemon: DaemonLifecycle,
    bootstrap_client: BootstrapApiClient,
    run_context: LiveRunContext,
    live_environment: LiveTestEnvironment,
    compose_project: str,
    inject_cleanup_failure: str | None,
) -> None:
    issue_id = run_context.issue_id
    run_execution_id = run_context.run_execution_id

    def _cancel_run() -> None:
        if issue_id is None or run_execution_id is None:
            return
        runs = client.issues.runs(issue_id)
        selected = next((run for run in runs if run.id == run_execution_id), None)
        if selected is None or selected.status.lower() in TERMINAL_RUN_STATUSES:
            return
        client.issues.cancel_task(issue_id, run_execution_id)
        _refresh_run_until_terminal(
            client,
            issue_id,
            run_execution_id,
            selected,
            timeout_seconds=CANCEL_WAIT_TIMEOUT_SECONDS,
        )

    def _remove_resource() -> None:
        if inject_cleanup_failure == "remove-resource":
            raise LiveCleanupError("remove-resource")
        if run_context.project_id is None or run_context.resource_id is None:
            return
        try:
            client.projects.resources.remove(run_context.project_id, run_context.resource_id)
        except NotFoundError:
            raise ResourceAbsentError() from None

    def _archive_agent() -> None:
        if run_context.agent_id is None:
            return
        try:
            client.agents.archive(run_context.agent_id)
        except NotFoundError:
            raise ResourceAbsentError() from None

    def _delete_project() -> None:
        if run_context.project_id is None:
            return
        try:
            client.projects.delete(run_context.project_id)
        except NotFoundError:
            raise ResourceAbsentError() from None

    def _stop_daemon() -> None:
        daemon.stop()

    def _wait_runtime_deregister() -> None:
        poll_runtime_deregistered(
            oracle,
            daemon_id=run_context.daemon_id,
            runtime_id=run_context.runtime_id,
        )

    def _delete_workspace() -> None:
        if run_context.workspace_id is None:
            return
        bootstrap_client.delete_workspace(run_context.workspace_id, identity.pat.reveal())

    def _remove_temp_paths() -> None:
        remove_live_run_context(run_context)

    def _postcondition_audit() -> None:
        if daemon.is_running:
            msg = f"daemon pid still running: {daemon.pid}"
            raise LiveSetupError("audit", msg)
        if not oracle.runtime_absent_or_non_routable(run_context.daemon_id, run_context.runtime_id):
            msg = "matching runtime still routable"
            raise LiveSetupError("audit", msg)
        if run_context.agent_id is not None:
            oracle.assert_agent_non_routable(run_context.agent_id)
        if run_context.project_id and run_context.resource_id:
            oracle.assert_project_resource_absent(run_context.project_id, run_context.resource_id)
        if run_context.project_id:
            oracle.assert_absent(f"/api/projects/{run_context.project_id}", "project")
        if run_context.workspace_id:
            oracle.assert_workspace_absent(run_context.workspace_id, identity.pat.reveal())
        if run_context.temp_root.exists():
            msg = f"temp root still exists: {run_context.temp_root}"
            raise LiveSetupError("audit", msg)
        if live_environment.managed_compose:
            ps = subprocess.run(
                [
                    "docker",
                    "ps",
                    "-a",
                    "--filter",
                    f"label=com.docker.compose.project={compose_project}",
                    "--format",
                    "{{.Names}}",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            names = [line for line in ps.stdout.splitlines() if line.strip()]
            if names:
                msg = f"docker objects remain for compose project {compose_project}: {names}"
                raise LiveSetupError("audit", msg)

    cleanup.register("cancel-run", _cancel_run)
    cleanup.register("remove-resource", _remove_resource)
    cleanup.register("archive-agent", _archive_agent)
    cleanup.register("delete-project", _delete_project)
    cleanup.register("stop-daemon", _stop_daemon)
    cleanup.register("wait-runtime-deregister", _wait_runtime_deregister)
    cleanup.register("delete-workspace", _delete_workspace)
    cleanup.register("remove-temp-paths", _remove_temp_paths)
    cleanup.register("postcondition-audit", _postcondition_audit)
