## ADDED Requirements

### Requirement: Multica 0.11.1 coverage extends existing case tables
Every changed command, response, presence rule, model, adapter, pagination rule, typed error, compatibility decision, and migration SHALL be covered by existing frozen table-case types or one focused test where lifecycle or interleaving behavior cannot be represented by a row.

#### Scenario: Coverage closure is exact
- **WHEN** focused unit, contract, and component coverage is audited
- **THEN** all 31 changed CLI nodes, all 102 changed response rows, all 94 retained rows, the one removed command, 55 added-node decisions, and five source-only decisions SHALL map to an assertion or reasoned non-surface/defer exclusion

#### Scenario: Presence and failure matrices are complete
- **WHEN** changed optional fields and constraints are tested
- **THEN** positive, negative, omission, explicit-null, explicit-empty, unknown-open-enum, pagination, malformed-wire, and reviewed 400/409/413 cases SHALL be present where applicable

### Requirement: Offline release gates are deterministic and clean
The published implementation revision SHALL pass strict OpenSpec validation, approved-contract validate/render/check, deterministic double regeneration and diff, source-link audit against exact commits, focused and complete non-live unit/contract/component tests, compatibility checks, mypy for source/tests/tools, Ruff check/format, documentation checks, package build/install checks, and Git cleanliness checks.

#### Scenario: Local automated run remains within limit
- **WHEN** an automated local gate completes within ten minutes
- **THEN** its command, exact revision, exit code, and material assertions SHALL be recorded

#### Scenario: Long automated run moves to CI intact
- **WHEN** a local automated suite is expected to exceed ten minutes or reaches ten minutes
- **THEN** only its owned process SHALL be stopped and the unsplit suite SHALL run in GitHub Actions against the published exact revision

#### Scenario: Repository remains evidence-clean
- **WHEN** tracked files and package contents are inspected
- **THEN** `.devlocal`, collector renderings, audit JSON, logs, hashes, screenshots, private endpoints, and environment-specific evidence SHALL be absent

### Requirement: Local E2E and image evidence are not required
Verification SHALL use existing deterministic lower-level and CI capabilities because this change updates SDK mappings, decoding, errors, compatibility, generation, documentation, and packaging without requiring a real backend interaction or changing human-facing tables, logs, progress, summaries, or browser UI.

#### Scenario: Every changed scenario has sufficient lower-level proof
- **WHEN** the verification matrix is reviewed
- **THEN** each scenario SHALL map to contract, unit, fake-CLI component, compatibility, type, documentation, package, or CI assertions and no task-specific live script or infrastructure SHALL be required

#### Scenario: No visible-output comparison applies
- **WHEN** independent verification confirms that human-facing output is unchanged
- **THEN** before/after text and PNG evidence SHALL be omitted with the recorded no-image rationale

### Requirement: Direct migration and rollback remain coherent
Documentation and package metadata SHALL describe direct `0.7.1` to `0.11.1` migration, the preserved `0.6.2` floor, maximum-tested `0.11.1`, exclusive `0.11.2` ceiling, `issue rerun-task` command migration, adapted retained behavior, deferred families, and rollback to the prior `0.7.1` contract projection.

#### Scenario: Package claims match the approved contract
- **WHEN** compatibility metadata, changelog, API reference, migration guide, generated projection, and package artifacts are inspected
- **THEN** they SHALL agree on target identity, compatibility interval, public surface, and migration behavior

#### Scenario: Rollback requires no data migration
- **WHEN** the implementation commit set is reverted
- **THEN** the prior `0.7.1` contract and projection SHALL be restorable without transforming persisted user data

### Requirement: Evidence and release handoff use one exact revision
Implementation and independent Tester evidence SHALL identify one clean published revision and SHALL keep product/test commits, CI results, manual observations, and Multica attachments traceable without rewriting history.

#### Scenario: Exact revision is reproducible
- **WHEN** delivery is handed to independent verification
- **THEN** local HEAD and remote branch SHA SHALL match and all commands, commits, CI links, files, and assertions SHALL name that SHA

#### Scenario: Evidence publication is confirmed
- **WHEN** the Tester posts final evidence
- **THEN** required MR/commit/file links and sanitized artifacts SHALL be attached in Multica and comment/attachment read-back SHALL confirm accessibility

#### Scenario: Cleanup preserves durable results
- **WHEN** verification finishes or fails
- **THEN** run-owned diagnostics and test environments SHALL be removed while evidence branches, commits, links, and attachments remain; merge, close, and branch deletion SHALL require separate authority
