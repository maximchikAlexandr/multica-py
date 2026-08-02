# Alpha migration guide

The relation graph is a deliberate 0.x API boundary. Resource results are
bound wrappers; scalar data is available through `to_data()`, and relations
load only at explicit load points such as `all()`, `page()`, `refresh()`, or
`MulticaClient.prefetch()`.

## Public surface migrations

| Legacy surface | Alpha replacement | Notes |
|---|---|---|
| `Agent.skills` eager tuple | `AgentData.skill_refs` and `Agent.skills` | The relation uses `agent skills list`; use `to_data().skill_refs` for the embedded snapshot. |
| `agent skill ...` commands | `agent skills list/set` | Singular argv is not a supported relation path. |
| `skill file ...` commands | `skill files list/upsert/delete` and `Skill.files` | Successful file mutations invalidate the bound skill relation. |
| `Issue.labels` eager names | `IssueData.label_names` and `Issue.labels` | `add_label()`/`remove_label()` invalidate the matching relation. |
| `Issue.children` eager stage summary | `IssueData.child_stages` and `Issue.children` | Child aggregate metadata remains on the lazy relation. |
| `Issue.metadata` eager entries | `IssueData.metadata_snapshot` and `Issue.metadata` | The relation is a typed `LazyMapping`; use `set_metadata()`/`delete_metadata()`. |
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
| `Autopilot.subscribers` eager tuple | `AutopilotData.subscriber_snapshot` and `Autopilot.subscribers` | Complete get-envelope data seeds the relation; omitted fields stay unloaded. |

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

`IssueEntity.attachments` is a passive tuple snapshot from the explicit
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
`Repository.projects`, a lazy attachment relation on `IssueEntity`, and
`Workspace.users`. There is no
hidden workspace scan, client-side filtering fallback, or per-child N+1 path.

Issue parent/project/assignee/creator and analogous autopilot/run references
remain scalar IDs or snapshots in this change. They are not `ManyRelation`
collections. A later `LazyRef` capability may define singular loading; this
release does not invent that API.

## Bound data and lifecycle

Use the explicit snapshot boundary when passing data to serializers or comparing
results:

```python
issue_data = issue.to_data()
```

Reading `issue.labels` or `autopilot.runs` creates a lazy object without I/O;
iteration, `all()`, `page()`, `refresh()`, and `prefetch()` are load points.
Missing embedded relation fields remain unloaded, while explicit complete empty
fields load as empty. Detached entities and missing inherited context raise the
typed relation errors before transport access.
