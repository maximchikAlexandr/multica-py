# Alpha migration guide

The relation graph is a deliberate 0.x API boundary. Resource results are
bound wrappers; scalar data is available through `to_json()` / `to_dict()`,
and relations load only at explicit load points such as `all()`, `page()`,
`refresh()`, or `MulticaClient.prefetch()`.

## Execution backends

Local subprocess execution remains the default. Remote execution is explicit:
install the chosen optional extra, import its executor from
`multica_py.execution.<provider>`, and pass it to `MulticaClient(executor=...)`.
There is no plugin registry or automatic provider discovery. See
[execution backends](execution-backends.md) for installation commands,
target-path/environment/staging rules, process-control guarantees, and the
provider-adapter contract.

## Breaking alpha migration table

This release intentionally removes one-operation input containers and public
summary rows. The **After** snippets below are the compiling public forms;
stable reusable filters and semantic values remain where they carry domain
meaning. The removed names are retained only in this historical **Before**
column so a migration can be completed mechanically.

### Removed one-operation DTOs: direct typed calls

| Removed **Before** | Compiling **After** |
|---|---|
| `AgentCreateRequest(name="build")` | `client.agents.create(name="build")` |
| `AgentUpdateRequest(name="build")` | `client.agents.update(agent_id, name="build")` |
| `ProjectCreateRequest(name="alpha")` | `client.projects.create(name="alpha")` |
| `ProjectUpdateRequest(name="alpha")` | `client.projects.update(project_id, name="alpha")` |
| `SkillCreateRequest(name="lint")` | `client.skills.create(name="lint")` |
| `SkillUpdateRequest(name="lint")` | `client.skills.update(skill_id, name="lint")` |
| `LabelUpdateRequest(name="ready")` | `client.labels.update(label_id, name="ready")` |
| `IssueCreateRequest(title="Deploy")` | `client.issues.create(title="Deploy")` |
| `IssueUpdateRequest(description="Ready")` | `client.issues.update(issue_id, description="Ready")` |
| `IssueAssignmentRequest(issue_id=issue_id, member_id=member_id)` | `client.issues.assign(issue_id, member_id)` |
| `IssueAssignmentRequest(issue_id=issue_id, agent_id=agent_id)` | `client.issues.assign(issue_id, agent_id)` |
| `IssueReorderRequest(issue_id=issue_id, before_id=target_id)` | `client.issues.reorder(issue_id, before_id=target_id)` |
| `CommentListFlatRequest(issue_id=issue_id, since=since)` | `client.issues.comments.list_flat(issue_id=issue_id, since=since)` |
| `CommentListRecentRequest(issue_id=issue_id, limit=20)` | `client.issues.comments.list_recent(issue_id=issue_id, limit=20)` |
| `CommentListThreadRequest(issue_id=issue_id, thread_id=thread_id, cursor=cursor, limit=50)` | `client.issues.comments.list_thread(issue_id=issue_id, thread_id=thread_id, cursor=cursor, limit=50)` |
| `MetadataListRequest(issue_id=issue_id, predicates=predicates, cursor=cursor, limit=limit)` | `client.issues.metadata.query(issue_id=issue_id, predicates=predicates, cursor=cursor, limit=limit)` |
| `MetadataSetRequest(issue_id=issue_id, key="build.id", value="42")` | `issue.set_metadata("build.id", "42")` |
| `ProjectResourceAddLocalDirectoryRequest(local_path=path, daemon_id=daemon_id)` | `project.add_local_directory(local_path=path, daemon_id=daemon_id)` |
| `ProjectResourceUpdateLocalDirectoryRequest(local_path=path)` | `client.projects.resources.update_local_directory(project_id, resource_id, local_path=path)` |
| `AutopilotUpdateRequest(title="Nightly")` | `client.autopilots.update(autopilot_id, title="Nightly")` |
| `AutopilotTriggerCreate(title="Daily", kind="schedule")` | `client.autopilots.trigger_add(autopilot_id, title="Daily", kind="schedule")` |
| `AutopilotTriggerUpdate(kind="schedule")` | `client.autopilots.trigger_update(autopilot_id, trigger_id, kind="schedule")` |
| `RuntimeUpdate(target_version="stable")` | `client.runtimes.update(runtime_id, target_version="stable")` |
| `UserProfileUpdate(description="On call")` | `client.users.profile_update(description="On call")` |

