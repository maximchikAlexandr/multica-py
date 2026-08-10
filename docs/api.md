# API Reference

Migration details and removed/renamed surfaces are documented in
[docs/migration.md](migration.md). A complete bound-graph example is in
[examples/resource_relations.py](../examples/resource_relations.py).

## Client

- `MulticaClient(config: ClientConfig | None = None)` — construct with immutable configuration; `None` uses `ClientConfig()`
- `MulticaClient.with_options(...)` — derive an isolated client view with keyword-scoped execution settings
- `MulticaClient.with_profile(profile)` — clone with a different profile
- `MulticaClient.with_workspace(workspace_id)` — clone with a different workspace
- `MulticaClient.with_timeout(timeout)` — clone with a different default timeout
- `MulticaClient.with_cwd(cwd)` — clone with a different working directory
- `MulticaClient.with_environment(environment)` — clone with a replacement environment
- `ClientConfig` — frozen `msgspec.Struct`: `executable`, `server_url`, independent `app_url` and `workspace_slug`, `workspace_id`, `profile`, `cwd`, `environment` (immutable tuple), `timeout`, `compatibility` (CompatibilityPolicy enum), `debug`, `encoding`, `max_processes`

## Inspectable command plans

Every CLI-executing resource method also has a typed `*_command()` sibling.
It returns the public `Command[T]` type, where `T` is the same result type as
the eager method. `Command[T].commands` is always a tuple: it is empty for a
cache-hit no-op, has one item for a single CLI call, and contains ordered
commands or reference templates for a composite operation. Preview performs no
I/O. Calling `run()` executes that same immutable plan and returns `T`.

The preview is shell-rendered and redacted for display; execution still passes
the original argv values to the transport. Composite plans expose dependencies
such as `${create.id}` in their ordered command templates. The eager API remains
the default when inspection is not needed.

## Raw CLI commands

`client.cli.command(*argv, options=None)` builds a bounded
`Command[CliResult]` for a controlled raw CLI invocation. The first argument
must be a non-blank command name and must not repeat the configured executable;
all arguments must be strings without NUL bytes. Later empty values are valid.
Construction validates locally and performs no I/O. Preview renders quoted
arguments, while execution passes the original argument tuple to the
transport. `CliResult` contains only redaction-safe `stdout`, `stderr`, and
`duration`; it does not expose argv or secret values.

```python
from multica_py.resources.cli import CliResult

command = client.cli.command("issue", "get", "issue_123", "$(literal)")
assert command.commands == ("multica issue get issue_123 '$(literal)'",)
result: CliResult = command.run()
```

## Entity permalinks

Configure web routing independently from CLI/API execution:

```python
client = MulticaClient(
    ClientConfig(
        server_url="https://api.example.test/api",
        app_url="https://app.example.test",
        workspace_slug="team-space",
    )
)
issue = client.issues.get("issue_123")
assert issue.permalink() == "https://app.example.test/team-space/issues/issue_123"
```

`Issue.permalink()` and `Project.permalink()` are local-only helpers. They
URL-encode workspace and entity ID segments, perform no I/O, and require both
`app_url` and `workspace_slug` on the bound entity's originating client.
Missing context raises `MissingPermalinkContextError`; neither helper has a
command sibling. `app_url` accepts HTTPS (or loopback HTTP for self-hosting),
while `workspace_slug` must be one nonblank path segment.

## SDK-wide operation conventions

CLI-backed methods use explicit typed parameters. The final parameter on every
eager/`*_command()` pair is the keyword-only
`options: OperationOptions | None = None`; it changes the effective execution
configuration, never the operation-specific argv. Use a frozen
`OperationOptions` per operation, or use keyword settings with
`client.with_options(...)` when a group of calls shares a scope:

```python
from datetime import timedelta

from multica_py import IssueStatus, MulticaClient, OperationOptions
from multica_py.models.issues import IssueListFilter

client = MulticaClient()
options = OperationOptions(profile="automation", timeout=timedelta(seconds=30))
direct = client.issues.list(status=IssueStatus.backlog, limit=50, options=options)
scoped = client.with_options(profile="automation", timeout=timedelta(seconds=30))
page = scoped.issues.list(status=IssueStatus.backlog, limit=50)
```

`with_environment(environment)` replaces the complete environment tuple; it
does not merge with the originating client. Pass `environment=()` to clear all
environment entries on the derived client.

`IssueListFilter` is the one retained reusable filter value object. It can be
passed to `issues.list()` when a filter is assembled or reused; its fields are
the same typed fields exposed by the direct form. Removed one-operation DTOs
have no object overload. Stable target IDs remain positional, direct
operation fields are explicit, and invalid values are rejected before
transport access.

Direct updates use `Unset` to mean omission. The all-optional updates use a
read-only get plan when every mutable field is `Unset`. `None` means an approved nullable
clear, while `""`, `()`, `False`, and `0` remain explicit values when their
field accepts them. All-optional updates delegate an all-omitted call to the
matching read command; required-value updates reject omission/`None` before
transport and never create a no-op read.
Required-value project-resource and runtime updates reject omitted/`None`
required fields before I/O and never create a no-op read.

