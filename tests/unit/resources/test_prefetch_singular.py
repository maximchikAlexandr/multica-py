from __future__ import annotations

import datetime
import threading
import types
from collections.abc import Mapping
from typing import cast
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.entities.issues import Issue
from multica_py.enums import CompatibilityPolicy, IssueStatus
from multica_py.exceptions import MissingRelationContextError
from multica_py.execution import LocalExecutor
from multica_py.models.relations import LazyCollection, LazyMapping, LazyRef


def _issue(client: MulticaClient, issue_id: str, parent_id: str | None = "parent-1") -> Issue:
    presence = () if parent_id is not None else (("parent_id", "null"),)
    return Issue(
        id=issue_id,
        title="Source",
        status=IssueStatus.todo,
        parent_id=parent_id,
        _wire_presence=presence,
        _client=client,
    )


def _target(client: MulticaClient, title: str) -> Issue:
    return Issue(id="parent-1", title=title, status=IssueStatus.todo, _client=client)


def test_prefetch_coalesces_equal_scopes_and_rebinds_independent_targets() -> None:
    client = MulticaClient(ClientConfig())
    derived = client.with_options()
    calls = MagicMock()
    target = _target(client, "Target")
    calls.side_effect = lambda _issue_id: client.issues._plan(
        steps=(), finalize=lambda _results: target
    )
    client.issues.get_command = calls  # type: ignore[method-assign]

    first = _issue(client, "source-1")
    second = _issue(derived, "source-2")
    first_ref = first.parent
    second_ref = second.parent

    try:
        client.prefetch((first, second), lambda issue: issue.parent, max_parallel=2)  # type: ignore[type-var]

        assert calls.call_count == 1
        first_target = first_ref.value
        second_target = second_ref.value
        assert first_target is not None
        assert second_target is not None
        assert first_target is not second_target
        assert first_target is not target
        assert second_target is not target
        assert first_target._client is client
        assert second_target._client is derived
        first_nested = first_target.parent
        second_nested = second_target.parent
        assert first_nested is not second_nested
    finally:
        derived.close()
        client.close()


def test_prefetch_deduplicates_repeated_singular_destination_handle() -> None:
    client = MulticaClient(ClientConfig())
    calls = MagicMock()
    target = _target(client, "Target")
    calls.return_value = client.issues._plan(steps=(), finalize=lambda _results: target)
    client.issues.get_command = calls  # type: ignore[method-assign]
    source = _issue(client, "source-1")
    reference = source.parent
    publish = MagicMock(wraps=reference._prefetch_publish)
    reference._prefetch_publish = publish  # type: ignore[method-assign]

    try:
        client.prefetch((source, source), lambda _issue: reference, max_parallel=1)  # type: ignore[type-var]

        calls.assert_called_once_with("parent-1")
        publish.assert_called_once_with(target)
    finally:
        client.close()


def test_prefetch_runs_equal_targets_in_different_profiles_separately() -> None:
    client = MulticaClient(ClientConfig())
    other = client.with_profile("other")
    first_calls = MagicMock()
    other_calls = MagicMock()
    first_calls.side_effect = lambda _issue_id: client.issues._plan(
        steps=(), finalize=lambda _results: _target(client, "first")
    )
    other_calls.side_effect = lambda _issue_id: other.issues._plan(
        steps=(), finalize=lambda _results: _target(other, "other")
    )
    client.issues.get_command = first_calls  # type: ignore[method-assign]
    other.issues.get_command = other_calls  # type: ignore[method-assign]
    first = _issue(client, "source-1")
    second = _issue(other, "source-2")

    try:
        client.prefetch((first, second), lambda issue: issue.parent, max_parallel=2)  # type: ignore[type-var]

        assert first_calls.call_count == 1
        assert other_calls.call_count == 1
        assert first.parent.value is not second.parent.value
    finally:
        other.close()
        client.close()


def test_prefetch_skips_explicit_null_singular_absence() -> None:
    client = MulticaClient(ClientConfig())
    calls = MagicMock()
    client.issues.get_command = calls  # type: ignore[method-assign]
    issue = _issue(client, "source-1", parent_id=None)

    try:
        reference = issue.parent
        assert reference.loaded
        client.prefetch((issue,), lambda value: value.parent)  # type: ignore[type-var]
        assert reference.value is None
        calls.assert_not_called()
    finally:
        client.close()


