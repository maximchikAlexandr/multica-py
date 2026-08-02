## Context

At `main` commit `9a87967`, services return detached frozen `msgspec.Struct`
values. `BaseResource` only executes/decode commands; `with_*()` creates a new
transport and semaphore; nested services exist but are reachable from the
client rather than a bound parent. Issue #14 identifies 26 services, 33 safe
collection/query relations, and 19 contract divergences against Multica CLI
`0.4.9` at upstream commit `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`.

The issue predates the merged `issue-list-pagination` change, so
`IssueListFilter.project_id/offset` and public `IssueListPage` are existing
inputs, not new work. All other claims must be revalidated against current
`main`, the pinned source, and verified response fixtures before editing the
approved contract.

## Goals / Non-Goals

**Goals:**

- Deliver the complete 33-relation roadmap from issue #14.
- Correct the 19 prerequisite command/shape/presence divergences first.
- Provide one coherent bound-entity, identity, cache, pagination, query,
  refresh, prefetch, invalidation, and lifecycle model.
- Ensure private relation loaders call approved typed services and never raw argv.
- Avoid hidden workspace scans and per-child N+1 relations.

**Non-Goals:**

- Singular `LazyRef` relations.
- Relations unsupported by server-side filter/batch capability:
  `Project.autopilots`, agent/squad autopilots, `Label.issues`, `Skill.agents`,
  `Runtime.agents`, `Repository.projects`, `Issue.attachments`, and arbitrary
  workspace users.
- Automatic persistence or mutation through entity attribute assignment.
- TTL/distributed cache coherence or asynchronous APIs.

## Decisions

### 1. Contract correctness is a hard phase gate

Before a relation is exposed, its direct service operation must have green
approved argv and decoder fixtures. Phase 0 corrects:

| ID | Legacy surface / defect | Fixed disposition | Operation / shape | Required tests |
|---|---|---|---|---|
| D01 | `IssueListFilter` lacked project/offset | Keep merged fix | `issues.list`; `--project`, `--offset` | `D01-positive`, `D01-omit`, `D01-negative-offset` |
| D02 | issue list discarded page metadata | Keep merged fix | `IssueListPage(issues,total,limit,offset,has_more)` | `D02-full`, `D02-legacy-omitted` |
| D03 | children decoded a bare stage list | Change | `issues.children`; `IssueChildrenResult(children,total,child_stages,unstaged)` | `D03-grouped`, `D03-malformed` |
| D04 | pull requests expected a bare list | Change | `issues.pull_requests`; extract `pull_requests` wrapper | `D04-wrapper`, `D04-malformed` |
| D05 | metadata expected entry list | Change | `issues.metadata.list`; decode JSON object to typed mapping | `D05-object`, `D05-list-rejected` |
| D06 | run messages used issue positional + `--run-id` | Change | `issues.run_messages(task_run_id, *, issue_id=None)` → `issue run-messages <task_run_id> [--issue <issue_id>]` | `D06-task`, `D06-task-issue`, `D06-legacy-rejected` |
| D07 | rerun/cancel used issue plus run ID | Change | `issues.rerun(issue_id)`; `issues.cancel_task(task_id)` | `D07-rerun`, `D07-cancel`, `D07-legacy-rejected` |
| D08 | `agent skill` singular group | Change | `agents.skills.list/set` → `agent skills list/set` | `D08-list`, `D08-set`, `D08-singular-rejected` |
| D09 | `skill file` singular group | Change | `skills.files.*` → `skill files ...` | `D09-crud`, `D09-singular-rejected` |
| D10 | autopilot get decoded bare object | Change | `autopilots.get`; `AutopilotGetWire(autopilot,triggers)` | `D10-envelope`, `D10-bare-rejected` |
| D11 | `autopilots.run` used nonexistent command | Rename/change | `autopilots.trigger(id)` → `autopilot trigger <id>` | `D11-trigger`, `D11-run-absent` |
| D12 | `autopilots.get_run` has no upstream command | Remove | no replacement operation; use `history()` | `D12-not-discoverable`, `D12-migration` |
| D13 | legacy nested trigger list/create/delete | Replace | read from get; `trigger_add/update/delete` → `trigger-add/update/delete` | `D13-seed`, `D13-mutations`, `D13-legacy-absent` |
| D14 | attachment list/upload modeled issue + `--file` | Remove/change | remove `attachments.list`; `upload(path: Path, *, task_id: str | None = None)` → `attachment upload <path> [--task <id>]`; `download(attachment_id, *, output_dir: Path)` → `attachment download <id> --output-dir <dir>` | `D14-list-absent`, `D14-upload`, `D14-download` |
| D15 | arbitrary `users.list/get` unsupported | Remove/replace | expose governed `users.profile_get/profile_update`; workspace membership uses `Workspace.members` | `D15-profile`, `D15-arbitrary-absent` |
| D16 | repository get/id/branch model unsupported | Remove/change | remove `repositories.get`; list/add/remove/checkout use URL and optional `ref` | `D16-list`, `D16-checkout-ref`, `D16-get-absent` |
| D17 | runtime get unsupported | Remove | retain governed list/usage/activity/update/rename/delete; no `get` | `D17-supported`, `D17-get-absent` |
| D18 | avatar used upload/`--image` | Change | `agents.avatar(agent_id, file)` → `agent avatar <id> --file <path>` | `D18-avatar`, `D18-legacy-rejected` |
| D19 | missing embedded fields collapsed to empty | Change | wire-only `msgspec.UNSET`; seed only catalogued complete fields | `D19-missing`, `D19-empty`, `D19-value` |

