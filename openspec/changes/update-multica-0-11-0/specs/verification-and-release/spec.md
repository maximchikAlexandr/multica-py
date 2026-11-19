## ADDED Requirements

### Requirement: Offline verification closes the approved 0.11.0 contract
Offline verification SHALL run strict OpenSpec validation, approved-contract
validate/render/check, second-render equality, exact source-link audit, public
operation completeness, focused unit/contract/component/packaging checks, Ruff,
`mypy` for source and tests, documentation checks, package build/import, and
forbidden-content checks. Offline tests SHALL require no backend or network.

#### Scenario: Candidate is ready for independent verification
- **WHEN** all required offline gates run on one candidate revision
- **THEN** every gate succeeds and records its exact command, exit status, and material assertion

#### Scenario: Automated suite exceeds the local limit
- **WHEN** an automated suite is expected to exceed or reaches ten minutes locally
- **THEN** only its owned process is stopped and the unsplit suite runs in GitHub Actions on the published exact revision

### Requirement: Exact-revision live verification uses the existing isolated seam
Live verification SHALL extend only `scripts/e2e/verify_multica_test.py` and
its trusted exact-PR-head workflow. It SHALL use wrapper-owned `multica-test`
configuration, isolated disposable stand data, observed CLI `0.11.0`, an
outside-checkout output directory, exact product/test revision recording,
sanitized allowlisted evidence, and failure-safe cleanup.

#### Scenario: Readiness passes
- **WHEN** the verifier starts on an authorized candidate
- **THEN** exact local/remote SHA, wrapper isolation, observed target version, focused lower-level gates, output policy, and cleanup authority are proven before a live action

#### Scenario: Readiness identity differs
- **WHEN** the checkout, remote head, configured wrapper, or observed CLI version differs from the approved target
- **THEN** the verifier exits before creating or mutating stand data

### Requirement: Live cases are limited to remaining integration gaps
The live verifier and independent Tester SHALL cover only behavior that requires
real process/server persistence: literal inline text, file text, escaped metadata
keys, and archived-project mutation refusal. Private non-member behavior,
rerun-task lifecycle shape, no-body cancellation, webhook validation,
runtime-delete conflict, and skill-limit handling SHALL use deterministic
lower-level evidence unless safe authorized live prerequisites are available.

#### Scenario: Literal and file persistence are verified
- **WHEN** disposable issues are updated through inline and file channels and read through a separate SDK call
- **THEN** stored text matches the approved literal and newline contracts and cleanup succeeds

#### Scenario: Archived mutation is refused
- **WHEN** a disposable project is archived through the isolated CLI and updated through the SDK
- **THEN** the SDK returns the typed conflict, state is unchanged, and cleanup restores before deletion

#### Scenario: Unsafe live prerequisite is absent
- **WHEN** a case needs a second identity, nondeterministic cancellation, or mutation of the stand-owned runtime
- **THEN** no live PASS is claimed and focused lower-level evidence records the limitation

### Requirement: Independent evidence is published outside Git
The Tester SHALL perform fresh public actions and inspect resulting output or
state rather than merely rerun the automatic verifier. Real logs, outputs,
diagnostic JSON, hashes, commands, exit statuses, provenance, and images SHALL
be published only in Multica with comment and attachment read-back; ordinary
scripts, fixtures, generated product artifacts, and commits SHALL remain in Git.

#### Scenario: Tester publishes a verdict
- **WHEN** independent verification completes on the consolidated revision
- **THEN** every planned case has a revision-bound outcome, assertion summary, evidence link or stated limitation, cleanup result, and read-back confirmation

#### Scenario: Visible output remains unchanged
- **WHEN** implementation does not change terminal tables, logs, progress, summaries, browser UI, or Mac-rendered output
- **THEN** no decorative before/after image is required and the evidence records that rationale

### Requirement: Planning and implementation publication are exact-SHA safe
Planning SHALL contain only OpenSpec artifacts and `delivery-plan.md` in one
Conventional Commit. Planning and implementation publication SHALL use ordinary
push, SHALL prove remote SHA equals the verified local SHA, and SHALL exclude
`.devlocal`, collector renderings, transient audit output, and generated visual
reports from tracked Git.

#### Scenario: Planning package is published
- **WHEN** the planning commit is pushed
- **THEN** the worktree is clean, remote branch SHA equals local HEAD, and implementation remains behind explicit human approval
