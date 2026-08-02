## Why

The SDK returns detached immutable DTOs, forcing consumers to carry clients,
parent identifiers, paging state, and ad-hoc caches for every graph traversal.
GitHub issue [#14](https://github.com/maximchikAlexandr/multica-py/issues/14)
defines the complete target: correct the CLI contract first, then expose all
33 server-supported batch, paged, aggregate, cursor, and mapping relations as
typed bound entities without hidden workspace scans or per-child N+1 calls.

## What Changes

- Correct all 19 CLI/response/presence divergences identified in issue #14
  before relations make those calls implicit: issue list/children/pull
  requests/metadata/runs, agent skills/avatar, skill files, autopilot
  get/trigger/run surfaces, attachments, users, repositories, runtimes, and
  wire-field presence.
- **BREAKING**: replace detached public entity DTO results with bound entity
  wrappers over immutable typed data snapshots. Existing scalar values remain
  readable and `to_data()` provides explicit snapshot serialization.
- Make derived `MulticaClient` views reuse the originating client's
  `ProcessSemaphore`; otherwise keep clients independent. Bound entities retain
  their originating client view and own per-entity lazy state. No client
  family runtime, identity map, enrichment, or global relation cache is added.
- Add parameterized query views, `LazyCollection`, `OffsetLazyCollection`,
  `CursorLazyCollection`, and `LazyMapping`. Paging is implemented by private
  `_collect_offsets`/`_collect_cursors` helpers; no public strategy or
  descriptor framework is introduced.
- Add the full 33-relation matrix:
  - `Workspace.members/agents/skills/projects/issues/labels/autopilots/repositories/runtimes/squads`;
  - `Agent.skills/tasks/issues`, `Skill.files`, `Squad.members/issues`, and
    `WorkspaceMember.issues`;
  - `Project.resources/issues`;
  - `Issue.comments/recent_comment_threads/labels/subscribers/metadata/pull_requests/children/runs`,
    `CommentThread.comments`, and `TaskRun.messages`;
  - `Autopilot.runs/triggers/subscribers` and `AutopilotRun.messages`.
- Add lazy-state seeding only for explicitly present, contract-proven-complete
  embedded fields; coalesced first loads, blocking atomic refresh, local
  parent-addressable mutation invalidation, detached entity errors, pagination
  progress guards, and bounded `prefetch()`.
- **BREAKING**: rename conflicting eager fields (`Issue.labels` to
  `label_names`, issue stage summaries to `child_stages`, agent embedded skill
  data to a seed/snapshot field) so relation names have one consistent public
  meaning.
- **BREAKING**: remove or replace public methods unsupported by pinned CLI
  `0.4.9`, including arbitrary user list/get, repository/runtime get,
  attachment list-by-issue, autopilot get-run, and invalid nested autopilot
  trigger commands; document the supported migration for every removal.
- Keep singular references (`Issue.parent/project/assignee/creator` and
  analogous autopilot/run refs) outside this change; they require a later
  `LazyRef` design and are not among the 33 collection/query relations.
- Reconcile the still-incomplete D15–D17 surfaces from traced source evidence:
  profile-description updates, multi-URL workspace-repository mutations, and
  runtime usage/activity/update management. Daemon-only repository checkout
  is intentionally outside the SDK surface.
- Consolidate existing bound wrappers behind a typed private foundation and
  explicit semantic binding adapters, without changing public entity names or
  adding a dynamic relation registry.

## Capabilities

### New Capabilities

- `bound-resource-relations`: defines bound entities, the complete 33-relation
  graph, five loading strategies, query views, cache/identity/presence rules,
  refresh/prefetch, invalidation, and lifecycle errors.

### Modified Capabilities

- `sdk-surface`: changes public entity/data boundaries, resolves eager-field
  name conflicts, and removes or replaces unsupported CLI surfaces.
- `subprocess-transport`: all derived clients and relation loads share one
  bounded process runtime and lifecycle while retaining view configuration.
- `upstream-contract`: all relation operations and 19 drift corrections must
  be approved before private loader closures may call their typed services.
- `verification-and-release`: adds complete relation-matrix contract,
  component, concurrency, cache, pagination, migration, and gated live proof.
- `autopilot-resource`: reconciles the canonical autopilot requirements with
  bound entities, seeded relations, `trigger()`/`history()` behavior, and the
  removal of unsupported `get_run()`.

## Impact

- Public API: multiple entity types become bound wrappers; 33 relations and
  lazy/query types are added; conflicting fields and unsupported methods have
  documented 0.x migrations.
- Runtime: client construction, all participating resources and wire adapters,
  shared semaphore injection, per-entity lazy state, and synchronization
  change across the SDK.
- Contract/generator: every operation behind a relation and every corrected
  drift item requires pinned source evidence, exact argv/shape/presence
  semantics, compatibility classification, and deterministic generation from
  `contracts/sdk-contract.json` only.
- Tests/docs: canonical operation completeness remains authoritative;
  repeated coverage stays table-driven; live tests remain gated and separate.
- Dependencies: no new runtime or test dependency is introduced.
