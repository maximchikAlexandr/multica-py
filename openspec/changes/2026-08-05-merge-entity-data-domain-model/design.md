## Context

The SDK today splits each domain concept across up to four public types. For
`Issue` the flow is:

```text
_IssueWire (private, in _internal/wire_models.py)
  -> models.issues.Issue        (passive DTO, used by IssueChildrenResult)
  -> models.issues.IssueData    (frozen msgspec.Struct, the "data" layer)
  -> resources.issues.IssueEntity (ResourceEntity[IssueData], forwarding props + relations)
```

The same field (e.g. `title`) is declared on `IssueWire`, on the passive
`Issue` DTO, on `IssueData`, and forwarded by `IssueEntity.title`. Converters
glue them together: `issue_data_from_wire`, `issue_from_wire` (returns the
passive DTO), `_issue_data_from_issue` (DTO -> data), `_bind_issue` (data ->
entity), `IssueEntity.to_data()`, `IssueEntity.from_data()`.

The pattern repeats for every bound concept. The full inventory of
`*Entity` + `*Data` + redundant passive DTO pairs found in the codebase:

| Concept | Passive DTO (models/) | `*Data` (models/) | `*Entity` (resources/) | Wire model |
|---|---|---|---|---|
| Issue | `models.issues.Issue` | `models.issues.IssueData` | `resources.issues.IssueEntity` | `IssueWire` |
| Project | `models.projects.Project` | `models.projects.ProjectData` | `resources.projects.Project` (already the entity) | `ProjectWire` |
| Agent | `models.agents.Agent` | `models.agents.AgentData` | `resources.agents.AgentEntity` | (decodes directly to `Agent`) |
| Workspace | `models.workspaces.Workspace` | `models.workspaces.WorkspaceData` | `resources.workspaces.WorkspaceEntity` | (decodes directly to `Workspace`) |
| Skill | `models.skills.Skill` | `models.skills.SkillData` | `resources.skills.SkillEntity` | (decodes directly to `Skill`) |
| Autopilot | `models.autopilots.Autopilot` | `models.autopilots.AutopilotData` | `resources.autopilots.AutopilotEntity` | `AutopilotWire` |
| AutopilotRun | `models.autopilots.AutopilotRun` | `models.autopilots.AutopilotRunData` | `resources.autopilots.AutopilotRunEntity` | `AutopilotRunWire` |
| Squad | `models.system.Squad` | `models.system.SquadData` | `resources.squads.SquadEntity` | (decodes directly to `Squad`) |
| WorkspaceMember | `models.workspaces.WorkspaceMember` | `models.system.WorkspaceMemberData` | `resources.workspaces.WorkspaceMemberEntity` | (decodes directly to `WorkspaceMember`) |
| Comment | `models.issue_activity.Comment` | `models.issue_activity.CommentData` | `resources.issue_comments.Comment` (already the entity) | `CommentWire` |
| CommentThread | `models.issue_activity.CommentThread` | `models.issue_activity.CommentThreadData` | `resources.issue_comments.CommentThread` (already the entity) | `CommentThreadWire` |
| TaskRun | `models.issue_activity.TaskRun` | `models.issue_activity.TaskRunData` | `resources.issues.TaskRun` (already the entity) | (decodes directly to `TaskRun`) |
| Label | (none) | `models.labels.LabelData` | `resources.labels.Label` (already the entity) | (decodes directly to `LabelData`) |

Two concepts already have the entity class occupying the canonical name:
`resources.projects.Project` (a `ResourceEntity[ProjectData]`) and
`resources.issue_comments.Comment` / `CommentThread` (entities named `Comment`
/ `CommentThread`). For these the migration is mostly "absorb `*Data` into the
existing entity class and drop the passive DTO". For the rest, the entity
class is renamed to the canonical name and absorbs the `*Data` fields.

The public surface is pinned by `tests/contract/test_bound_public_surface.py`
(an export table mapping `multica_py.Issue -> IssueEntity`, `AgentData ->
AgentData`, etc.), `tests/contract/test_bound_public_docs.py` (doc string
checks), `tests/contract/test_public_invariants.py` (the
`assert_public_annotations_precise` helper with `IssueEntity` in its
resolution namespace), `tests/cases/operations.py` (the canonical
`OPERATION_CASES` table — 207 case IDs, 123 canonical entries, 123 unique
`sdk_method`s, 77 unique `contract_operation_id`s), and
`tests/unit/resources/test_operations.py::test_discovered_public_methods`
(asserts the discovered set equals the canonical set; no allowlist). The
invariant this change must preserve is "the discovered set equals the
canonical set; no canonical `sdk_method` is renamed" — not a hardcoded
count. The
`RelationMetadata` dataclass in `models/relations.py` types
`unstaged: tuple[IssueEntity, ...]` under a `TYPE_CHECKING` import.

