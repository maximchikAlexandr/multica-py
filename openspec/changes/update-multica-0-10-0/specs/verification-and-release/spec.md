## ADDED Requirements

### Requirement: Multica 0.10.0 coverage extends existing case tables
Every changed command, response, model, adapter, error, and compatibility rule SHALL be covered by the repository's existing frozen table-case types or by one focused test where table-driven form cannot express distinct lifecycle, privacy, concurrency, or cleanup logic.

#### Scenario: Required behavior matrices are complete
- **WHEN** focused unit, contract, and component coverage is collected
- **THEN** it SHALL cover all `94` changed response verdicts; rerun-task resume/fresh; literal inline/file/stdin/empty/omitted text; metadata escaping; webhook constraints; private membership; project activity/archive/list pagination; subscriber delivery; no-body `499`; archived-project `409`; and bounded runtime-delete conflicts

#### Scenario: Existing completeness assertion remains exact
- **WHEN** public operation discovery runs
- **THEN** discovered public methods SHALL equal canonical operation cases with no allowlist or ungoverned method

### Requirement: Existing isolated verifier proves selected target process paths
The delivery SHALL set `e2e_required=true` and SHALL extend `scripts/e2e/verify_multica_test.py` rather than add a second runner. The verifier SHALL keep its wrapper-owned `multica-test` isolation, expected-version gate updated to `0.10.0`, output-outside-checkout rule, sanitized `multica-py-e2e-v2` artifact schema, immediate resource registration, and failure-safe cleanup.

#### Scenario: Readiness gate protects the run
- **WHEN** the existing verifier starts against the isolated project stand
- **THEN** it SHALL prove the exact product/test-code revision, clean published candidate, matching remote SHA, executable identity `multica-test`, observed CLI `0.10.0`, wrapper-owned profile/server/workspace isolation, empty run-owned output directory, focused lower-level readiness, and cleanup authority before creating fixtures

#### Scenario: Literal inline text round-trips
- **WHEN** the verifier creates a disposable issue through the public SDK with inline text containing literal backslashes and escape-looking sequences and reads it through a separate SDK get
- **THEN** the stored text SHALL equal the literal input and cleanup SHALL delete the disposable project/issue lifecycle

#### Scenario: File text round-trips
- **WHEN** the verifier writes a run-owned multiline UTF-8 file ending in one LF, updates the disposable issue through the approved public file-description channel, and performs a separate SDK get
- **THEN** the stored text SHALL equal the file content except the one target-trimmed trailing LF and the run-owned file SHALL be removed during cleanup

#### Scenario: Escaped metadata key round-trips
- **WHEN** the verifier calls `issues.metadata.set(issue_id, key, value)` and `issues.metadata.get(issue_id, key)` with one key containing slash, percent, space, and Unicode characters
- **THEN** one metadata entry with the exact key/value SHALL be returned, no extra path segment or entry SHALL exist, and cleanup SHALL delete the metadata before deleting the issue lifecycle

#### Scenario: Archived project rejects mutation
- **WHEN** the verifier creates a disposable project through the SDK, archives that exact project with `multica-test project archive <project-id> --output json`, then calls `projects.update(project_id, description=...)`
- **THEN** the SDK call SHALL raise the typed conflict mapped from HTTP `409`, the project SHALL remain archived and unchanged, and cleanup SHALL run `multica-test project restore <project-id> --output json` before SDK deletion

#### Scenario: Independent walkthrough is distinct
- **WHEN** Tester verifies the selected live scenarios
- **THEN** Tester SHALL use fresh disposable resources and separate public SDK/CLI actions to inspect stored text, metadata, archived state, typed error, and cleanup rather than invoke the verifier a second time

#### Scenario: Visible-output images remain unnecessary
- **WHEN** verification confirms that terminal tables, logs, progress, summaries, and browser UI are unchanged
- **THEN** no renderer prerequisite or before/after PNG SHALL be required and the evidence SHALL state the no-image rationale

## MODIFIED Requirements

### Requirement: Offline release gates are deterministic and clean
The published implementation revision SHALL pass contract validate/render/check, second-render equality, source-link audit, strict OpenSpec validation, focused tests, public-operation completeness, the full non-live suite, mypy for source and tests, Ruff check/format, documentation checks, packaging checks, live-test collection isolation, and forbidden-content audits.

#### Scenario: Local automated run remains within limit
- **WHEN** an automated local gate completes within ten minutes
- **THEN** its command, exact revision, exit code, and material assertions SHALL be recorded

#### Scenario: Long automated run moves to CI intact
- **WHEN** a local automated suite is expected to exceed ten minutes or reaches ten minutes
- **THEN** only its owned process SHALL be stopped and the unsplit suite SHALL run in GitHub Actions against the published exact revision