Each `After` call also has a matching `*_command()` form with the same
explicit inputs and a final keyword-only `options: OperationOptions | None`.
`Unset` omits a field, approved nullable `None` clears it, and validation runs
before transport access.

### Read paths, domain verbs, uploads, and execution options

| Former surface | Compiling **After** |
|---|---|
| `IssueSummary` rows from list/search/relations | `for issue in client.issues.list().items: issue.set_status_command("todo")` |
| `Page[IssueSummary]` or tuple relation rows | `Page[Issue]`; `project.issues.all()` returns bound `Issue` values |
| `issues.assign(issue_id, to_id=...)` mode flags | `issues.assign(issue_id, member_id)` or `issues.unassign(issue_id)` |
| `issues.reorder(issue_id, top=True, bottom=True, before_id=..., after_id=...)` | `issues.move_to_top(issue_id)`, `move_to_bottom`, `move_before(issue_id, target_id)`, or `move_after(issue_id, target_id)`; advanced `reorder` accepts exactly one target |
| `attachments.upload_bytes(filename, payload)` as the primary API | `attachments.upload(payload, filename=filename)`; `upload_bytes(filename, payload)` remains an exact compatibility alias |
| `client.issues.create(..., project_id=project_id)` for a project relation | `client.projects.get(project_id).issues.create(title="Deploy")` |
| operation-specific timeout/profile kwargs | `client.issues.list(limit=50, options=OperationOptions(timeout=30))` |
| shell-string escape hatch | `client.cli.command("issue", "get", issue_id, options=options)` → `Command[CliResult]` |
| API URL used as a frontend permalink origin | `ClientConfig(app_url=app_url, workspace_slug=slug)` then `issue.permalink()` or `project.permalink()` |
| `ClientConfig(encoding=...)` | omit it; CLI stdout/stderr decoding is UTF-8 only |

`Issue.permalink()` and `Project.permalink()` are local-only, URL-encode path
segments, require a bound client and both routing values, and perform no I/O.

### Curated root imports

The root keeps common workflow types and primary entities. Advanced models and
resource outputs move to their dedicated modules:

| Former import | Compiling **After** |
|---|---|
| `from multica_py import IssueListFilter` | `from multica_py.models.issues import IssueListFilter` |
| `from multica_py import IssueListPage, IssueChildrenResult` | `from multica_py.models.issues import IssueListPage, IssueChildrenResult` |
| `from multica_py import IssueDescriptionInput, NoDescription, InlineDescription, FileDescription` | `from multica_py.models.issues import IssueDescriptionInput, NoDescription, InlineDescription, FileDescription` |
| `from multica_py import AutopilotListPage, AutopilotRunListPage` | `from multica_py.models.autopilots import AutopilotListPage, AutopilotRunListPage` |
| `from multica_py import CommentCursor` | `from multica_py.models.common import CommentCursor` |
| `from multica_py import MetadataPage` | `from multica_py.models.issue_activity import MetadataPage` |
| `from multica_py import ProjectResourceRecord, LocalDirectoryResourceRef` | `from multica_py.models.project_resources import ProjectResourceRecord, LocalDirectoryResourceRef` |
| `from multica_py import CursorPage, OffsetPage, RelationMetadata` | `from multica_py.models.relations import CursorPage, OffsetPage, RelationMetadata` |
| `from multica_py import RuntimeUpdateResult` | `from multica_py.models.system import RuntimeUpdateResult` |
| `from multica_py import JsonValue` | `from multica_py.types import JsonValue` |
| `from multica_py import LazyCollection, OffsetLazyCollection, CursorLazyCollection, LazyMapping` | `from multica_py.models.relations import LazyCollection, OffsetLazyCollection, CursorLazyCollection, LazyMapping` |
| `from multica_py import CliResult` | `from multica_py.resources.cli import CliResult` |

The canonical `Issue`, `Project`, and other primary entities are available from
`multica_py.entities`; the root exports remain available for compatibility. The
historical `multica_py.resources.<domain>` paths are direct re-exports with the
same class identity:

```python
from multica_py import Issue as RootIssue
from multica_py.entities import Issue
from multica_py.resources.issues import Issue as ResourceIssue

assert Issue is RootIssue is ResourceIssue
```

Entity modules contain immutable domain state and pure relation helpers.
Resource modules own service commands, wire conversion, transport, and cache
invalidation. Code that needs a domain type should import from `entities`; code
that needs a service should use the bound client resources.

## Managed process results

