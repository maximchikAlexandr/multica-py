# Service usage patterns

These patterns target long-running workers, web-service adapters, schedulers,
and maintenance scripts. The examples use only the public SDK and keep
framework-specific lifecycle code outside the library boundary.

## Construct one production client

Create the client in a composition root, select a named CLI profile, enable
strict compatibility checks, and bound subprocess concurrency:

```python
from datetime import timedelta

from multica_py import ClientConfig, CompatibilityPolicy, MulticaClient

client = MulticaClient(
    ClientConfig(
        server_url="https://multica.example.com",
        profile="automation",
        compatibility=CompatibilityPolicy.strict,
        timeout=timedelta(seconds=30),
        max_processes=4,
    )
)
```

Application code should depend on a narrow adapter that owns this client.
This keeps SDK exceptions, retry policy, and CLI compatibility checks at one
boundary. Do not construct a new client for every operation.

Use a derived view when a unit of work is scoped to a workspace:

```python
workspace_client = client.with_workspace("ws_123")
issue = workspace_client.issues.get("issue_456")
```

Derived views keep independent immutable configuration and share the original
process semaphore. Closing one view does not close another.

## Direct keyword vs request object

Most methods accept input either as a request object or as direct keyword arguments. The two styles are mutually exclusive — passing both raises `TypeError("Pass either a request object or keyword arguments, not both.")`. Passing neither raises `TypeError("Pass a ... or its keyword arguments; got neither.")`.

Direct keyword form is available for: `projects.create`, `projects.update`, `agents.create`, `agents.update`, `skills.create`, `skills.update`, `issues.create`, `issues.update`, `issues.assign`, `issues.reorder`, `runtimes.update`, `project_resources.add_local_directory`, `project_resources.update_local_directory`, `users.profile_update`.

For these methods, request objects remain valuable when you need to reuse a parameter set, validate input early, store pending input, or assemble arguments across layers. The request-object form is the only option for: `issue_comments.list_flat`, `issue_comments.list_thread`, `issue_comments.list_recent`, `issue_metadata.query`, `issue_metadata.set_typed`.

## Filter and page before local selection

For a queue or polling loop, ask the server only for the relevant status and
project. Continue from the returned offset instead of repeatedly scanning the
first page:

```python
from collections.abc import Iterator

from multica_py import IssueStatus, MulticaClient
from multica_py.models.issues import IssueListFilter, IssueSummary


def iter_backlog(client: MulticaClient, project_id: str) -> Iterator[IssueSummary]:
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
```

Use the project relation when all project summaries are genuinely needed:
`client.projects.get(project_id).issues.all()`. Both paths return
`IssueSummary`; call `client.issues.get(summary.id)` only for a full issue.
Prefer the filtered direct service for a status-specific queue.

## Use bound relations at graph boundaries

```python
issue = client.issues.get("issue_456")

labels = issue.labels        # no I/O
metadata = issue.metadata    # no I/O

if not labels.loaded:
    labels.all()
metadata_values = metadata.all()
```

Repeated reads use the wrapper-local cache. Successful entity mutation helpers
invalidate only the affected relation. Call `refresh()` when the application
requires a current read from the server.

For a batch of entities with the same client origin:

```python
summaries = client.projects.get("project_123").issues.all()
issues = tuple(client.issues.get(summary.id) for summary in summaries)
client.prefetch(issues, lambda issue: issue.labels, max_parallel=4)
```

`prefetch()` skips loaded relations, deduplicates repeated handles, respects
the shared process semaphore, and reports the earliest input failure.

## Guard state transitions

Read the current entity immediately before changing status. This does not make
the remote operation transactional, but it prevents an integration from
blindly overwriting a state it did not expect:

```python
from multica_py import IssueStatus, MulticaClient


class UnexpectedIssueStateError(RuntimeError):
    pass


def move_if_current(
    client: MulticaClient,
    issue_id: str,
    expected: IssueStatus,
    target: IssueStatus,
) -> None:
    issue = client.issues.get(issue_id)
    if issue.status is not expected:
        raise UnexpectedIssueStateError(
            f"issue {issue_id} changed: expected {expected.value}, "
            f"got {issue.status.value}"
        )
    client.issues.set_status(issue_id, target)
```

If multiple writers need a true compare-and-set guarantee, enforce it at the
owning service boundary; a client-side reread alone cannot close a race.

## Make retried work idempotent

Persist an external operation key in metadata and use a stable comment marker.
On retry, inspect the bound relations before writing:

```python
operation_key = "deployment:2026-08-02:42"
issue = client.issues.get("issue_456")

if issue.metadata.all().get("automation.operation") != operation_key:
    issue.set_metadata("automation.operation", operation_key)

marker = f"[automation:{operation_key}]"
if not any(comment.body.startswith(marker) for comment in issue.comments.all()):
    issue.add_comment(f"{marker} deployment completed")
```

This is application-level idempotency: choose a key namespace owned by your
integration and define how conflicting values are handled.

## Serialize snapshots, not bound runtime state

```python
import msgspec

issue = client.issues.get("issue_456")
payload = msgspec.json.encode(issue.to_data())
```

`to_data()` is passive and excludes the client, lazy caches, locks, and loader
closures. It is the correct boundary for persistence and messages.

## Local self-hosted setup

Loopback HTTP is accepted for local development:

```python
from multica_py import ClientConfig, MulticaClient

client = MulticaClient(
    ClientConfig(
        executable="/usr/local/bin/multica",
        server_url="http://localhost:8080",
        profile="self-hosted",
    )
)
```

Interactive first-time setup remains process-backed:

```python
process = client.setup.self_host("http://localhost:8080")
process.wait()
```

See the complete runnable examples under [examples/](../examples/).