Constraints carried over from the existing specs and AGENTS.md:

- No CLI, transport, subprocess, argv, or generated-contract change.
- No public resource method renamed, split, or removed (the
  discovered-public-methods invariant must stay green).
- No request, filter, or reorder model removed; `IssueSummary` stays a
  distinct partial-response type.
- `uv run mypy src` and `uv run mypy tests` pass; no `Any` leaks; test helpers
  live under the typed `tests.*` override.
- Tests reuse the existing table-driven pattern (`OperationCase`,
  `ArgvCase`, `DecodeCase`, `CommandCase`); coverage grows as new rows, not
  new files. Only stdlib + pytest.
- Default suite is offline (`uv run pytest -m "not live"`); live tests stay
  gated with their triple marker.

## Goals / Non-Goals

**Goals:**

- One public immutable class per full domain concept, named after the concept.
- Public domain fields declared once, frozen, on the unified class.
- Private `_client` and lazy-relation caches on the same class, excluded from
  equality, repr, and serialization.
- Attached and detached instances use the same class; operations requiring a
  client raise `DetachedEntityError` on a detached instance.
- Explicit `to_json`/`from_json`/`to_dict`/`from_dict` and `detach()` replace
  `to_data()`/`from_data()`.
- Wire models become private `_...Wire` and remain only where they normalize;
  direct decode into the unified class where the CLI output already matches.
- Remove `ResourceEntity` (public) and the `*Data`/`*Entity`/passive-DTO
  duplication; replace with a minimal private `_BoundEntity` helper if needed.
- Keep the 33-relation inventory, the request/filter models, `IssueSummary`,
  and all resource method names unchanged.

**Non-Goals:**

- No merging of create/update/assignment/filter/reorder request models into the
  domain class.
- No exposing wire models publicly.
- No moving transport or CLI argv construction into domain classes.
- No identity map, auto-sync, globally mutable entities, shared field
  registry, generic field schema, metaclass, partially-loaded full entity,
  `loaded_fields`, lazy scalar properties, or auto-request-on-attribute-access.
- No retaining `*Data` as `*Snapshot` without a proven distinct serialization
  contract. (None exists today; the migration removes `*Data` outright.)
- No removing `IssueSummary` or the five list-backed relations that yield it.
- No public base class (`_BoundEntity` stays private; users do not subclass it).
- No change to `MulticaClient`, `ClientConfig`, `CliTransport`, the generated
  contract, or the upstream-contract pipeline.

## Decisions

### Decision 1: One unified class per concept, frozen domain fields + private runtime state

Each unified class is a `@dataclass(frozen=True, slots=True)` (per the issue's
proposed design) OR a `msgspec.Struct(frozen=True, kw_only=True)` (matching the
existing `*Data` shape). We choose **`msgspec.Struct`** for the unified class
because:

- The existing `*Data` classes are already `msgspec.Struct, frozen=True,
  kw_only=True` and the codebase standardizes on msgspec for all model types
  (the closed-types spec requirement and `test_models_are_frozen`).
- `msgspec.Struct` gives us `UNSET` semantics, typed decoding, and
  `msgspec.json.decode` / `encode` for free, which we need for
  `to_json`/`from_json`.
- A `@dataclass` would force us to re-implement frozen validation, JSON
  round-trip, and `kw_only` behavior that msgspec already provides.

The private `_client` and lazy-relation cache fields use
`msgspec.field(default_factory=...)` with `name="..."` aliasing so they are
excluded from default decoding and from `to_json`. Concretely:

```python
class Issue(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    title: str
    status: IssueStatus
    description: str | None = None
    # ... public domain fields ...
    label_names: tuple[str, ...] = ()
    metadata_snapshot: tuple[IssueMetadataItem, ...] = ()
    attachments: tuple[AttachmentResult, ...] = ()
    # private runtime state — excluded from equality/repr/serialization
    _client: MulticaClient | None = msgspec.field(default=None, name="_client")
    _comments: LazyCollection[Comment] | None = msgspec.field(default=None, name="_comments")
    # ... other lazy caches ...
```

