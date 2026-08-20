## MODIFIED Requirements

### Requirement: Closed public types

The SDK MUST use immutable `msgspec` models and closed public enums or primitive
unions without public `Any`. Each full domain concept SHALL be represented by
one public immutable class named after the concept (`Issue`, `Project`,
`Agent`, `Workspace`, `Skill`, `Autopilot`, `AutopilotRun`, `Squad`,
`WorkspaceMember`, `Comment`, `CommentThread`, `TaskRun`, `Label`). The unified
class SHALL declare its public domain fields once, frozen, on the class. It
SHALL hold a private `_client: MulticaClient | None` and private lazy-relation
caches excluded from equality, `repr`, and serialization. The SDK SHALL NOT
expose separate `*Data`, `*Entity`, or passive DTO classes for a concept whose
state and lifecycle are the same. The SDK SHALL NOT expose a public
`ResourceEntity` generic base. Request, assignment, filter, and reorder models
(`IssueCreateRequest`, `IssueUpdateRequest`, `IssueAssignmentRequest`,
`IssueReorderRequest`, `IssueListFilter`, ...) SHALL remain separate where
they represent distinct input contracts. `IssueSummary` SHALL remain a distinct
partial-response model for `issues.list` and the five list-backed relations;
the SDK SHALL NOT construct a misleading full `Issue` from incomplete list rows.
Recursive public `JsonValue` object nodes SHALL be immutable
`Mapping[str, JsonValue]` snapshots (arrays are immutable tuples); SDK
serialization SHALL materialize ordinary JSON dict/list containers at the
`to_dict()` / `to_json()` boundary.

#### Scenario: One public class per concept
- **WHEN** a consumer imports a full domain concept
- **THEN** exactly one public class represents it (e.g. `Issue`, `Project`,
  `Agent`) and no separate `*Data`, `*Entity`, or passive DTO class for that
  concept is exported from `multica_py` or its submodules

#### Scenario: Public domain fields are declared once and frozen
- **WHEN** the unified class is inspected
- **THEN** each public domain field is declared exactly once on the class and
  the class is `msgspec.Struct, frozen=True, kw_only=True`

#### Scenario: Runtime state is private and excluded
- **WHEN** a unified instance is compared, printed, or serialized
- **THEN** `_client`, lazy-relation caches, locks, and loaders are excluded
  from equality, `repr`, `to_json`, and `to_dict`

#### Scenario: No public ResourceEntity base
- **WHEN** the public surface is inspected
- **THEN** `ResourceEntity` is absent from `multica_py.__all__` and from
  `multica_py.models.__all__`; a private `_BoundEntity` helper may exist but
  is not exported

#### Scenario: Request and filter models stay separate
- **WHEN** a create, update, assignment, reorder, or list-filter operation is
  inspected
- **THEN** its request/filter model (`IssueCreateRequest`,
  `IssueUpdateRequest`, `IssueAssignmentRequest`, `IssueReorderRequest`,
  `IssueListFilter`, ...) remains a distinct public class and is not merged
  into the unified domain class

#### Scenario: IssueSummary stays a distinct partial response
- **WHEN** `issues.list` or a list-backed relation returns rows
- **THEN** the rows are `IssueSummary` values and the SDK does not construct a
  full `Issue` with empty defaults for fields the list response omitted

#### Scenario: JSON values have immutable public snapshots
- **WHEN** a consumer reads an `AutopilotRun.trigger_payload` or `result`
  value
- **THEN** object nodes are typed as `Mapping[str, JsonValue]`, arrays are
  tuples, and recursively mutating the original input cannot change the run

#### Scenario: JSON values serialize through the SDK boundary
- **WHEN** a consumer calls `AutopilotRun.to_dict()` or `to_json()`
- **THEN** immutable Mapping/tuple snapshots are materialized as standard
  JSON dict/list containers and the result is directly serializable

### Requirement: Synchronous resource client

The SDK MUST expose one synchronous `MulticaClient` with stateless domain
resources and immutable typed models. Domain class methods on the unified
classes SHALL be thin delegates to resources; CLI command construction,
subprocess handling, and wire decoding SHALL remain in resources or shared
command infrastructure. The unified class SHALL NOT build argv, run a
subprocess, or decode wire output.

#### Scenario: Resource calls remain stateless
- **WHEN** a consumer calls a resource method or a unified-class instance
  method
- **THEN** the unified class delegates to the resource for any I/O and
  performs no hidden Active Record persistence or argv construction

#### Scenario: Domain methods delegate to resources
- **WHEN** a unified-class instance method (e.g. `Issue.add_comment`,
  `Issue.set_status`, `Project.add_local_directory`) is called on an attached
  instance
- **THEN** it delegates to the originating client's resource method and does
  not construct CLI argv or invoke the transport directly

### Requirement: Unified domain class serialization and detach

The unified class SHALL expose `to_json() -> str`, `from_json(payload: str |
bytes) -> Self`, `to_dict() -> dict[str, object]`, and `from_dict(data:
dict[str, object]) -> Self` covering only public domain fields. It SHALL
expose `detach() -> Self` returning the same class with `_client=None` and
relation caches reset to their unloaded state. The SDK SHALL NOT serialize
`_client`, lazy caches, locks, or loaders. `from_json` / `from_dict` SHALL
construct a detached instance (`_client=None`). The legacy
`ResourceEntity.to_data()` / `from_data()` boundary SHALL be removed.

#### Scenario: to_json round-trips public fields only
- **WHEN** `issue.to_json()` is decoded via `Issue.from_json(payload)`
- **THEN** the result equals `issue.detach()` on public fields and its
  `_client is None`

