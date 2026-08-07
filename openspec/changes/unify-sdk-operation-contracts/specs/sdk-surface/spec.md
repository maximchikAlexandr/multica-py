## MODIFIED Requirements

### Requirement: Dual input convention for request-bearing resource methods

The SDK SHALL support two equivalent public calling conventions on every
public method that accepts a typed request or filter: (1) a single positional
request/filter object and (2) that object's fields passed directly as
keyword-only arguments. The rule SHALL apply to both eager methods and their
`*_command()` siblings, including the same methods exposed by bound entities.
The two conventions SHALL be mutually exclusive within one call.

The governed typed-input set SHALL include
`ProjectCreateRequest`, `ProjectUpdateRequest`, `AgentCreateRequest`,
`AgentUpdateRequest`, `SkillCreateRequest`, `SkillUpdateRequest`,
`IssueCreateRequest`, `IssueUpdateRequest`, `IssueAssignmentRequest`,
`IssueReorderRequest`, `IssueListFilter`, `CommentListFlatRequest`,
`CommentListThreadRequest`, `CommentListRecentRequest`,
`MetadataListRequest`, `MetadataSetRequest`, `RuntimeUpdate`,
`ProjectResourceAddLocalDirectoryRequest`,
`ProjectResourceUpdateLocalDirectoryRequest`, `UserProfileUpdate`,
`AutopilotTriggerCreate`, `AutopilotTriggerUpdate`, and the new
`AutopilotUpdateRequest` and `LabelUpdateRequest`. A structural contract test
SHALL discover this set from the public signatures so a future typed-input
method cannot be added without both forms.

The direct keyword form SHALL be the primary form presented in documentation.
The typed-object form SHALL remain available for reuse, validation, storage,
and cross-layer assembly. No public method SHALL be renamed or split to expose
the two forms.

#### Scenario: Direct keyword arguments build the same typed input

- **WHEN** a typed-input method is called with keyword-only fields matching its
  request/filter model's names, types, defaults, and validation
- **THEN** the SDK constructs the equivalent typed object and emits the same
  command plan, argv, execution mode, stdin, timeout, and public result as the
  equivalent object call.

#### Scenario: Object call remains supported

- **WHEN** a typed-input method is called with its typed object in the single
  positional object slot
- **THEN** the call remains valid and has the same public behavior as the
  direct keyword form.

#### Scenario: Mixed input is rejected before I/O

- **WHEN** a caller supplies both the positional typed object and one or more
  direct keyword fields
- **THEN** the SDK raises `TypeError` with
  `Pass either a request object or keyword arguments, not both.` before command
  construction performs subprocess I/O.

#### Scenario: Direct fields are keyword-only

- **WHEN** a caller passes a request/filter field positionally rather than in
  the typed object slot
- **THEN** Python raises `TypeError` before any subprocess invocation.

#### Scenario: Optional filter may be omitted

- **WHEN** `issues.list()` or `issues.list_command()` is called without a
  filter object and without filter keywords
- **THEN** the SDK uses `IssueListFilter()` and emits the same unfiltered
  operation as an explicit empty filter.

#### Scenario: Required create input may not be omitted

- **WHEN** a create-style typed-input method is called without its request
  object and without its required direct fields
- **THEN** the SDK raises `TypeError` before I/O and names the missing input.

#### Scenario: Update input may contain no changed fields

- **WHEN** an update-style method is called with only its target identifier or
  with an all-`Unset` request
- **THEN** it performs no mutation and returns the current entity through the
  corresponding inspectable read command.

#### Scenario: Static signatures expose both forms

- **WHEN** eager and command method overloads are inspected or type-checked
- **THEN** both expose the exact typed-object and keyword-only forms, and the
  command return is `Command[T]` for the eager return `T`.

#### Scenario: Bound trigger methods follow the same convention

- **WHEN** `Autopilot.trigger_add` or `Autopilot.trigger_update` is called with
  a typed trigger request or equivalent direct keywords
- **THEN** both forms route to the same top-level autopilot resource command and
  preserve the same cache invalidation behavior.

### Requirement: Dual input convention documentation default

The SDK documentation SHALL present direct keyword arguments as the default
form for every typed-input method and SHALL present the typed object as the
reusable alternative. Documentation SHALL describe the exactly-one-style rule,
optional-filter empty call, update no-op call, and pre-I/O `TypeError` for
mixed input. Documentation SHALL NOT retain a list of request-object-only
exceptions.

#### Scenario: Docs show direct keyword form first

- **WHEN** a typed-input resource method is documented
- **THEN** its primary example uses direct keyword arguments and its secondary
  example uses the equivalent typed object.

#### Scenario: Docs explain reusable typed objects

- **WHEN** the SDK-wide calling convention is documented
- **THEN** it states that typed objects are useful for reuse, validation,
  storage, and cross-layer assembly without changing operation semantics.

#### Scenario: Docs contain no typed-input exception list

