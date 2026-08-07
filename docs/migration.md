# Alpha migration guide

The relation graph is a deliberate 0.x API boundary. Resource results are
bound wrappers; scalar data is available through `to_json()` / `to_dict()`,
and relations load only at explicit load points such as `all()`, `page()`,
`refresh()`, or `MulticaClient.prefetch()`.

## Command preview (additive)

The eager API and its return types are unchanged. The only new public type is
`Command[T]`, returned by typed `*_command()` siblings for CLI operations and
relation load points. Its `commands` property is always a tuple: empty for a
cache-hit no-op, one item for one CLI call, or ordered items/templates for a
composite operation. Preview performs no I/O, and `run()` executes the same
immutable plan. Composite previews may contain result references such as
`${create.id}`. This is an additive feature; no eager method was renamed,
removed, or split.

Recursive JSON fields such as `AutopilotRun.trigger_payload` and `result` now
use immutable snapshots: object nodes implement the public
`Mapping[str, JsonValue]` contract and arrays are tuples. The unified entity's
`to_dict()` and `to_json()` methods materialize ordinary dict/list containers
when data crosses into a serializer; callers should use those methods rather
than serializing an internal snapshot node directly.

## v0.4.20 SDK additions and behavior

### Agent copy

`agents.copy(source_agent_id, **overrides)` is the eager form and returns a
bound `Agent`; `agents.copy_command(source_agent_id, **overrides)` returns
`Command[Agent]`. Both share the same keyword-only presence-aware overrides:
`name`, `runtime_id`, `description`, `instructions`, `model`,
`thinking_level`, `service_tier`, `custom_args`, `max_concurrent_tasks`,
`permission_mode`, `public_to_workspace`, `public_to_member_ids`, and
`copy_skills`. Omitted values use `Unset`, so present empty strings remain
present and `copy_skills=False` emits `--no-skills`.

When copying across runtimes, `runtime_id` plus an omitted `model` emits
`--model ""`; this is the sole automatic runtime-specific default. Omitted
`thinking_level` and `service_tier` flags remain absent, and present values
are forwarded as open upstream strings. The SDK intentionally excludes
secret or machine-local configuration: `custom_env`, `mcp_config`, and
`runtime_config` are not part of either signature or argv.

### Issue search

`issues.search(query)` still returns an eager `tuple[IssueSummary, ...]`, and
`issues.search_command(query)` returns `Command[tuple[IssueSummary, ...]]`.
The exact command remains `issue search <query> --output json`. The decoder
accepts the v0.4.20 `issues` envelope and the legacy top-level array without
introducing a result wrapper. `IssueSummary.match_source` is an optional open
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
`multica_py.resources.agents.Agent` (also re-exported as `multica_py.Agent`).
`multica_py.models.agents` contains only wire/request types and does not export
the bound `Agent` class.