These IDs are closed scope. Newly discovered drift requires a spec amendment
or a follow-up change and MUST NOT be absorbed into D19. Items are reconciled
to the issue matrix rather than accepted by name. Every
positional/flag input is traced through upstream `RunE` and helpers to its
path/query/body/process destination. Unsupported public surfaces are removed
or replaced as intentionally breaking contract decisions, not silently kept.

Exact callable decisions for D09 and D13–D18 are:

| ID | Final Python signature | Exact command template | Result / validation |
|---|---|---|---|
| D09 | `skills.files.list(skill_id: str) -> tuple[SkillFile, ...]` | `skill files list <skill_id> --output json` | nonblank ID; typed tuple |
| D09 | `skills.files.upsert(skill_id: str, path: str, content: str) -> SkillFile` | `skill files upsert <skill_id> --path <path> --content <content> --output json` | nonblank ID/path; content preserves empty string |
| D09 | `skills.files.delete(skill_id: str, file_id: str) -> None` | `skill files delete <skill_id> <file_id>` | both IDs nonblank |
| D13 | `autopilots.trigger_add(autopilot_id: str, request: AutopilotTriggerCreate) -> AutopilotTrigger` | `autopilot trigger-add <id>` plus governed request flags | replaces legacy trigger create; nonblank ID |
| D13 | `autopilots.trigger_update(autopilot_id: str, trigger_id: str, request: AutopilotTriggerUpdate) -> AutopilotTrigger` | `autopilot trigger-update <id> <trigger-id>` plus present request flags | `Unset` omits; IDs nonblank |
| D13 | `autopilots.trigger_delete(autopilot_id: str, trigger_id: str) -> None` | `autopilot trigger-delete <id> <trigger-id>` | IDs nonblank |
| D14 | `attachments.upload(path: Path, *, task_id: str | None = None) -> AttachmentResult` | `attachment upload <path> [--task <id>] --output json` | local path; task omitted uses CLI context |
| D14 | `attachments.download(attachment_id: str, *, output_dir: Path) -> Path` | `attachment download <id> --output-dir <dir> --output json` | nonblank ID; decoded path |
| D15 | `users.profile_get() -> UserProfile` | `user profile get --output json` | replaces arbitrary get/list |
| D15 | `users.profile_update(request: UserProfileUpdate) -> UserProfile` | `user profile update` plus present governed flags and `--output json` | `Unset` omits; at least one field required |
| D16 | `repositories.list() -> tuple[RepositoryRecord, ...]` | `repo list --output json` | record identity is URL/ref, not ID |
| D16 | `repositories.add(url: str, *, description: str | None = None) -> RepositoryRecord` | `repo add <url> [--description <text>] --output json` | absolute supported URL required |
| D16 | `repositories.remove(url: str) -> None` | `repo remove <url>` | exact URL required |
| D16 | `repositories.checkout(url: str, *, ref: str | None = None) -> RepositoryCheckoutResult` | `repo checkout <url> [--ref <ref>] --output json` | URL required; ref omitted means upstream default |
| D17 | `runtimes.list() -> tuple[RuntimeDefinition, ...]` | `runtime list --output json` | typed tuple |
| D17 | `runtimes.usage(runtime: str) -> RuntimeUsage` | `runtime usage <runtime> --output json` | nonblank runtime ref |
| D17 | `runtimes.activity(runtime: str) -> RuntimeActivity` | `runtime activity <runtime> --output json` | nonblank runtime ref |
| D17 | `runtimes.update(runtime: str, request: RuntimeUpdate) -> RuntimeDefinition` | `runtime update <runtime>` plus present governed flags and `--output json` | `Unset` omits; at least one field |
| D17 | `runtimes.rename(runtime: str, name: str) -> RuntimeDefinition` | `runtime rename <runtime> <name> --output json` | both values nonblank |
| D17 | `runtimes.delete(runtime: str) -> None` | `runtime delete <runtime>` | nonblank runtime ref |
| D18 | `agents.avatar(agent_id: str, file: Path) -> None` | `agent avatar <agent-id> --file <path>` | nonblank ID; existing local file |

