## ADDED Requirements

### Requirement: Issue property query options use the target CLI contract

The existing property catalog and issue property value operations SHALL remain
unchanged. `issues.get` SHALL additionally support opt-in property resolution.
`issues.list` SHALL additionally support an ordered fields allowlist,
repeatable property predicates, opt-in property resolution, and property sort
using the target command destinations and validations. The default list/get
projection SHALL continue returning the raw property UUID map.

#### Scenario: Property resolution is opt-in
- **WHEN** issue get or list is called with `resolve_properties=True`
- **THEN** argv emits `--resolve-properties` once and the decoder returns the reviewed name/type/value/display projection

#### Scenario: Raw property map remains default
- **WHEN** property resolution is omitted or false
- **THEN** argv omits the flag and the existing raw UUID-keyed property map remains unchanged

#### Scenario: Same and different property names compose correctly
- **WHEN** list receives `Impact=High`, `Impact=Medium`, and `Environment=prod`
- **THEN** all three flags are emitted in order, the two Impact values represent OR, and Environment composes with them as AND

#### Scenario: Unset sentinel and reserved operators are enforced
- **WHEN** a predicate uses `Name=__none__` versus `Name>=Value`, `Name<=Value`, or `Name!=Value`
- **THEN** the unset sentinel is accepted and each reserved comparison spelling is rejected before transport

#### Scenario: Property sorting is constrained
- **WHEN** list sorting names a reviewed sortable property versus an archived or unsortable property
- **THEN** the reviewed form reaches `--sort property:<name-or-id>` and unsupported forms fail with the documented validation behavior

### Requirement: Issue field projection preserves partial-row typing

The issue-list `fields` option SHALL use the target allowlist and SHALL return
partial list rows without constructing falsely complete Issue entities.
Required identity fields used by binding and pagination SHALL remain available,
and omission of unrequested fields SHALL remain distinct from explicit null.

#### Scenario: Fields are emitted deterministically
- **WHEN** a caller supplies an ordered nonempty fields selection
- **THEN** the exact reviewed `--fields` encoding is emitted once and unsupported or duplicate-invalid selections fail before transport

#### Scenario: Partial rows do not invent values
- **WHEN** a valid projection omits optional IssueSummary fields
- **THEN** decoding preserves absence according to the reviewed projection model and relation binding performs no per-item get
