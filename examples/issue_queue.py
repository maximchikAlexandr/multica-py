"""Page a server-filtered backlog and select a stable highest-priority issue."""

from collections.abc import Iterator

from multica_py import ClientConfig, Issue, IssueStatus, MulticaClient
from multica_py.models.issues import IssueListFilter

_PRIORITY_RANK = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


def iter_backlog(client: MulticaClient, project_id: str) -> Iterator[Issue]:
    offset = 0
    while True:
        page = client.issues.list(
            IssueListFilter(
                project_id=project_id,
                status=IssueStatus.backlog,
                limit=100,
                offset=offset,
            )
        )
        yield from page.issues
        if not page.has_more:
            return
        if not page.issues:
            raise RuntimeError("issue pagination stopped making progress")
        offset += len(page.issues)


def select_queue_head(client: MulticaClient, project_id: str) -> Issue | None:
    candidates = tuple(
        issue for issue in iter_backlog(client, project_id) if issue.parent_id is None
    )
    if not candidates:
        return None

    def queue_key(issue: Issue) -> tuple[int, str]:
        return (
            _PRIORITY_RANK.get(issue.priority or "", len(_PRIORITY_RANK)),
            issue.id,
        )

    return min(candidates, key=queue_key)


if __name__ == "__main__":
    selected = select_queue_head(MulticaClient(ClientConfig()), "project_123")
    if selected is not None:
        print(selected.id, selected.title)
