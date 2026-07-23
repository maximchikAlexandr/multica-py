"""Three-phase agent-sandbox workflow with immediate LIFO cleanup.

Exports:
  - ``prepare_sandbox(env, workspace) -> PreparedSandbox``: phase 1.
  - ``run_assignment(sandbox, assignment) -> CompletedAssignment``: phase 2.
  - ``verify_sandbox(sandbox, completed) -> SandboxVerification``: phase 3.

Each phase registers its own cleanup on the session ``ExitStack`` as soon
as it acquires its resources (immediate LIFO cleanup, see
``contracts/live-core.md``).

The two-layer ``RunContext`` / ``Assignment`` split keeps phase 1 isolated
from backend work (it never touches the API) and lets phase 2 carry
the assignment-time inputs without leaking them into phase 3.
"""

from __future__ import annotations

import pathlib
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

from multica_py.client import MulticaClient
from multica_py.exceptions import NotFoundError
from multica_py.models.agents import AgentCreateRequest
from multica_py.models.issues import (
    FileDescription,
    InlineDescription,
    IssueAssignmentRequest,
    IssueCreateRequest,
)
from multica_py.models.project_resources import ProjectResourceAddLocalDirectoryRequest
from multica_py.models.projects import ProjectCreateRequest
from tests.live._live_helpers import LiveRunContext, remove_live_run_context
from tests.live.backend import (
    TERMINAL_RUN_STATUSES,
    BootstrapApiClient,
    DaemonLifecycle,
    poll_runtime_deregistered,
    poll_runtime_online,
    setup_sandbox_session,
)
from tests.live.diagnostics import DiagnosticCollector
from tests.live.sandbox.models import (
    CompletedAssignment,
    FileManifest,
    PreparedSandbox,
    SandboxVerification,
    build_file_manifest,
)
from tests.live.sandbox.policy import (
    assert_manifest_policy,
    canary_issue_description_for_run,
    canary_issue_title_for_run,
    issue_description_for_run,
    write_initial_sandbox_files,
)
from tools.live_support.environment import (
    AgentSandboxSettings,
    LiveSetupError,
    OpenCodeCanarySettings,
    ResourceAbsentError,
)

RUN_ASSIGNMENT_TIMEOUT_SECONDS = 120.0
CANCEL_WAIT_TIMEOUT_SECONDS = 10.0

__all__ = [
    "Assignment",
    "CompletedAssignment",
    "LiveCleanupError",
    "PreparedSandbox",
    "SandboxCleanupRegistry",
    "SandboxVerification",
    "prepare_sandbox",
    "run_assignment",
    "verify_sandbox",
]


class LiveCleanupError(RuntimeError):
    """Raised when an injected cleanup step fails deterministically."""


@dataclass(frozen=True, slots=True)
class Assignment:
    """Inputs for phase 2 (run the agent)."""

    settings: AgentSandboxSettings
    canary_settings: OpenCodeCanarySettings | None = None
    inject_cleanup_failure: str | None = None


def _resolved_sandbox_settings(assignment: Assignment) -> AgentSandboxSettings:
    if assignment.canary_settings is not None:
        return assignment.canary_settings.to_sandbox_settings()
    return assignment.settings


class SandboxCleanupRegistry:
    """Fixed-order cleanup registry for agent sandbox runs (T070, T071).

    Cleanup actions run in a stable contract order so each subsequent step
    sees a consistent state. ``ResourceAbsentError`` and ``NotFoundError``
    are absorbed; everything else becomes a ``{name, message}`` failure
    on the returned list. The primary failure is recorded once and never
    overwritten.
    """

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
        """Record the primary workflow failure without overwriting."""
        if self._primary_failure is None and exc is not None:
            self._primary_failure = exc

    @property
    def primary_failure(self) -> BaseException | None:
        return self._primary_failure

    def execute_all(self) -> list[dict[str, str]]:
        """Run the registered actions in contract order; return failures."""
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
            except Exception as exc:  # surfaced on the result
                failures.append({"name": name, "message": str(exc)})
        return failures