def test_singular_scope_preserves_environment_order_and_ignores_display_fields() -> None:
    base = MulticaClient(
        ClientConfig(
            environment=(("X", "b"), ("X", "a")),
            app_url="https://app.example",
            workspace_slug="base",
        )
    )
    reversed_environment = MulticaClient(
        ClientConfig(
            environment=(("X", "a"), ("X", "b")),
            app_url="https://other.example",
            workspace_slug="other",
        ),
        executor=base._executor,
        _semaphore=base._semaphore,
    )
    display_variant = MulticaClient(
        ClientConfig(
            environment=(("X", "b"), ("X", "a")),
            app_url="https://other.example",
            workspace_slug="other",
        ),
        executor=base._executor,
        _semaphore=base._semaphore,
    )

    try:
        base_key = base._singular_scope_key("Issue", "issue-1")
        assert base_key != reversed_environment._singular_scope_key("Issue", "issue-1")
        assert base_key == display_variant._singular_scope_key("Issue", "issue-1")
    finally:
        display_variant.close()
        reversed_environment.close()
        base.close()


_SCOPE_COMPONENTS: tuple[tuple[str, dict[str, object], bool], ...] = (
    ("workspace", {"workspace_id": "workspace-2"}, False),
    ("profile", {"profile": "profile-2"}, False),
    ("server", {"server_url": "https://server.example"}, False),
    ("executable", {"executable": "/opt/multica"}, False),
    ("cwd", {"cwd": "/tmp/multica"}, False),
    ("environment", {"environment": (("X", "b"), ("X", "a"))}, False),
    ("timeout", {"timeout": datetime.timedelta(seconds=12)}, False),
    ("debug", {"debug": True}, False),
    ("encoding", {"encoding": "utf-16"}, False),
    ("compatibility", {"compatibility": CompatibilityPolicy.strict}, False),
    ("min-cli", {"min_cli_version": "0.4.28"}, False),
    ("max-cli", {"max_cli_version": "0.4.29"}, False),
    ("executor", {}, True),
)


def test_prefetch_separates_every_non_semaphore_scope_component() -> None:
    base_config = ClientConfig(environment=(("X", "a"), ("X", "b")))
    root = MulticaClient(base_config)
    clients: list[MulticaClient] = [root]
    sources = [_issue(root, "source-root")]
    calls: list[MagicMock] = []

    for name, changes, separate_executor in _SCOPE_COMPONENTS:
        config = msgspec.structs.replace(base_config, **changes)
        executor = LocalExecutor() if separate_executor else root._executor
        client = MulticaClient(config, executor=executor, _semaphore=root._semaphore)
        clients.append(client)
        sources.append(_issue(client, f"source-{name}"))
        calls_for_client = MagicMock()
        target = _target(client, name)
        calls_for_client.side_effect = lambda _issue_id, target=target, client=client: (
            client.issues._plan(steps=(), finalize=lambda _results, target=target: target)
        )
        client.issues.get_command = calls_for_client  # type: ignore[method-assign]
        calls.append(calls_for_client)

    root_calls = MagicMock()
    root_target = _target(root, "root")
    root_calls.side_effect = lambda _issue_id: root.issues._plan(
        steps=(), finalize=lambda _results: root_target
    )
    root.issues.get_command = root_calls  # type: ignore[method-assign]
    calls.insert(0, root_calls)

    try:
        root.prefetch(tuple(sources), lambda issue: issue.parent, max_parallel=len(sources))  # type: ignore[type-var]
        assert [call.call_count for call in calls] == [1] * len(calls)
    finally:
        for client in reversed(clients[1:]):
            client.close()
        root.close()


def test_prefetch_rejects_foreign_semaphore_before_singular_io() -> None:
    root = MulticaClient(ClientConfig())
    derived = root.with_profile("derived")
    foreign = MulticaClient(ClientConfig())
    first = _issue(root, "first")
    second = _issue(derived, "second")
    third = _issue(foreign, "third")
    selected = 0

    def selector(issue: Issue) -> LazyRef[Issue | None]:
        nonlocal selected
        selected += 1
        return issue.parent

    try:
        with pytest.raises(ValueError, match="origin"):
            root.prefetch((first, second, third), selector)  # type: ignore[type-var]
        assert selected == 2
        assert first.parent.loaded is False
        assert second.parent.loaded is False
    finally:
        foreign.close()
        derived.close()
        root.close()