**Excluding runtime state from equality/repr/serialization:** msgspec's
`to_json` only encodes configured struct fields. We mark runtime fields with a
private name (`_client`, `_comments`, ...) and configure the struct to omit
them from `repr` and `eq`. msgspec does not have a built-in `repr=False` /
`compare=False` per-field flag, so we implement `__eq__`/`__hash__`/`__repr__`
on the private `_BoundEntity` helper to compare/encode only the public
fields. The public fields are enumerated once via a class-level
`_PUBLIC_FIELDS: tuple[str, ...]` (derived from `__struct_fields__` minus the
runtime fields). This is a small, explicit helper — not a generic framework.

**Mutable memo dict (`Issue._recent_threads`):** `Issue._recent_threads` is
not a single `LazyCollection | None` but a mutable memoization map keyed by
`(limit, cursor)`. It is declared as
`_recent_threads: dict[...] = msgspec.field(default_factory=dict, name="_recent_threads")`
and updated by mutating the dict in place — the frozen struct holds the dict
reference, and the dict's contents are mutable even though the struct field
itself cannot be reassigned.

**Why not `@dataclass(frozen=True, slots=True)` as the issue suggests:**
`dataclass` would require us to hand-roll JSON encode/decode, `kw_only`
defaults, and `UNSET` handling that msgspec already gives us. The codebase
standardizes on msgspec for all models (`test_models_are_frozen` walks
`msgspec.Struct` subclasses only). Mixing one `@dataclass`-based entity in
would break that invariant and force a parallel serialization path. We keep
msgspec and add the runtime-state exclusion explicitly.

**Conditional seed kwargs (`Autopilot.triggers`/`subscribers`):** msgspec
auto-generates `__init__` from the struct fields, so the unified `Autopilot`
declares `triggers`/`subscribers` as kw-only fields defaulting to
`msgspec.UNSET`. The conditional seed logic (build a `LazyCollection` only
when the caller passed a non-`UNSET` value, otherwise leave the cache
unloaded) cannot be expressed as a static `default_factory`. The unified
class therefore implements `__post_init__` and uses `object.__setattr__` to
build the seeded `LazyCollection` when `triggers`/`subscribers` is not
`msgspec.UNSET`; the msgspec-generated `__init__` still accepts the kwargs
unchanged. The implementer does not hand-write `__init__`.

### Decision 2: A minimal private `_BoundEntity` helper, not a public base

`models/__init__.py` currently exposes `ResourceEntity[TData]` as a public
generic base. The issue asks us to remove it or replace it with a private
`_BoundEntity`. We replace it with a private mixin class in
`src/multica_py/models/_bound.py`:

```python
class _BoundEntity(msgspec.Struct, frozen=True, kw_only=True):
    _client: MulticaClient | None = msgspec.field(default=None, name="_client")

    def _require_client(self, *, entity_type: str, entity_id: str, relation_name: str) -> MulticaClient:
        if self._client is None:
            raise DetachedEntityError(entity_type, entity_id, relation_name)
        return self._client

    def detach(self) -> Self:
        return msgspec.structs.replace(self, _client=None)  # plus cache clears per subclass
```

Each unified class extends `_BoundEntity` and adds its lazy caches as private
fields. `_BoundEntity` is private (underscore prefix), not exported in
`multica_py.__all__`, and not subclassed by users. The existing
`client._BoundEntity` Protocol (which only needs `._client`) stays unchanged
and is satisfied by the new `_BoundEntity` mixin.

**Equality / repr / serialization:** `_BoundEntity` defines
`__eq__`/`__hash__`/`__repr__` that operate on the public fields only
(discovered via `__struct_fields__` minus a `_RUNTIME_FIELDS` classvar each
subclass sets). `to_json` uses `msgspec.json.encode` with a hook that drops
runtime fields; `from_json` decodes into the public shape and constructs with
`_client=None`. `to_dict` / `from_dict` use `msgspec.structs.to_builtins` /
`from_builtins` scoped to public fields.

**Alternative considered:** drop the base class entirely and inline
`_require_client` / `detach` on each unified class (13 classes). Rejected:
duplicates the same 5-line `_require_client` 13 times, drifts, and the issue
explicitly allows "retain a minimal private base class only if several
entities still share meaningful runtime behavior" — they do (all 13 share
the client-reference + lazy-cache pattern).

