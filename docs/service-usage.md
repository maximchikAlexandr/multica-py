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

## Collect or stream a managed process

Buffered process APIs provide one immutable `ProcessResult` for the complete
stdout/stderr capture:

```python
from multica_py import ProcessResult

process = client.auth.login()
result = process.result(timeout=30)
assert isinstance(result, ProcessResult)
assert result is process.result()  # cached identity
assert process.wait() == result.exit_code
```

`result()` uses `communicate()` to collect both pipes and decodes them as strict
UTF-8. A timeout is retryable and keeps the output available; `terminate()` and
`kill()` also leave the result collectible. `close()` discards the process and
prevents late access until a new process is finalized. `ProcessOutputModeError`
identifies the current mode and requested consumer when buffered and streaming
access are mixed.

For unbounded output, select streaming by iterating the process output before
any buffered access. The context manager releases the process when iteration
ends:

```python
with client.daemon.logs() as process:
    for line in process.stdout_lines():
        consume(line)
```

Streaming is captured on the first iteration and cannot be switched to
`result()`/`wait()` afterward. `wait()` is buffered and retains stdout and stderr
in memory, so prefer streaming for large output; the two modes must not be mixed.

## Stream task-run events incrementally

A bound `TaskRun` from `Issue.runs` exposes `stream_events(*, poll_interval=1.0)`,
a synchronous iterator yielding immutable `RunEvent` objects. This is
polling-backed incremental delivery, not server push or a real-time guarantee:

```python
from multica_py import RunStatusChangedEvent, RunTextEvent

issue = client.issues.get("iss_1")
run = issue.runs.all()[0]
for event in run.stream_events(poll_interval=1.0):
    if isinstance(event, RunTextEvent):
        consume(event.text)
    elif isinstance(event, RunStatusChangedEvent):
        if event.status in {"completed", "failed", "cancelled"}:
            break
```

The iterator manages the sequence cursor, suppresses identical replayed rows,
raises `OutputShapeError` on a conflicting payload, and refreshes run status
after each batch. For `completed`/`failed` it drains incremental reads until one
quiet response and then yields the terminal status event last. For `cancelled`
(and any future status terminal only via `completed_at`) it requires two
consecutive quiet reads separated by `poll_interval`. `poll_interval` must be a
positive finite number and at most 3600.0 seconds. Prefer this iterator over
polling `TaskRun.messages` directly when you want ordered, deduplicated event
delivery with terminal-status awareness.

Web routing is configured independently when an application needs entity
links. The API server URL is never used as a frontend fallback:

```python
client = MulticaClient(
    ClientConfig(
        server_url="https://api.example.test/api",
        app_url="https://app.example.test",
        workspace_slug="team-space",
    )
)
issue = client.issues.get("issue_456")
print(issue.permalink())
```

`permalink()` is a passive local helper. It URL-encodes the workspace and ID
segments and raises `MissingPermalinkContextError` if the bound client lacks
either setting; it never discovers routing context or performs CLI/network
I/O. Use loopback HTTP only for local self-hosted deployments.

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

For a bounded command that is not represented by a higher-level resource,
use the controlled raw CLI view. It validates the argument shape before any
transport access and keeps shell metacharacters as literal arguments:

```python
raw = client.cli.command("issue", "get", "issue_123", "$(literal)")
assert raw.commands == ("multica issue get issue_123 '$(literal)'",)
result = raw.run()
print(result.stdout)
```

Raw commands do not accept shell strings, an alternate executable, or
unbounded interactive/spawn modes. The result exposes only `stdout`, `stderr`,
and `duration`, so diagnostic argv and secret values cannot leak through the
public result.

The raw boundary is path-specific. These forms are rejected locally with a
typed replacement and no transport or spawn call:

- root `login` without the bounded `--token <token>` operand (including suffixes)
  → `client.auth.login()` for the `ManagedProcess` interactive flow;