`AutopilotTriggerCreate`, `AutopilotTriggerUpdate`, `UserProfileUpdate`, and
`RuntimeUpdate` are frozen request structs whose fields and flag mappings are
generated exclusively from the approved contract; the signatures above fix
their owning public method and presence policy. Phase 0 verifies source/flags
and may amend the spec if pinned evidence contradicts a row; it does not choose
a different public API during implementation.

### 2. Immutable data and runtime-bound entities are separate

Wire structs adapt to immutable `*Data` snapshots. Public ID-bearing graph
nodes `Workspace`, `Project`, `Issue`, `Agent`, `Skill`, `Squad`,
`WorkspaceMember`, `Label`, `Comment`, `CommentThread`, `TaskRun`, `Autopilot`,
and `AutopilotRun` become `ResourceEntity[TData]`
wrappers with read-only scalar properties and private context. `to_data()` is
the explicit passive snapshot boundary. Runtime state never participates in
repr/equality/hash/serialization and none of those operations triggers I/O.

This 0.x breaking change is preferred to `Bound[T]` proxies and to embedding
client state in `msgspec.Struct`, both of which obscure public typing or mix
wire and runtime state.

### 3. Independent client views with one shared semaphore

Each `MulticaClient` keeps its immutable `ClientConfig`, `CliTransport`, and
resource services. The private constructor accepts an existing
`ProcessSemaphore`; every `with_*()` method creates an otherwise independent
client view with its derived config and the same semaphore. There is no shared
runtime, family close state, transport registry, or cross-view cancellation.

Each bound wrapper privately retains exactly the originating `MulticaClient`
view; loader closures capture that view's typed service. Workspace relations
use `client.with_workspace(workspace.id)`, preserving server/profile/cwd/
environment/timeout while reusing the semaphore. Closing one view does not
close or invalidate another view.

### 4. Binding returns immutable replacement entities

`BaseResource` gains `_adapt`, `_bind_one`, `_bind_many`, `_bind_page`, and
presence-aware relation seeding. Every service response creates a new bound
wrapper over a frozen `*Data` snapshot. A later `get()` returns a new richer
wrapper; it does not mutate or reuse an object returned by `list()`.

Bound wrappers use ordinary object identity (`a == b` only when `a is b`) and
ordinary object hashing. Structural equality and serialization apply only to
`a.to_data()`. There is no identity map, snapshot rank, merge rule,
OriginScope, or cross-wrapper relation state.

Embedded collections seed relation cache only when the wire field was
explicitly present and the approved contract says it is complete. Wire
adapters use wire-only `msgspec.UNSET` to distinguish
missing, explicit empty, and non-empty.

The closed seed catalog is:

| Operation | Wire field | Relation | Complete |
|---|---|---|---|
| `autopilots.get` | `triggers` | `Autopilot.triggers` | yes |
| `autopilots.get` | `autopilot.subscribers` | `Autopilot.subscribers` | yes |

No other embedded field seeds a relation in this change. Missing remains
UNLOADED; explicit empty/non-empty in a catalogued field sets LOADED. JSON
null is rejected unless the approved wire field is nullable; zero and false
remain ordinary present scalar values.

### 5. Typed loader closures and private traversal helpers

Entity properties create one of four public lazy containers around a typed
loader closure that calls a governed resource service:

- `LazyCollection`: one list/aggregate call for workspace lists, agent skills/tasks, skill
  files, project resources, issue labels/subscribers/runs, squad members;
- `OffsetLazyCollection`: workspace/project/assignee issues and autopilot runs;
- `CursorLazyCollection`: comment thread and recent-comment query views;
- `LazyMapping`: issue metadata.

