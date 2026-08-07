## Context

The checked-out `main` already contains the two foundations this change must
reuse:

- `direct-keyword-arguments` added `_resolve_request` and dual overloads to 14
  methods, but deliberately left list/filter, comment, metadata, and autopilot
  trigger requests object-only.
- PR #29 implemented `Command[T]`, 181 command-builder methods, and a closed
  test invariant over 124 canonical resource methods: every CLI-executing eager
  method has an argument-identical `*_command()` sibling and executes through
  that command plan.

The remaining inconsistencies are structural rather than transport problems.
There are four page families with different item names (`items`, `issues`,
`autopilots`, `runs`), two separate public `Page` definitions, an ad hoc
`MetadataPage`, and tuple-returning list methods. Update inputs mix `Unset` with
`None`-means-omit, so `AgentUpdateRequest`, `SkillUpdateRequest`,
`IssueUpdateRequest`, `AutopilotResource.update`, and `LabelResource.update`
cannot consistently distinguish an omitted field from an explicit clear.
Action methods currently return a mixture of `None`, `str`,
`RepositoryMutationResult`, and `RuntimeUpdateResult`; the existing
`models.common.ActionResult` is not used.

The repository's approved `contracts/sdk-contract.json` already records
signatures, mappings, response decoders, presence policies, source references,
and test vectors for governed operations. Per `AGENTS.md`, it—not extracted
evidence—is the only acceptable production contract. The design therefore
extends that approved layer instead of creating a second runtime registry.

## Goals / Non-Goals

**Goals:**

- Make typed-object and direct-keyword calls mechanically complete and
  identical across eager, command, nested-resource, and bound-entity surfaces.
- Give every all-optional update field an explicit omitted/null/empty/zero/false
  contract, with all-omitted calls returning the current entity without
  mutation; keep required-value update validation explicit.
- Normalize canonical CLI collection operations and direct resource collection
  results around one immutable sequence page API while retaining temporary
  resource-named aliases.
- Normalize action-only results around one generic wrapper without discarding
  useful typed payloads.
- Preserve the command plan as the single execution path and make return
  conventions fail closed when new operations are added.
- Keep the plan implementable with the existing `msgspec`, transport, approved
  contract, table-driven test, and documentation architecture.

**Non-Goals:**

- No new transport, HTTP client, asynchronous client, subprocess mode, or
  dependency.
- No automatic public behavior derived from upstream source extraction.
- No change to wire response shapes or Multica persistence semantics.
- No conversion of lazy relation containers (`LazyCollection`,
  `OffsetLazyCollection`, `CursorLazyCollection`, `LazyMapping`) into pages;
  they already provide a common iterable relation abstraction. Their
  relation snapshots from `.all()` remain tuples and are explicitly outside
  the page contract; their direct page loaders adopt the new page result where
  applicable.
- No removal of request classes, resource-specific page class names, or page
  item aliases in this release.
- No expansion of upstream command coverage merely because newer flags exist;
  this change normalizes the approved public fields only.

## Decisions

### Decision 1: Extend the approved operation contract with public conventions

Add a required public-convention record to each canonical entry point in
`contracts/sdk-contract.json` and its schema. The record contains:

| Field | Meaning |
|---|---|
| `category` | One of `retrieve`, `create`, `update`, `collection`, `action`, `process`, `scalar`, `mapping` |
| `response_id` | Existing or new response catalog identifier for the exact public return |
| `typed_input_id` | Governed request/filter type, or `null` |
| `input_mode` | `direct`, `dual_required`, or `dual_optional` |
| `presence_policy_ids` | Ordered field-to-policy references for update/filter inputs |
| `command_symbol` | Fully-qualified `*_command` sibling |

The existing operation ID and entry point remain the identity. The convention
record is not a parallel manifest: schema validation, contract loading, case
generation, and discovery checks consume it from the approved contract.
Handwritten canonical operations not yet generated must receive equivalent
manual records before the runtime change lands.

Why: the existing contract already owns public signatures, responses,
presence, evidence, and tests. A second Python registry would drift and violate
the repository's approved-contract boundary.

Alternative considered: infer categories from method names and annotations.
Rejected because `runtimes.update` is an action result, `auth.login` has scalar
and process overloads, metadata list is a mapping, and relation mutations can
return collection snapshots. Inference is useful only as a test that compares
against reviewed declarations.

### Decision 2: Use one generic immutable page core with compatibility subtypes

Replace the duplicate page cores with one `models.common.Page[T]`, implemented
as a frozen generic `msgspec.Struct` with:

```python
items: tuple[T, ...]
limit: int | None = None
offset: int | None = None
total: int | None = None
has_more: bool = False
next_cursor: str | CommentCursor | None = None
```

