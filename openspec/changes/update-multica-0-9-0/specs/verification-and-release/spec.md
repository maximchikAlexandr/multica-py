## ADDED Requirements

### Requirement: Upgrade scenarios have table-driven lower-level coverage
Every changed retained command, response field, relationship, error path, and migration behavior SHALL map to an existing or extended table-driven unit, contract, component, or packaging check with exact assertions.

#### Scenario: Presence matrix is complete
- **WHEN** verification inspects issue, project, task, attachment, comment, runtime, user, workspace, and subscriber additions
- **THEN** present, omitted, allowed-null, malformed, older-server, and future-open-value cases SHALL be mapped to explicit assertions

#### Scenario: Command mapping is exact
- **WHEN** verification inspects an adapted operation
- **THEN** canonical and negative cases SHALL assert complete argv, destination, validation timing, response adapter, standard error behavior, and eager/preview equivalence

### Requirement: Repository gates remain deterministic and offline by default
The implementation SHALL pass strict OpenSpec validation, approved-contract validate/render/check, byte-stable generation, source-link audit, public-operation completeness, non-live collection isolation, focused and full non-live tests, mypy, Ruff, documentation, packaging, and release checks.

#### Scenario: Local automated suite reaches the time limit
- **WHEN** an automated local suite is expected to exceed or reaches ten minutes
- **THEN** only that run-owned test process SHALL be stopped and the unsplit suite SHALL run in GitHub Actions on the published exact revision

#### Scenario: Transient evidence remains untracked
- **WHEN** repository cleanliness is checked before publication
- **THEN** `.devlocal`, archives, binaries, collector output, raw logs, diagnostic JSON, screenshots, and transient renders SHALL be absent from Git

### Requirement: Exact-revision live gaps are verified independently
An independent Tester SHALL verify the protected live cases that cannot be sufficiently proven at lower layers against the published exact candidate revision and isolated test stand.

#### Scenario: Readiness gate precedes live actions
- **WHEN** Tester begins live verification
- **THEN** the candidate SHA, approved target CLI identity, isolated primary and denied profiles, backend, database, ports, protected rerun/runtime/subscription fixtures, distinct authenticated identities, cleanup callbacks, renderer availability, and focused lower-level results SHALL be confirmed before dispatch, and a missing prerequisite SHALL block the live attempt

#### Scenario: Live boundary cases are observed
- **WHEN** Tester executes the focused public SDK/CLI paths
- **THEN** rerun-task resume/fresh, private-project 404/list omission, project subscriber provenance, safe nonexistent-runtime update failure, and exact runtime-usage window SHALL follow the specified setup/action/assertion/cleanup sequences and record case-specific evidence

#### Scenario: Cancellation without a public trigger stays deterministic
- **WHEN** verification covers the reviewed server 499/no-body cancellation path for which pinned `0.9.0` exposes no safe deterministic public trigger
- **THEN** the required fake-CLI/process fixture SHALL emit the exact no-body nonzero response, assert standard cancellation rather than output-shape failure, and the live suite SHALL NOT claim or attempt server-side 499 proof

### Requirement: Visible output evidence is genuine and reviewable
Changed terminal output SHALL have equivalent baseline and candidate text plus real macOS PNG captures; unchanged or non-visible behavior SHALL not receive decorative images.

#### Scenario: Visible output changes
- **WHEN** implementation changes a CLI table, read output, log, progress state, or final summary
- **THEN** Tester SHALL capture equivalent `0.7.1` and `0.9.0` fixtures at the same locale, width, and output mode using the confirmed renderer, and missing captures SHALL prevent PASS

#### Scenario: Output is unchanged
- **WHEN** a case changes only typed decoding or internal error classification and actual visible output is unchanged
- **THEN** Tester SHALL publish text/assertion evidence and an explicit no-image rationale

### Requirement: Publication preserves exact provenance
Implementation and verification SHALL use normal pushes and SHALL publish the exact local/remote SHA, commands, exit codes, assertions, CI or PR links, file or commit links, and accessible evidence attachments in Multica.

#### Scenario: Remote revision matches
- **WHEN** publication completes
- **THEN** the remote branch SHA SHALL equal the locally verified SHA and no force push, merge, branch deletion, or implementation start SHALL be inferred

#### Scenario: Evidence is read back
- **WHEN** Tester posts final evidence
- **THEN** the Multica comment and attachments SHALL be read back successfully while private URLs, hostnames, personal data, credentials, and raw diagnostics remain outside public Git
