## ADDED Requirements

### Requirement: SDK operation convention matrix

The repository SHALL maintain a machine-checked convention record for every
canonical public operation. Each record SHALL identify its typed-input model or
absence, presence policy, operation category, public response convention,
command sibling, approved source references, and table-driven test references.
The approved SDK contract SHALL remain the only production input; extracted
upstream evidence SHALL NOT change a public convention automatically.

#### Scenario: Matrix and discovered surface are bijective

- **WHEN** the canonical resource methods are discovered
- **THEN** each has exactly one convention record and no convention record
  names a missing canonical method.

#### Scenario: Public convention requires approved evidence

- **WHEN** an upstream command adds or changes update-presence or response
  behavior
- **THEN** contract validation fails until a reviewer records the approved
  mapping and source references in `contracts/sdk-contract.json`.

#### Scenario: Generator consumes only approved conventions

- **WHEN** runtime signatures, response adapters, docs, fixtures, or tests are
  rendered
- **THEN** only the approved SDK contract supplies production convention data.

### Requirement: Dual-input structural and behavioral verification

The offline suite SHALL discover every public method accepting a governed typed
request/filter and verify typed-object/direct-keyword overload parity on both
the eager and command forms. One frozen table SHALL drive behavioral parity for
valid, mixed, missing-required, and validation-failure cases.

#### Scenario: Typed-input inventory is complete

- **WHEN** public annotations are scanned for governed request/filter types
- **THEN** the discovered set equals the dual-input case table and every method
  has both overloads on eager and command forms.

#### Scenario: Equivalent forms have exact command parity

- **WHEN** a typed object and direct keywords represent the same input
- **THEN** tests assert identical `Command.commands`, argv, execution mode,
  stdin, timeout, subprocess count, and decoded result.

#### Scenario: Invalid dispatch performs zero I/O

- **WHEN** mixed inputs, missing required input, unknown fields, or request
  validation fail
- **THEN** the expected exception is asserted and every transport method has
  zero calls.

### Requirement: Update presence vector verification

Every field on every all-optional update-style public input SHALL have an
approved and tested presence vector covering omission, `None`, empty string or
empty tuple, zero, and false wherever each value is type-applicable. The
all-optional set is exactly `ProjectUpdateRequest`, `AgentUpdateRequest`,
`SkillUpdateRequest`, `IssueUpdateRequest`, `AutopilotUpdateRequest`,
`LabelUpdateRequest`, `AutopilotTriggerUpdate`, and `UserProfileUpdate`.
Tests SHALL assert the exact command plan and final transport argv, including
multi-step clear operations and all-optional no-op read delegation. The
required-value update inputs `ProjectResourceUpdateLocalDirectoryRequest` and
`RuntimeUpdate` SHALL instead have explicit missing/null rejection vectors for
`local_path` and `target_version`; they are excluded from the no-op guarantee.

#### Scenario: All-optional presence vectors are field-complete

- **WHEN** all-optional update model fields and direct update parameters are
  discovered
- **THEN** each field maps to exactly one approved presence vector and one
  table-driven verification row per applicable input state.

#### Scenario: Required-value update boundary is explicit

- **WHEN** required-value update models are discovered
- **THEN** tests cover omission and explicit `None` for
  `ProjectResourceUpdateLocalDirectoryRequest.local_path` and
  `RuntimeUpdate.target_version`, and expect pre-I/O validation rather than a
  no-op read.

#### Scenario: All-optional no-op update is read-only

- **WHEN** every mutable field is omitted from an all-optional update model
- **THEN** the focused case asserts the read command preview, one read
  invocation, no update invocation, and the normal entity result.

#### Scenario: Unsupported clear fails closed

- **WHEN** a nullable public field lacks an approved upstream clear mapping
- **THEN** contract validation fails before generated/runtime behavior can
  silently map `None` to omission.

### Requirement: Return-category verification

The canonical operation case table SHALL assert the declared operation
category and exact eager/command return annotation for every public method.
Runtime assertions SHALL verify entity binding, page element types,
`ActionResult.value` types, `ManagedProcess` transport mode, and scalar/mapping
exceptions to the common conventions.

#### Scenario: Annotation matches declared category

- **WHEN** eager and command annotations are compared with the approved matrix
- **THEN** entity, page, action, process, scalar, and mapping return types match
  their declared conventions exactly.

#### Scenario: Action migration is complete

- **WHEN** the canonical surface is inspected after migration
- **THEN** no CLI-executing public method returns bare `None`, and the four
  payload-bearing action groups expose their payload only through typed
  `ActionResult.value`.

#### Scenario: Canonical collection migration is complete

- **WHEN** canonical CLI collection operation and direct resource collection
  return annotations and runtime results are inspected
- **THEN** every result is `Page[T]` or an approved compatible subtype with
  `.items` and direct sequence behavior.

#### Scenario: Relation snapshot exception is preserved

- **WHEN** relation loaders expose `.all()` snapshots from
  `LazyCollection`, `OffsetLazyCollection`, or `CursorLazyCollection`
- **THEN** those snapshots remain tuples and are excluded from the page-result
  migration gate; any direct relation `.page()` result remains page-checked.

### Requirement: Operation convention documentation gate

Public API and migration documentation SHALL describe one SDK-wide calling,
presence, command, return-category, and page contract. It SHALL distinguish
all-optional update no-op reads from required-value update validation and SHALL
state the tuple contract for relation snapshots. Contract tests SHALL pin the
primary direct-keyword examples, the typed-object alternative, update presence
table, action-result migration, iterable `.items` page examples, relation
snapshot tuple examples, and legacy page aliases.

#### Scenario: Documentation examples type-check

- **WHEN** documented direct, request-object, command, action-result, and page
  examples are included in the documentation contract fixtures
- **THEN** their public symbols and signatures match the shipped SDK surface.

#### Scenario: Migration guide covers breaking changes

- **WHEN** a caller upgrades from the prior surface
- **THEN** the migration guide identifies tuple/page return changes, bare
  `None`/payload action changes, explicit-`None` update changes, and the
  compatibility lifetime of resource-named page aliases.

#### Scenario: Documentation states command equivalence

- **WHEN** the SDK-wide conventions section is read
- **THEN** it states that a normal method and its `*_command(...).run()` form
  share one operation plan and one result contract.
