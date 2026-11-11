## ADDED Requirements

### Requirement: New resource families follow the existing explicit SDK shape
The client SHALL expose explicit typed resources for issue statuses, workflows, saved views, project members, and runtime concurrency using the existing `BaseResource`, `Command`, `Page`, `ActionResult`, `msgspec.Struct`, and `OperationOptions` seams.

#### Scenario: Client registration is explicit
- **WHEN** `MulticaClient` is constructed
- **THEN** each approved top-level resource is registered and receives the same client binding and scoped options behavior as existing resources

#### Scenario: Subresources preserve ownership
- **WHEN** project member or project workflow behavior is invoked
- **THEN** it is exposed under the project resource boundary with typed methods rather than a duplicate top-level transport wrapper

### Requirement: Issue status catalog preserves open values and server constraints
The SDK SHALL model status key, name, category, color, description, icon, position, and archived state with open upstream-owned strings where future values are valid; create/update/archive/list/get methods SHALL preserve built-in immutability and occupied-archive conflict behavior.

#### Scenario: Custom status lifecycle succeeds
- **WHEN** valid create, update, get, list, and unoccupied archive calls are made
- **THEN** exact argv and typed status results preserve required fields, optional icon reset, ordering position, and archived inclusion

#### Scenario: Occupied or built-in status cannot be archived
- **WHEN** the CLI returns the reviewed conflict for an occupied or immutable status
- **THEN** the SDK raises the existing typed conflict boundary with reviewed safe fields and no retry or data loss

### Requirement: Workflow, saved-view, project-member, and concurrency inputs are exact
The SDK SHALL preserve workflow step-file channels and repeatable `old=new` mappings, saved-view pagination and field selection, strict project-member resolution, and runtime concurrency values `1..50` or explicit clear.

#### Scenario: Workflow dry-run performs no write
- **WHEN** project workflow set or workflow update is requested with dry-run
- **THEN** exact argv carries `--dry-run`, returns the reviewed plan result, and no SDK-side follow-up mutation is executed

#### Scenario: Runtime concurrency distinguishes retain, set, and clear
- **WHEN** concurrency is omitted, an integer from 1 through 50, or explicit clear
- **THEN** the SDK respectively emits no operation, `<limit>`, or `none`, and rejects booleans and out-of-range integers before transport

#### Scenario: View issue pages retain cursor and open fields
- **WHEN** a saved view is evaluated with cursor, limit, today, or selected fields
- **THEN** exact argv preserves the documented bounds and the page decoder retains unknown future status/icon strings without losing recognized issue fields

### Requirement: Retained issue and attachment surfaces adopt 0.8.2 semantics
Issue search SHALL support reviewed project and updated-time filters; PR auto-complete SHALL preserve create atomicity and update partial-confirmation behavior; comment/attachment methods SHALL retain literal paths, atomic binding, and cleanup guarantees.

#### Scenario: Issue search encodes only present filters
- **WHEN** project, updated-after, or updated-before is present or omitted
- **THEN** complete expected argv contains each supplied flag exactly once and contains no omitted flag

#### Scenario: PR auto-complete update partially fails
- **WHEN** the issue field write succeeds and the separate auto-complete setting write fails
- **THEN** the SDK reports the reviewed partial-confirmation failure without claiming rollback or atomic success

#### Scenario: Comment attachment binding fails
- **WHEN** upload succeeds but final comment binding fails
- **THEN** the SDK follows the reviewed failure cleanup, exposes no local path or secret, and does not upload the same file through a second path

### Requirement: Changed response fields retain precise public models
The SDK SHALL model reviewed `0.7.1` to `0.8.2` additive fields including attachment dimensions, usage credit millionths, creator identities, workspace pinning, nullable seen-version, task restriction/subtree metadata, and PR auto-complete state with source-proven omission and nullability.

#### Scenario: Optional additive fields are absent
- **WHEN** a retained `0.7.1` payload omits a field introduced later in the interval
- **THEN** decoding succeeds with the documented default or absence representation and does not invent a value

#### Scenario: Credit precision is retained
- **WHEN** a task usage payload contains `credits_micros`
- **THEN** the SDK exposes the exact integer millionths value without conversion through binary floating point

## MODIFIED Requirements

### Requirement: Closed public types
The SDK MUST use immutable `msgspec` models and closed public enums or primitive unions without public `Any`.

#### Scenario: Structured output stays closed and typed
- **WHEN** structured output is decoded
- **THEN** it is a typed model or documented closed primitive.
<!-- Source IDs: 001:FR-033–FR-039 -->
<!-- Modified by issue-list-pagination: `IssueListPage` is a frozen `msgspec.Struct`
     with typed `issues: tuple[IssueSummary, ...]` and closed-scalar pagination
     fields; no public `Any`. -->

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

#### Scenario: Command and approved 0.8.2 models remain closed

- **WHEN** the public surface is inspected after the `0.8.2` upgrade
- **THEN** `Command` remains an immutable generic with no public mutable state;
  each newly approved issue-status, project-member, workflow, saved-view,
  runtime-concurrency, rerun-task, or additive response concept is represented
  by one frozen typed model or documented closed primitive; and no unapproved
  public type or public `Any` is added

