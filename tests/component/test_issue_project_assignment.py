from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.models.issue_activity import IssueUsage
from multica_py.models.issues import IssueCreateRequest, IssueUpdateRequest

from .conftest import configure_mock_transport, patch_client_transport
from .resource_support import CommandCase

ISSUE_PROJECT_CASES: tuple[CommandCase, ...] = (
    CommandCase(
        id="issues.create.omit-project",
        invoke=lambda c: c.issues.create(IssueCreateRequest(title="New issue")),
        expected_argv=("issue", "create", "--title", "New issue", "--output", "json"),
        stdout='{"id":"iss_001","title":"New issue","status":"todo"}',
        sdk_method="issues.create",
        check="not_none",
    ),
    CommandCase(
        id="issues.create.with-project",
        invoke=lambda c: c.issues.create(
            IssueCreateRequest(title="New issue", project_id="pr_001")
        ),
        expected_argv=(
            "issue",
            "create",
            "--title",
            "New issue",
            "--project",
            "pr_001",
            "--output",
            "json",
        ),
        stdout='{"id":"iss_001","title":"New issue","status":"todo"}',
        sdk_method="issues.create",
        check="not_none",
    ),
    CommandCase(
        id="issues.update.omit-project",
        invoke=lambda c: c.issues.update("iss_001", IssueUpdateRequest(title="Updated")),
        expected_argv=("issue", "update", "iss_001", "--title", "Updated", "--output", "json"),
        stdout='{"id":"iss_001","title":"Updated","status":"todo"}',
        sdk_method="issues.update",
        check="not_none",
    ),
    CommandCase(
        id="issues.update.with-project",
        invoke=lambda c: c.issues.update("iss_001", IssueUpdateRequest(project_id="pr_001")),
        expected_argv=("issue", "update", "iss_001", "--project", "pr_001", "--output", "json"),
        stdout='{"id":"iss_001","title":"Updated","status":"todo"}',
        sdk_method="issues.update",
        check="not_none",
    ),
    CommandCase(
        id="issues.usage.cost-usd-present",
        invoke=lambda c: c.issues.usage("iss_001"),
        expected_argv=("issue", "usage", "iss_001", "--output", "json"),
        stdout='{"total_runs":1,"cost_usd":0.05}',
        sdk_method="issues.usage",
        check="not_none",
    ),
    CommandCase(
        id="issues.usage.cost-usd-omitted",
        invoke=lambda c: c.issues.usage("iss_001"),
        expected_argv=("issue", "usage", "iss_001", "--output", "json"),
        stdout='{"total_runs":1}',
        sdk_method="issues.usage",
        check="not_none",
    ),
)


@pytest.mark.parametrize("case", ISSUE_PROJECT_CASES, ids=lambda item: item.id)
def test_issue_project_assignment(case: CommandCase, fake_cli_client: MulticaClient) -> None:
    mock = MagicMock(spec=CliTransport)
    configure_mock_transport(case, mock)
    patch_client_transport(fake_cli_client, mock)
    result = case.invoke(fake_cli_client)
    transport = mock.run_bytes if mock.run_bytes.called else mock.run_text
    assert transport.call_args.args[0] == case.expected_argv
    if case.id == "issues.usage.cost-usd-present":
        assert isinstance(result, IssueUsage)
        assert result.cost_usd == 0.05
    if case.id == "issues.usage.cost-usd-omitted":
        assert isinstance(result, IssueUsage)
        assert result.cost_usd is None


def test_issue_create_rejects_empty_project_id() -> None:
    with pytest.raises(ValueError, match="project_id must be non-empty"):
        IssueCreateRequest(title="New issue", project_id="")


def test_issue_update_rejects_empty_project_id() -> None:
    with pytest.raises(ValueError, match="project_id must be non-empty"):
        IssueUpdateRequest(project_id="")