Private `_collect_offsets` and `_collect_cursors` helpers own traversal.
Aggregate extraction stays in resource wire adapters. Load closures never
store command tokens or invoke transport. Parameterized
recent/thread comment views are explicit methods/query objects, not misleading
unbounded properties.

### 6. Complete relation inventory

The single normative inventory is the 33-row table in
`specs/bound-resource-relations/spec.md`. Runtime code, contract entries, case
IDs, and tasks MUST reference those row numbers instead of maintaining a
second matrix. Missing required parent context raises
`MissingRelationContextError`; it never falls back to a broad scan.

### 7. Cache, refresh, invalidation, and concurrency

Each bound entity memoizes its relation/query objects in
`_relations[(relation_name, normalized_params)]`. Each lazy object owns one
`threading.Lock`, state, and immutable cached tuple/mapping. Property access is
zero-I/O. Iteration delegates to `all()`. `page()` performs one page, binds its
items, and does not change complete-load state. Failures remain retryable.
Concurrent calls on the same memoized lazy object serialize under its lock.

`refresh()` loads a replacement before swapping and swaps only on success.
Successful mutations call `invalidate()` only when their signature contains
the exact parent ID: project resources, agent skills, skill files, squad
members, parent-addressed comment add, issue labels/subscribers/metadata, and
autopilot triggers/subscribers. Parentless comment delete/resolve and broad
filtered collections require explicit refresh. Errors never invalidate.

Lazy state is `UNLOADED`, `LOADING`, or `LOADED`. `loaded` is true only in
LOADED. `all()`, `refresh()`, and `invalidate()` acquire the same
`threading.Lock`; refresh holds it for the whole reload, so concurrent readers
block rather than observing stale data. First-load failure returns to UNLOADED;
failed refresh retains the prior value and LOADED state. Invalidation waits for
the lock and changes LOADED→UNLOADED. This deliberately defers non-blocking
refresh and condition-variable coordination.

Offset and cursor iterators detect empty/repeated/no-progress pages.
Aggregate adapters retain secondary metadata such as child stage grouping.

### 8. Conflicting fields receive fixed migrations

The only valid before/after names are defined by the table in section 11; no
alias or alternative seed name is introduced.

### 9. Prefetch is bounded orchestration, not fake server batching

`client.prefetch(entities, selector, max_parallel=N) -> None` accepts a typed
selector `Callable[[TEntity], LazyLoadable]`, deduplicates identical selected
lazy objects, skips loaded objects, and calls `all()` with
`concurrent.futures.ThreadPoolExecutor(max_workers=N)`. `N < 1`, mixed
I/O. Only `N < 1` fails validation. Jobs are submitted in input order. After any failure, not-yet-started
futures are cancelled, running futures are awaited, and the exception at the
lowest failed input index is raised; completed successful loads remain cached.

### 10. Exact public contracts

```python
class ResourceEntity[TData]:
    def to_data(self) -> TData: ...
    @classmethod
    def from_data(cls, data: TData) -> Self: ...

class LazyCollection[T](Collection[T]):
    @property
    def loaded(self) -> bool: ...
    def all(self) -> tuple[T, ...]: ...
    def refresh(self) -> tuple[T, ...]: ...
    def invalidate(self) -> None: ...
    def __iter__(self) -> Iterator[T]: ...  # complete load
    def __len__(self) -> int: ...  # complete load
    def __contains__(self, item: object) -> bool: ...  # complete load
    @property
    def metadata(self) -> RelationMetadata: ...

class OffsetLazyCollection[T](LazyCollection[T]):
    def page(self, *, limit: int | None = None, offset: int = 0) -> OffsetPage[T]: ...

class CursorLazyCollection[T](LazyCollection[T]):
    def page(self, *, cursor: CommentCursor | None = None) -> CursorPage[T]: ...

class LazyMapping[K, V](Mapping[K, V]):
    @property
    def loaded(self) -> bool: ...
    def all(self) -> Mapping[K, V]: ...
    def refresh(self) -> Mapping[K, V]: ...
    def invalidate(self) -> None: ...
    def __getitem__(self, key: K) -> V: ...  # complete load
    def __iter__(self) -> Iterator[K]: ...  # complete load
    def __len__(self) -> int: ...  # complete load

def prefetch[TEntity](
    entities: Iterable[TEntity],
    relation: Callable[[TEntity], LazyCollection[object] | LazyMapping[object, object]],
    *,
    max_parallel: int = 4,
) -> None: ...
```