`ManagedProcess.result(timeout=...)` is the buffered API. It collects both pipes,
strictly decodes UTF-8, and returns one immutable `ProcessResult` with exactly
`argv`, `exit_code`, `stdout`, and `stderr`, plus `ok` and `failed` properties.
The finalized object is cached, so repeated `result()` calls preserve object
identity and `wait()` preserves the same output:

```python
from multica_py import ProcessResult, ProcessOutputModeError

process = client.auth.login()
result = process.result(timeout=30)
assert isinstance(result, ProcessResult)
assert result is process.result()
assert process.wait() == result.exit_code
```

Timeouts remain retryable without cleanup or cache publication. `terminate()`
and `kill()` leave the result collectible. `close()` discards the process and
forbids late access until finalization is explicitly repeated. A process can be
buffered or streaming, but not both; `ProcessOutputModeError` reports the
current mode and requested consumer. Streaming starts on first iteration:

```python
with client.daemon.logs() as process:
    for line in process.stdout_lines():
        consume(line)
```

Buffered mode, including `wait()`, retains all output in memory, so use
context-managed streaming for unbounded output. Do not call `result()`/`wait()`
after streaming has been selected.

## Command preview (additive)

The eager API and command-plan behavior remain unified, while the operation
contract below records the breaking page/action return migrations. `Command[T]`
is returned by typed `*_command()` siblings for CLI operations and relation load
points. Its `commands` property is always a tuple: empty for a cache-hit no-op,
one item for one CLI call, or ordered items/templates for a composite operation.
Preview performs no I/O, and `run()` executes the same immutable plan. Composite previews may contain result references such as
`${create.id}`. This is an additive feature; no eager method was renamed,
removed, or split.

## SDK-wide operation contract (breaking return/input changes)

The unified operation contract applies the same rules across resources:

- Direct keyword arguments are the public form for the removed one-operation
  DTOs. `IssueListFilter` is the retained reusable filter value object; stable
  target IDs stay positional and operation fields are explicit keyword-only
  parameters.
- `Unset` means omitted. An approved nullable `None` means clear; accepted
  `""`, `()`, `False`, and `0` remain present values. All-optional updates
  delegate an all-`Unset` call to a read command. Required project-resource
  `local_path` and runtime `target_version` updates reject omission/`None`
  before I/O and have no no-op read.
- Eager and `*_command()` calls share one plan and result type. `Command[T]`
  previews are redacted and I/O-free; `run()` executes that same plan.
- Canonical/direct-resource collections return immutable `Page[T]` values.
  Use `.items`, iteration, `len()`, and indexing. Compatibility aliases such
  as `.issues`, `.autopilots`, `.runs`, and `.children` remain read-only views
  of the same tuple.
- Approved actions return `ActionResult[T]` and payloads are in `.value`;
  former void actions use `ActionResult[None]`. Transport, validation, exit,
  and decode failures remain exceptions.

### Breaking return matrix

| Former public result | Current public result | Access pattern |
|---|---|---|
| Direct top-level and nested CLI/resource `tuple[T, ...]` lists | `Page[T]` or a compatible page subtype | `page.items`, iteration, `len(page)`, indexing |
| `IssueListPage`, `AutopilotListPage`, `AutopilotRunListPage`, `MetadataPage`, and `IssueChildrenResult` duplicate cores | Frozen generic `Page[T]` core with warning-free compatibility aliases | Prefer `items`; aliases are identity-preserving |
| `None` from archive/avatar/restore, delete/remove, cancellation/rerun, watcher, subscriber, membership, and configuration-set actions | `ActionResult[None]` | Check `.success` and optional redacted `.message` |
| `str` from token login | `ActionResult[str]` | Read `.value`; v0.4.28 uses root `login` |
| `RepositoryMutationResult` from repository add/remove | `ActionResult[RepositoryMutationResult]` | Read `.value.added`, `.value.repos`, and related fields |
| `RuntimeUpdateResult` from runtime update | `ActionResult[RuntimeUpdateResult]` | Read `.value` |
| Resource-specific command assumptions | `Command[T]` matching eager `T` | Inspect `.commands`, then call `.run()` |

The page migration covers canonical issue/autopilot/history/comment/metadata
query/children results, top-level agents/labels/projects/repositories/runtimes/
skills/squads/workspaces lists, and nested agent skills/tasks, issue comments/
labels/subscribers/pull requests/runs/run messages/search, project resources,
runtime activity/usage, skill files, squad members, workspace members, and
daemon disk usage. Issue-label add/remove refreshed collections use the
compatible label page contract. `issues.metadata.list` and aggregate/natural
scalar, mapping, entity, and process results remain their approved natural
types.

