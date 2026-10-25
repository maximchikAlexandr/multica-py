## ADDED Requirements

### Requirement: Upgrade coverage is closed and table-driven

Verification SHALL map every changed requirement and all 196 supported response
work items to a frozen case-table row, an existing sufficient assertion, or an
explicit non-surface decision. New repeated coverage SHALL extend existing case
tables rather than create parallel frameworks.

#### Scenario: Coverage reconciliation runs

- **WHEN** contract and test discovery compare the approved inventory with test references
- **THEN** every supported item has one verdict and sufficient positive, negative, fixture, and documentation coverage

### Requirement: Offline release gates are deterministic

The exact candidate SHALL pass strict source-link audit, approved-contract
validation, deterministic render, generated freshness check, offline unit,
contract, component, packaging, type, lint, and distribution checks. Generated
files SHALL NOT be hand-edited and transient evidence SHALL remain untracked.

#### Scenario: A deterministic gate detects drift

- **WHEN** a second render, generated check, source link, package import, or offline assertion differs
- **THEN** release readiness fails until the approved source or handwritten implementation is reconciled

### Requirement: Exact-revision live verification is isolated

Live verification SHALL use the test repository declared by the project, an
isolated test profile/workspace and exact candidate SHA, and SHALL never use the
primary Multica profile, daemon, containers, or reference checkout. It SHALL
record automatic and independent-agent results separately.

#### Scenario: The isolated lifecycle succeeds

- **WHEN** Tester verifies readiness and executes the approved `0.7.0` cases
- **THEN** each case records the tested product revision, test-code revision, fixtures, assertions, command exit status, cleanup result, and accessible Multica evidence

#### Scenario: Revision or environment identity differs

- **WHEN** the checkout, CLI version, profile, workspace, database, port, or service identity does not match the plan
- **THEN** live execution stops before consuming an attempt and no PASS is reported

### Requirement: Changed terminal output has genuine before and after evidence

Changed CLI read/table output SHALL have actual baseline and candidate text plus
PNG renders created by the bundled `scripts/render_terminal.swift` on macOS,
using equivalent fixtures, locale, width, and output mode. TTY, ANSI, and progress
limitations SHALL be stated honestly.

#### Scenario: Visible output is compared

- **WHEN** daemon status or another reviewed visible output changes
- **THEN** Tester publishes labeled baseline/candidate text and PNG attachments with revision provenance in Multica

#### Scenario: Required capture is unavailable

- **WHEN** genuine baseline or candidate output cannot be captured
- **THEN** verification remains incomplete and no synthetic image is substituted