def test_prefetch_keeps_collection_and_mapping_identity_dedup_for_all_inventory_rows() -> None:
    relation_names = (
        "Workspace.members",
        "Workspace.agents",
        "Workspace.skills",
        "Workspace.projects",
        "Workspace.issues",
        "Workspace.labels",
        "Workspace.autopilots",
        "Workspace.repositories",
        "Workspace.runtimes",
        "Workspace.squads",
        "Workspace.plugins",
        "Workspace.properties",
        "Workspace.mcp_servers",
        "Agent.skills",
        "Agent.tasks",
        "Agent.issues",
        "Agent.mcp_servers",
        "Skill.files",
        "Squad.members",
        "Squad.issues",
        "WorkspaceMember.issues",
        "Project.resources",
        "Project.issues",
        "Issue.comments",
        "Issue.recent_comment_threads",
        "Issue.labels",
        "Issue.subscribers",
        "Issue.metadata",
        "Issue.pull_requests",
        "Issue.children",
        "Issue.runs",
        "Issue.properties",
        "CommentThread.comments",
        "TaskRun.messages",
        "Autopilot.runs",
        "Autopilot.triggers",
        "Autopilot.subscribers",
        "AutopilotRun.messages",
    )
    mapping_rows = {"Issue.metadata", "Issue.properties"}
    client = MulticaClient(ClientConfig())
    try:
        for relation_name in relation_names:
            calls = {"count": 0}

            def mapping_loader() -> Mapping[str, str]:
                calls["count"] += 1
                return {"value": relation_name}

            def collection_loader() -> tuple[object, ...]:
                calls["count"] += 1
                return ()

            if relation_name in mapping_rows:
                relation: LazyMapping[str, str] | LazyCollection[object] = LazyMapping(
                    mapping_loader
                )
            else:
                relation = LazyCollection(collection_loader)
            entity = types.SimpleNamespace(_client=client)
            selected = iter((relation, relation))
            client.prefetch((entity, entity), lambda _entity: next(selected), max_parallel=1)
            assert calls["count"] == 1, relation_name
    finally:
        client.close()


@pytest.mark.parametrize("shape", ["omitted", "null", "value"])
def test_prefetch_fanout_preserves_nested_provenance_and_local_state(shape: str) -> None:
    root = MulticaClient(ClientConfig())
    secondary = root.with_options()
    nested_target_calls: list[tuple[MulticaClient, str]] = []

    if shape == "omitted":
        target = Issue(
            id="shared",
            title="Target",
            status=IssueStatus.todo,
            parent_id=None,
            _wire_presence=(),
            _client=root,
        )
    elif shape == "null":
        target = Issue(
            id="shared",
            title="Target",
            status=IssueStatus.todo,
            parent_id=None,
            _wire_presence=(("parent_id", "null"),),
            _client=root,
        )
    else:
        target = Issue(
            id="shared",
            title="Target",
            status=IssueStatus.todo,
            parent_id="nested-1",
            _wire_presence=(("parent_id", "value"),),
            _client=root,
        )

    def get_command(client: MulticaClient, issue_id: str) -> object:
        nested_target_calls.append((client, issue_id))
        if issue_id == "shared":
            value = target
        else:
            value = Issue(
                id=issue_id,
                title="Nested",
                status=IssueStatus.todo,
                _client=client,
            )

        def finalize(_results: tuple[object, ...], value: Issue = value) -> Issue:
            return value

        return client.issues._plan(steps=(), finalize=finalize)

    root_get = MagicMock(side_effect=lambda issue_id: get_command(root, issue_id))
    secondary_get = MagicMock(side_effect=lambda issue_id: get_command(secondary, issue_id))
    root.issues.get_command = root_get  # type: ignore[method-assign]
    secondary.issues.get_command = secondary_get  # type: ignore[method-assign]
    first = _issue(root, "first", parent_id="shared")
    second = _issue(secondary, "second", parent_id="shared")

    try:
        root.prefetch((first, second), lambda issue: issue.parent, max_parallel=2)  # type: ignore[type-var]
        first_target = first.parent.value
        second_target = second.parent.value
        assert first_target is not None
        assert second_target is not None
        assert first_target is not second_target
        assert first_target._client is root
        assert second_target._client is secondary
        assert first_target._wire_presence == second_target._wire_presence == target._wire_presence
        first_nested = first_target.parent
        second_nested = second_target.parent
        assert first_nested is not second_nested

        if shape == "omitted":
            with pytest.raises(MissingRelationContextError):
                first_nested.get()
            with pytest.raises(MissingRelationContextError):
                second_nested.get()
            assert root_get.call_count == 1
            assert secondary_get.call_count == 0
        elif shape == "null":
            assert first_nested.loaded and second_nested.loaded
            assert first_nested.value is None and second_nested.value is None
            assert root_get.call_count == 1
            assert secondary_get.call_count == 0
        else:
            first_loaded = first_nested.get()
            second_loaded = second_nested.get()
            assert first_loaded is not None
            assert second_loaded is not None
            assert first_loaded._client is root
            assert second_loaded._client is secondary
            assert first_loaded is not second_loaded
            first_nested.invalidate()
            assert first_nested.loaded is False
            assert second_nested.loaded is True
            assert [(client, issue_id) for client, issue_id in nested_target_calls] == [
                (root, "shared"),
                (root, "nested-1"),
                (secondary, "nested-1"),
            ]
    finally:
        secondary.close()
        root.close()


