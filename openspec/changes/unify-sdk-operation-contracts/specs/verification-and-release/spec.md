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

Every field on every update-style public input SHALL have an approved and
tested presence vector covering omission, `None`, empty string or empty tuple,
zero, and false wherever each value is type-applicable. Tests SHALL assert the
exact command plan and final transport argv, including multi-step clear
operations and no-op read delegation.

#### Scenario: Presence vectors are field-complete

- **WHEN** update model fields and direct update parameters are discovered
- **THEN** each field maps to exactly one approved presence vector and one
  table-driven verification row per applicable input state.

#### Scenario: No-op update is read-only

- **WHEN** every update field is omitted
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

#### Scenario: Collection migration is complete

- **WHEN** collection-read return annotations and runtime results are inspected
- **THEN** every result is `Page[T]` or an approved compatible subtype with
  `.items` and direct sequence behavior.

### Requirement: Operation convention documentation gate

Public API and migration documentation SHALL describe one SDK-wide calling,
presence, command, return-category, and page contract. Contract tests SHALL pin
the primary direct-keyword examples, the typed-object alternative, update
presence table, action-result migration, iterable `.items` page examples, and
legacy page aliases.

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
