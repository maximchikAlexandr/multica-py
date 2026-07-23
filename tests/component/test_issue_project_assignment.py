from __future__ import annotations

import pytest

from multica_py.models.issues import IssueCreateRequest, IssueUpdateRequest


def test_issue_create_rejects_empty_project_id() -> None:
    with pytest.raises(ValueError, match="project_id must be non-empty"):
        IssueCreateRequest(title="New issue", project_id="")


def test_issue_update_rejects_empty_project_id() -> None:
    with pytest.raises(ValueError, match="project_id must be non-empty"):
        IssueUpdateRequest(project_id="")