| Removed name | Unified class |
|---|---|
| `multica_py.resources.issues.IssueEntity` | `multica_py.resources.issues.Issue` |
| `multica_py.resources.agents.AgentEntity` | `multica_py.resources.agents.Agent` |
| `multica_py.resources.skills.SkillEntity` | `multica_py.resources.skills.Skill` |
| `multica_py.resources.squads.SquadEntity` | `multica_py.resources.squads.Squad` |
| `multica_py.resources.workspaces.WorkspaceEntity` | `multica_py.resources.workspaces.Workspace` |
| `multica_py.resources.workspaces.WorkspaceMemberEntity` | `multica_py.resources.workspaces.WorkspaceMember` |
| `multica_py.resources.autopilots.AutopilotEntity` | `multica_py.resources.autopilots.Autopilot` |
| `multica_py.resources.autopilots.AutopilotRunEntity` | `multica_py.resources.autopilots.AutopilotRun` |
| `multica_py.models.issues.IssueData` | `multica_py.resources.issues.Issue` |
| `multica_py.models.issues.Issue` passive DTO | `multica_py.resources.issues.Issue` |
| `multica_py.models.projects.ProjectData` | `multica_py.resources.projects.Project` |
| `multica_py.models.projects.Project` passive DTO | `multica_py.resources.projects.Project` |
| `multica_py.models.agents.AgentData` | `multica_py.resources.agents.Agent` |
| `multica_py.models.agents.Agent` passive DTO | `multica_py.resources.agents.Agent` |
| `multica_py.models.skills.SkillData` | `multica_py.resources.skills.Skill` |
| `multica_py.models.skills.Skill` passive DTO | `multica_py.resources.skills.Skill` |
| `multica_py.models.system.SquadData` | `multica_py.resources.squads.Squad` |
| `multica_py.models.system.Squad` passive DTO | `multica_py.resources.squads.Squad` |
| `multica_py.models.workspaces.WorkspaceData` | `multica_py.resources.workspaces.Workspace` |
| `multica_py.models.workspaces.Workspace` passive DTO | `multica_py.resources.workspaces.Workspace` |
| `multica_py.models.workspaces.WorkspaceMemberData` | `multica_py.resources.workspaces.WorkspaceMember` |
| `multica_py.models.workspaces.WorkspaceMember` passive DTO | `multica_py.resources.workspaces.WorkspaceMember` |
| `multica_py.models.autopilots.AutopilotData` | `multica_py.resources.autopilots.Autopilot` |
| `multica_py.models.autopilots.Autopilot` passive DTO | `multica_py.resources.autopilots.Autopilot` |
| `multica_py.models.autopilots.AutopilotRunData` | `multica_py.resources.autopilots.AutopilotRun` |
| `multica_py.models.autopilots.AutopilotRun` passive DTO | `multica_py.resources.autopilots.AutopilotRun` |
| `multica_py.models.issue_activity.CommentData` | `multica_py.resources.issue_comments.Comment` |
| `multica_py.models.issue_activity.Comment` passive DTO | `multica_py.resources.issue_comments.Comment` |
| `multica_py.models.issue_activity.CommentThreadData` | `multica_py.resources.issue_comments.CommentThread` |
| `multica_py.models.issue_activity.CommentThread` passive DTO | `multica_py.resources.issue_comments.CommentThread` |
| `multica_py.models.issue_activity.TaskRunData` | `multica_py.resources.issues.TaskRun` |
| `multica_py.models.issue_activity.TaskRun` passive DTO | `multica_py.resources.issues.TaskRun` |
| `multica_py.models.labels.LabelData` | `multica_py.resources.labels.Label` |
| `multica_py.models.project_resources.ProjectResourceData` | `multica_py.models.project_resources.ProjectResourceRecord` |
| `multica_py.models.ResourceEntity[TData]`, `to_data()`, `from_data()` | direct class fields + `to_json()` / `to_dict()` / `from_dict()` on the unified class |

The private helper `_BoundEntity` (in `multica_py.models._bound`) backs
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

Direct issue lists and the five list-backed relations now expose immutable
`IssueSummary` values. They are list projections, not compact bound issues.
Use the explicit `issues.get(summary.id)` call only when bound behavior or
complete issue state is needed.

| Caller | Before | After |
|---|---|---|
| Direct list | `for issue in client.issues.list(filter).issues` | `for summary in client.issues.list(filter).issues` |
| `Workspace.issues` | `for issue in client.workspaces.get(workspace_id).issues.all()` | `for summary in client.workspaces.get(workspace_id).issues.all()` |
| `Project.issues` | `for issue in client.projects.get(project_id).issues.all()` | `for summary in client.projects.get(project_id).issues.all()` |
| `Agent.issues` | `for issue in client.agents.get(agent_id).issues.all()` | `for summary in client.agents.get(agent_id).issues.all()` |
| `Squad.issues` | `for issue in client.squads.get(squad_id).issues.all()` | `for summary in client.squads.get(squad_id).issues.all()` |
| `WorkspaceMember.issues` | `for issue in member.issues.all()` | `for summary in member.issues.all()` |

```python
from multica_py import IssueStatus
from multica_py.models.issues import IssueSummary

for summary in client.issues.list(filter).issues:
    summary: IssueSummary
    if summary.status is IssueStatus.backlog:
        bound_issue = client.issues.get(summary.id)
        bound_issue.add_comment("ready")
```

The summary path is the default for queue discovery. The explicit get is the
intentional boundary when a caller needs comments, mutation helpers, or other
bound relations.

## Workspace-member identity

`WorkspaceMember.id` is the workspace membership identity and remains the
value used by `WorkspaceMember.issues` as `assignee_id`. It is not an alias for
the related user. `WorkspaceMember.user_id` is the optional user identity for
reconciling `IssueSummary.creator_id`, and `WorkspaceMember.email` is the
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

## Unsupported inverse and singular relations

The following members intentionally do not exist: `Project.autopilots`,
agent/squad autopilots, `Label.issues`, `Skill.agents`, `Runtime.agents`,
`Repository.projects`, a lazy attachment relation on `Issue`, and
`Workspace.users`. There is no
hidden workspace scan, client-side filtering fallback, or per-child N+1 path.

Issue parent/project/assignee/creator and analogous autopilot/run references
remain scalar IDs or snapshots in this change. They are not `ManyRelation`
collections. A later `LazyRef` capability may define singular loading; this
release does not invent that API.

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
