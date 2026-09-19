## ADDED Requirements

### Requirement: Multica 0.5.0 provenance and inventory gates
Release acceptance SHALL verify exact baseline and target identities, a 189-to-194 public-node reconciliation with five additions and no removals/renames/moves, all changed label flags, and a 163-entrypoint response audit split into six changed and 157 unchanged rows.

#### Scenario: Inventory gate is exact
- **WHEN** provenance and inventory checks run at the delivery SHA
- **THEN** identities, totals, dispositions, source links, and unique work-item coverage SHALL match the approved contract exactly

### Requirement: Targeted table-driven behavior matrices
New and changed behavior SHALL extend existing frozen dataclass case tables and shared fixtures. Positive and negative cases SHALL cover exact argv, validation timing, presence/null/empty/value behavior, response decoding, conflict classification, relation invalidation, and no-partial-mutation guarantees.

#### Scenario: Required matrices are complete
- **WHEN** focused tests run
- **THEN** comment update, skill labels, label inputs, skill-list labels, task deltas, OMP validation, and runtime-delete success/conflict variants SHALL each have positive and negative table rows

#### Scenario: Existing inventories remain complete
- **WHEN** discovered methods, canonical vectors, component cases, legacy fingerprints, relations, and response dispositions are reconciled
- **THEN** exact set equality SHALL pass without allowlists or duplicate tests

### Requirement: Deterministic contract-driven delivery
Strict pinned-source contract validation SHALL pass before render. Two renders from the approved contract SHALL have identical relative paths and bytes, and generated or transient evidence SHALL not be tracked.

#### Scenario: Rendering is reproducible
- **WHEN** the contract is rendered twice to clean ignored locations
- **THEN** their relative file sets and bytes SHALL be identical and the committed runtime SHALL match the approved projection

### Requirement: Offline quality and packaging gates
Acceptance SHALL run strict OpenSpec validation, contract validate/render/check, source-link audit, focused suites, Ruff format/check, mypy for source/tests/scripts/tools, full non-live pytest, live-node collection exclusion, build, and package validation without requiring backend or network.

#### Scenario: Mandatory gates pass at one SHA
- **WHEN** the implementation is ready for delivery
- **THEN** every mandatory offline command SHALL exit zero at the recorded exact SHA and the worktree SHALL be clean

#### Scenario: Live verification is reported separately
- **WHEN** an authorized prepared target is unavailable
- **THEN** its absence SHALL be reported without weakening or failing the mandatory offline acceptance gates

### Requirement: Direct migration and atomic rollback
Documentation and package claims SHALL describe one direct `0.4.44` to `0.5.0` migration, new operation gates, presence and conflict semantics, and the reviewed compatibility interval. Contract, generated runtime, public behavior, fixtures, docs, and package metadata SHALL roll back together.

#### Scenario: Release claims are coherent
- **WHEN** API, compatibility, migration, maintainer, release, README, changelog, and package assertions are compared
- **THEN** they SHALL agree on exact target, interval, new surface, changed semantics, non-SDK exclusions, and atomic rollback