`OffsetPage[T]` contains `items`, `total`, `limit`, `offset`, and `has_more`.
Next offset is `offset + len(items)`; `has_more` is authoritative, but
`has_more=True` with an empty page raises `RelationPaginationError`.
`RelationMetadata` is frozen and contains `total: int | None = None`,
`child_stages: tuple[IssueChildStage, ...] = ()`, and
`unstaged: tuple[Issue, ...] = ()`. It is replaced only by successful
`all()`/`refresh()`, cleared by invalidation, and unchanged by `page()`.
`CommentCursor` atomically contains both opaque `before: str` and `before_id: str`;
a half-pair is invalid before I/O. `CursorPage[T]` contains `items` and
`next_cursor`. Repeated cursors raise `RelationPaginationError`.

Error hierarchy is fixed:

```python
class RelationError(MulticaError): ...
class DetachedEntityError(RelationError):
    entity_type: str; entity_id: str; relation_name: str
class MissingRelationContextError(RelationError):
    entity_type: str; entity_id: str; relation_name: str; missing_field: str
class RelationPaginationError(RelationError):
    relation_name: str
    reason: Literal["empty_page", "repeated_offset", "repeated_cursor"]
```

Client views have independent lifecycle; `CliTransport.close()` retains its
current behavior. Relation calls use the originating view and existing
transport timeout/cancellation semantics without new close errors.

### 11. Fixed public field migrations

| Before | After | Type / visibility |
|---|---|---|
| `Agent.skills` eager tuple | `AgentData.skill_refs`; `Agent.skills` relation | public `tuple[AgentSkill, ...]`; `LazyCollection[Skill]` |
| `Issue.labels` eager names | `IssueData.label_names`; `Issue.labels` relation | public `tuple[str, ...]`; `LazyCollection[Label]` |
| `Issue.children` stage summary | `IssueData.child_stages`; `Issue.children` relation | public `tuple[IssueChildStage, ...]`; `LazyCollection[Issue]` |
| `Issue.metadata` eager map | `IssueData.metadata_snapshot`; `Issue.metadata` relation | public immutable mapping; `LazyMapping[str, MetadataValue]` |
| `Autopilot.subscribers` eager tuple | `AutopilotData.subscriber_snapshot`; relation | public tuple; `LazyCollection[AutopilotSubscriber]` |

The `*Data` catalog is closed. Each row copies the exact field names, types,
defaults, and wire rename behavior of the named current frozen public model at
base commit `9a87967`, except for the explicit migration column. No implementer
may add another data type or alter an unlisted field.

| Bound wrapper | Frozen `msgspec.Struct` snapshot | Base schema | Only schema change |
|---|---|---|---|
| `Workspace` | `WorkspaceData` | current `Workspace` | none |
| `Project` | `ProjectData` | current `Project` | none |
| `Issue` | `IssueData` | current `Issue` | `labels→label_names`; stage summary→`child_stages`; eager metadata→`metadata_snapshot` |
| `Agent` | `AgentData` | current `Agent` | eager `skills→skill_refs` |
| `Skill` | `SkillData` | current `Skill` | none |
| `Squad` | `SquadData` | current `Squad` | none |
| `WorkspaceMember` | `WorkspaceMemberData` | current `WorkspaceMember` | none |
| `Label` | `LabelData` | current `Label` | none |
| `Comment` | `CommentData` | current `Comment` | none |
| `CommentThread` | `CommentThreadData` | current `CommentThread` | add private inherited `issue_id` to wrapper only, not snapshot |
| `TaskRun` | `TaskRunData` | current `TaskRun` | add private inherited `issue_id` to wrapper only, not snapshot |
| `Autopilot` | `AutopilotData` | canonical autopilot model | `subscribers→subscriber_snapshot` as specified in autopilot delta |
| `AutopilotRun` | `AutopilotRunData` | canonical run model | none |

Immutable non-bound record types keep their current frozen schemas and names:
`AgentSkill`, `AgentTask`, `SkillFile`, `SquadMember`, `RepositoryRecord`
(current repository fields corrected to URL/ref by D16), `RuntimeDefinition`,
`ProjectResourceRecord`, `Subscriber`, `MetadataValue`, `LinkedPullRequest`,
`RunMessage`, `AutopilotTrigger`, and `AutopilotSubscriber`.

Strategies, operation IDs, loaders, client references, and semaphore injection are
private. Public exports are bound entities, `*Data`, lazy containers, page/
cursor types, and relation errors only.

### 12. File ownership

