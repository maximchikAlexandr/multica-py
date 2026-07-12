"""Temporal Activity example using multica-py."""

from datetime import timedelta

from multica_py import ClientConfig, MulticaClient
from multica_py.models.issues import InlineDescription, IssueCreateRequest


def create_issue_activity(title: str, description: str | None = None) -> dict:
    config = ClientConfig(timeout=timedelta(seconds=60))
    client = MulticaClient(config)
    request = (
        IssueCreateRequest(title=title)
        if description is None
        else IssueCreateRequest(
            title=title,
            description_input=InlineDescription(text=description),
        )
    )
    issue = client.issues.create(request)
    return {"id": issue.id, "title": issue.title}
