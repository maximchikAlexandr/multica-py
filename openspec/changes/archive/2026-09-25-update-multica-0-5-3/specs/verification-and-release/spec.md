## ADDED Requirements

### Requirement: Multica 0.5.3 patch coverage is table-driven
Offline verification SHALL extend the existing frozen contract, provenance,
operation, response, usage, compatibility, documentation, and package case tables.
It SHALL prove exact target identity, the zero command and response-shape delta,
correct target-provided usage values, unchanged public inventories, and explicit
negative scope without creating a parallel fixture framework.

#### Scenario: Usage semantics cover target edge cases
- **WHEN** regression cases represent resumed baseline subtraction, multiple models, cache reads and writes, counter reset, missing or corrupt snapshots, no-result fallback, rejected resume, and agent/issue/runtime aggregates
- **THEN** decoded values match target payloads exactly and no prior-session total is double-counted by SDK logic

#### Scenario: Existing public surface remains closed
- **WHEN** model, symbol, operation, signature, dependency, relation, and response inventories are checked
- **THEN** they match the approved `0.5.2` surface except for target/provenance and compatibility metadata

### Requirement: Complete upstream audits are reproducible for 0.5.3
Maintainer evidence SHALL reproduce official release and checksum identities,
separate baseline and target binaries, version output, direct source comparison,
the full 201-node command inventory, source-only classifications, gap decisions,
and all 167 supported response entries. Tracked files and distributions SHALL NOT
contain release archives, executables, `.devlocal`, source checkouts, collector or
audit output, or transient deterministic-render directories.

#### Scenario: Reproduced audits agree with the approved contract
- **WHEN** pinned evidence is regenerated from the `0.5.2` and `0.5.3` endpoints
- **THEN** exact identities, zero CLI/wire delta, semantic usage decision, and exclusions agree or validation fails

#### Scenario: Evidence stays outside source and packages
- **WHEN** tracked and built contents are audited
- **THEN** no binary, archive, checkout, collector, audit, or transient render artifact is included

### Requirement: Direct 0.5.2 to 0.5.3 migration and rollback are atomic
README, API, compatibility, migration, changelog, prepared-live, and release
guidance SHALL describe one direct `0.5.2` to `0.5.3` patch migration. They SHALL
state that public CLI and SDK shapes are unchanged, explain corrected resumed
Claude usage values, and identify unrelated upstream features as excluded. The
contract, generated projection, fixtures, docs, and package claims SHALL roll back
together.

#### Scenario: Migration guidance matches the approved interval
- **WHEN** a maintainer or consumer reads upgrade documentation
- **THEN** it identifies `0.5.2` as baseline, `0.5.3` as maximum tested, `0.5.4` as the exclusive next-patch ceiling, and requires no `0.5.2` feature migration work

#### Scenario: Rollback restores one coherent baseline
- **WHEN** provenance, generation, usage fixtures, offline gates, or packaging fails
- **THEN** all target metadata and claims revert together to the approved `0.5.2` state

### Requirement: Offline quality and packaging gates remain strict and clean
Delivery SHALL pass strict OpenSpec validation; approved-contract source
validation, deterministic double render, and check; source-link audit; focused
contract and usage suites; complete non-live pytest; non-live collect-only with no
live nodes; Ruff check and format check; mypy source and tests; build; isolated
package validation; diff checks; and tracked/package content audits. Prepared live
status SHALL be reported separately and SHALL NOT cause offline tests to provision
or contact a backend.

#### Scenario: Complete offline gate passes
- **WHEN** the implementation is ready for review
- **THEN** every required offline, type, lint, build, package, determinism, source-link, and content-audit command exits successfully

#### Scenario: Live validation remains explicitly gated
- **WHEN** prepared-target smoke is unavailable or not selected
- **THEN** offline acceptance remains backend-free and reports live status separately without fabricating evidence