### Decision 3: Wire models become private `_...Wire`, retained only where they normalize

Rename the public-ish `*Wire` classes in `_internal/wire_models.py` to
`_...Wire` (they are already module-internal, but the rename makes the intent
explicit). Keep a wire model only where it does at least one of: field rename
(`parent_issue_id -> parent_id`), `UNSET` normalization (`msgspec.UNSET ->
()`), nested object conversion (`labels: tuple[LabelData, ...] ->
label_names: tuple[str, ...]`), validation, or schema isolation.

| Concept | Wire model | Why kept / why removed |
|---|---|---|
| Issue (full) | `_IssueWire` | kept: `UNSET` normalization for `pull_requests`/`children`/`labels`/`metadata`/`attachments`; renames `parent_issue_id -> parent_id`; converts `labels: tuple[LabelData] -> label_names: tuple[str]` and `metadata: dict -> metadata_snapshot: tuple` |
| Issue summary | `_IssueSummaryWire` | kept: same `UNSET` + rename + nested conversion for the list path |
| Autopilot | `_AutopilotWire` | kept: `UNSET` for `subscribers`; the get envelope seeds triggers/subscribers |
| Autopilot run | `_AutopilotRunWire` | kept: distinct run shape with `trigger_payload`/`result` JSON values |
| Project | `_ProjectWire` | kept: renames `title -> name` |
| Comment | `_CommentWire` | kept: renames `content -> body`, `parent_id -> thread_id` |
| Comment thread | `_CommentThreadWire` | kept: nested comment conversion |
| Project resource | `_ProjectResourceRecordWire` | kept: validates `resource_type == "local_directory"`, resolves absolute path |

Concepts that decode directly into the public model today (Agent, Workspace,
Skill, Squad, WorkspaceMember, TaskRun, LabelData) keep doing so — no wire
model is introduced for them. The existing direct-decode calls
(`_run_json_decode(..., Agent)`, `... , Workspace`, `... , Skill`, `... ,
Squad`, `... , WorkspaceMember`, `... , TaskRun`, `... , LabelData`) now
decode into the unified class (which carries the same fields).

### Decision 4: Converters construct the unified class directly

`*_from_wire` helpers construct the unified class directly. The DTO round-trip
helpers are removed:

- `issue_data_from_wire` -> `_issue_from_wire(wire) -> Issue` (unified).
- `issue_from_wire` (returned the passive DTO) -> removed; callers that needed
  the passive DTO (`IssueChildrenResult.children`, `.unstaged`) now take
  `Issue` (unified) directly.
- `_issue_data_from_issue` -> removed.
- `_autopilot_data_from_model` -> removed; `_autopilot_from_wire(wire) ->
  Autopilot` constructs the unified class directly.
- `autopilot_run_data_from_model` -> removed; `_autopilot_run_from_wire(wire)
  -> AutopilotRun` constructs the unified class.
- `_comment_data` / `_thread_data` -> removed; `_bind_comment` /
  `_bind_thread` construct the unified `Comment` / `CommentThread` directly
  from the wire model.
- `_bind_workspace_member` -> constructs `WorkspaceMember` (unified) directly.
- `Project._bind_project` -> constructs `Project` (unified) directly from
  `_ProjectWire` (no `ProjectData` intermediate).

`IssueChildrenResult.children` and `.unstaged` become `tuple[Issue, ...]`
(unified). `RelationMetadata.unstaged` becomes `tuple[Issue, ...]`.

### Decision 5: Serialization replaces `to_data()` / `from_data()`

The unified class exposes:

```python
def to_dict(self) -> dict[str, object]: ...      # public fields only
@classmethod
def from_dict(cls, data: dict[str, object]) -> Self: ...  # _client=None
def to_json(self) -> str: ...                     # public fields only
@classmethod
def from_json(cls, payload: str | bytes) -> Self: ...  # _client=None
def detach(self) -> Self: ...                     # _client=None, caches cleared
```

Only public domain fields are serialized. `_client`, lazy caches, locks, and
loaders are excluded. `detach()` returns the same class with `_client=None`
and relation caches reset to their unloaded state. This replaces
`ResourceEntity.to_data()` / `from_data()` and the implicit "data is a pure
client-free container" guarantee — the unified class is the container, and
`detach()` / `to_dict()` produce the client-free view explicitly.

