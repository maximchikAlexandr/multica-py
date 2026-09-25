# Changelog

## 0.5.2

- Approved target: Multica CLI `0.5.2`, release `394535503`, source commit
  `d45aba1cd7582bef9210b921bbb7dc198b48e1ee`, with compatibility bounds
  `[0.4.42, 0.5.3)`.
- Migrate directly from `0.5.1`; no intermediate SDK delivery is required.
- Add immutable duplicate issue snapshots, read-only task supplement metadata,
  and ordered atomic `IssuePropertyAssignment` inputs to issue creation. New
  fields and properties require CLI `0.5.2`; retained operations keep their
  existing minimums.
- Keep task-supplement and duplicate mutation/receipt APIs, issue timeline and
  attachment inputs, issue wakeup, and runtime-profile surfaces deferred.
- If acceptance gates fail, roll back the approved contract, generated runtime,
  models/resources, tests, docs, and package claims atomically to the prior
  `0.5.1` state.

## Unreleased — unified SDK operation contracts

This breaking alpha makes direct typed inputs, bound `Issue` read paths, and
one inspectable command contract canonical. Relation `.all()` tuple snapshots
remain unchanged. The complete compiling migration table is in
[docs/migration.md](docs/migration.md).

### Historical Multica 0.5.1 compatibility migration

- Targets CLI `0.5.1` at
  `f41fae6b08fb734afcbd13205c0b3203dd0bc9c6`, with bounds
  `[0.4.42, 0.5.2)`; migrate directly from `0.5.0` with no intermediate SDK
  release.
- Preserves optional open-string `TaskRun.wakeup_id` and `RunMessage.call_id`
  when supplied, while omitted legacy values remain `None` and malformed
  values fail at the typed protocol boundary.
- Reconciles 194 baseline to 201 target command nodes: 192 unchanged, two
  changed existing nodes (`issue` and `runtime profile create`), and seven
  deferred `issue wakeup` additions. Runtime profiles remain outside the SDK
  surface. Contract, generated runtime, tests, docs, and package claims roll
  back atomically if gates fail.

### Historical Multica 0.5.0 compatibility migration

- Targets CLI `0.5.0` at
  `2df765a3c8f39789c9fb76316378bcffc20d22d9`, with bounds
  `[0.4.42, 0.5.1)`; migrate directly from `0.4.44` with no intermediate
  SDK release.
- Baseline release `391379076` used archive
  `b4bae1001c30a870c784b19123437df9f09308f750a699ce3693877ba6ffc5d1` and
  extracted executable
  `e8305b68e13d7cceeaaf382723d465552a9555b6540f1899527eccb36847e094`.
- Adds text-only optimistic `issues.comments.update` with a required positive
  revision, typed `skills.labels.list/add/remove`, and preloaded `Skill.labels`.
- Extends labels with reviewed `issue`/`skill` resource types and
  presence-aware descriptions: `Unset` omits and `None`/`""` clears.
- Preserves absent versus known-empty task deltas, open failure reasons such as
  `runtime_access_denied`, and local OMP validation: create requires a nonblank
  model, thinking requires an effective model, and update clear-plus-thinking
  fails before transport. Structured or plain runtime-delete conflicts remain
  supported without cascade or retry.
- Reconciles 189 baseline to 194 target command nodes and all 163 response
  work items. Archive, executable, and version JSON checksums remain separate;
  activity, maintenance, Dingtalk, telemetry, and other non-SDK changes stay
  excluded. Contract, generated runtime, API, fixtures, docs, and package
  claims roll back atomically if gates fail.

### Historical Multica 0.4.44 compatibility migration

- Targets CLI `0.4.44` at
  `c7f259c70a60bff30011c403fada79ab382f608a`, with bounds
  `[0.4.42, 0.4.45)`; migrate directly from `0.4.43` and retain support for
  `0.4.42` where the operation is retained.
- Adds strict comment tombstones and target keep-replies deletion. Safe delete
  requires CLI `0.4.44`; the reviewed pre-support 404 never triggers a
  destructive fallback.
- Preserves custom lifecycle keys with legacy category projection and rejects
  every present Triage parent update atomically with `issue_in_triage`.
- Keeps release archive, executable, and version JSON checksum roles separate;
  activity, daemon garbage collection, maintenance, Dingtalk, and telemetry
  changes remain outside the SDK surface. Contract, generated runtime, public
  behavior, tests, docs, and package claims roll back atomically if gates fail.

