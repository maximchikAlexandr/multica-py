## MODIFIED Requirements

### Requirement: Synchronous resource client

The SDK MUST expose one synchronous `MulticaClient` with stateless domain
resources and immutable typed models. Domain class methods on the unified
classes SHALL be thin delegates to resources; CLI command construction,
subprocess handling, and wire decoding SHALL remain in resources or shared
command infrastructure. The unified class SHALL NOT build argv, run a
subprocess, or decode wire output.

For every CLI-executing public resource operation `operation(...)`, the
SDK SHALL expose a typed sibling `operation_command(...) -> Command[result]`
whose arguments, overloads, type narrowing, and validation match the eager
operation exactly. The eager operation SHALL be a thin delegation through
`operation_command(...).run()`. `Command[T]` SHALL be the only new public
type. The SDK SHALL NOT add `preview=True` parameters, union return types,
a mirrored `client.commands.*` tree, callable proxies, metaclasses, a
generic workflow/DAG API, public mutable step objects, or public
result-reference objects. Local-only methods that perform no CLI subprocess
SHALL NOT receive a command variant.

#### Scenario: Resource calls remain stateless

- **WHEN** a consumer calls a resource method or a unified-class instance
  method
- **THEN** the unified class delegates to the resource for any I/O and
  performs no hidden Active Record persistence or argv construction

#### Scenario: Domain methods delegate to resources

- **WHEN** a unified-class instance method (e.g. `Issue.add_comment`,
  `Issue.set_status`, `Project.add_local_directory`) is called on an
  attached instance
- **THEN** it delegates to the originating client's resource method and
  does not construct CLI argv or invoke the transport directly

#### Scenario: Every CLI-executing operation has a command sibling

- **WHEN** the public resource surface is discovered
- **THEN** every CLI-executing public resource method has a typed
  `*_command()` sibling whose arguments and validation match the eager
  operation, and the eager method delegates through
  `*_command(...).run()`

#### Scenario: No preview flag or mirrored namespace

- **WHEN** the public surface is inspected
- **THEN** no `preview=True` parameter, no union return type on eager
  operations, no `client.commands.*` namespace, no callable proxy, and no
  generic workflow/DAG API exists

#### Scenario: No command variant for local-only methods

- **WHEN** the public surface is inspected
- **THEN** methods that perform no CLI subprocess (e.g. `invalidate()`)
  have no `*_command()` variant and no fake command is constructed for
  them

### Requirement: Closed public types

The SDK MUST use immutable `msgspec` models and closed public enums or
primitive unions without public `Any`. Each full domain concept SHALL be
represented by one public immutable class named after the concept (`Issue`,
`Project`, `Agent`, `Workspace`, `Skill`, `Autopilot`, `AutopilotRun`,
`Squad`, `WorkspaceMember`, `Comment`, `CommentThread`, `TaskRun`,
`Label`). The unified class SHALL declare its public domain fields once,
frozen, on the class. It SHALL hold a private `_client: MulticaClient |
None` and private lazy-relation caches excluded from equality, `repr`,
and serialization. The SDK SHALL NOT expose separate `*Data`, `*Entity`,
or passive DTO classes for a concept whose state and lifecycle are the
same. The SDK SHALL NOT expose a public `ResourceEntity` generic base.
Request, assignment, filter, and reorder models (`IssueCreateRequest`,
`IssueUpdateRequest`, `IssueAssignmentRequest`, `IssueReorderRequest`,
`IssueListFilter`, ...) SHALL remain separate where they represent
distinct input contracts. `IssueSummary` SHALL remain a distinct
partial-response model for `issues.list` and the five list-backed
relations; the SDK SHALL NOT construct a misleading full `Issue` from
incomplete list rows. Recursive public `JsonValue` object nodes SHALL be
immutable `Mapping[str, JsonValue]` snapshots (arrays are immutable
tuples); SDK serialization SHALL materialize ordinary JSON dict/list
containers at the `to_dict()` / `to_json()` boundary. The new
`Command[T]` SHALL be the only additional public type and SHALL be a
generic with no public mutable state.

#### Scenario: One public class per concept

- **WHEN** a consumer imports a full domain concept
- **THEN** exactly one public class represents it (e.g. `Issue`,
  `Project`, `Agent`) and no separate `*Data`, `*Entity`, or passive DTO
  class for that concept is exported from `multica_py` or its submodules

#### Scenario: Public domain fields are declared once and frozen

- **WHEN** the unified class is inspected
- **THEN** each public domain field is declared exactly once on the class
  and the class is `msgspec.Struct, frozen=True, kw_only=True`

#### Scenario: Runtime state is private and excluded

- **WHEN** a unified instance is compared, printed, or serialized
- **THEN** `_client`, lazy-relation caches, locks, and loaders are
  excluded from equality, `repr`, `to_json`, and `to_dict`

#### Scenario: No public ResourceEntity base

- **WHEN** the public surface is inspected
- **THEN** `ResourceEntity` is absent from `multica_py.__all__` and from
  `multica_py.models.__all__`; a private `_BoundEntity` helper may exist
  but is not exported

#### Scenario: Request and filter models stay separate

- **WHEN** a create, update, assignment, reorder, or list-filter
  operation is inspected
- **THEN** its request/filter model (`IssueCreateRequest`,
  `IssueUpdateRequest`, `IssueAssignmentRequest`, `IssueReorderRequest`,
  `IssueListFilter`, ...) remains a distinct public class and is not
  merged into the unified domain class

#### Scenario: IssueSummary stays a distinct partial response

- **WHEN** `issues.list` or a list-backed relation returns rows
- **THEN** the rows are `IssueSummary` values and the SDK does not
  construct a full `Issue` with empty defaults for fields the list
  response omitted

#### Scenario: JSON values have immutable public snapshots

- **WHEN** a consumer reads an `AutopilotRun.trigger_payload` or
  `result` value
- **THEN** object nodes are typed as `Mapping[str, JsonValue]`, arrays
  are tuples, and recursively mutating the original input cannot change
  the run

#### Scenario: JSON values serialize through the SDK boundary

- **WHEN** a consumer calls `AutopilotRun.to_dict()` or `to_json()`
- **THEN** immutable Mapping/tuple snapshots are materialized as standard
  JSON dict/list containers and the result is directly serializable

#### Scenario: Command is the only new public type

- **WHEN** the public surface is inspected after this change
- **THEN** `Command` is exported from `multica_py`, is a generic with no
  public mutable state, and no other new public type is added

## ADDED Requirements

### Requirement: Command preview documentation default

The SDK documentation SHALL present the eager form as the default example
for every CLI-executing operation and SHALL document the `*_command()`
form as the inspectable alternative, explaining when command preview is
useful (debugging, scripting, audit, asserting CLI routing in tests). It
SHALL state that `commands` is always a tuple (empty for a no-op, one
item for one CLI call, ordered items/templates for a composite
operation), that preview construction performs no I/O, and that
`command.run()` executes the same immutable plan.

#### Scenario: Docs show eager form first

- **WHEN** the resource method documentation for a CLI-executing
  operation is reviewed
- **THEN** the primary example uses the eager form and a secondary
  example shows the `*_command()` form labeled as the inspectable
  alternative

#### Scenario: Docs explain the commands tuple shape

- **WHEN** the `Command` documentation is reviewed
- **THEN** it states that `commands` is always a tuple, explains the
  empty/one-item/ordered-items cases, and notes that preview performs no
  I/O while `run()` executes the same immutable plan