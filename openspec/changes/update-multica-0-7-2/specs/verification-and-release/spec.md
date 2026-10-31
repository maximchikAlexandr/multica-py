## ADDED Requirements

### Requirement: Multica 0.7.2 coverage extends existing case tables
Verification SHALL extend existing frozen unit/contract/component/process/live case tables and shared fixtures rather than add a second test framework. Coverage SHALL include rerun full/short IDs, issue narrowing, fresh presence, legacy warning, steering permission/self/caps/races/attachment conflict/multiple receipts, daemon force lifecycle, property 50/51/200/201, task authority/redaction, and foreign-chat 404. Every repository task SHALL be Implementer-owned preparation or implementation work; independent execution SHALL occur only as a parent-level gate after all WP children fan in.

#### Scenario: Lower-level tests prove deterministic SDK behavior
- **WHEN** focused offline checks run
- **THEN** complete argv, input validation, transport mode, response decoding, privacy-safe typed errors, public inventory, deterministic generation, and malformed shapes SHALL be asserted without a live-server claim

#### Scenario: Live tests prove server-owned behavior only
- **WHEN** the isolated live suite runs against exact Multica `0.7.2` after four independently authenticated caller profiles are supplied
- **THEN** real authority/privacy steering and foreign-chat cases SHALL be observed, while cap/race mapping, daemon lifecycle, contract generation, and local validation SHALL remain deterministic lower-level checks and SHALL not be redundantly retested live

#### Scenario: Missing caller authentication blocks the live gate
- **WHEN** the environment provides only the existing single preauthenticated profile or lacks documented supported provisioning for any required caller
- **THEN** readiness SHALL fail before mutation, the authority/privacy case SHALL remain blocked rather than skipped or simulated, and no implementation or Tester evidence SHALL claim it passed

### Requirement: Isolated E2E evidence is exact-revision and recoverable
The live test repository SHALL be `https://github.com/maximchikAlexandr/multica-py`. After full WP fan-in, Tester SHALL use the isolated `multica-test` stand, four test-owner-provisioned authenticated caller profiles and run-owned data, never the primary profile/daemon/containers or reference checkout. Each case SHALL record product SHA, CLI version/commit, fixture IDs, command, exit status, assertions, and cleanup; actual logs, diagnostic JSON, hashes, and images SHALL be Multica-only.

#### Scenario: Readiness gates protect the environment
- **WHEN** Tester begins a live attempt
- **THEN** exact candidate SHA, target CLI identity, distinct caller identities, provisioning provenance, stand readiness, permissions, and test fixture ownership SHALL be confirmed before mutation

#### Scenario: Cleanup preserves evidence but removes mutable state
- **WHEN** live verification completes or fails
- **THEN** each captured nonterminal run SHALL be cancelled and refreshed to terminal within the bounded cleanup window before the owning member deletes the uniquely named disposable project; public read-back SHALL prove project/issue gets and captured chat-thread reads raise redacted `NotFoundError` and run IDs are absent from captured agents' task listings, while supplied credentials/profiles and evidence links/commits remain untouched

#### Scenario: Residual graph state blocks further attempts
- **WHEN** a captured run does not become terminal, project deletion fails, or any issue/run/chat fixture remains observable after deletion
- **THEN** cleanup and the case SHALL fail, a sanitized recovery manifest SHALL retain the disposable project and captured object identifiers for the environment owner, no unsupported per-object delete SHALL be attempted, and no further live attempt SHALL start until recovery is confirmed

### Requirement: Release gates and documentation describe the direct migration
User and maintainer documentation SHALL describe direct `0.7.1` to `0.7.2` migration, preserved `0.6.2` minimum, maximum-tested `0.7.2`, exclusive `0.7.3` ceiling, rerun deprecation/migration, steering/force/property/privacy behavior, and rollback. Delivery SHALL pass strict OpenSpec, contract/source validation, transient render/check, source-link, deterministic diff, operation completeness, focused tests, live isolation collection, typing, Ruff, docs, packaging, and exact local/remote SHA gates.

#### Scenario: Published exact revision is independently verifiable
- **WHEN** the OpenSpec-only plan or later implementation revision is delivered
- **THEN** local HEAD SHALL equal the normally pushed remote branch SHA, required commands/exit codes and CI/MR/commit/file links SHALL be published, attachments SHALL be read back, and no collector output, archive, binary, audit, transient rendering, private hostname, credential, or personal data SHALL be tracked

#### Scenario: Long automated suites follow the workspace limit
- **WHEN** an automated local suite is expected to exceed or reaches ten minutes
- **THEN** only its owned test process SHALL stop and the unsplit suite SHALL run in GitHub Actions on the published exact revision; manual Tester walkthroughs SHALL remain governed by evidence and attempt controls rather than the automated-suite time limit