Relation `.all()` snapshots are explicitly unchanged: `LazyCollection.all()`,
`OffsetLazyCollection.all()`, and `CursorLazyCollection.all()` still return
tuples. A relation's direct `.page()` follows the Page contract. Resource-named
page aliases remain warning-free for at least one minor release and may only
be removed in a future major release.

Recursive JSON fields such as `AutopilotRun.trigger_payload` and `result` now
use immutable snapshots: object nodes implement the public
`Mapping[str, JsonValue]` contract and arrays are tuples. The unified entity's
`to_dict()` and `to_json()` methods materialize ordinary dict/list containers
when data crosses into a serializer; callers should use those methods rather
than serializing an internal snapshot node directly.

## v0.4.28 SDK additions and behavior

### Plugins and Remote MCP

`client.plugins` covers `plugin list|status|validate|pack|init|install` and
`plugin remote-mcp configure|test|approve|revoke`. List/status rows decode to
frozen `Plugin`. Validate/pack decode `PluginDigest`. `install()` and all
Remote MCP mutations are human-local guarded upstream; the SDK builds exact
argv and does not fake success in offline contexts. Remote MCP configure
requires `--endpoint` and accepts credentials only through file or
`credential_stdin: bytes | None` channels. Plugin list/status return `Page[Plugin]`.

### Workspace property catalog and issue properties

`client.properties` maps to `property list|get|create|update|archive|unarchive`.
Actor and multi-actor catalog types reject option tuples at construction.
`client.issues.properties` maps to `issue property list|set|unset` and is
distinct from `issues.metadata`. Bound `Issue.properties` loads through the
list command as a `LazyMapping` keyed by property name.

### Workspace and agent MCP

`workspaces.mcp` and nested `agents.mcp` expose reviewed MCP server
operations. Add requires exactly one config channel; update allows at most one.
`server_config_stdin: bytes | None` supplies the stdin payload. Direct MCP
list/mutation methods return `Page[McpServer]`; bound relation snapshots remain
tuples.
Secret-bearing inline JSON and stdin/file contents are redacted from preview
and diagnostics while executed argv still receives the reviewed flags. File
contents are read only at `run()` time using binary I/O, so non-UTF-8 payloads
remain executable and are redacted by exact bytes in diagnostics. Successful
typed decoders receive original stdout/stderr; the public raw `CliResult`
redacts its success streams.

### Skill refresh and search

`skills.refresh(skill_id)` emits `skill refresh <id> --output json`.
`skills.search(query)` returns `Page[SkillSearchResult]` from
`skill search <query> --output json`.

### Issue status pass-through

Issue status inputs (list filters, `set_status`, bound `Issue.set_status`) accept
the seven `IssueStatus` members or any upstream string without local membership
rejection. Email assignees map to `--assignee` when provided as strings.

### Bound relations R34–R38

`Workspace.plugins`, `Workspace.properties`, `Workspace.mcp_servers`,
`Agent.mcp_servers`, and `Issue.properties` are lazy relations with explicit
load points. The relation inventory now contains 38 rows.
Successful bound MCP mutations invalidate an already-loaded MCP relation.
`workspace mcp remove` is a text action returning `ActionResult[None]`, not a
JSON page. Plugin init likewise has no `--output`; Remote MCP configure accepts
`public_config_file` without SDK-side file reads.

## v0.4.20 SDK additions and behavior (historical)

### Agent copy

`agents.copy(source_agent_id, *, name=..., runtime_id=..., description=...,
instructions=..., model=..., thinking_level=..., service_tier=..., custom_args=...,
max_concurrent_tasks=..., permission_mode=..., public_to_workspace=...,
public_to_member_ids=..., copy_skills=..., options=...)` is the eager form and
returns a bound `Agent`; `agents.copy_command(source_agent_id, *, name=...,
runtime_id=..., description=..., instructions=..., model=..., thinking_level=...,
service_tier=..., custom_args=..., max_concurrent_tasks=..., permission_mode=...,
public_to_workspace=..., public_to_member_ids=..., copy_skills=..., options=...)` returns
`Command[Agent]`. Both share the same keyword-only presence-aware overrides:
`name`, `runtime_id`, `description`, `instructions`, `model`,
`thinking_level`, `service_tier`, `custom_args`, `max_concurrent_tasks`,
`permission_mode`, `public_to_workspace`, `public_to_member_ids`, and
`copy_skills`. Omitted values use `Unset`, so present empty strings remain
present and `copy_skills=False` emits `--no-skills`.

