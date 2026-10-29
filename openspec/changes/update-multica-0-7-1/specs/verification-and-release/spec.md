## ADDED Requirements

### Requirement: Multica 0.7.1 coverage extends existing case tables
Every changed command, response, model, adapter, error, and compatibility rule SHALL be covered by the repository's existing frozen table-case types or by one focused test where table-driven form cannot express distinct lifecycle or concurrency logic.

#### Scenario: Required behavior matrices are complete
- **WHEN** focused unit, contract, and component coverage is collected
- **THEN** it SHALL cover wakeup blocked create/update/get/list/events and negatives; agent allowed/reserved/retained/omitted/empty arguments; autopilot success/blocked/retry/legacy-null settlement; issue boundary and assignee behavior; project-resource concurrency; skill portable/atomic success and failures; and open process-cleanup outcomes

#### Scenario: Existing completeness assertion remains exact
- **WHEN** public operation discovery runs
- **THEN** discovered public methods SHALL equal canonical operation cases with no allowlist or ungoverned method

### Requirement: Offline release gates are deterministic and clean
The published implementation revision SHALL pass contract validate/render/check, source-link audit, strict OpenSpec validation, focused tests, the full non-live suite, mypy for source and tests, Ruff check/format, documentation checks, packaging checks, and live-test collection isolation.

#### Scenario: Local automated run remains within limit
- **WHEN** an automated local gate completes within ten minutes
- **THEN** its command, exact revision, exit code, and material assertions SHALL be recorded

#### Scenario: Long automated run moves to CI intact
- **WHEN** a local automated suite is expected to exceed ten minutes or reaches ten minutes
- **THEN** only its owned process SHALL be stopped and the unsplit suite SHALL run in GitHub Actions against the published exact revision

#### Scenario: Repository remains evidence-clean
- **WHEN** all implementation and verification artifacts are inspected before delivery
- **THEN** no `.devlocal` evidence, logs, diagnostic JSON, screenshots, hashes, or environment-specific output SHALL be tracked

### Requirement: Existing lower-level checks prove the SDK corrections
The implementation SHALL use the repository's existing unit, contract, fake-CLI component, lifecycle, concurrency, documentation, packaging, and CI capabilities to prove every changed SDK scenario without adding a task-specific live script, repository target, or infrastructure.

#### Scenario: Every changed scenario has sufficient coverage
- **WHEN** wakeup, agent, autopilot, issue, project-resource, skill, and process-cleanup coverage is reviewed
- **THEN** every scenario SHALL map to a deterministic test and assertion at the lowest sufficient layer, including controlled lifecycle and interleaving fixtures where a simple table row is insufficient

#### Scenario: Independent verification uses the exact revision
- **WHEN** the Tester verifies the delivery from a fresh checkout
- **THEN** the Tester SHALL confirm the exact published revision, inspect the scenario-to-test mapping, run the focused lower-level checks, and verify the corresponding CI evidence without representing those checks as live-server proof

#### Scenario: No new infrastructure is introduced
- **WHEN** verification artifacts and dependencies are inspected
- **THEN** no task-specific E2E script, repository URL, profile, daemon, backend, database, port, credential, or additional runner SHALL be required

#### Scenario: No decorative images are required
- **WHEN** verification confirms that terminal tables, logs, progress, summaries, and browser UI are unchanged
- **THEN** the evidence SHALL omit before/after PNGs and SHALL state why no visible-output comparison applies

### Requirement: Evidence and release handoff use one exact revision
Implementation and Tester evidence SHALL identify one published revision and SHALL keep product/test commits, CI results, manual observations, and Multica attachments traceable without rewriting evidence history.

#### Scenario: Exact revision is reproducible
- **WHEN** delivery is handed to verification
- **THEN** local HEAD and remote branch SHA SHALL match and all commands, commits, CI links, files, and assertions SHALL name that SHA

#### Scenario: Evidence publication is confirmed
- **WHEN** the Tester posts the final Multica comment
- **THEN** required MR/commit/file links and sanitized text artifacts SHALL be attached, comment read-back SHALL confirm accessibility, and private hostnames, credentials, profiles, tokens, and personal data SHALL be absent

#### Scenario: Cleanup preserves durable development results
- **WHEN** verification finishes or fails
- **THEN** run-owned local diagnostic output SHALL be removed while the evidence branch, commits, links, and Multica attachments remain available; merge, closure, and branch deletion SHALL require separate authorization

### Requirement: Direct migration and rollback remain coherent
User documentation SHALL describe direct `0.7.0` to `0.7.1` migration, the preserved `0.6.2` minimum, maximum-tested `0.7.1`, exclusive `0.7.2` ceiling, changed retained behavior, open-value policy, and rollback to the prior contract projection.

#### Scenario: Package claims match the approved contract
- **WHEN** the package and documentation are inspected before release
- **THEN** compatibility metadata, changelog, API examples, migration guidance, and generated projection SHALL agree on the target and supported envelope

#### Scenario: Rollback requires no data migration
- **WHEN** the implementation commit set is reverted
- **THEN** the prior `0.7.0` contract and generated projection SHALL be restorable without transforming persisted user data