- **WHEN** public API documentation is checked
- **THEN** every documented typed request/filter method supports both forms and
  no method is described as request-object-only.

## ADDED Requirements

### Requirement: Presence-aware update contract

Every update-style public input SHALL distinguish omission from an explicit
value. Omitted fields SHALL use `Unset` and SHALL NOT be sent. Explicit `None`
SHALL clear a field only when that field's public update type is nullable;
`None` for a non-nullable field SHALL raise `TypeError` or `ValueError` before
I/O. Explicit empty strings, empty tuples, `False`, and `0` SHALL remain present
when accepted by the field type and SHALL never be removed by truthiness tests.

The presence-aware update models SHALL be:

- `ProjectUpdateRequest`: `name: str | UnsetType`; nullable `description`.
- `AgentUpdateRequest`: `name: str | UnsetType`; nullable `description`.
- `SkillUpdateRequest`: `name: str | UnsetType`; nullable `description`.
- `IssueUpdateRequest`: non-nullable `title` and `priority`; nullable
  `description`, `assignee_id`, `project_id`, and `parent_id`; every field also
  accepts `UnsetType`.
- `AutopilotUpdateRequest`: non-nullable `title`, `agent`, `priority`, `status`,
  and `execution_mode`; nullable `description`, `project_id`, and
  `issue_title_template`; `subscribers` is `tuple[str, ...] | UnsetType`, where
  an empty tuple explicitly clears subscribers; every field defaults to
  `Unset`.
- `LabelUpdateRequest`: non-nullable `name` and `color`, both defaulting to
  `Unset`.
- Existing `ProjectResourceUpdateLocalDirectoryRequest`,
  `AutopilotTriggerUpdate`, and `UserProfileUpdate` SHALL follow the same rule;
  user profile `description=None` SHALL explicitly clear the description.

Each nullable clear SHALL map to approved upstream behavior. If the pinned CLI
cannot represent a required clear distinctly, the SDK change SHALL fail closed
at contract validation rather than silently treating `None` as omission.

#### Scenario: Omitted update field is not sent

- **WHEN** an update request leaves a field as `Unset`
- **THEN** neither the field's flag nor any clearing action appears in the
  inspectable command plan.

#### Scenario: Explicit nullable None clears

- **WHEN** a nullable update field is passed as `None`
- **THEN** the command plan contains the approved clear representation and the
  returned entity exposes that field as cleared.

#### Scenario: None is rejected for non-nullable field

- **WHEN** a non-nullable update field such as a name, title, status, priority,
  color, or execution mode is passed as `None`
- **THEN** validation fails before subprocess I/O instead of treating the value
  as omitted.

#### Scenario: Falsey values remain present

- **WHEN** an accepted update field is explicitly `""`, `()`, `False`, or `0`
- **THEN** its approved representation is emitted and is not dropped by a
  truthiness check.

#### Scenario: Empty subscriber tuple clears subscribers

- **WHEN** `AutopilotUpdateRequest(subscribers=())` or the equivalent direct
  call is used
- **THEN** the command uses the approved clear-subscribers behavior, while an
  omitted `subscribers` field leaves the subscriber set unchanged.

#### Scenario: Empty update delegates to retrieval

- **WHEN** every mutable field is omitted
- **THEN** `update_command()` exposes the corresponding read command, `run()`
  returns the current entity, and no update command is executed.

#### Scenario: Presence behavior matches both input forms

- **WHEN** equivalent request-object and direct-keyword update calls exercise
  omitted, `None`, empty, false, and zero values
- **THEN** their command plans and returned values are identical.

### Requirement: SDK-wide operation return categories

Every canonical public operation SHALL declare exactly one category in the
approved SDK contract: `retrieve`, `create`, `update`, `collection`, `action`,
`process`, `scalar`, or `mapping`. Its eager method and `*_command()` sibling
SHALL use the response convention for that category.

- `retrieve`, `create`, and entity `update` SHALL return the corresponding
  typed entity or state snapshot whenever Multica provides one.
- `collection` SHALL return an immutable `Page[T]` or a documented compatible
  page subtype.
- `action` SHALL return `ActionResult[T]`; every operation currently returning
  `None` SHALL become `ActionResult[None]`.
- `issues.deprioritize` SHALL return `ActionResult[str]`,
  `repositories.add/remove` SHALL return
  `ActionResult[RepositoryMutationResult]`, `runtimes.update` SHALL return
  `ActionResult[RuntimeUpdateResult]`, and token-based `auth.login` SHALL return
  `ActionResult[str]`.
- `process` SHALL return `ManagedProcess`, including interactive
  `auth.login(token=None)`.
- `scalar` and `mapping` SHALL be reserved for operations whose natural output
  is a primitive, bytes/path, immutable scalar snapshot, or key/value mapping;
  they SHALL NOT be used to avoid the collection or action conventions.

#### Scenario: Retrieval creation and entity update return entities