For example, `client.agents.copy(source_agent_id, runtime_id=runtime_id)` is a
signature-valid direct call; its command form accepts the same explicit names.

When copying across runtimes, `runtime_id` plus an omitted `model` emits
`--model ""`; this is the sole automatic runtime-specific default. Omitted
`thinking_level` and `service_tier` flags remain absent, and present values
are forwarded as unrestricted upstream strings. The SDK intentionally excludes
secret or machine-local configuration: `custom_env`, `mcp_config`, and
`runtime_config` are not part of either signature or argv.

### Issue search

`issues.search(query)` now returns an eager `Page[Issue]`, and
`issues.search_command(query)` returns `Command[Page[Issue]]`.
The exact command remains `issue search <query> --output json`. The decoder
accepts the v0.4.20 `issues` envelope and the legacy top-level array without
introducing a result wrapper. `Issue.match_source` is an optional
string, preserved when returned by upstream and `None` when absent.

### Typed failures and runtime deletion

`ConflictError` and `ValidationError` expose actionable redacted detail in
`str(exc)`, `stderr`, and `stdout`; the conflict retains the actual CLI exit
code, while v0.4.20 semantic validation uses exit code `5`. A non-cascade
runtime delete preserves the upstream dependent-agent conflict. With
`runtimes.delete(runtime_id, cascade=True)`, dependent agents are unbound,
their queued/running work is cancelled, and the runtime is deleted while
their configuration, chats, and task history are preserved. Documentation
must not describe this as deleting or archiving those agents.

## Class rename table (entity + data unification)

The 0.x release unifies each prior `*Entity` + `*Data` (+ redundant passive
DTO) pair into a single immutable domain class. The unified class is the
only public name; no `IssueData = Issue` style aliases are shipped. The
unified class carries private runtime state (client, lazy caches), so
persistence should go through `to_json()` / `to_dict()`.

The canonical public import path for the bound agent domain class is
`multica_py.entities.Agent`. The historical
`multica_py.resources.agents.Agent` path is a direct compatibility re-export,
also re-exported as `multica_py.Agent`, and all three names preserve identity.
`multica_py.models.agents` contains only the retained output models
`AgentSkill` and `AgentTask`; it does not export the bound `Agent` class.

