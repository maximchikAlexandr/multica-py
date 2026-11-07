## ADDED Requirements

### Requirement: Verification covers every reviewed delta at the lowest sufficient layer
Implementation SHALL extend existing table-driven unit, contract, and fake-CLI component coverage for every affected command constraint and all 23 changed response entrypoints. It SHALL cover paired updated-time bounds, invalid RFC3339 and ranges, literal comma attachments, steering/attachment conflict as a deferred-surface guard, runtime absent/null/integer states, comment projections, old/new response rows, invalid wire types, and unknown open-enum values.

#### Scenario: Coverage reconciliation
- **WHEN** the scenario-to-test matrix is audited
- **THEN** every changed requirement and response row SHALL map to a concrete assertion, existing sufficient coverage, or an explicit non-surface exclusion

### Requirement: Offline contract and generation gates are mandatory
Verification SHALL run collector validation/render reconciliation against pinned sources, approved contract validation, contract diff classification, deterministic render and check mode, generated-source freshness, pinned GitHub source-link checks, focused tests, offline tests, Ruff, mypy for source and tests, documentation, packaging, and live-test collection exclusion. Automated local suites predicted to exceed or reaching ten minutes SHALL run unsplit in GitHub Actions on the published exact revision.

#### Scenario: Exact-revision gates pass
- **WHEN** the candidate revision is published for verification
- **THEN** all required gates SHALL pass on that exact revision and local HEAD SHALL equal the remote branch SHA

### Requirement: Independent verification evidence is Multica-only
An independent Tester SHALL verify the exact candidate revision from a fresh checkout, inspect scenario coverage, execute focused lower-level checks, confirm linked CI, and publish commands, exit codes, assertion summaries, commit/MR/file links, and applicable attachments in Multica with read-back. Raw logs, diagnostic JSON, hashes, screenshots, provenance dumps, private hosts, credentials, and generated evidence SHALL NOT be committed.

#### Scenario: Evidence publication and cleanup
- **WHEN** independent verification completes
- **THEN** the Multica comment and attachments SHALL be readable, the evidence branch and commits SHALL remain preserved, and cleanup SHALL remove only run-owned local diagnostics without merging, closing, or deleting the branch

### Requirement: Visible-output evidence is required only when output changes
This change SHALL require no decorative images because the specified SDK change does not alter human-facing terminal tables, logs, progress, summaries, or browser UI. If implementation changes visible output, verification SHALL stop for a planning revision that specifies equivalent baseline/candidate text and actual Mac PNG renders through bundled `scripts/render_terminal.swift`.

#### Scenario: No visible output change
- **WHEN** implementation preserves all visible CLI output and changes only SDK arguments, models, decoders, validation, and documentation
- **THEN** the Tester SHALL record that no before/after image is applicable
