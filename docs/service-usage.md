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

## Inspect a command before running it

Eager methods remain the default. When an integration needs an audit trail or
debuggable CLI routing, use the matching `*_command()` sibling. Construction
performs no transport I/O, `commands` is a tuple of redacted shell previews,
and `run()` executes the same immutable plan:

```python
command = client.issues.get_command("issue_123")
print(command.commands)
issue = command.run()
```

Copy an agent with the inspectable command path when the operation needs an
audit preview. The eager method and command method have the same keyword-only
arguments and the same bound `Agent` result:

```python
from multica_py import Unset

copy_command = client.agents.copy_command(
    "agent-source",
    runtime_id="runtime-target",
    model=Unset,
    thinking_level=Unset,
    service_tier=Unset,
)
assert "--runtime-id runtime-target" in copy_command.commands[0]
assert "--model" in copy_command.commands[0]  # present with an empty value
copied = copy_command.run()
```

For a cross-runtime copy, an omitted model is deliberately emitted as
`--model ""` so the target runtime selects its default. Omitted
`thinking_level` and `service_tier` remain omitted, while present values pass
through as open upstream strings. `copy_skills=False` emits `--no-skills`.
Secret and machine-local configuration is excluded from this surface:
`custom_env`, `mcp_config`, and `runtime_config` are not accepted or emitted.

Search returns a small immutable page suitable for queue discovery:

```python
matches = client.issues.search("deploy")
for summary in matches.items:
    print(summary.id, summary.match_source)
```

The command remains `issue search <query> --output json`; the SDK adapts both
the v0.4.20 `{"issues": [...], "total": ...}` envelope and the legacy array
to `Page[IssueSummary]`. `match_source` is an optional open string and
can be absent or a future upstream value.

Composite operations expose their ordered steps and result references. For
example, creating labels with an issue shows the create step, one label-add
step per label, and the final get step; the add and get steps refer to the
created object as `${create.id}`:

```python
command = client.issues.create_command(
    title="Deploy",
    label_ids=("release", "queued"),
)
assert any("${create.id}" in rendered for rendered in command.commands)
issue = command.run()
```

## Direct keywords, typed objects, and presence

Governed resource methods accept either a frozen request/filter object or its
explicit keyword-only fields. The forms share one resolver and one command
plan; passing both raises `TypeError("Pass either a request object or keyword
arguments, not both.")`, and required operations preserve their exact missing
input error. Optional filters and all-optional updates may omit every field.

Use direct keywords first when the call is local and readable, or retain a
typed object when values are reused or assembled by another layer:

```python
from multica_py import IssueStatus
from multica_py.models.issues import IssueListFilter

direct_page = client.issues.list(status=IssueStatus.backlog, limit=50)
request = IssueListFilter(status=IssueStatus.backlog, limit=50)
typed_page = client.issues.list(request)
assert direct_page.items == typed_page.items
```

The same dual form is available for create/update requests, issue/comment
filters, metadata query/set, autopilot trigger add/update, and autopilot/label
updates. Stable IDs remain positional; request fields are keyword-only. Every
`*_command()` sibling has the same parameters and returns `Command[T]` for the
eager method's exact `T`.

Update presence is explicit: `Unset` omits a field, approved nullable `None`
values clear it, and accepted empty strings, empty tuples, `False`, and `0`
are sent as values. All-optional update models use a read-only no-op plan when
all mutable fields are `Unset`. Project-resource `local_path` and runtime
`target_version` are required-value updates; omitted or `None` fails before
transport and never becomes a no-op read.

Actions return `ActionResult[T]` with payloads in `.value`; void actions use
`ActionResult[None]`. Scalar/entity/process operations retain their natural
typed result, and transport/decode/validation failures remain exceptions.

```python
mutation = client.repositories.add("https://example.com/team/repo.git")
if mutation.success:
    for record in mutation.value.added:
        print(record.url)
```

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
            project_id=project_id,
            status=IssueStatus.backlog,
            limit=100,
            offset=offset,
        )
        yield from page.items
        if not page.has_more:
            return
        if not page.items:
            raise RuntimeError("issue pagination stopped making progress")
        offset += len(page.items)
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
issue = client.issues.get("issue_456")
payload = issue.to_json()
```

`to_json()` is passive and excludes the client, lazy caches, locks, and loader
closures. It is the correct boundary for persistence and messages. The
round-trip is `from_json(payload)` (returns a detached instance) plus
`detach()` if mutability must remain sealed.

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

## Handle typed upstream failures

Conflict and validation exceptions retain actionable, redacted upstream
detail. A runtime with dependent active agents refuses a non-cascade delete;
use the cascade form only when unbinding those agents and cancelling their
active work is intended. Their configuration, chats, and task history remain
preserved:

```python
from multica_py.exceptions import ConflictError, ValidationError

try:
    client.runtimes.delete("runtime-1")
except ConflictError as exc:
    print(f"delete refused ({exc.exit_code}): {exc}")
    client.runtimes.delete("runtime-1", cascade=True)
except ValidationError as exc:
    print(f"upstream input rejected ({exc.exit_code}): {exc}")
```

The pinned v0.4.20 API spelling is `autopilots.trigger`; there is no public
`autopilots.run` alias. `str(exc)`, `stderr`, and `stdout` contain redacted
detail, and diagnostics never retain the actual subprocess argv.
