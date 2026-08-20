from __future__ import annotations

from typing import cast
from unittest.mock import MagicMock

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.entities.issues import Issue
from multica_py.enums import IssueStatus
from multica_py.models.relations import LazyRef


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