### Decision 6: Public export surface shrinks

`src/multica_py/__init__.py` changes:

- Drop: `ResourceEntity`, `AgentData`, `AutopilotData`, `AutopilotRunData`,
  `CommentData`, `CommentThreadData`, `IssueData`, `LabelData`, `ProjectData`,
  `ProjectResourceData`, `SkillData`, `SquadData`, `TaskRunData`,
  `WorkspaceData`, `WorkspaceMemberData`.
- Keep / add: `Issue`, `Project`, `Agent`, `Workspace`, `Skill`, `Autopilot`,
  `AutopilotRun`, `Squad`, `WorkspaceMember`, `Comment`, `CommentThread`,
  `TaskRun`, `Label`, `IssueSummary`, `IssueChildrenResult`,
  `ProjectResourceRecord`, `LocalDirectoryResourceRef`, all request/filter
  models, all relation types, all enums, all exceptions, `MulticaClient`,
  `ClientConfig`, `ManagedProcess`, `Unset`.
- The `as` aliases (`AgentEntity as Agent`, `IssueEntity as Issue`, ...) are
  replaced by direct imports of the unified classes (which now live under
  their canonical names in `resources.*` or `models.*`).

`tests/contract/test_bound_public_surface.py::PUBLIC_EXPORT_CASES` is
rewritten to the new table; the parametrized tests still run and pin the new
surface. `test_models_package_exports_only_non_runtime_relation_types` keeps
passing (the `models/__init__.py` `__all__` shrinks but still has no `_`-prefixed
entries).

### Decision 7: Location of the unified class definitions

The `*Entity` classes already live in `resources/*.py` and carry the
lazy-relation behavior. The `*Data` classes live in `models/*.py`. To keep the
diff small and the relation loaders next to the resources that own them, the
**unified class stays in `resources/*.py`** (renamed from `*Entity` to the
canonical name). `models/*.py` keeps the request/filter/summary/enum-support
types and the relation infrastructure. This avoids moving 13 classes between
modules and keeps the lazy-relation loaders co-located with their resources.

The passive DTOs in `models/*.py` (`models.issues.Issue`,
`models.projects.Project`, `models.agents.Agent`, `models.workspaces.Workspace`,
`models.skills.Skill`, `models.autopilots.Autopilot`,
`models.autopilots.AutopilotRun`, `models.system.Squad`,
`models.system.WorkspaceMember`, `models.issue_activity.Comment`,
`models.issue_activity.CommentThread`, `models.issue_activity.TaskRun`) are
removed. Callers that imported the passive DTO name (`models.issues.Issue`)
now import the unified class from `multica_py` (`from multica_py import Issue`)
or from the resource module (`from multica_py.resources.issues import Issue`).

### Decision 8: Tests update in place, no new framework

- `tests/contract/test_bound_public_surface.py` — `PUBLIC_EXPORT_CASES` is
  rewritten to the unified names; `UNSUPPORTED_RELATION_CASES` and
  `SINGULAR_RELATION_CASES` reference the unified class; the
  `_consumer_type_examples` function body updates `IssueEntity -> Issue`,
  `AgentEntity -> Agent`, etc.
- `tests/contract/test_public_invariants.py` — the
  `assert_public_annotations_precise` resolution namespace swaps
  `IssueEntity -> Issue`; `_DIRECT_KEYWORD_METHODS` is unchanged (no method
  renamed).
- `tests/contract/test_bound_public_docs.py` — `MIGRATION_CASES` and
  `EXAMPLE_CASES` update `IssueData.label_names -> Issue.label_names`,
  `IssueEntity.attachments -> Issue.attachments`, `issue.to_data ->
  issue.to_json` (or `to_dict`); the `docs/migration.md` content is updated to
  match.
- `tests/cases/operations.py` — `assert_result` closures referencing
  `IssueEntity`/`IssueData` update to `Issue`; the canonical method count and
  case IDs do not change (no method renamed).
- `tests/unit/resources/test_*_relations.py` and `test_issues.py` — import
  the unified class names; the mock-transport assertions are unchanged
  (argv/transport behavior is unchanged).
- `tests/unit/resources/test_direct_keyword_arguments.py` — unchanged (no
  method renamed).
- `tests/live/test_smoke.py` — import unified names; the smoke calls are
  unchanged.