def _sandbox_expectation(*, is_canary: bool, agent_mode: str) -> dict[str, Any]:
    if is_canary:
        return {
            "expected_run_status": "completed",
            "expect_target_change": True,
            "expect_cancelled": False,
            "expect_file_assertion_failure": False,
            "record_canary_cost": True,
        }
    if agent_mode == "success":
        return {
            "expected_run_status": "completed",
            "expect_target_change": True,
            "expect_cancelled": False,
            "expect_file_assertion_failure": False,
            "record_canary_cost": False,
        }
    if agent_mode == "error":
        return {
            "expected_run_status": "failed",
            "expect_target_change": False,
            "expect_cancelled": False,
            "expect_file_assertion_failure": False,
            "record_canary_cost": False,
        }
    if agent_mode == "timeout":
        return {
            "expected_run_status": None,
            "expect_target_change": False,
            "expect_cancelled": True,
            "expect_file_assertion_failure": False,
            "record_canary_cost": False,
        }
    if agent_mode == "wrong-edit":
        return {
            "expected_run_status": "completed",
            "expect_target_change": True,
            "expect_cancelled": False,
            "expect_file_assertion_failure": True,
            "record_canary_cost": False,
        }
    return {
        "expected_run_status": None,
        "expect_target_change": False,
        "expect_cancelled": False,
        "expect_file_assertion_failure": False,
        "record_canary_cost": False,
    }


def _select_post_assignment_run(
    runs: tuple[Any, ...],
    *,
    assigned_at: float,
    first_seen: dict[str, float],
    previous_selected: str | None,
) -> tuple[Any | None, str | None]:
    candidates: list[Any] = []
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
        key=lambda run: run.started_at.timestamp() if run.started_at else float("-inf"),
    )
    if previous_selected is not None and selected.id != previous_selected:
        raise LiveSetupError(
            "run",
            f"multiple post-assignment runs detected: {previous_selected} vs {selected.id}",
        )
    return selected, selected.id


def _refresh_run_until_terminal(
    client: MulticaClient,
    issue_id: str,
    run_id: str,
    selected: Any,
    *,
    timeout_seconds: float,
) -> tuple[Any, str]:
    deadline = time.monotonic() + timeout_seconds
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
    return refreshed, refreshed.status.lower()


def _poll_issue_run(
    client: MulticaClient,
    issue_id: str,
    *,
    assigned_at: float,
    deadline_seconds: float = RUN_ASSIGNMENT_TIMEOUT_SECONDS,
) -> tuple[Any, bool]:
    deadline = time.monotonic() + deadline_seconds
    first_seen: dict[str, float] = {}
    previous_selected: str | None = None
    selected: Any | None = None
    while time.monotonic() < deadline:
        runs = client.issues.runs(issue_id)
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


def _assert_canary_usage_cost(
    client: MulticaClient,
    issue_id: str,
    ceiling_usd: float,
) -> float:
    try:
        usage = client.issues.usage(issue_id)
    except Exception as exc:
        raise LiveSetupError("usage", f"issues.usage failed: {exc}") from exc
    if usage.cost_usd is None:
        raise LiveSetupError("usage", "cost_usd missing from issues.usage payload")
    if usage.cost_usd > ceiling_usd:
        raise LiveSetupError(
            "usage",
            f"cost_usd {usage.cost_usd} exceeds ceiling {ceiling_usd}",
        )
    return usage.cost_usd


@dataclass(slots=True)
class _WorkflowIds:
    """Captured remote identifiers for the active sandbox run."""

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


def prepare_sandbox(
    session: Any,
    workspace: pathlib.Path,
    *,
    run_id: str,
) -> PreparedSandbox:
    """Phase 1: create an isolated sandbox directory and write the starting files.

    Registers an immediate rmtree cleanup on ``session`` so the workspace
    is removed when the session exits.
    """
    sandbox_dir = workspace.resolve() / "sandbox"
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    write_initial_sandbox_files(sandbox_dir, run_id)
    if session is not None:

        def _cleanup() -> None:
            import shutil

            shutil.rmtree(workspace, ignore_errors=True)

        session.defer_cleanup(_cleanup)
    return PreparedSandbox(
        sandbox_dir=sandbox_dir,
        run_id=run_id,
        target_path=sandbox_dir / "target.txt",
        control_path=sandbox_dir / "control.txt",
    )