| Removed name | Unified class |
|---|---|
| `multica_py.resources.issues.IssueEntity` | `multica_py.entities.Issue` (compat: `multica_py.resources.issues.Issue`) |
| `multica_py.resources.agents.AgentEntity` | `multica_py.entities.Agent` (compat: `multica_py.resources.agents.Agent`) |
| `multica_py.resources.skills.SkillEntity` | `multica_py.entities.Skill` (compat: `multica_py.resources.skills.Skill`) |
| `multica_py.resources.squads.SquadEntity` | `multica_py.entities.Squad` (compat: `multica_py.resources.squads.Squad`) |
| `multica_py.resources.workspaces.WorkspaceEntity` | `multica_py.entities.Workspace` (compat: `multica_py.resources.workspaces.Workspace`) |
| `multica_py.resources.workspaces.WorkspaceMemberEntity` | `multica_py.entities.WorkspaceMember` (compat: `multica_py.resources.workspaces.WorkspaceMember`) |
| `multica_py.resources.autopilots.AutopilotEntity` | `multica_py.entities.Autopilot` (compat: `multica_py.resources.autopilots.Autopilot`) |
| `multica_py.resources.autopilots.AutopilotRunEntity` | `multica_py.entities.AutopilotRun` (compat: `multica_py.resources.autopilots.AutopilotRun`) |
| `multica_py.models.issues.IssueData` | `multica_py.entities.Issue` (compat: `multica_py.resources.issues.Issue`) |
| `multica_py.models.issues.Issue` passive DTO | `multica_py.entities.Issue` (compat: `multica_py.resources.issues.Issue`) |
| `multica_py.models.projects.ProjectData` | `multica_py.entities.Project` (compat: `multica_py.resources.projects.Project`) |
| `multica_py.models.projects.Project` passive DTO | `multica_py.entities.Project` (compat: `multica_py.resources.projects.Project`) |
| `multica_py.models.agents.AgentData` | `multica_py.entities.Agent` (compat: `multica_py.resources.agents.Agent`) |
| `multica_py.models.agents.Agent` passive DTO | `multica_py.entities.Agent` (compat: `multica_py.resources.agents.Agent`) |
| `multica_py.models.skills.SkillData` | `multica_py.entities.Skill` (compat: `multica_py.resources.skills.Skill`) |
| `multica_py.models.skills.Skill` passive DTO | `multica_py.entities.Skill` (compat: `multica_py.resources.skills.Skill`) |
| `multica_py.models.system.SquadData` | `multica_py.entities.Squad` (compat: `multica_py.resources.squads.Squad`) |
| `multica_py.models.system.Squad` passive DTO | `multica_py.entities.Squad` (compat: `multica_py.resources.squads.Squad`) |
| `multica_py.models.workspaces.WorkspaceData` | `multica_py.entities.Workspace` (compat: `multica_py.resources.workspaces.Workspace`) |
| `multica_py.models.workspaces.Workspace` passive DTO | `multica_py.entities.Workspace` (compat: `multica_py.resources.workspaces.Workspace`) |
| `multica_py.models.workspaces.WorkspaceMemberData` | `multica_py.entities.WorkspaceMember` (compat: `multica_py.resources.workspaces.WorkspaceMember`) |
| `multica_py.models.workspaces.WorkspaceMember` passive DTO | `multica_py.entities.WorkspaceMember` (compat: `multica_py.resources.workspaces.WorkspaceMember`) |
| `multica_py.models.autopilots.AutopilotData` | `multica_py.entities.Autopilot` (compat: `multica_py.resources.autopilots.Autopilot`) |
| `multica_py.models.autopilots.Autopilot` passive DTO | `multica_py.entities.Autopilot` (compat: `multica_py.resources.autopilots.Autopilot`) |
| `multica_py.models.autopilots.AutopilotRunData` | `multica_py.entities.AutopilotRun` (compat: `multica_py.resources.autopilots.AutopilotRun`) |
| `multica_py.models.autopilots.AutopilotRun` passive DTO | `multica_py.entities.AutopilotRun` (compat: `multica_py.resources.autopilots.AutopilotRun`) |
| `multica_py.models.issue_activity.CommentData` | `multica_py.entities.Comment` (compat: `multica_py.resources.issue_comments.Comment`) |
| `multica_py.models.issue_activity.Comment` passive DTO | `multica_py.entities.Comment` (compat: `multica_py.resources.issue_comments.Comment`) |
| `multica_py.models.issue_activity.CommentThreadData` | `multica_py.entities.CommentThread` (compat: `multica_py.resources.issue_comments.CommentThread`) |
| `multica_py.models.issue_activity.CommentThread` passive DTO | `multica_py.entities.CommentThread` (compat: `multica_py.resources.issue_comments.CommentThread`) |
| `multica_py.models.issue_activity.TaskRunData` | `multica_py.entities.TaskRun` (compat: `multica_py.resources.issues.TaskRun`) |
| `multica_py.models.issue_activity.TaskRun` passive DTO | `multica_py.entities.TaskRun` (compat: `multica_py.resources.issues.TaskRun`) |
| `multica_py.models.labels.LabelData` | `multica_py.entities.Label` (compat: `multica_py.resources.labels.Label`) |
| `multica_py.models.project_resources.ProjectResourceData` | `multica_py.models.project_resources.ProjectResourceRecord` |
| `multica_py.models.ResourceEntity[TData]`, `to_data()`, `from_data()` | direct class fields + `to_json()` / `to_dict()` / `from_dict()` on the unified class |

The private helper `_BoundEntity` (in `multica_py.entities._base`) backs
every unified class. It is not exported; treat it as implementation detail.

## Public surface migrations