- `login --token` or an option-like operand → `client.auth.login(token)`;
- `setup cloud` → `client.setup.cloud()`;
- `setup self-host` → `client.setup.self_host(url)`;
- `daemon start` → `client.daemon.start()`;
- `daemon logs` → `client.daemon.logs()`;
- top-level `update` with any suffix → `client.maintenance.update()`.

The bounded `login --token <token>` form remains allowed with trailing
options. Unknown bounded non-interactive argv also
remains available when it passes structured-argument validation. Rejection
errors never include the token or raw argv; allowed previews and diagnostics
use the redaction marker `***`.

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
through as unrestricted upstream strings. `copy_skills=False` emits `--no-skills`.
Secret and machine-local configuration is excluded from this surface:
`custom_env`, `mcp_config`, and `runtime_config` are not accepted or emitted.

Search returns a small immutable page suitable for queue discovery:

```python
matches = client.issues.search("deploy")
for issue in matches.items:
    print(issue.id, issue.match_source)
```

The command remains `issue search <query> --output json`; the SDK adapts both
the v0.4.28 `{"issues": [...], "total": ...}` envelope and the legacy array
to `Page[Issue]`. `match_source` is an optional string and
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

## Direct inputs, options, and presence

CLI-backed methods use one explicit typed signature for eager and command
forms. The final keyword-only parameter is
`options: OperationOptions | None = None`; it scopes execution and is never
added to operation argv. `IssueListFilter` remains a reusable filter value
object for callers that assemble a list filter dynamically:

```python
from datetime import timedelta

from multica_py import OperationOptions
from multica_py.models.issues import IssueListFilter

options = OperationOptions(profile="automation", timeout=timedelta(seconds=30))
direct_page = client.issues.list(
    status="todo", limit=50, options=options
)
filter_value = IssueListFilter(status="todo", limit=50)
filtered_page = client.issues.list(filter_value, options=options)
assert direct_page.items == filtered_page.items
```

Removed one-operation input DTOs do not have an object overload. Stable IDs
remain positional and every explicit field is validated before transport.
Every `*_command()` sibling has the same parameters and returns `Command[T]`
for the eager method's exact `T`.

Use ordinary descriptions and the canonical project reference for new issue
calls. `description_file` accepts text paths without preview-time filesystem
access; `description_input` is retained only for the semantically distinct
inline, file, stdin, and explicit-no-description variants:

```python
project = client.projects.get("project_123")
issue = client.issues.create(
    title="Investigate login",
    description="Investigate the login failure",
    project=project,
)
```

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

Use explicit domain verbs for issue assignment and ordering. The root
`assign`, `unassign`, `move_to_top`, `move_to_bottom`, `move_before`, and
`move_after` methods each have a matching command form; bound `Issue` methods
forward the same operation and return a new immutable bound issue. The
advanced `reorder` method requires exactly one target.

```python
issue = client.issues.get("issue_456")
preview = issue.move_after_command("issue_457", options=options)
next_issue = preview.run()
client.issues.unassign("issue_456", options=options)
```

Project-scoped creation derives the project ID from the bound relation, so the
public method has no duplicate `project_id` parameter:

```python
project = client.projects.get("project_123")
issue = project.issues.create(
    title="Deploy", description="Deploy the reviewed release", label_ids=("release",)
)
```

Attachments use one typed source API. Paths are passed through unchanged;
bytes-like values and binary streams are materialized only by `run()` and
cleaned up on every completion path. `upload_bytes(payload, filename=...)`
is an exact compatibility alias for `upload(payload, filename=...)`.

```python
from pathlib import Path

path_command = client.attachments.upload_command(
    Path("artifact.zip"), filename="artifact.zip", task_id="task_123", options=options
)
uploaded = path_command.run()
```

## Filter and page before local selection

For a queue or polling loop, ask the server only for the relevant status and
project. Continue from the returned offset instead of repeatedly scanning the
first page:

```python
from collections.abc import Iterator

from multica_py import MulticaClient
from multica_py.models.issues import IssueListFilter
from multica_py.entities import Issue


def iter_backlog(client: MulticaClient, project_id: str) -> Iterator[Issue]:
    offset = 0
    while True:
        page = client.issues.list(
            project_id=project_id,
            status="todo",
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
`client.projects.get(project_id).issues.all()`. Both paths return partial,
bound `Issue` values, so action commands can be built directly without a
follow-up `issues.get`.
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
issues = client.projects.get("project_123").issues.all()
client.prefetch(issues, lambda issue: issue.labels, max_parallel=4)
```

`prefetch()` skips loaded relations, deduplicates repeated handles, respects
the shared process semaphore, and reports the earliest input failure.

## Use typed singular references explicitly

The singular-reference API is available for the reviewed compatibility interval
`[0.4.28, 0.4.33)`. Use the dedicated import; it is intentionally not a root
or `multica_py.models` import:

```python
from multica_py.models.relations import LazyRef
```

Exactly nine passive handles are supported:

| Property | Type | Governed service |
| --- | --- | --- |
| `Issue.parent` | `LazyRef[Issue | None]` | `issues.get` |
| `Issue.project` | `LazyRef[Project | None]` | `projects.get` |
| `Issue.assignee_ref` | `LazyRef[Agent | Squad | None]` | `agents.get` / `squads.get` |
| `Autopilot.project` | `LazyRef[Project | None]` | `projects.get` |
| `Autopilot.assignee` | `LazyRef[Agent | Squad]` | `agents.get` / `squads.get` |
| `AutopilotRun.autopilot` | `LazyRef[Autopilot]` | `autopilots.get` |
| `AutopilotRun.issue` | `LazyRef[Issue | None]` | `issues.get` |
| `TaskRun.issue` | `LazyRef[Issue]` | `issues.get` |
| `TaskRun.agent` | `LazyRef[Agent | None]` | `agents.get` |

Property access, `loaded`, `value`, and command inspection are zero-I/O. Use
`get()` or `get_command().run()` to load an unloaded target, and use
`refresh()` or `refresh_command().run()` to replace a loaded target. A loaded
optional `None` represents explicit absence: `get()` and `refresh()` return it
without I/O and their commands are no-step plans. Omitted optional fields raise
`MissingRelationContextError`; detached sources raise `DetachedEntityError`;
unsupported assignee kinds, including v0.4.28 workspace-member/email results,
raise `UnsupportedReferenceTargetError` before any transport call.

For a bounded batch, prefetch the selected handle and then read `.value`:

```python
issues = client.issues.list(limit=20).items
client.prefetch(issues, lambda issue: issue.project, max_parallel=2)
projects = tuple(issue.project.value for issue in issues if issue.project.loaded)
```

`prefetch()` skips loaded absence, coalesces equal target and complete
execution scopes, keeps different scopes separate and bounded, and publishes
independent destination-bound targets. Inspecting a property never triggers a
hidden lookup; explicit I/O remains at the operations listed above.

## Guard state transitions

Read the current entity immediately before changing status. This does not make
the remote operation transactional, but it prevents an integration from
blindly overwriting a state it did not expect:

```python
from multica_py import MulticaClient


class UnexpectedIssueStateError(RuntimeError):
    pass


def move_if_current(
    client: MulticaClient,
    issue_id: str,
    expected: str,
    target: str,
) -> None:
    issue = client.issues.get(issue_id)
    if issue.status.value != expected:
        raise UnexpectedIssueStateError(
            f"issue {issue_id} changed: expected {expected}, "
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

The pinned v0.4.28 API spelling is `autopilots.trigger`; there is no public
`autopilots.run` alias. `str(exc)`, `stderr`, and `stdout` contain redacted
detail, and diagnostics never retain the actual subprocess argv.