def run_assignment(
    env: Any,
    sandbox: PreparedSandbox,
    assignment: Assignment,
    *,
    diagnostics: DiagnosticCollector,
) -> CompletedAssignment:
    """Phase 2: bootstrap session, start daemon, run the agent, return result.

    Registers each acquired resource in a ``SandboxCleanupRegistry`` and
    runs the cleanup immediately before returning. Returns a
    ``CompletedAssignment``; the caller invokes ``verify_sandbox`` next.
    """
    is_canary = assignment.canary_settings is not None
    resolved_sandbox_settings = _resolved_sandbox_settings(assignment)
    run_context: LiveRunContext = replace(
        env.agent_sandbox_run_context,
        sandbox_dir=sandbox.sandbox_dir,
    )
    write_initial_sandbox_files(sandbox.sandbox_dir, sandbox.run_id)
    cleanup_registry = SandboxCleanupRegistry()
    ids = _WorkflowIds()
    file_assertion_failed = False
    primary_error: str | None = None
    cost_usd: float | None = None
    run_status = "unknown"
    cancelled = False
    manifest_before: FileManifest = {}
    manifest_after: FileManifest = {}
    daemon: DaemonLifecycle | None = None
    try:
        secret_values: list[str] = []
        if assignment.canary_settings is not None:
            secret_values.extend(assignment.canary_settings.secret_values().values())
        bootstrap = setup_sandbox_session(
            server_url=env.server_url,
            run_id=sandbox.run_id,
            cli_executable=env.cli_executable,
            home_dir=run_context.home,
            profile_name=run_context.profile_name,
            secret_values=secret_values,
            sandbox_bootstrap=True,
        )
        diagnostics.register_secrets(secret_values)
        client = bootstrap.client
        oracle = bootstrap.oracle
        identity = bootstrap.identity
        ids.workspace_id = bootstrap.workspace.id
        daemon = DaemonLifecycle(
            cli_executable=env.cli_executable,
            home_dir=run_context.home,
            profile_name=run_context.profile_name,
            daemon_id=run_context.daemon_id,
            workspaces_root=run_context.workspaces_root,
            opencode_path=resolved_sandbox_settings.opencode_path,
            opencode_model=resolved_sandbox_settings.opencode_model,
            agent_mode=resolved_sandbox_settings.agent_mode,
            diagnostics=diagnostics,
        )
        daemon.start()
        ids.runtime_id = poll_runtime_online(oracle, daemon_id=run_context.daemon_id)
        agent = client.agents.create(
            AgentCreateRequest(
                name=f"{run_context.prefix}-agent",
                runtime_id=ids.runtime_id,
                model=resolved_sandbox_settings.opencode_model,
            )
        )
        ids.agent_id = agent.id
        project = client.projects.create(ProjectCreateRequest(name=f"{run_context.prefix}-project"))
        ids.project_id = project.id
        issue_title = (
            canary_issue_title_for_run(sandbox.run_id)
            if is_canary
            else f"Agent sandbox edit {sandbox.run_id}"
        )
        if is_canary:
            description_input: FileDescription | InlineDescription = InlineDescription(
                text=canary_issue_description_for_run(sandbox.run_id)
            )
        else:
            description_path = run_context.home / "sandbox-issue-description.txt"
            description_path.write_text(issue_description_for_run(sandbox.run_id), encoding="utf-8")
            description_input = FileDescription(path=str(description_path))
        issue = client.issues.create(
            IssueCreateRequest(
                title=issue_title,
                description_input=description_input,
                project_id=project.id,
            )
        )
        ids.issue_id = issue.id
        resource = client.projects.resources.add_local_directory(
            project.id,
            ProjectResourceAddLocalDirectoryRequest(
                local_path=sandbox.sandbox_dir,
                daemon_id=run_context.daemon_id,
            ),
        )
        ids.resource_id = resource.id
        listed = client.projects.resources.list(project.id)
        assert len(listed) == 1
        assert listed[0].resource_ref.local_path == str(sandbox.sandbox_dir)
        assert listed[0].resource_ref.daemon_id == run_context.daemon_id
        manifest_before = build_file_manifest(sandbox.sandbox_dir)
        assigned_at = time.monotonic()
        client.issues.assign(IssueAssignmentRequest(issue_id=issue.id, agent_id=agent.id))
        selected_run, timed_out = _poll_issue_run(client, issue.id, assigned_at=assigned_at)
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
        manifest_after = build_file_manifest(sandbox.sandbox_dir)
        expectation = _sandbox_expectation(
            is_canary=is_canary,
            agent_mode=resolved_sandbox_settings.agent_mode,
        )

        def _assert_policy() -> None:
            assert_manifest_policy(
                manifest_before,
                manifest_after,
                sandbox.run_id,
                expect_target_change=bool(expectation["expect_target_change"]),
            )
            assert not expectation["expect_file_assertion_failure"], (
                "expected file assertion failure for wrong-edit mode"
            )

        try:
            _assert_policy()
        except AssertionError as exc:
            file_assertion_failed = True
            primary_error = str(exc)
            cleanup_registry.set_primary_failure(exc)
        if (
            not file_assertion_failed
            and expectation["record_canary_cost"]
            and assignment.canary_settings is not None
        ):
            from tools.live_support.environment import CANARY_COST_CEILING_USD

            cost_usd = _assert_canary_usage_cost(client, issue.id, CANARY_COST_CEILING_USD)
            diagnostics.write_json(
                "canary-usage.json",
                {"issue_id": issue.id, "cost_usd": cost_usd},
            )
        merged_context = ids.merge(run_context)
        _register_session_cleanup(
            registry=cleanup_registry,
            client=client,
            oracle=oracle,
            identity=identity,
            daemon=daemon,
            bootstrap_client=bootstrap.bootstrap_client,
            run_context=merged_context,
            inject_cleanup_failure=assignment.inject_cleanup_failure,
        )
    except BaseException as exc:
        cleanup_registry.set_primary_failure(exc)
        raise
    finally:
        cleanup_failures = cleanup_registry.execute_all()
        diagnostics.record_cleanup(
            {
                "failures": cleanup_failures,
                "primary_failure": (
                    None
                    if cleanup_registry.primary_failure is None
                    else str(cleanup_registry.primary_failure)
                ),
            }
        )
        if daemon is not None:
            oracle.close()
    return CompletedAssignment(
        run_status=run_status,
        cancelled=cancelled,
        manifest_before=manifest_before,
        manifest_after=manifest_after,
        cleanup_errors=tuple(item["message"] for item in cleanup_failures),
        cost_usd=cost_usd,
        primary_error=primary_error,
        file_assertion_failed=file_assertion_failed,
    )


