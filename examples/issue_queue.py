"""Page a server-filtered queue and select a bound Issue without N+1 reads."""

from collections.abc import Iterator

from multica_py import ClientConfig, Issue, MulticaClient
from multica_py.models.issues import IssueMetadataItem

_PRIORITY_RANK = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


def iter_queue(client: MulticaClient, project_id: str, external_key: str) -> Iterator[Issue]:
    offset = 0
    while True:
        page = client.issues.list(
            project_id=project_id,
            status="todo",
            limit=100,
            offset=offset,
            metadata=(IssueMetadataItem(key="external_key", value=external_key),),
        )
        yield from page.items
        if not page.has_more:
            return
        if not page.items:
            raise RuntimeError("issue pagination stopped making progress")
        offset += len(page.items)


def select_queue_head(client: MulticaClient, project_id: str, external_key: str) -> Issue | None:
    def queue_key(issue: Issue) -> tuple[int, str]:
        return (
            _PRIORITY_RANK.get(issue.priority or "", len(_PRIORITY_RANK)),
            issue.id,
        )

    return min(
        (
            issue
            for issue in iter_queue(client, project_id, external_key)
            if issue.parent_id is None
            and "queue" in issue.label_names
            and {item.key: item.value for item in issue.metadata_snapshot}.get("external_key")
            == external_key
        ),
        key=queue_key,
        default=None,
    )


if __name__ == "__main__":
    selected = select_queue_head(MulticaClient(ClientConfig()), "project_id", "external-key")
    if selected is not None:
        print(selected.id, selected.title)