### Multica 0.4.43 compatibility migration

- Targets CLI `0.4.43` at
  `2ae2dbbb8f9ed9ffe1739ecf5abfe31a940ee50c`, with bounds
  `[0.4.42, 0.4.44)`; the retained surface remains compatible with `0.4.42`.
- Adds validated `conversation_starters` to agent create/update; explicit
  starter mutations require CLI `0.4.43`, while omission preserves old argv.
- Preserves cancellation actors, tri-state message truncation, and independent
  exact usage coverage counts without fabricating absent values.
- Pins server-side status sorting, run-message 404/500 classification, source
  and checksum roles, non-SDK `repo checkout --fresh`, and atomic rollback.

### Historical Multica 0.4.42 compatibility migration

- Historically targeted CLI `0.4.42` at
  `76f59f5f1cd9b6e779d0d34c603407d5d4001bf7`, with bounds
  `[0.4.42, 0.4.43)`; this interval is superseded by the current `0.4.44`
  target and `[0.4.42, 0.4.45)` bounds.
- Removes Plugin operations, models, exports, and `Workspace.plugins`; there
  is no replacement API. Autopilot create/update no longer accept `priority`.
- Makes Skill get content explicit, keeps Skill lists metadata-only, and adds
  opt-in issue fields, property predicates/sorting, and resolved properties.
- Defers timeline, trigger-list, and compact active/sibling run envelopes
  until separately reviewed. Contract, generated runtime, public API, tests,
  and docs must be reverted atomically if release gates fail.

### Breaking before/after inventory

Each removed one-operation DTO now compiles as the direct call shown here;
`options=OperationOptions(...)` may be appended to either eager or command
forms:

| Before | After |
|---|---|
| `AgentCreateRequest(name="build")` | `client.agents.create(name="build", model="gpt-5")` |
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
| `AutopilotTriggerCreate(title="Daily", kind="schedule")` | `client.autopilots.trigger_add(autopilot_id, kind="schedule", cron_expression="*/30 * * * *", timezone="Europe/Minsk", label="Daily")` |
| `AutopilotTriggerUpdate(kind="schedule")` | `client.autopilots.trigger_update(autopilot_id, trigger_id, cron_expression="0 */3 * * *", timezone="Europe/Minsk", enabled=False)` |
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
`ClientConfig.encoding` is removed; CLI output is UTF-8 only.

Advanced filters, pages, cursor/metadata/value types, relation implementations,
resource outputs, and `CliResult` are imported from their dedicated modules;
the exact before/after import table is maintained in the migration guide.

- **Page and actions** — list results use immutable `Page[T]`; void actions use `ActionResult[None]` and payloads are in `.value`.
- **Command execution** — every CLI-backed `*_command()` returns `Command[T]` matching eager `T`; previews are redacted and I/O-free, and `.run()` executes the same plan.

### Fixed

- Secret redaction now skips environment-derived values shorter than 8 characters, preventing short env values (e.g. `API_KEY=1`) from corrupting unrelated diagnostic text. Explicit `--token`/file/stdin secret channels are unaffected.
- Issue decoding preserves CLI 0.4.32 scalar assignees and rejects conflicting
  nested/scalar projections. `IssueUsage` exposes exact token, cost-tick, and
  uncosted categories, while `TaskRun` retains reviewed runtime, worktree,
  result, and failure context. Historical notes for CLI 0.4.32 retain the
  superseded interval `[0.4.28, 0.4.33)`; the historical `0.5.1` target had
  compatibility interval `[0.4.42, 0.5.2)`; the current approved target is
  `0.5.2` with `[0.4.42, 0.5.3)`. The `0.5.0` release is comparison
  provenance only.

## 0.1.0 (unreleased)

- Initial SDK release
- Complete Multica CLI coverage from pinned baseline `48b8dbf`
- Library-only: install from GitHub via `uv add "multica-py @ git+https://github.com/maximchikAlexandr/multica-py@v0.1.0"` (no PyPI publish yet)
- Removed earlier in-tree CLI (`multica-py` console script); SDK is consumed as a Python library
- Spawn/streaming timeouts raise `ProcessTimeoutError` (`CommandTimeoutError` / `MulticaError`) instead of bare `TimeoutError`; missing pipes raise `ProcessOutputCaptureError`; stream decode failures raise `EncodingError`