| Path | Responsibility |
|---|---|
| `src/multica_py/client.py` | derived-view construction and shared `ProcessSemaphore` injection |
| `src/multica_py/_internal/relations.py` | private loaders, offset/cursor collectors, lazy state implementation |
| `src/multica_py/models/relations.py` | public lazy/page/cursor interfaces and relation errors |
| `src/multica_py/models/*.py` | immutable same-name `*Data` plus bound wrappers; no alternative snapshot names, argv, or wire parsing |
| `src/multica_py/resources/_base.py` | adapt/bind/page helpers |
| `src/multica_py/resources/*.py` | governed operation calls, aggregate adapters, precise invalidation |
| `src/multica_py/_internal/wire_models.py` | wire-only `msgspec.UNSET` presence and adapters |
| `contracts/sdk-contract.json` | sole operation/argv/shape/compatibility source |
| `src/multica_py/_generated/approved_sdk.py` | generated operation bindings only |
| `tests/unit/resources/` | public call/argv/call-count case tables |
| `tests/contract/` | wire, drift, presence, migration contracts |
| `tests/component/` | per-entity lazy state, semaphore reuse, concurrency, and prefetch flows |
| `tests/live/test_smoke.py` | representative prepared-target graph flows |

## Risks / Trade-offs

- [Large breaking surface] → Stage implementation behind green phase gates,
  document every migration, and require full offline/live proof before merge.
- [Implicit I/O becomes surprising] → Property access and passive inspection
  remain zero-I/O; only iteration/all/page/refresh/prefetch are load points.
- [Repeated list/get objects are distinct] → Treat `to_data()` as the explicit
  structural comparison boundary; callers replace an older wrapper with get result.
- [Pagination loops] → Require progress guards and adversarial fixtures for
  every paged strategy.
- [Stale caches] → Targeted mutation invalidation plus explicit refresh; no
  unsupported global coherence promise.
- [Issue #14 evidence is stale] → Revalidate every claim against current main,
  pinned source, and verified fixtures before contract edits.

## Migration Plan

1. Phase 0: correct and govern all 19 drift areas and relation operations.
2. Phase 1: shared semaphore injection, binding primitives, project vertical slice.
3. Phase 2: workspace graph.
4. Phase 3: agent/skill/squad/member graph and plural command fixes.
5. Phase 4: issue/comment/run graph, presence, aggregate/cursor/mapping adapters.
6. Phase 5: autopilot graph, conflicting/unsupported API migration, refresh,
   invalidation, bounded prefetch, documentation, and full verification.

Each phase must keep direct resource operations and completed earlier phases
green. Rollback reverts the approved contract and bound surface together and
regenerates output; generated files are never hand-edited.

## Post-review amendments

### 12. Bound-wrapper foundation stays explicit

`ResourceEntity[TData]` remains the public generic name. Its private
implementation owns the frozen data snapshot and nullable originating
`MulticaClient`, exposes `to_data()`/`from_data()`, and provides one typed
client requirement helper. Concrete entities retain explicit inherited context
and entity-local lazy caches. No dynamic `__getattr__`, identity map,
descriptor registry, or cross-entity cache is introduced.

### 13. Binding adapters are semantic and narrow

Repeated Issue summary/data, workspace-member, autopilot/run, and page binding
uses explicit typed helpers which receive the exact originating or scoped
client. They preserve immutable replacement and inherited context. A generic
string/registry binder is rejected because it conceals public types and source
ownership.

### 14. D15–D17 corrected disposition

`users.profile_get()` returns a frozen projection of reviewed `id`, `name`,
`email`, and `profile_description` fields. Frozen `UserProfileUpdate` has one
`description: str | Unset` field: `Unset` omits, including `""` emits the
description flag, and `None` is invalid. The SDK exposes neither CLI stdin/file
variants nor a name update.

`RepositoryRecord` has URL and description. Add/remove are multi-URL
workspace-registry mutations returning frozen mutation envelopes. `repo
checkout` is daemon-task-only; it requires daemon environment variables and
local daemon HTTP, so it and `RepositoryCheckoutResult` are removed.

Runtime usage/activity are tuples; usage validates days 1–365. Update requires
target-version and supports wait; rename supports machine; delete supports
cascade. Exact response fields, wire decoders, command vectors, and presence
decisions are governed in the approved contract before code.

## Open Questions

None. D15–D17 source-versus-binary disposition is explicit; raw evidence
remains review-only until approved in `contracts/sdk-contract.json`.