Result categories are closed: entity/state methods return typed entities,
canonical and direct-resource collections return immutable `Page[T]` (or a
documented compatible subtype), actions return `ActionResult[T]`, and process
operations return `ManagedProcess`. `ActionResult.value` carries payloads;
void actions use `ActionResult[None]`. Transport, validation, exit-code, and
decode failures remain typed exceptions rather than unsuccessful wrappers.
`Page.items` is the immutable tuple payload and pages support iteration,
`len(page)`, and indexing without I/O. Bound relation `.all()` snapshots are
the deliberate exception and remain tuples.

## Resources

All resources accessed as attributes of `MulticaClient`:

- **auth**: `status()` → `AuthenticationStatus`, token `login(token)` → `ActionResult[str]`, interactive `login()` → `ManagedProcess`, `logout()` → `AuthenticationStatus`
- **setup**: `cloud()`, `self_host(url)` → both return `ManagedProcess`
- **daemon**: `start/logs()` → `ManagedProcess`, `status/stop/restart()` → `DaemonStatus`, `disk_usage()` → `Page[DaemonDiskUsageEntry]`
- **workspaces**: `list/members` → `Page[T]`, `get()` → object, `watch/unwatch` → `ActionResult[None]`
- **issues**: full CRUD + `comments`, `recent_comment_threads`, `labels`, `subscribers`, `metadata`, `pull_requests`, `children`, `runs`, `run_messages`, `usage`, `rerun(issue_id)`, `cancel_task(task_id)`, `assign`, `unassign`, `move_to_top`, `move_to_bottom`, `move_before`, and `move_after`; root create accepts optional `project_id`, while project-scoped create supplies it from the bound project
- **issues.comments**: `list` for flat comments, `list_flat`, `list_thread`, `list_recent`, `add`, `reply`, `delete`, `resolve`, `unresolve`
- **issues.metadata**: `list`, `query`, `get`, `set`, `set_typed`, `delete`
- **issues.subscribers**: `list/add/remove`
- **issues.labels**: `list/add/remove`
- **projects**: `list/get/create/update/delete/set_status`
- **projects.resources**: `list`, `add_local_directory`, `update_local_directory`, `remove`
- **labels**: `list/get/create/update/delete`
- **agents**: `list/get/create/update/copy/copy_command/archive/restore/tasks/avatar`
- **agents.skills**: `list/set`
- **skills**: `list/get/create/update/delete/import_from_url`
- **skills.files**: `list/upsert/delete`
- **autopilots**: `list/get/create/update/delete/trigger/history/trigger_add/trigger_update/trigger_delete`
- **repositories**: `list/add/remove/checkout`
- **runtimes**: `list/usage/activity/update/rename/delete`; `delete(..., cascade=True)`
  unbinds dependent agents, cancels their queued/running work, and deletes the
  runtime while preserving agent configuration, chats, and task history. Without
  cascade, an upstream dependent-agent conflict is raised instead.
- **attachments**: unified `upload`/`upload_command` for paths, bytes-like values, and binary streams, compatibility `upload_bytes` aliases, and `download`/`download_bytes` (no `list`)
- **cli**: `command(*argv, options=None)` → `Command[CliResult]` for bounded raw invocations
- **configuration**: `show/get/set`
- **squads**: `list/get`
- **users**: `profile_get/profile_update`
- **maintenance**: `version()` → `MaintenanceVersion`, `update()` → `ManagedProcess`

## Agent copy and issue search

`agents.copy` eagerly returns a bound `Agent`; `agents.copy_command` returns the
same result lazily as `Command[Agent]`. Both use the same presence-aware,
keyword-only override surface (omitted values use `Unset`):

```python
agent = client.agents.copy(
    source_agent_id,
    name=Unset,
    runtime_id=Unset,
    description=Unset,
    instructions=Unset,
    model=Unset,
    thinking_level=Unset,
    service_tier=Unset,
    custom_args=Unset,
    max_concurrent_tasks=Unset,
    permission_mode=Unset,
    public_to_workspace=Unset,
    public_to_member_ids=Unset,
    copy_skills=True,
)
preview = client.agents.copy_command(source_agent_id, runtime_id="runtime-2")
# The executed argv contains: --runtime-id runtime-2 --model "" --output json.
agent = preview.run()
```

`copy()` is exactly the eager form of `copy_command().run()`. When
`runtime_id` is present and `model` is omitted, the SDK emits `--model ""` so
the target runtime selects its default model. This is the only automatic
runtime-specific default: omitted `thinking_level` and `service_tier` flags
stay absent. Present model, thinking-level, and service-tier strings are sent
verbatim. Secret or machine-local settings are intentionally not part of this
API: `custom_env`, `mcp_config`, and `runtime_config` are neither accepted nor
emitted; skills can be omitted only with `copy_skills=False`.

