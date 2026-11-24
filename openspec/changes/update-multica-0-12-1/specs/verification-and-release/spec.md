## ADDED Requirements

### Requirement: Multica 0.12.1 coverage extends existing test layers
Every adapted command, response, model, adapter, compatibility rule, error, migration, and replacement operation SHALL map to an existing frozen table case or one focused lifecycle/integration test where a table cannot express the risk.

#### Scenario: Command and response matrices are complete
- **WHEN** focused coverage is audited
- **THEN** it SHALL cover all `34` changed commands, the removed and replacement issue operation, all `118` changed response rows, positive and negative inputs, omission/nullability/open-enum/pagination cases, malformed output, and typed 400/409/413/499 errors

#### Scenario: Public operation completeness remains exact
- **WHEN** public method discovery runs
- **THEN** discovered eager and command methods SHALL equal canonical approved operation cases with no allowlist or ungoverned method

### Requirement: Four live cases close material integration gaps
The isolated project stand SHALL verify issue description revision conflict, comment idempotent replay, skill base-revision conflict, and guest/project-progress visibility against the exact published candidate using the `multica-test` profile and daemon.

#### Scenario: Readiness gate protects the stand and attempt budget
- **WHEN** Tester prepares a live attempt
- **THEN** the exact candidate and test revisions, target CLI version, isolated profile/daemon, frontend/API reachability, disposable data namespace, permissions, and runner collection SHALL be confirmed before mutation

#### Scenario: Revision and replay semantics hold live
- **WHEN** Tester performs the planned issue, comment, and skill create/read/write/replay actions
- **THEN** current revisions SHALL succeed, stale revisions SHALL return typed conflicts without lost state, and repeated idempotent comment creation SHALL resolve to one logical comment

#### Scenario: Guest redaction and project progress hold live
- **WHEN** the non-guest owner creates two UUID-named run-owned issues in a dedicated empty prepared project already readable by the guest, leaves one `todo`, moves one to `done`, and both actors inspect that same project/workspace state
- **THEN** both project projections SHALL report the reviewed progress fields for one done of two total and 50 percent where supplied, the non-guest workspace projection SHALL preserve the approved guest project scope, the guest-visible membership projection SHALL omit redacted project identifiers, and cleanup SHALL delete every run-owned issue and restore the prepared project to its empty baseline without mutating the project or membership

#### Scenario: Failure-safe cleanup preserves evidence
- **WHEN** a live case passes or fails
- **THEN** Tester SHALL remove run-owned test entities and local diagnostics while preserving branch, commits, CI links, and Multica evidence

### Requirement: Visible-output evidence is conditional and honest
The planned implementation SHALL not claim a visible CLI/UI change because the SDK consumes structured output; actual baseline/candidate text and PNG capture SHALL become mandatory only if implementation changes terminal tables, logs, progress, summaries, or browser UI.

#### Scenario: No visible output changed
- **WHEN** implementation and independent review confirm no human-visible renderer changed
- **THEN** evidence SHALL record the no-image rationale and SHALL not include decorative screenshots

#### Scenario: Visible output changes unexpectedly
- **WHEN** any human-visible output differs on the candidate
- **THEN** verification SHALL stop until a planning revision names equivalent baseline/candidate fixtures, actual text capture, locale/width/output mode, a confirmed Mac renderer, before/after PNG filenames, and Multica attachment checks

### Requirement: Offline and CI release gates are deterministic
The published implementation revision SHALL pass strict OpenSpec validation, contract validate/render/check, deterministic regeneration diff, source-link audit, focused tests, public-operation completeness, live-test collection isolation, mypy for source/tests/scripts, Ruff check/format, documentation checks, package build/validation, compatibility jobs, and the full non-live suite.

#### Scenario: Local automated run remains within limit
- **WHEN** an automated local gate completes within ten minutes
- **THEN** its exact command, candidate revision, exit code, and material assertions SHALL be recorded

#### Scenario: Long automated run moves intact to CI
- **WHEN** an automated suite is expected to exceed or reaches ten minutes locally
- **THEN** only its owned process SHALL be stopped and the unsplit suite SHALL run in GitHub Actions against the published exact revision

#### Scenario: Repository remains evidence-clean
- **WHEN** tracked files and package contents are inspected
- **THEN** `.devlocal`, archives, binaries, collector output, response manifests, transient renders, logs, screenshots, diagnostic JSON, hashes, credentials, private hostnames, and personal data SHALL be absent

### Requirement: Independent evidence names one published revision
Implementation and Tester evidence SHALL identify one normally pushed candidate revision and SHALL keep development results, tests, CI, manual observations, and Multica attachments traceable without rewriting history.

#### Scenario: Exact revision is reproducible
- **WHEN** delivery is handed to Tester
- **THEN** local HEAD and remote branch SHA SHALL match and all commands, commits, CI/MR/file links, and assertions SHALL identify that SHA

#### Scenario: Tester remains independent
- **WHEN** Tester verifies from a fresh checkout
- **THEN** Tester SHALL not edit implementation, CI tests, fixtures, or evidence-generating product scripts and SHALL report findings against the exact revision

#### Scenario: Evidence publication is confirmed
- **WHEN** Tester posts final evidence in Multica
- **THEN** required text, command/exit/assertion summaries, commit/MR/file/CI links, and any required images SHALL be attached or linked, and comment plus attachment read-back SHALL confirm accessibility

### Requirement: Direct migration and rollback remain coherent
User documentation SHALL describe direct `0.7.1` to `0.12.1` migration, preserved `0.6.2` floor, maximum-tested `0.12.1`, exclusive `0.12.2` ceiling, `rerun` replacement, revision/conflict/replay/redaction semantics, deferred families, and rollback to the prior approved projection.

#### Scenario: Package claims agree
- **WHEN** package metadata, generated projection, changelog, API examples, compatibility, coverage, migration, and release documentation are inspected
- **THEN** all SHALL agree on the target, compatibility envelope, public operation set, and deferred scope

#### Scenario: Rollback requires no persisted-data migration
- **WHEN** the implementation commit set is reverted
- **THEN** the prior `0.7.1` contract and projection SHALL be restorable without transforming persisted user data