`Page[T]` implements `collections.abc.Sequence[T]` behavior through
`__iter__`, `__len__`, and typed integer/slice `__getitem__`; these methods only
read the frozen tuple. The single core becomes the public import used by
comment and metadata resources.

Existing specialized names remain concrete compatibility subtypes because
callers may import or type-check them:

| Current type | New base/shape | Compatibility member |
|---|---|---|
| `IssueListPage` | `Page[IssueSummary]` | `issues` property returns `items` |
| `AutopilotListPage[T]` | `Page[T]` | `autopilots` property returns `items` |
| `AutopilotRunListPage[T]` | `Page[T]` | `runs` property returns `items` |
| issue-activity `Page[T]` | import/re-export common `Page[T]` | `total_count` maps to `total` only if retained by upstream contract |
| `MetadataPage` | `Page[MetadataEntry]` | no ad hoc field needed |
| `IssueChildrenResult` | compatible `Page[Issue]` subtype | `children` returns `items`; stage fields remain |

The three resource-named item aliases and `children` are warning-free during
the compatibility window; docs and new code use `.items`. Removal requires a
future major release and a separate change.

Every canonical CLI collection operation and every direct resource collection
result whose current public return is `tuple[T, ...]` becomes `Page[T]`.
Existing page-returning operations populate the common fields from their wire
metadata. An unpaged array becomes `Page(items=..., total=len(items))` with
neutral limit/offset/cursor fields.
`issues.metadata.list` remains `Mapping[str, MetadataValue]`; scalar bytes,
paths, strings, and state snapshots remain scalar/retrieve results. Lazy
relation snapshots from `LazyCollection.all()`,
`OffsetLazyCollection.all()`, and `CursorLazyCollection.all()` continue
returning their existing tuples because a lazy relation container, not its
loaded snapshot, is the common relation interface. Those snapshots are not
canonical CLI collection operation/direct resource collection results; a
relation `.page()` result remains a page where that operation exists.

Why: one concrete core gives autocomplete and runtime consistency without
forcing all resource-specific metadata into a lowest-common-denominator
protocol. Sequence behavior preserves the most common tuple usages (iteration,
length, indexing) while making `.items` universal.

Alternative considered: add only `.items` properties to current page types.
Rejected because unpaged resource lists would still return tuples and the SDK
would still expose multiple incompatible metadata names and duplicate `Page`
classes.

### Decision 3: Make `ActionResult[T]` the only action wrapper

Generalize the existing frozen `ActionResult` to:

```python
class ActionResult(msgspec.Struct, Generic[T], frozen=True, kw_only=True):
    success: bool = True
    value: T | None = None
    message: str | None = None
```

Transport, validation, exit-code, and decode failures continue raising the
existing exceptions; the SDK does not convert failures into
`ActionResult(success=False)`. `success` preserves upstream successful/partial
action status where a decoded payload provides one. Void actions construct
`ActionResult[None]` after the existing command succeeds and may retain
non-secret stdout in `message` where it is already public.

The exact migrations are:

| New result | Canonical operations |
|---|---|
| `ActionResult[None]` | `agents.archive`, `agents.avatar`, `agents.restore`, `agents.skills.set`, `autopilots.delete`, `autopilots.trigger_delete`, `configuration.set`, `issues.cancel_task`, `issues.comments.delete`, `issues.comments.resolve`, `issues.comments.unresolve`, `issues.metadata.delete`, `issues.rerun`, `issues.subscribers.add`, `issues.subscribers.remove`, `labels.delete`, `projects.delete`, `projects.resources.remove`, `runtimes.delete`, `skills.delete`, `skills.files.delete`, `squads.members.add`, `squads.members.remove`, `workspaces.switch`, `workspaces.watch`, `workspaces.unwatch` |
| `ActionResult[str]` | `issues.deprioritize`; `auth.login(token=str)` |
| `ActionResult[RepositoryMutationResult]` | `repositories.add`, `repositories.remove` |
| `ActionResult[RuntimeUpdateResult]` | `runtimes.update` |
| `ManagedProcess` | `daemon.start`, `daemon.logs`, `maintenance.update`, `setup.cloud`, `setup.self_host`, and `auth.login(token=None)` |

Bound-entity and nested-resource aliases inherit the top-level result rather
than wrapping a second time. Mutations that naturally return an entity,
state snapshot, metadata entry, comment, attachment, or updated label
collection keep that natural typed result. Collection snapshots use the new
page convention.

Why: a generic wrapper provides one access path while retaining useful domain
payloads. Returning bare `None` loses acknowledgement metadata; forcing every
action to return only `None` would discard repository and runtime results.

Alternative considered: keep domain-specific action result types and define a
protocol. Rejected because callers would still need resource-specific result
knowledge and the issue explicitly asks for one convention.

### Decision 4: Make dual input structural, not a curated exception list