#### Scenario: Repository remains evidence-clean
- **WHEN** all implementation and verification artifacts are inspected before delivery
- **THEN** no `.devlocal` evidence, logs, diagnostic JSON, screenshots, hashes, environment-specific output, or visual HTML SHALL be tracked or packaged

### Requirement: Existing lower-level checks prove the SDK corrections
The implementation SHALL use the repository's existing unit, contract, fake-CLI component, lifecycle, privacy, concurrency, documentation, packaging, and CI capabilities for every scenario that does not require the selected real process/server interactions. It SHALL NOT invent unsafe or unavailable live fixtures.

#### Scenario: Private membership is deterministic below live E2E
- **WHEN** member and privileged non-member project responses are verified without a second authorized stand identity
- **THEN** pinned response fixtures SHALL prove member get/list success, non-member not-found/omission, redaction, and malformed private fields without claiming live authorization proof

#### Scenario: Cancellation is deterministic below live E2E
- **WHEN** the fake CLI returns target exit behavior for HTTP `499` with empty stdout/body
- **THEN** transport tests SHALL assert the typed cancellation exception, preserved exit semantics, no JSON-shape error, and no retry

#### Scenario: Runtime-delete conflict is deterministic below live E2E
- **WHEN** fake CLI fixtures return structured, optional-field, plain-text, and malformed runtime-delete `409` diagnostics
- **THEN** existing transport/component seams SHALL assert bounded typed conflict details, redaction, no cascade, and no follow-up deletion without risking the stand-owned runtime

#### Scenario: Rerun and webhook validation stay deterministic
- **WHEN** rerun-task resume/fresh and webhook filter constraints are tested
- **THEN** existing argv/component cases SHALL prove exact identity/mode/result mappings and that invalid required/conflicting inputs create no process

#### Scenario: Every changed scenario has one sufficient boundary
- **WHEN** OpenSpec scenarios, the verification matrix, and test discovery are reconciled
- **THEN** each scenario SHALL map to one selected live case, one sufficient lower-level assertion, or one explicit non-surface decision with no duplicate runner

### Requirement: Evidence and release handoff use one exact revision
Implementation and Tester evidence SHALL identify one published revision and SHALL keep product/test commits, CI results, selected live observations, lower-level outcomes, and Multica attachments traceable without rewriting evidence history.

#### Scenario: Exact revision is reproducible
- **WHEN** delivery is handed to verification
- **THEN** local HEAD and remote branch SHA SHALL match and all commands, commits, CI links, files, live artifacts, and assertions SHALL name that SHA

#### Scenario: Evidence publication is confirmed
- **WHEN** the Tester posts the final Multica comment
- **THEN** required MR/commit/file links and sanitized text artifacts SHALL be attached, comment and attachment read-back SHALL confirm accessibility, and private hostnames, credentials, profiles, tokens, and personal data SHALL be absent

#### Scenario: Cleanup preserves durable development results
- **WHEN** verification finishes or fails
- **THEN** run-owned local output and disposable stand resources SHALL be removed while the evidence branch, commits, links, and Multica attachments remain available; merge, closure, and branch deletion SHALL require separate authorization

### Requirement: Direct migration and rollback remain coherent
User documentation SHALL describe direct `0.7.1` to `0.10.0` migration, the preserved `0.6.2` minimum, maximum-tested `0.10.0`, policy-derived exclusive ceiling, changed retained behavior, rerun-task migration, open-value policy, deferred families, and rollback to the prior `0.7.1` contract projection.

#### Scenario: Package claims match the approved contract
- **WHEN** the package and documentation are inspected before release
- **THEN** compatibility metadata, changelog, API examples, migration guidance, generated projection, and deferred-surface list SHALL agree on the target and supported envelope

#### Scenario: Rollback requires no data migration
- **WHEN** the implementation commit set is reverted
- **THEN** the prior `0.7.1` contract and generated projection SHALL be restorable without transforming persisted user data

## REMOVED Requirements

### Requirement: Local E2E and image evidence are not required
**Reason**: Target `0.10.0` introduces selected process/server behaviors whose literal persistence and archived-state conflict cannot be fully proved by fake-CLI fixtures alone.

**Migration**: Extend the existing `scripts/e2e/verify_multica_test.py` only for the explicit live scenarios in `Existing isolated verifier proves selected target process paths`; keep images unnecessary because visible output does not change.

### Requirement: Multica 0.7.1 coverage extends existing case tables
**Reason**: The active target is `0.10.0` and the changed behavior matrix is broader.

**Migration**: Use `Multica 0.10.0 coverage extends existing case tables` and preserve the `0.7.1` rows as regression coverage.
