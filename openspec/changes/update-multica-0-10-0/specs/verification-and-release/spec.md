## ADDED Requirements

### Requirement: Table-driven offline and CI verification
Every changed requirement and contract row SHALL map to an existing or extended table-driven unit, contract, fake-CLI component, packaging, documentation, or exact-revision CI check.

#### Scenario: Positive and negative matrix is complete
- **WHEN** scenario coverage is audited
- **THEN** present/omitted/null/malformed response fields, argument presence/conflicts, rerun modes, private membership, cancellation, archive/runtime-delete errors, literal text, metadata escaping, and webhook filters SHALL each have explicit positive and negative assertions

#### Scenario: Repository gates pass at one SHA
- **WHEN** final verification runs at the delivery SHA
- **THEN** strict OpenSpec validation, contract validate/render/check, second-render equality, source-link audit, focused tests, public-operation completeness, non-live collect-only isolation, mypy for source/tests, Ruff check/format, documentation, package build/import, and forbidden-content audits SHALL pass

#### Scenario: Long automated suites use CI
- **WHEN** an automated local suite is expected to exceed or reaches ten minutes
- **THEN** only the owned test process SHALL stop and the unsplit suite SHALL run in GitHub Actions against the published exact revision

### Requirement: Isolated Multica 0.10.0 E2E verification
The delivery SHALL provide one repository-native `scripts/e2e_multica_010.py` verification script and an independent manual walkthrough against the isolated project test stand using `multica-test`, its own profile/daemon, disposable data, and failure-safe cleanup.

#### Scenario: Readiness gate protects the attempt
- **WHEN** Tester prepares an E2E attempt
- **THEN** the script SHALL first prove exact product and test-code revisions, observed CLI `0.10.0`, isolated executable/profile/daemon/server/workspace bindings, required renderer status, focused test readiness, and absence of primary-profile inputs

#### Scenario: Real boundaries are observed
- **WHEN** the E2E script and manual walkthrough run
- **THEN** they SHALL exercise representative public SDK paths for private membership visibility, literal file/stdin text, metadata escaping, rerun-task, no-body cancellation, and bounded archive/runtime-delete failures with explicit outputs, exit codes, state assertions, and cleanup results

#### Scenario: Independent actions are not a test rerun
- **WHEN** Tester performs the manual walkthrough
- **THEN** Tester SHALL issue fresh public actions and independently inspect CLI/SDK output and remote state rather than merely invoking the automated script a second time

### Requirement: Evidence and image publication
Tester SHALL publish sanitized exact-revision commands, exit codes, assertions, provenance, CI/MR/commit/file links, hashes, and applicable artifacts in the final Multica comment and SHALL verify comment/attachment read-back.

#### Scenario: No decorative images are required
- **WHEN** public terminal tables, logs, progress, summaries, and browser UI remain visually unchanged
- **THEN** the evidence SHALL state the no-image rationale and SHALL NOT manufacture before/after PNGs

#### Scenario: Diagnostics stay outside Git
- **WHEN** evidence is published and the stand is cleaned
- **THEN** real outputs, logs, diagnostic JSON, hashes, screenshots, credentials, private URLs, and personal data SHALL remain untracked and sanitized, while ordinary test scripts, fixtures, generated product outputs, and real development commits may remain in Git

### Requirement: Compatibility documentation and rollback
Compatibility metadata, API examples, migration guidance, CLI coverage, changelog, contribution, packaging, and release documentation SHALL agree on target `0.10.0`, deferred families, rerun migration, and supported version envelope.

#### Scenario: Migration does not promise deferred APIs
- **WHEN** documentation is audited
- **THEN** it SHALL identify mandatory retained adaptations and explicit deferred candidates without examples or claims for unsupported methods

#### Scenario: Delivery is reversible
- **WHEN** the implementation commit set is reverted
- **THEN** the prior `0.7.1` approved contract and generated projection SHALL be restorable without transforming persisted user data
