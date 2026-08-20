## Why

The SDK represents one domain concept through several overlapping public types.
For an issue, the data flow today is:

```text
IssueWire (private)
  -> passive Issue DTO (models.issues.Issue)
  -> IssueData (models.issues.IssueData)
  -> IssueEntity (resources.issues.IssueEntity, ResourceEntity[IssueData])
  -> forwarding scalar properties
```

The same field is declared up to four times (wire, passive DTO, `*Data`,
`*Entity` property), then forwarded by a property, and converted by helpers
(`issue_data_from_wire`, `issue_from_wire`, `_issue_data_from_issue`,
`_bind_issue`, `to_data`, `from_data`). The same pattern repeats for `Project`,
`Agent`, `Workspace`, `Skill`, `Autopilot`, `AutopilotRun`, `Squad`,
`WorkspaceMember`, `Comment`, `CommentThread`, `TaskRun`, and `Label`.
Issue #21 asks the SDK to collapse each `*Data` + `*Entity` (and the redundant
passive DTO between them) into one public immutable domain class that holds the
fields once and carries the bound behavior as thin delegates.

## What Changes

- Replace each `*Entity` + `*Data` pair with one public immutable class named
  after the domain concept (`Issue`, `Project`, `Agent`, `Workspace`, `Skill`,
  `Autopilot`, `AutopilotRun`, `Squad`, `WorkspaceMember`, `Comment`,
  `CommentThread`, `TaskRun`, `Label`).
- The unified class holds the public domain fields once (frozen) and a private
  `_client: MulticaClient | None` plus private lazy-relation caches. It is
  constructed both attached (from a resource, with a client) and detached
  (without a client) from the same class.
- Remove the redundant passive DTOs that sit between the wire model and the
  data/entity pair when they only duplicate fields (`models.issues.Issue`,
  `models.projects.Project`, `models.agents.Agent`, `models.workspaces.Workspace`,
  `models.skills.Skill`, `models.autopilots.Autopilot`,
  `models.autopilots.AutopilotRun`, `models.system.Squad`,
  `models.system.WorkspaceMember`, `models.issue_activity.Comment`,
  `models.issue_activity.CommentThread`, `models.issue_activity.TaskRun`).
  Keep the public class name on the unified bound class.
- Rename wire models to private `_...Wire` names and keep them only where they
  perform meaningful normalization (field rename, `UNSET` normalization, nested
  conversion, validation, isolation from the unstable external schema). Where
  the CLI output already matches the public model, decode directly into the
  unified class.
- Remove `ResourceEntity[TData]` as a public base; replace it with a minimal
  private `_BoundEntity` helper that holds the client reference and
  `_require_client` and excludes runtime state from equality/repr/serialization.
  Do not expose `_BoundEntity` publicly.
- Replace `Entity.to_data()` / `Entity.from_data()` with explicit serialization
  on the unified class: `to_dict()`, `from_dict()`, `to_json()`, `from_json()`.
  Public domain fields only; `_client`, lazy caches, locks, and loaders are
  excluded. Add `detach()` returning the same class with `_client=None` and
  cleared relation caches.
- Keep request, assignment, filter, and reorder models separate
  (`IssueCreateRequest`, `IssueUpdateRequest`, `IssueAssignmentRequest`,
  `IssueReorderRequest`, `IssueListFilter`, etc.).
- Keep `IssueSummary` as a distinct partial-response model for `issues.list`
  and the five list-backed relations; do not construct a misleading full `Issue`
  from incomplete list rows.
- Mutation methods on the unified class are thin delegates to resources and
  return a new unified instance when an updated representation is available
  (`set_status` returns a new `Issue`; `add_label` returns the labels tuple,
  matching today's behavior).
- CLI command construction, subprocess handling, and wire decoding stay in
  resources; the unified class never builds argv or runs a subprocess.
- Update `src/multica_py/__init__.py` exports: drop `*Data`, `*Entity` aliases,
  and `ResourceEntity`; export the unified class names.
- Update `docs/migration.md`, `docs/api.md`, `docs/service-usage.md`, and
  examples to the unified names; replace `to_data()` examples with `to_json()` /
  `to_dict()`.
- Update the contract tests (`test_bound_public_surface.py`,
  `test_bound_public_docs.py`, `test_public_invariants.py`) and the canonical
  `OPERATION_CASES` to the unified names; the discovered-public-methods
  invariant count stays valid because no resource method is renamed.

### Migration is direct, not aliased

The SDK is alpha with limited compatibility guarantees. We do not introduce
misleading `IssueData = Issue` aliases (the unified object carries private
runtime state and would violate the old "pure client-free data container"
guarantee). The migration lands in one breaking change; `docs/migration.md`
records the rename table.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdk-surface`: replace the "Bound entity data boundary" + "Closed public
  types" expectations with a single immutable domain class per concept;
  document the unified class shape, attached/detached support, explicit
  serialization, and the removal of `ResourceEntity`/`*Data`/`*Entity`.
- `bound-resource-relations`: rewrite the "Bound entity data boundary" and
  "Immutable wrapper replacement" requirements so the unified class is the
  bound wrapper; the 33-relation inventory is unchanged but the entity types
  referenced become the unified class names; `RelationMetadata.unstaged` is
  typed as `tuple[Issue, ...]` (unified) instead of `tuple[IssueEntity, ...]`.

## Impact

- `src/multica_py/models/` — remove `*Data` classes and redundant passive DTOs;
  the unified class definitions move here (or stay in `resources/` where they
  already live as `*Entity`, renamed). `models/__init__.py` drops
  `ResourceEntity` and the `*Data` re-exports.
- `src/multica_py/resources/` — each `*Entity` becomes the unified class;
  `_bind_*` helpers construct the unified class directly from the wire model
  (or directly from the CLI decode when no wire normalization is needed);
  `to_data()`/`from_data()` removed; relation loaders return the unified class.
- `src/multica_py/_internal/wire_models.py` — rename `*Wire` to `_...Wire`;
  `*_from_wire` helpers construct the unified class directly; remove the
  passive-DTO round-trip helpers (`issue_from_wire` returning a passive DTO,
  `_issue_data_from_issue`, `_autopilot_data_from_model`,
  `autopilot_run_data_from_model`, `_comment_data`, `_thread_data`).
- `src/multica_py/client.py` — `_BoundEntity` Protocol stays (it already
  matches the unified class shape); no public change.
- `src/multica_py/models/relations.py` — `RelationMetadata.unstaged` becomes
  `tuple[Issue, ...]`; the `TYPE_CHECKING` import of `IssueEntity` becomes
  `Issue`.
- `tests/` — update `tests/contract/test_bound_public_surface.py` (export
  table), `test_bound_public_docs.py` (doc strings), `test_public_invariants.py`
  (resolution namespace), `tests/cases/operations.py` (assert_result closures
  referencing `IssueEntity`/`IssueData`), and the unit/component relation
  tests importing `*Entity`. The discovered-public-methods invariant must stay
  green; no canonical method is renamed.
- `docs/` — `migration.md` gains the rename table and the
  `to_data()` -> `to_json()`/`to_dict()` note; `api.md` and `service-usage.md`
  flip to unified names; `examples/resource_relations.py` updates
  `issue.to_data` to `issue.to_json` (or `to_dict`).
- No CLI, transport, subprocess, dependency, packaging, or generated-contract
  change. No public resource method is renamed, split, or removed. No request
  class is removed. `IssueSummary` stays.