- **WHEN** a get, create, or entity-update operation succeeds
- **THEN** the eager call and command run return the corresponding typed entity
  with the same binding behavior.

#### Scenario: Void action returns ActionResult

- **WHEN** a delete, remove, archive, restore, toggle, cancellation, rerun,
  watcher, subscriber, membership, or configuration-set operation that
  formerly returned `None` succeeds
- **THEN** it returns `ActionResult[None](success=True, value=None, ...)` rather
  than bare `None`.

#### Scenario: Action payload is retained

- **WHEN** deprioritize, repository mutation, runtime update, or token login
  produces a useful non-entity payload
- **THEN** the payload is available through the typed `ActionResult.value` and
  is not discarded or returned ad hoc.

#### Scenario: Failure remains exceptional

- **WHEN** a CLI-backed action fails transport, exit-code, decode, or validation
  rules
- **THEN** the existing typed exception is raised and no unsuccessful
  `ActionResult` is fabricated.

#### Scenario: Long-running operation returns ManagedProcess

- **WHEN** an operation starts or attaches to a live process
- **THEN** both eager and command forms return `ManagedProcess`, not
  `ActionResult`, text, or an ad hoc handle.

#### Scenario: Every canonical operation is classified

- **WHEN** the discovered canonical public operation set is compared with the
  approved category matrix
- **THEN** the sets are equal and each operation has exactly one public response
  convention.

### Requirement: Common page contract

Every public collection result SHALL expose an immutable, generic page
interface with `items: tuple[T, ...]`, `limit: int | None`,
`offset: int | None`, `total: int | None`, `has_more: bool`, and the supported
typed cursor metadata. A page SHALL implement direct iteration, `len(page)`,
and integer/slice indexing over `items` without performing I/O.

Unpaged collection reads SHALL return a page with `total == len(items)`,
`limit is None`, `offset is None`, `has_more is False`, and no next cursor.
Offset-paged and cursor-paged reads SHALL preserve upstream metadata without
inventing values. `IssueChildrenResult` SHALL be a compatible page subtype
that retains stage grouping; the issue metadata mapping read SHALL remain a
mapping rather than pretending key/value entries are a sequence page.

`IssueListPage.issues`, `AutopilotListPage.autopilots`, and
`AutopilotRunListPage.runs` SHALL remain warning-free, read-only aliases of
`.items` for the documented compatibility window. New documentation and code
SHALL use `.items`.

#### Scenario: Items are common across resources

- **WHEN** callers list issues, projects, agents, skills, workspaces,
  autopilots, runs, comments, or any other collection resource
- **THEN** the returned page exposes the typed elements through `.items`.

#### Scenario: Page is directly iterable

- **WHEN** a page is used in `for`, `len`, integer indexing, or slice indexing
- **THEN** those operations delegate to the immutable `items` tuple and perform
  no additional command.

#### Scenario: Offset metadata round-trips

- **WHEN** an upstream response reports limit, offset, total, and has-more
  values
- **THEN** the public page preserves those values exactly.

#### Scenario: Cursor metadata round-trips

- **WHEN** a comment or metadata response reports a next cursor
- **THEN** the public page preserves the complete typed cursor and leaves
  offset-only fields unset.

#### Scenario: Unpaged list uses neutral metadata

- **WHEN** an upstream list operation returns only an array
- **THEN** the SDK wraps it in a page whose `items` preserve response order and
  whose neutral metadata reports a complete, unpaged result.

#### Scenario: Legacy resource alias mirrors items

- **WHEN** a caller reads `issues`, `autopilots`, or `runs` on its legacy page
  type during the compatibility window
- **THEN** the property returns the identical tuple object exposed by `.items`
  and performs no I/O.

### Requirement: Executable operation command equivalence

Every public CLI-executing eager operation SHALL expose an argument-identical
`*_command()` sibling returning `Command[T]`, and the eager operation SHALL be
observationally equivalent to `*_command(...).run()`. This requirement SHALL
include top-level resources, nested resources, bound-entity mutations,
collection page reads, local-I/O wrappers, composite operations, and process
operations. Command construction SHALL remain inspectable and I/O-free.

#### Scenario: Eager and command signatures match

- **WHEN** a canonical eager method and its command sibling are inspected
- **THEN** their parameter overloads are identical and the command's result
  parameter is the eager return type.

#### Scenario: Running command matches eager result

- **WHEN** an eager method and its command form are invoked with equivalent
  inputs against the same response
- **THEN** they execute the same plan and return equal public result categories
  and values.

#### Scenario: Command construction performs no I/O

- **WHEN** any valid `*_command()` method is called
- **THEN** its redacted command sequence is inspectable before execution and no
  subprocess starts until `run()` is called.

#### Scenario: New operation without command form fails coverage gate

- **WHEN** a CLI-executing public method is added without a matching command
  sibling and canonical preview case
- **THEN** contract verification fails closed.