`issues.search(query)` returns a `Page[Issue]`; `search_command(query)`
returns `Command[Page[Issue]]`. The exact invocation is
`issue search <query> --output json`. Results accept the v0.4.20 envelope or
the legacy top-level array; iterate the page or use `.items`, and each issue may expose the open optional
string `match_source` (`"title"`, `"description"`, `"comment"`, or a future
upstream value). It defaults to `None` when omitted; the envelope's `total`
is preserved as page metadata.

## Exceptions

- `MulticaError` — base
- `ExecutableNotFoundError`, `ExecutableNotRunnableError` — executable
- `UnsupportedCliVersionError` — version check
- `CommandTimeoutError`, `CommandCancelledError` — lifecycle
- `CommandExecutionError` (+ subclasses: `AuthenticationError`, `AuthorizationError`, `NotFoundError`, `ConflictError`, `ValidationError`, `NetworkError`, `UnknownCommandError`)
- `ProtocolError` (+ `JsonOutputError`, `OutputShapeError`, `EncodingError`)

`ConflictError` and `ValidationError` preserve actionable upstream detail in
`str(exc)` and the redacted `stderr`/`stdout` attributes. Conflict failures
retain the actual CLI exit code; v0.4.20 semantic validation failures use exit
code `5` (including raw HTTP 400/422 mappings). Diagnostics contain redacted
argv only, never secrets or the actual subprocess argv:

```python
from multica_py.exceptions import ConflictError, ValidationError

try:
    client.runtimes.delete("runtime-1")
except ConflictError as exc:
    print(exc.exit_code, str(exc))  # use --cascade after reviewing the detail
except ValidationError as exc:
    print(exc.exit_code, str(exc))  # fix the reported upstream input
```

## Shared Models

- `_BoundEntity` (private mixin in `multica_py.models._bound`) — frozen
  `msgspec.Struct(kw_only=True)` base that backs every unified domain class.
  Carries the `_client` field, `_require_client`, `detach`,
  `__eq__`/`__hash__`/`__repr__` over `_PUBLIC_FIELDS`, and `to_dict()` /
  `from_dict()` / `to_json()` / `from_json()`. Not exported; treat as
  implementation detail.
- Unified domain classes (`Issue`, `Project`, `Agent`, `Skill`, `Squad`,
  `Workspace`, `WorkspaceMember`, `Autopilot`, `AutopilotRun`, `Comment`,
  `CommentThread`, `TaskRun`, `Label`) — single immutable bound class per
  resource; replaces the prior `*Entity` + `*Data` pair. See
  [docs/migration.md](migration.md) for the rename table.
- `multica_py.models.relations.LazyCollection[T]` — cached one-call collection
- `multica_py.models.relations.OffsetLazyCollection[T]` — offset-paged collection with `page()` and bounded traversal
- `multica_py.models.relations.CursorLazyCollection[T]` — cursor-paged collection with progress guards
- `multica_py.models.relations.LazyMapping[K, V]` — cached mapping relation
- `Page[T]` — frozen generic page with immutable `.items`, metadata, iteration,
  length, and read-only indexing for non-relation paged services
- `ActionResult[T]` — frozen typed `success`, `value`, and optional redacted
  `message` container for approved action results
- `multica_py.models.issues.IssueListPage` and `IssueChildrenResult`, plus
  `multica_py.models.autopilots.AutopilotListPage` and `AutopilotRunListPage` —
  compatibility page subclasses
- `multica_py.models.common.CommentCursor` and
  `multica_py.models.issue_activity.MetadataPage` — cursor/metadata types
- `multica_py.models.project_resources.ProjectResourceRecord` and
  `LocalDirectoryResourceRef` — typed project-resource models
- `multica_py.models.issue_activity.IssueUsage.cost_usd` — optional float decoded from `issue usage` JSON
- `multica_py.types.JsonValue` — closed recursive JSON union. Object nodes are immutable
  `Mapping[str, JsonValue]` snapshots and arrays are tuples; use
  `AutopilotRun.to_dict()` / `to_json()` to materialize standard JSON
  containers for serializers.

## Bound entities and load points

Workspace, project, issue, agent, skill, squad, member, label, comment,
comment-thread, task-run, autopilot, and autopilot-run results are unified
domain classes. Scalar properties are passive. Relation property access is
also passive; `all()`, `page()`, iteration, `refresh()`, and
`MulticaClient.prefetch()` may invoke the CLI.

Each wrapper owns its cache. A later `get()` returns a new wrapper rather than
mutating an earlier list result. `to_json()` / `to_dict()` exclude client,
cache, and loader state. `from_json()` / `from_dict()` construct a detached
instance with `_client=None`. Detached entities raise `DetachedEntityError`
before transport access.

The complete relation inventory and removed surfaces are documented in
[docs/migration.md](migration.md).