- New coverage: add `OperationCase`/`DecodeCase` rows asserting
  `Issue.from_json(issue.to_json()) == issue.detach()` and that
  `Issue(...)` with `_client=None` raises `DetachedEntityError` on
  `issue.comments`. Add a `DecodeCase` row per unified class for the
  `to_json`/`from_json` round-trip.

### Decision 9: Migration is one breaking change, no aliases

The SDK is alpha. We do not ship `IssueData = Issue` aliases (the unified
object carries private runtime state and would violate the old "pure
client-free data container" guarantee of `IssueData`). `docs/migration.md`
records the full rename table and the `to_data() -> to_json()/to_dict()` move.
The single breaking change lands in one branch.

## Risks / Trade-offs

- **Risk:** msgspec `Struct` does not natively support `compare=False` /
  `repr=False` per field, so equality/repr/serialization must be hand-written
  on `_BoundEntity` to exclude `_client` and lazy caches.
  → **Mitigation:** one small `_BoundEntity` mixin implements `__eq__`,
  `__hash__`, `__repr__`, `to_dict`, `from_dict`, `to_json`, `from_json`,
  `detach` against a per-class `_PUBLIC_FIELDS` tuple. Tests assert
  `Issue(..., _client=c) == Issue(..., _client=None)` and that
  `to_json()` omits `_client`.
- **Risk:** Lazy-relation caches are mutable private fields on a `frozen`
  msgspec struct. msgspec frozen structs forbid attribute assignment after
  init.
  → **Mitigation:** lazy caches are stored as `msgspec.field(default=None)`
  and mutated via `object.__setattr__` (the existing `ResourceEntity` pattern
  already does this through `__init__` assignment; we keep the same escape
  hatch). Alternatively, lazy caches can live in a side `dict` keyed by id —
  rejected, it reintroduces an identity map. The `object.__setattr__` escape
  on a frozen struct is the existing pattern and is acceptable for cache
  state that is not part of equality/repr/serialization.
- **Risk:** Removing `*Data` breaks downstream code that imports it.
  → **Mitigation:** alpha SDK, breaking change is expected; `migration.md`
  records the table. No alias is shipped because the semantic guarantee
  changes (the unified class is not a pure client-free container).
- **Risk:** The 13-class migration is large; doing it in one commit risks a
  half-green suite.
  → **Mitigation:** tasks are ordered one concept at a time (Issue first as
  the most entangled, then Project, then the rest), each landing green before
  the next starts. The contract tests are updated alongside each concept.
- **Risk:** `RelationMetadata.unstaged` typed as `tuple[Issue, ...]` creates
  an import cycle (`models.relations` -> `resources.issues.Issue`).
  → **Mitigation:** keep the existing `TYPE_CHECKING` import pattern; the
  runtime type stays `tuple[object, ...]` via `TYPE_CHECKING` guard, as today.
- **Trade-off:** the unified class stays in `resources/*.py` (not
  `models/*.py`) so the lazy loaders stay co-located with their resources.
  This means `from multica_py.resources.issues import Issue` is the canonical
  import path, re-exported from `multica_py`. The issue's example showed
  `Issue` as a standalone dataclass; we keep it as a msgspec struct in the
  resource module for co-location, re-exported from the top package.

## Migration Plan

- One breaking change, no deprecation aliases. Lands in
  `feat/merge-entity-data-domain-model`.
- Order: (1) shared `_BoundEntity` + serialization helper, (2) `Issue` (most
  entangled — `IssueChildrenResult`, `RelationMetadata`, 8 relations), (3)
  `Project`, (4) `Agent`, (5) `Skill`, (6) `Autopilot` + `AutopilotRun`, (7)
  `Squad` + `WorkspaceMember`, (8) `Workspace`, (9) `Comment` +
  `CommentThread` + `TaskRun` + `Label`, (10) wire renames + converter
  cleanup, (11) public exports + docs, (12) final verification.
- Each step lands green: `uv run pytest -m "not live"`, `uv run mypy src`,
  `uv run mypy tests`, `uv run ruff check`, `uv run ruff format --check`.
- Rollback: revert the branch; no wire, storage, or persisted-state impact.

## Open Questions

None. The scope, class shape (msgspec.Struct + private `_BoundEntity`),
serialization surface (`to_json`/`from_json`/`to_dict`/`from_dict`/`detach`),
wire-retention table, and the no-alias decision are settled by the proposal
and the existing codebase constraints.