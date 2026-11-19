## ADDED Requirements

### Requirement: Multica 0.11.0 evidence is the exact contract authority
The approved contract SHALL identify Multica release `0.11.0`, release id
`449794198`, commit `cb190810a659c1a61c4a86d9f6ecfc9df4b086d8`, and the
verified release-asset, binary, version, and source provenance recorded by
`MYL-668`. Moving branch references SHALL NOT satisfy source authority.

#### Scenario: Exact target identity is accepted
- **WHEN** contract validation inspects target provenance
- **THEN** every target identity and exact-commit source link matches the approved `0.11.0` evidence

#### Scenario: Moving or mismatched provenance is rejected
- **WHEN** any target identity differs or a source link uses a moving branch
- **THEN** validation fails before generation

### Requirement: Direct-range command reconciliation is complete
The approved contract SHALL classify all `256` target help nodes and every
added, removed, or changed child, flag, positional argument, alias, default, and
constraint as `retain`, `adapt`, `remove`, `defer`, or
`not_sdk_surface`. It SHALL separately classify the source-only names
`multica`, `probe-runtimes`, `environment`, and hidden `rerun`.

#### Scenario: Complete command review validates
- **WHEN** the direct `0.7.1` to `0.11.0` command review is validated
- **THEN** every target node and source-only name has exactly one disposition and zero unresolved review items

#### Scenario: Evidence cannot publish a deferred operation
- **WHEN** extraction discovers a command whose approved disposition is `defer` or `not_sdk_surface`
- **THEN** no public SDK symbol or generated command mapping is created

### Requirement: Direct-range response reconciliation is complete
The approved contract SHALL contain all `196` supported response work items,
including `102` changed and `94` unchanged rows, with old and target source
traces, factual conclusions, SDK actions, test actions, and documentation
actions. Pending response review SHALL equal zero.

#### Scenario: Response review is closed
- **WHEN** the response registry is validated
- **THEN** all `196` rows are uniquely covered and no pending row remains

#### Scenario: Presence-sensitive response lacks a decision
- **WHEN** a changed optional, nullable, enum, page, or error field lacks an explicit compatibility action
- **THEN** strict contract validation fails

### Requirement: Approved contract alone drives deterministic generation
The reviewed `contracts/sdk-contract.json` SHALL remain the sole production
generator input. Collector files, audit copies, response reviews, and transient
renderings SHALL remain review evidence and SHALL NOT directly alter generated
runtime behavior.

#### Scenario: Equivalent renders are byte-identical
- **WHEN** the approved target contract is rendered twice in clean output locations
- **THEN** committed and transient relative paths and bytes are identical

#### Scenario: Transient evidence is changed
- **WHEN** review evidence changes without a corresponding approved contract edit
- **THEN** the committed runtime projection remains unchanged
