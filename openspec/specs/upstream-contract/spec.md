## Purpose

Define how reviewed upstream CLI evidence becomes deterministic public SDK
behavior.

## Requirements

### Requirement: Pinned source authority
The approved contract MUST cite full pinned source commits and locations, while extraction records only declared declarative facts.
#### Scenario: Unknown patterns require review
- **WHEN** extraction sees an unknown pattern
- **THEN** it emits a review item and changes no approved behavior.
<!-- Source IDs: 001:FR-032A–FR-032G,002:FR-001,FR-002,FR-027 -->

### Requirement: Verified evidence
Evidence collection MUST record verified binary identity, release identity, ordered declarative facts, and review items outside version control.
#### Scenario: Collection records verified evidence
- **WHEN** collection succeeds
- **THEN** its two files satisfy the schemas in `generation.md`.
<!-- Source IDs: 002:FR-003,FR-004,FR-012,FR-023,FR-032 -->

### Requirement: Reviewed mapping semantics
Every approved mapping MUST state source evidence, destination, five-state presence, enum policy, and normalized constraints with positive and negative evidence.
#### Scenario: Mappings state reviewed semantics
- **WHEN** a mapping is incomplete or unresolved
- **THEN** validation fails.
<!-- Source IDs: 002:FR-028,007:FR-009,FR-010 -->

### Requirement: Deterministic generation
The approved contract MUST be the only generator input and MUST render one committed runtime module plus deterministic transient projections.
#### Scenario: Rendering is deterministic
- **WHEN** rendered twice
- **THEN** all relative paths and bytes are identical.
<!-- Source IDs: 002:FR-017,FR-018,007:FR-012–FR-014 -->

### Requirement: Generated compatibility
The generated runtime module MUST provide the tested CLI interval from the approved target version.
#### Scenario: Compatibility uses the generated interval
- **WHEN** a client reads default policy
- **THEN** it uses generated minimum and exclusive next-patch maximum versions.
<!-- Source IDs: 002:FR-025,FR-033 -->

### Requirement: Git promotion
A reviewed Git merge changing the approved contract and runtime projection MUST be the only promotion action.
#### Scenario: Git review promotes the contract
- **WHEN** a PR is merged
- **THEN** no candidate, supported, observer, or journal state is written.
<!-- Source IDs: 002:FR-030,007:FR-011 -->