| Legacy surface | Alpha replacement | Notes |
|---|---|---|
| `Agent.skills` eager tuple | `Agent.skill_refs` and `Agent.skills` | The relation uses `agent skills list`; `skill_refs` exposes the embedded snapshot directly. |
| `agent skill ...` commands | `agent skills list/set` | Singular argv is not a supported relation path. |
| `skill file ...` commands | `skill files list/upsert/delete` and `Skill.files` | Successful file mutations invalidate the bound skill relation. |
| `Issue.labels` eager names | `Issue.label_names` and `Issue.labels` | `add_label()`/`remove_label()` invalidate the matching relation. |
| `Issue.children` eager stage summary | `Issue.child_stages` and `Issue.children` | Child aggregate metadata remains on the lazy relation. |
| `Issue.metadata` eager entries | `Issue.metadata_snapshot` and `Issue.metadata` | The relation is a typed `LazyMapping`; use `set_metadata()`/`delete_metadata()`. |
| `IssueData.pull_requests` embedded snapshot | `Issue.pull_request_snapshot` and `Issue.pull_requests` | `pull_request_snapshot` is the immutable get-response field; `pull_requests` remains the R26 lazy relation and therefore cannot also be a field name. |
| `issues.rerun(issue_id, run_id)` | `issues.rerun(issue_id)` | Rerun is addressed only by issue ID. |
| `issues.cancel_task(issue_id, run_id)` | `issues.cancel_task(task_id)` | Cancellation is addressed by task ID. |
| Legacy run-message addressing | `issues.run_messages(task_run_id, issue_id=None)` | The CLI receives the task-run ID and optional inherited issue ID. |
| `agents.upload_avatar(...)` / `--image` | `agents.avatar(agent_id, file)` | The governed command is `agent avatar <id> --file <path>`. |
| `attachments.list(issue_id)` | Removed | The pinned CLI has no safe issue attachment collection. |
| Issue-based attachment upload | `attachments.upload(path, task_id=None)` | No issue ID or `--file` flag is emitted. |
| Legacy attachment download signature | `attachments.download(attachment_id, output_dir=...)` | The CLI uses `--output-dir`; `download_bytes()` remains the byte helper. |
| `users.list()` / `users.get(user_id)` | `users.profile_get()` / `users.profile_update(...)` | Workspace membership is `Workspace.members`; arbitrary user scans are not replaced. |
| `repositories.get(repo_id)` | `repositories.list/add/remove` | Repository identity is URL/ref; there is no SDK single-repository get replacement. |
| `runtimes.get(runtime_id)` | `runtimes.list/usage/activity/update/rename/delete` | There is no CLI-backed single-runtime get replacement. |
| `autopilots.run(autopilot_id)` | `autopilots.trigger(autopilot_id)` | The command is `autopilot trigger <id>`. |
| `autopilots.get_run(run_id)` | `autopilots.history(autopilot_id)` | Select a run from the returned page; no single-run fetch exists. |
| Nested autopilot trigger list/create/delete | Get-envelope seed plus `trigger_add/update/delete` | Trigger reads come from governed get; mutations use `trigger-add/update/delete`. |
| `Autopilot.subscribers` eager tuple | `Autopilot.subscriber_snapshot` and `Autopilot.subscribers` | Complete get-envelope data seeds the relation; omitted fields stay unloaded. |

## Issue list projections

Direct issue lists, the five list-backed relations, and child collections now
expose immutable partial, bound `Issue` values. Missing get-only fields use
documented defaults, and no implicit `issues.get` hydration occurs.

| Caller | Before | After |
|---|---|---|
| Direct list | `for issue in client.issues.list(filter).issues` | `for issue in client.issues.list(filter).issues` |
| `Workspace.issues` | `for issue in client.workspaces.get(workspace_id).issues.all()` | `for issue in client.workspaces.get(workspace_id).issues.all()` |
| `Project.issues` | `for issue in client.projects.get(project_id).issues.all()` | `for issue in client.projects.get(project_id).issues.all()` |
| `Agent.issues` | `for issue in client.agents.get(agent_id).issues.all()` | `for issue in client.agents.get(agent_id).issues.all()` |
| `Squad.issues` | `for issue in client.squads.get(squad_id).issues.all()` | `for issue in client.squads.get(squad_id).issues.all()` |
| `WorkspaceMember.issues` | `for issue in member.issues.all()` | `for issue in member.issues.all()` |

```python
from multica_py.entities import Issue

for issue in client.issues.list(filter).issues:
    issue: Issue
    if issue.status == "todo":
        issue.add_comment_command("ready")
```

The same bound `Issue` value supports queue discovery and immediate command
construction; execution remains explicit through the returned command plan.

## Workspace-member identity

`WorkspaceMember.id` is the workspace membership identity and remains the
value used by `WorkspaceMember.issues` as `assignee_id`. It is not an alias for
the related user. `WorkspaceMember.user_id` is the optional user identity for
reconciling `Issue.creator_id`, and `WorkspaceMember.email` is the
optional member email.

