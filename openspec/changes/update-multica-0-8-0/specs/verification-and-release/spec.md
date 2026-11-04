## ADDED Requirements

### Requirement: Multica 0.8.0 coverage extends existing case tables
Implementation SHALL extend the repository's existing frozen operation,
component, decode, compatibility, contract-mutation, and packaging tables.
Repeated behavior SHALL be added as rows rather than parallel test files or a
new test framework. Tests SHALL cover positive, negative, omission, null,
boundary, malformed, warning, privacy, and zero-I/O validation scenarios from
the delta specs.

#### Scenario: Public discovery and case coverage agree
- **WHEN** operation discovery and completeness assertions run
- **THEN** every canonical public operation has one canonical case, new aliases are absent, and removed rerun symbols have no stale row

#### Scenario: Changed response fields are table-driven
- **WHEN** task credits, runtime concurrency, workflow, rerun-task, steering, and diagnostic payload cases run
- **THEN** each reviewed variant is asserted through shared typed fixtures with exact argv and result behavior

### Requirement: Contract generation is deterministic and source pinned
Verification SHALL validate the reviewed contract against exact target source,
render runtime and transient projections, run the contract checker and
source-link audit, regenerate twice, and prove no diff from the checked-in
generated projection. Only the approved contract SHALL be a tracked generator
input.

#### Scenario: Deterministic regeneration is clean
- **WHEN** generation is repeated from the same reviewed contract and pinned source
- **THEN** the tracked projection is byte-identical and transient output remains outside Git

#### Scenario: Wrong source revision fails closed
- **WHEN** contract validation uses any source revision other than the approved target commit
- **THEN** validation fails before a compatibility claim is published

### Requirement: Offline quality and package gates remain strict
The candidate SHALL pass strict OpenSpec validation, focused model/resource/
transport tests, complete offline tests, Ruff, mypy for source and tests,
contract/source checks, compatibility tests, documentation checks, and package
build/install tests. Automated local suites expected to exceed the workspace
limit SHALL run in GitHub Actions against the published exact revision rather
than being split to evade the limit.

#### Scenario: One clean candidate owns the evidence
- **WHEN** release verification begins
- **THEN** every reported command, exit status, commit/file link, CI result, and assertion identifies the same candidate SHA and the tracked tree is clean

#### Scenario: Evidence artifacts stay out of Git
- **WHEN** collectors, archives, binaries, logs, diagnostic JSON, hashes, or images are produced during verification
- **THEN** they are published only through the required Multica evidence channel and are absent from the tracked tree

### Requirement: Direct migration and rollback are explicit
Documentation SHALL describe the direct `0.7.1` to `0.8.0` compatibility move,
the breaking rerun-method migration, supported/deferred/non-SDK command
decisions, open vocabularies, and the atomic rollback of contract, generated
code, source pins, tests, and claims.

#### Scenario: Consumer migration names the behavior change
- **WHEN** a consumer reads the migration guide for issue reruns
- **THEN** it identifies `rerun_task`, the task-run result, issue scope, fresh mode, and the absence of a silent legacy shim

#### Scenario: Release claim is bounded
- **WHEN** package and compatibility documentation announce `0.8.0`
- **THEN** they claim only reviewed SDK coverage and do not imply coverage for deferred picker, hidden commands, UI/provider-only changes, or unreviewed server routes