Retain one positional typed-object slot plus explicit keyword-only overloads.
Extend `_resolve_request` with an `allow_empty` mode:

- `allow_empty=False`: a missing object and missing keywords raises `TypeError`
  (create and required request operations).
- `allow_empty=True`: construct the model with defaults (optional filters and
  all-optional update models).
- object plus any keyword remains the existing exact `TypeError`.

Do not expose `**kwargs: Any`; implementation bodies may retain
`**kwargs: object`, but every public overload explicitly lists model fields.
The command method owns normalization and validation; the eager method remains
`return self.operation_command(...).run()`.

Existing dual-input methods remain. Add the direct form to:

- `issues.list` (`IssueListFilter`, optional-empty);
- `issues.comments.list_flat`, `list_thread`, and `list_recent`;
- `issues.metadata.query` and `set_typed`;
- top-level and bound `autopilots.trigger_add` and `trigger_update`.

Add `AutopilotUpdateRequest` and `LabelUpdateRequest`, then make
`autopilots.update` and `labels.update` dual-input. These two new models are
needed to express `Unset` consistently; they do not add fields or upstream
coverage. A test-side governed type registry identifies typed input models and
scans public eager/command annotations, including bound methods, so a future
typed request cannot remain object-only.

Why: the earlier finite scope created the inconsistency this issue removes.
Explicit overloads preserve IDE and mypy quality while a structural inventory
prevents future exceptions.

Alternative considered: accept a request object's fields through arbitrary
`**kwargs` on all methods without overloads. Rejected because it weakens
autocomplete, permits signature drift, and violates the no-public-`Any` rule.

### Decision 5: Encode update presence in models and approved field policies

All-optional update models default every mutable field to `Unset`, never `None`.
Field types then state nullability explicitly:

| Model | Non-nullable present fields | Nullable clear fields | Collection clear |
|---|---|---|---|
| `ProjectUpdateRequest` | `name` | `description` | — |
| `AgentUpdateRequest` | `name` | `description` | — |
| `SkillUpdateRequest` | `name` | `description` | — |
| `IssueUpdateRequest` | `title`, `priority` | `description`, `assignee_id`, `project_id`, `parent_id` | — |
| `AutopilotUpdateRequest` | `title`, `agent`, `priority`, `status`, `execution_mode` | `description`, `project_id`, `issue_title_template` | `subscribers=()` |
| `LabelUpdateRequest` | `name`, `color` | — | — |
| `AutopilotTriggerUpdate` | `title`, `kind` | — | — |
| `UserProfileUpdate` | — | `description` | — |

The all-optional update set is exactly `ProjectUpdateRequest`,
`AgentUpdateRequest`, `SkillUpdateRequest`, `IssueUpdateRequest`,
`AutopilotUpdateRequest`, `LabelUpdateRequest`, `AutopilotTriggerUpdate`, and
`UserProfileUpdate`. Their direct overloads mirror these annotations and an
all-omitted call is a read-only no-op.

Required-value update models are intentionally separate:

| Model | Required non-null field(s) | Optional control field | No-op contract |
|---|---|---|---|
| `ProjectResourceUpdateLocalDirectoryRequest` | `local_path` | — | omission/null rejected; no all-omitted no-op |
| `RuntimeUpdate` | `target_version` | `wait` | omission/null for `target_version` rejected; no all-omitted no-op |

The direct overloads for these models require their required keyword fields.
They are not included in the all-optional `Unset`/no-op guarantee.

The approved binding owns how a nullable clear is represented: a documented
empty flag, a dedicated clear flag, or a command-plan step such as unassign
followed by get. Before changing a nullable field, the implementer traces the
pinned upstream `RunE` path and records the mapping/source reference. Known CLI
clear affordances (`issue --parent ""`, `autopilot --project ""`, user profile
`--clear`) are candidates, not automatic approval. If no representation can
distinguish clear from omit, contract validation blocks that binding; runtime
code must not guess.

No-op update behavior applies only to the all-optional update set above. When
every mutable field is `Unset`, the command builder returns the target's
existing get/profile-get command instead of emitting a mutation with no flags.
Trigger update, which lacks a direct trigger get command, uses the approved
autopilot get command and extracts the matching trigger in the finalizer.
Required-value updates (`ProjectResourceUpdateLocalDirectoryRequest` and
`RuntimeUpdate`) always require their required non-null value and never enter
this no-op branch. No-op command previews therefore honestly show the read that
will execute only for the all-optional set.

Why: a sentinel makes omission explicit and lets `None`, `""`, `False`, `0`,
and `()` retain their normal values. Placing clear encodings in the approved
contract satisfies the repository's fail-closed upstream rules.

Alternative considered: keep `None` as omission and add per-field `clear_*`
booleans. Rejected because it multiplies resource-specific API concepts and
does not satisfy the issue's SDK-wide `None` rule.