def _register_session_cleanup(
    *,
    registry: SandboxCleanupRegistry,
    client: MulticaClient,
    oracle: Any,
    identity: Any,
    daemon: DaemonLifecycle,
    bootstrap_client: BootstrapApiClient,
    run_context: LiveRunContext,
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
        except NotFoundError as exc:
            raise ResourceAbsentError() from exc

    def _archive_agent() -> None:
        if run_context.agent_id is None:
            return
        try:
            client.agents.archive(run_context.agent_id)
        except NotFoundError as exc:
            raise ResourceAbsentError() from exc

    def _delete_project() -> None:
        if run_context.project_id is None:
            return
        try:
            client.projects.delete(run_context.project_id)
        except NotFoundError as exc:
            raise ResourceAbsentError() from exc

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
            raise LiveSetupError("audit", f"daemon pid still running: {daemon.pid}")
        if not oracle.runtime_absent_or_non_routable(run_context.daemon_id, run_context.runtime_id):
            raise LiveSetupError("audit", "matching runtime still routable")
        if run_context.agent_id is not None:
            oracle.assert_agent_non_routable(run_context.agent_id)
        if run_context.project_id and run_context.resource_id:
            oracle.assert_project_resource_absent(run_context.project_id, run_context.resource_id)
        if run_context.project_id:
            oracle.assert_absent(f"/api/projects/{run_context.project_id}", "project")
        if run_context.workspace_id:
            oracle.assert_workspace_absent(run_context.workspace_id, identity.pat.reveal())
        if run_context.temp_root.exists():
            raise LiveSetupError("audit", f"temp root still exists: {run_context.temp_root}")

    steps = (
        ("cancel-run", _cancel_run),
        ("remove-resource", _remove_resource),
        ("archive-agent", _archive_agent),
        ("delete-project", _delete_project),
        ("stop-daemon", _stop_daemon),
        ("wait-runtime-deregister", _wait_runtime_deregister),
        ("delete-workspace", _delete_workspace),
        ("remove-temp-paths", _remove_temp_paths),
        ("postcondition-audit", _postcondition_audit),
    )
    assert [name for name, _ in steps] == list(SandboxCleanupRegistry._ORDER)
    for name, action in steps:
        registry.register(name, action)


def verify_sandbox(
    sandbox: PreparedSandbox,
    completed: CompletedAssignment,
) -> SandboxVerification:
    """Phase 3: assert the run completed without a primary error.

    The cleanup is already registered by ``run_assignment``; this phase
    only validates and produces the final ``SandboxVerification``.
    """
    if completed.primary_error is not None:
        return SandboxVerification(verified=False, primary_error=completed.primary_error)
    if completed.cost_usd is not None and completed.run_status != "completed":
        return SandboxVerification(
            verified=False,
            primary_error=f"expected completed run, got {completed.run_status}",
        )
    return SandboxVerification(verified=True, primary_error=None)