def test_prefetch_distinguishes_target_type_collision() -> None:
    root = MulticaClient(ClientConfig())
    issue = _issue(root, "issue-source", parent_id="same-id")
    project_source = Issue(
        id="project-source",
        title="Source",
        status=IssueStatus.todo,
        project_id="same-id",
        _client=root,
    )
    issue_target = _target(root, "Issue target")
    project_target = _target(root, "Project target")
    issue_get = MagicMock(
        return_value=root.issues._plan(steps=(), finalize=lambda _results: issue_target)
    )
    project_get = MagicMock(
        return_value=root.projects._plan(steps=(), finalize=lambda _results: project_target)
    )
    root.issues.get_command = issue_get  # type: ignore[method-assign]
    root.projects.get_command = project_get  # type: ignore[method-assign]

    try:
        root.prefetch(
            (issue, project_source), lambda value: value.parent if value is issue else value.project
        )  # type: ignore[type-var]
        assert issue_get.call_count == 1
        assert project_get.call_count == 1
        assert id(issue.parent.value) != id(project_source.project.value)
    finally:
        root.close()


def test_prefetch_retries_a_failed_singular_generation() -> None:
    root = MulticaClient(ClientConfig())
    source = _issue(root, "source")
    calls: int = 0

    def command_for(_issue_id: str) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:

            def fail(_results: tuple[object, ...]) -> Issue:
                raise RuntimeError("transient")

            return root.issues._plan(steps=(), finalize=fail)
        return root.issues._plan(steps=(), finalize=lambda _results: _target(root, "retry"))

    root.issues.get_command = MagicMock(side_effect=command_for)  # type: ignore[method-assign]
    try:
        with pytest.raises(RuntimeError, match="transient"):
            root.prefetch((source,), lambda value: value.parent)  # type: ignore[type-var]
        assert source.parent.loaded is False
        root.prefetch((source,), lambda value: value.parent)  # type: ignore[type-var]
        retry_value = source.parent.value
        assert retry_value is not None
        assert retry_value.title == "retry"
        assert calls == 2
    finally:
        root.close()


def test_prefetch_respects_max_parallel_for_distinct_singular_jobs() -> None:
    root = MulticaClient(ClientConfig())
    clients = [root, root.with_profile("one"), root.with_profile("two")]
    sources = [_issue(client, f"source-{index}") for index, client in enumerate(clients)]
    lock = threading.Lock()
    release = threading.Event()
    active = 0
    maximum = 0

    def command_for(client: MulticaClient, _issue_id: str) -> object:
        def finalize(_results: tuple[object, ...]) -> Issue:
            nonlocal active, maximum
            with lock:
                active += 1
                maximum = max(maximum, active)
                if active == 2:
                    release.set()
            assert release.wait(timeout=2)
            with lock:
                active -= 1
            return _target(client, "bounded")

        return client.issues._plan(steps=(), finalize=finalize)

    for client in clients:
        client.issues.get_command = MagicMock(  # type: ignore[method-assign]
            side_effect=lambda issue_id, client=client: command_for(client, issue_id)
        )

    try:
        root.prefetch(tuple(sources), lambda value: value.parent, max_parallel=2)  # type: ignore[type-var]
        assert maximum == 2
    finally:
        for client in reversed(clients[1:]):
            client.close()
        root.close()
