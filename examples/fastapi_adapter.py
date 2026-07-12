"""FastAPI service example using multica-py."""

from datetime import timedelta

from multica_py import ClientConfig, MulticaClient
from multica_py.enums import IssueStatus
from multica_py.models.issues import (
    InlineDescription,
    IssueCreateRequest,
    IssueListFilter,
)

config = ClientConfig(
    server_url="https://my-multica.example.com",
    workspace_id="ws_main",
    timeout=timedelta(seconds=30),
)
client = MulticaClient(config)


def get_open_issues():
    filter = IssueListFilter(status=IssueStatus.in_progress)
    return client.issues.list(filter)


def create_bug_issue(title: str, description: str):
    request = IssueCreateRequest(
        title=title,
        description_input=InlineDescription(text=description),
        label=("bug",),
    )
    return client.issues.create(request)
