## ADDED Requirements

### Requirement: Multica 0.4.42 compatibility is verified end to end

Offline verification SHALL cover exact release/source/binary provenance, the
complete command and response inventories, removed Plugin and autopilot
priority surfaces, Issue/Comment/Agent/TaskRun fields, skill projections,
issue property queries, presence semantics, pagination, error mappings, docs,
packaging, and compatibility bounds. Repeated cases SHALL extend existing
frozen dataclass tables and shared fixtures. No offline gate SHALL require a
backend or network.

#### Scenario: Inventory and provenance gates are exact
- **WHEN** strict validation and source-link audit run
- **THEN** command totals are 199/189 with 166 unchanged, 21 changed, 2 added, and 12 removed; all 173 response work items are unique and pinned; and archive/binary hashes are not conflated

#### Scenario: Model and projection coverage is adversarial
- **WHEN** response fixtures exercise Issue, Comment, Agent, TaskRun, skills, and resolved properties
- **THEN** name, type, nesting, timestamp, integer precision, missing, null, empty, zero, and false behavior match the approved contract

#### Scenario: Removed surfaces have negative proof
- **WHEN** public discovery, imports, generated operations, type-check fixtures, docs, and command cases run
- **THEN** Plugin symbols and autopilot priority inputs are absent and no compatibility alias or fabricated replacement remains

#### Scenario: Query and pagination cases are complete
- **WHEN** issue-list cases exercise fields, properties, resolution, sort, limits, `__none__`, reserved operators, truncation, repeats, malformed pages, and unavailable totals
- **THEN** valid cases preserve exact argv/results and invalid/no-progress cases fail deterministically without partial completion

#### Scenario: Failure matrix is complete
- **WHEN** success and validation, auth, not-found, conflict/revision, rate, transport, malformed-output, timeout, and local-process fixtures run
- **THEN** every case has the approved payload/exit mapping and secret-safe diagnostic behavior

#### Scenario: Full offline and packaging gate passes
- **WHEN** the implementation is ready for delivery
- **THEN** strict OpenSpec, contract validate against pinned source, deterministic transient render comparison, contract check, source-link audit, Ruff, format, mypy for source/tests/scripts, non-live pytest/coverage, build, and package validation all pass

#### Scenario: Git tree contains no transient evidence
- **WHEN** repository tracked files and status are audited
- **THEN** no `.devlocal`, collector evidence, downloads, response-review, gap-audit, or transient render output is tracked

### Requirement: Direct migration and release policy is explicit

Documentation SHALL describe one direct SDK migration from CLI `0.4.28` to
`0.4.42`; it SHALL not require delivery releases for intervening versions.
The changelog/API/migration/compatibility documentation SHALL identify all
breaking removals, projection choices, opt-in additions, exact bounds, and
rollback. A gated live-negative suite SHALL use an authorized prepared
`0.4.42` target only and SHALL not weaken offline acceptance when credentials
are absent.

#### Scenario: Migration describes consumer action
- **WHEN** a consumer upgrades directly from the old baseline
- **THEN** docs identify Plugin and autopilot priority removals, skill projection behavior, issue query additions, and the exact `0.4.42` compatibility requirement

#### Scenario: Rollback is contract-atomic
- **WHEN** implementation cannot satisfy target gates
- **THEN** contract, generated runtime, public surface, tests, and docs are reverted together rather than publishing a mixed compatibility claim

#### Scenario: Live checks remain gated
- **WHEN** authorized `0.4.42` credentials and target are unavailable
- **THEN** live status is reported separately and all offline/source-backed gates remain mandatory

## REMOVED Requirements

### Requirement: v0.4.28 compatibility delta is verified end to end

**Reason**: Release verification now covers the direct `0.4.28` to `0.4.42` upgrade and target removals.

**Migration**: Use the `Multica 0.4.42 compatibility is verified end to end` requirement above.
