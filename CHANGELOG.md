# Changelog

## Unreleased — unified SDK operation contracts

This breaking alpha makes direct typed inputs, bound `Issue` read paths, and
one inspectable command contract canonical. Relation `.all()` tuple snapshots
remain unchanged. The complete compiling migration table is in
[docs/migration.md](docs/migration.md).

### Breaking before/after inventory

Each removed one-operation DTO now compiles as the direct call shown here;
`options=OperationOptions(...)` may be appended to either eager or command
forms:

| Before | After |
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

The same import move applies to `IssueDescriptionInput` and description
variants (`multica_py.models.issues`), compatibility pages
(`multica_py.models.autopilots`), cursor/page/relation types
(`multica_py.models.relations`), and `RuntimeUpdateResult`
(`multica_py.models.system`).

Other breaking moves are equally direct: list/search/relations now yield
`Issue` (not `IssueSummary`), assignment uses `assign`/`unassign`, ordering
uses the four `move_*` verbs, and project issue creation is
`project.issues.create(...)` without a public `project_id`. Use
`attachments.upload(payload, filename=...)` (with `upload_bytes` as an exact
alias), `client.cli.command(*argv, options=None)` for bounded raw argv, and
`ClientConfig(app_url=..., workspace_slug=...)` for passive entity permalinks.

Advanced filters, pages, cursor/metadata/value types, relation implementations,
resource outputs, and `CliResult` are imported from their dedicated modules;
the exact before/after import table is maintained in the migration guide.

- **Page and actions** — list results use immutable `Page[T]`; void actions use `ActionResult[None]` and payloads are in `.value`.
- **Command execution** — every CLI-backed `*_command()` returns `Command[T]` matching eager `T`; previews are redacted and I/O-free, and `.run()` executes the same plan.

## 0.1.0 (unreleased)

- Initial SDK release
- Complete Multica CLI coverage from pinned baseline `48b8dbf`
- Library-only: install from GitHub via `uv add "multica-py @ git+https://github.com/maximchikAlexandr/multica-py@v0.1.0"` (no PyPI publish yet)
- Removed earlier in-tree CLI (`multica-py` console script); SDK is consumed as a Python library
- Spawn/streaming timeouts raise `ProcessTimeoutError` (`CommandTimeoutError` / `MulticaError`) instead of bare `TimeoutError`; missing pipes raise `ProcessOutputCaptureError`; stream decode failures raise `EncodingError`