### Decision 6: Reuse the existing command plan without a second execution path

Return adaptation happens in `Command._map`/plan finalizers. Resource command
builders remain the only place that builds argv, performs multi-step clear/no-op
plans, decodes wire values, binds entities, wraps pages/actions, and invalidates
relations. Eager methods never repeat normalization or adaptation.

The existing signature invariant in
`test_discovered_public_methods` is extended to compare the approved category
and response ID. Composite clears and no-op reads are added to
`OperationCase.expected_commands`/`expected_transport_argvs`; preview remains
redacted, immutable, and I/O-free.

Why: PR #29 already solved preview/execution drift. Reusing it avoids a broad
rewrite and directly proves the GitHub issue's eager/command equivalence.

Alternative considered: build the page/action wrapper only in eager methods.
Rejected because `command.run()` would then have a different public result.

### Decision 7: Migrate tests and docs from the same convention tables

Extend frozen table cases instead of creating per-resource test files:

- `OperationCase` gains expected category and public response ID.
- A frozen typed-input case table covers object/keyword parity and dispatch
  failures.
- A frozen all-optional update-field table covers every applicable
  omitted/null/empty/zero/false vector and its exact command plan; a separate
  required-value table covers missing/null rejection for project-resource and
  runtime updates and never expects a no-op.
- Existing canonical CLI/direct-resource collection rows change expected
  results to `Page` or `ActionResult`; relation `.all()` snapshot rows remain
  tuple assertions, and the discovery gate remains a strict set equality.
- Focused page tests cover immutability, `.items`, iteration, length, indexing,
  all metadata modes, alias identity, and the explicit tuple contract for
  relation snapshots.
- Contract documentation tests pin one SDK-wide conventions section and the
  migration matrix rather than repeating resource-specific explanations.

The offline suite remains the release authority; live tests validate a small
representative sample but do not weaken offline determinism.

## Risks / Trade-offs

- [Breaking return annotations for tuple and `None` callers] → Preserve
  sequence behavior and page aliases where possible, document `.value` and
  `.items` migrations, and release with a prominent breaking-change entry.
- [A nullable SDK field may lack a distinct CLI clear path] → Require pinned
  source tracing and an approved clear mapping before runtime code; fail the
  contract gate rather than collapsing `None` into omission.
- [A single page core could erase resource metadata] → Keep optional common
  fields plus concrete compatibility subtypes for stage/cursor metadata; test
  exact upstream round-trips.
- [Action wrapping could double-wrap bound/nested calls] → Wrap only in the
  top-level command finalizer and have bound methods map invalidation over the
  same `ActionResult`.
- [Generic `msgspec.Struct` inheritance and properties may have typing/runtime
  constraints] → Prove the model shape first with focused unit, mypy, encode,
  and decode tests; if subclassing is unsupported, use concrete frozen structs
  implementing the same fields/sequence methods rather than weakening the
  public contract.
- [Structural request discovery can misclassify response models] → Use the
  approved `typed_input_id` registry as the closed set and compare it with
  annotations; do not infer from class-name suffix alone.
- [No-op update reading current state adds one subprocess] → This is deliberate
  and inspectable; it preserves the declared entity return without issuing a
  meaningless mutation.
- [The active `cli-command-preview` OpenSpec change overlaps command
  requirements] → Treat its merged code and tests as baseline, do not rewrite
  `Command`, and reconcile duplicate normative text when changes are synced or
  archived.

## Migration Plan

1. Extend and validate the approved contract/schema with categories, response
   conventions, typed inputs, and field presence mappings for the full current
   canonical surface. Complete source tracing for every nullable clear before
   changing runtime signatures.
2. Introduce the generic common `Page[T]` and `ActionResult[T]`, public exports,
   compatibility page subtypes/aliases, and their focused type/runtime tests.
3. Convert update models and add `AutopilotUpdateRequest`/
   `LabelUpdateRequest`; land dual-input overload parity and no-op/clear command
   plans resource by resource.
4. Adapt canonical collection and action finalizers from the approved matrix,
   updating eager and command annotations together. Keep each resource slice
   green before moving to the next.
5. Migrate table-driven operation cases, component routing, contract/public
   surface tests, docs, examples, changelog, and migration guide.
6. Run the full offline, mypy, Ruff, packaging, OpenSpec, and contract
   validation chain. Live smoke remains separately gated.

Rollback is a branch revert because the SDK change does not mutate persisted
data or wire protocols. Resource-named page aliases stay for at least one
minor release and may be removed only by a separately specified major release.
The breaking action/page return changes are not silently toggled by an
environment flag; callers migrate explicitly using the documented matrix.

## Open Questions

None. Public behavior, compatibility aliases, category boundaries, and
fail-closed handling of unsupported upstream clears are settled by this design.
