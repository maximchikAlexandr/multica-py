from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from multica_py import MissingPermalinkContextError, MulticaClient
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.resources.issues import Issue
from multica_py.resources.projects import Project


def _issue(client: MulticaClient | None = None, *, entity_id: str = "issue_123") -> Issue:
    issue = Issue(id=entity_id, title="Title", status=IssueStatus.todo)
    return issue if client is None else issue._with_client(client)


def _project(client: MulticaClient | None = None, *, entity_id: str = "project_123") -> Project:
    project = Project(id=entity_id, name="Project", status=ProjectStatus.planned)
    return project if client is None else project._with_client(client)


@pytest.mark.parametrize(
    ("app_url", "expected"),
    (
        ("https://multica.ai", "https://multica.ai"),
        ("https://multica.ai/", "https://multica.ai"),
        ("https://app.example.test/console/", "https://app.example.test/console"),
        ("http://localhost:3000/", "http://localhost:3000"),
        ("http://127.0.0.1:8080", "http://127.0.0.1:8080"),
    ),
)
def test_client_config_normalizes_independent_app_url(app_url: str, expected: str) -> None:
    config = ClientConfig(app_url=app_url, workspace_slug="team")
    assert config.app_url == expected


@pytest.mark.parametrize(
    "app_url",
    (
        "http://example.test",
        "https://user:password@example.test",
        "https://example.test/?token=secret",
        "https://example.test/#fragment",
        "example.test",
    ),
)
def test_client_config_rejects_unsafe_app_url(app_url: str) -> None:
    with pytest.raises(ValueError):
        ClientConfig(app_url=app_url)


@pytest.mark.parametrize("workspace_slug", ("", " ", "team/sub", "team\\sub"))
def test_client_config_rejects_unsafe_workspace_slug(workspace_slug: str) -> None:
    with pytest.raises(ValueError):
        ClientConfig(workspace_slug=workspace_slug)


def test_issue_permalink_uses_app_context_and_encodes_segments_without_io() -> None:
    transport = MagicMock()
    client = MulticaClient(
        ClientConfig(
            server_url="https://api.example.test/v1",
            app_url="https://app.example.test/",
            workspace_slug="team space",
        )
    )
    client._transport = transport
    issue = _issue(client, entity_id="issue/123 with space")

    assert issue.permalink() == (
        "https://app.example.test/team%20space/issues/issue%2F123%20with%20space"
    )
    transport.method_calls.clear()
    assert issue.permalink() == (
        "https://app.example.test/team%20space/issues/issue%2F123%20with%20space"
    )
    transport.assert_not_called()
    assert not hasattr(Issue, "permalink_command")


def test_project_permalink_uses_app_url_not_server_url() -> None:
    client = MulticaClient(
        ClientConfig(
            server_url="https://api.example.test/api",
            app_url="https://frontend.example.test/",
            workspace_slug="workspace",
        )
    )

    assert _project(client, entity_id="project/123").permalink() == (
        "https://frontend.example.test/workspace/projects/project%2F123"
    )
    assert not hasattr(Project, "permalink_command")


@pytest.mark.parametrize(
    ("entity", "missing"),
    (
        (_issue(MulticaClient(ClientConfig(workspace_slug="team"))), ("app_url",)),
        (
            _project(MulticaClient(ClientConfig(app_url="https://app.example.test"))),
            ("workspace_slug",),
        ),
        (_issue(), ("app_url", "workspace_slug")),
    ),
)
def test_permalink_missing_context_is_typed_and_has_no_fallback(
    entity: Issue | Project, missing: tuple[str, ...]
) -> None:
    with pytest.raises(MissingPermalinkContextError) as raised:
        entity.permalink()

    assert raised.value.missing_fields == missing
    assert "web-routing context" in str(raised.value)


def test_permalink_does_not_infer_slug_from_workspace_id() -> None:
    client = MulticaClient(
        ClientConfig(app_url="https://app.example.test", workspace_id="workspace-id")
    )

    with pytest.raises(MissingPermalinkContextError) as raised:
        _issue(client).permalink()

    assert raised.value.missing_fields == ("workspace_slug",)