#### Scenario: to_dict excludes runtime state
- **WHEN** `issue.to_dict()` is inspected
- **THEN** the dict contains only public domain field keys and no `_client`,
  `_comments`, `_labels`, or other runtime-state keys

#### Scenario: detach clears client and caches
- **WHEN** `issue.detach()` is called on an attached issue
- **THEN** the result is an `Issue` with `_client is None` and any lazy
  relation caches reset to unloaded

#### Scenario: to_data and from_data are removed
- **WHEN** the public surface is inspected
- **THEN** no `to_data` or `from_data` method exists on any unified class and
  `ResourceEntity.to_data` / `from_data` are absent

### Requirement: Attached and detached instances use the same class

The same public unified class SHALL support both attached (constructed by a
resource with a client) and detached (constructed without a client)
instances. An operation requiring a client called on a detached instance SHALL
raise `DetachedEntityError` before any subprocess invocation. The SDK SHALL
NOT require a separate public `*Data` class to represent a detached instance.

#### Scenario: Attached instance delegates to resources
- **WHEN** `issue = client.issues.get("issue_123"); issue.add_comment("x")`
- **THEN** the call delegates to `client.issues.comments.add` and returns a
  bound `Comment`

#### Scenario: Detached instance raises on client-requiring operations
- **WHEN** `issue = Issue.from_json(payload); issue.add_comment("x")`
- **THEN** `DetachedEntityError` is raised before any subprocess invocation

#### Scenario: Detached instance scalar access works
- **WHEN** `issue = Issue.from_json(payload); print(issue.title)`
- **THEN** the public field is readable without a client and no I/O occurs

### Requirement: Wire models are private and retained only where they normalize

Wire models SHALL use private `_...Wire` names and SHALL be retained only
where they perform at least one of: field renaming, `UNSET` normalization,
nested object conversion, validation of CLI output, compatibility handling,
or isolation from an unstable external schema. Where the CLI output already
matches the public model, the SDK SHALL decode directly into the unified
class. Wire models SHALL NOT be exported from `multica_py` or its public
submodules.

#### Scenario: Wire models are private
- **WHEN** `_internal/wire_models.py` is inspected
- **THEN** every wire class is named with a leading underscore
  (`_IssueWire`, `_AutopilotWire`, `_ProjectWire`, `_CommentWire`, ...) and
  none is exported from `multica_py` or `multica_py.models`

#### Scenario: Wire models retained only with a reason
- **WHEN** a wire model exists
- **THEN** it performs at least one normalization (rename, `UNSET`, nested
  conversion, validation, or schema isolation) and is documented in the
  change design

#### Scenario: Direct decode where no normalization is needed
- **WHEN** the CLI output for a concept already matches the public model
  (Agent, Workspace, Skill, Squad, WorkspaceMember, TaskRun, Label)
- **THEN** the resource decodes directly into the unified class and no wire
  model is introduced for that concept

## ADDED Requirements

### Requirement: Unified domain class naming and migration

The SDK SHALL rename each `*Entity` class to the canonical domain name and
absorb the `*Data` fields into it. Redundant passive DTOs between the wire
model and the data/entity pair SHALL be removed. The migration is a single
breaking change; the SDK SHALL NOT ship `*Data = <Unified>` aliases because
the unified class carries private runtime state and does not preserve the
old pure-client-free-data-container guarantee. `docs/migration.md` SHALL
record the full rename table and the `to_data() -> to_json()/to_dict()`
replacement.

#### Scenario: Canonical names replace Entity names
- **WHEN** the public surface is inspected
- **THEN** `IssueEntity` is renamed `Issue`, `AgentEntity` is renamed `Agent`,
  `SkillEntity` is renamed `Skill`, `SquadEntity` is renamed `Squad`,
  `WorkspaceEntity` is renamed `Workspace`,
  `WorkspaceMemberEntity` is renamed `WorkspaceMember`,
  `AutopilotEntity` is renamed `Autopilot`,
  `AutopilotRunEntity` is renamed `AutopilotRun`, and the `Project` /
  `Comment` / `CommentThread` / `TaskRun` / `Label` entities already bearing
  the canonical name keep it

#### Scenario: Data classes are removed
- **WHEN** the public surface is inspected
- **THEN** `IssueData`, `ProjectData`, `AgentData`, `WorkspaceData`,
  `SkillData`, `AutopilotData`, `AutopilotRunData`, `SquadData`,
  `WorkspaceMemberData`, `CommentData`, `CommentThreadData`, `TaskRunData`,
  and `LabelData` are removed from public exports and their fields move to
  the unified class

#### Scenario: Redundant passive DTOs are removed
- **WHEN** the `models` package is inspected
- **THEN** the passive DTOs `models.issues.Issue`, `models.projects.Project`,
  `models.agents.Agent`, `models.workspaces.Workspace`,
  `models.skills.Skill`, `models.autopilots.Autopilot`,
  `models.autopilots.AutopilotRun`, `models.system.Squad`,
  `models.system.WorkspaceMember`, `models.issue_activity.Comment`,
  `models.issue_activity.CommentThread`, `models.issue_activity.TaskRun` are
  removed and the canonical name is used only by the unified class

#### Scenario: No misleading aliases
- **WHEN** the public surface is inspected
- **THEN** no `IssueData = Issue`, `AgentData = Agent`, or similar alias
  exists in `multica_py.__all__` or in any public module

#### Scenario: Migration table is documented
- **WHEN** `docs/migration.md` is reviewed
- **THEN** it contains a rename table mapping each removed `*Data`/`*Entity`/
  passive DTO name to the unified class name and records the
  `to_data() -> to_json()`/`to_dict()` replacement