Older or minimal member payloads may omit both user fields. In that case
`user_id is None` and `email is None`; callers should handle `None` explicitly
and must not fall back from `user_id` to the membership `id`.

## Embedded issue attachments

`IssueEntity.attachments` references in older guides map to `Issue.attachments`: the latter is a passive tuple snapshot from the explicit
`issues.get(issue_id)` response and reuses `AttachmentResult`. Both an omitted
`attachments` field and an explicit empty array decode as `()`.

The pinned upstream command may also omit the field when its best-effort
attachment read fails, so an empty tuple is not an atomic completion signal.
When a result is expected, retry with a fresh `issues.get(issue_id)` and pass a
known attachment directly to the existing byte helper:

```python
issue = client.issues.get(issue_id)
if issue.attachments:
    payload = client.attachments.download_bytes(issue.attachments[0].id)
```

The SDK does not add an attachment list relation, a selector helper, or a
second public attachment model.

## Issue activity models in CLI 0.4.32

`Issue.assignee` now accepts both the legacy nested object and the current
`assignee_id`/`assignee_type` pair. Matching dual projections are accepted;
partial or contradictory pairs raise `OutputShapeError` instead of silently
returning `None`.

`IssueUsage` preserves input, output, cache-read, and cache-write totals as
separate values, together with `task_count`, `cost_usd_ticks`, and matching
uncosted categories. Legacy `total_runs`, `total_tokens`, and `cost_usd`
remain readable. No new total adds cache reads to input and output.

`TaskRun` now carries typed runtime/worktree/result context. Prefer relative
work-directory fields for UI; absolute fields are intended for explicit local
tooling. Legacy run rows remain valid and leave the new fields as `None`.

## Singular reference migration (`[0.4.28, 0.4.33)`)

The following members intentionally do not exist: `Project.autopilots`,
agent/squad autopilots, `Label.issues`, `Skill.agents`, `Runtime.agents`,
`Repository.projects`, a lazy attachment relation on `Issue`, and
`Workspace.users`. There is no hidden workspace scan, client-side filtering
fallback, or per-child N+1 path. The additive `LazyRef` handle is imported only
from `multica_py.models.relations`; the exact inventory is shown below. The
public import spelling is:

```python
from multica_py.models.relations import LazyRef
```

These nine handles are not `ManyRelation` collections:

| Public property | Type | Governed lookup |
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

Existing scalar IDs remain unchanged, including `Issue.parent_id`,
`Issue.project_id`, and the run/autopilot/agent IDs. `Issue.assignee` remains
the immutable `IssueAssignee | None` embedded snapshot. `Issue.assignee_ref` is
the separate, passive handle and never replaces that snapshot.

The unsupported singular edges remain absent: creator/member, autopilot
trigger, task, squad leader, comment author, workspace user,
`PropertyValue.property_id`, `Plugin.uploader_id`, and MCP record IDs. A
workspace-member object or email accepted by v0.4.28 assignment likewise stays
an embedded member snapshot; it does not imply a member lookup.

Reference-changing Issue mutations (`update(parent_id=...)`,
`update(project_id=...)`, `update(assignee_id=...)`, `assign(...)`, and
`unassign()`) return an immutable replacement decoded from the complete response
snapshot. The returned scalar/snapshot and presence-aware handles are
authoritative; the original wrapper, its scalar fields, and its loaded or
unloaded handle caches are never retargeted. Failed mutations publish no
replacement. Serialize the replacement if it must cross an application
boundary; serialization and manual construction do not invent explicit-null
provenance.

For the passive/explicit-I/O lifecycle, see
[the API reference](api.md#singular-references) and the runnable
[singular-reference example](../examples/singular_references.py).

## Bound data and lifecycle

Use `to_json()` or `to_dict()` when passing data to serializers or comparing
results. Both exclude the client, lazy caches, locks, and loader closures:

```python
import msgspec

issue = client.issues.get("issue_456")
payload = issue.to_json()
restored = msgspec.json.decode(payload, type=dict[str, object])
```

Reading `issue.labels` or `autopilot.runs` creates a lazy object without I/O;
iteration, `all()`, `page()`, `refresh()`, and `prefetch()` are load points.
Missing embedded relation fields remain unloaded, while explicit complete empty
fields load as empty. Detached entities and missing inherited context raise the
typed relation errors before transport access.
