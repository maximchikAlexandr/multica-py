## ADDED Requirements

### Requirement: Multica 0.4.43 direct-patch compatibility is verified end to end
Offline verification SHALL cover exact `0.4.42`/`0.4.43` release, source,
archive, and executable provenance; `189/189` command inventories; all 160
approved operations and 163 unique response entrypoints; conversation-starter
request mapping; cancellation actor, run-message truncation, issue-usage counts;
status-category sorting; run-message 404/500 behavior; docs, packaging, and
`[0.4.42,0.4.44)` bounds. Repeated cases SHALL extend existing frozen dataclass
tables and shared fixtures. No mandatory offline gate SHALL require a backend or
network.

#### Scenario: Request matrix is exhaustive
- **WHEN** starter cases exercise omission, `[]`, malformed/non-tuple input, `None`, more than three entries, blank fields, and 80/81-label plus 4000/4001-prompt boundaries
- **THEN** valid cases preserve complete exact argv and invalid cases execute no transport

#### Scenario: Response matrix is presence-sensitive
- **WHEN** task-run, run-message, and issue-usage fixtures exercise legacy absence, current values, malformed shapes, open actor types, exact integers, timestamps, and false/true truncation
- **THEN** decoded values and failures match the approved contract without fabricated defaults

#### Scenario: Status and error semantics are pinned
- **WHEN** target fixtures exercise canonical/custom status sorting and run-message 404/500 diagnostics
- **THEN** order and exception classes match target semantics while unrelated sorts and transport classification remain unchanged

#### Scenario: Full offline and package gates pass
- **WHEN** implementation is ready for delivery
- **THEN** strict OpenSpec, pinned-source contract validate, two-render byte equality, contract check, source-link audit, focused suites, Ruff format/check, mypy for source/tests/scripts/tools, full non-live pytest/coverage, live-node exclusion, build, and package validation all exit zero

#### Scenario: Git tracks no transient evidence
- **WHEN** repository files and final status are audited
- **THEN** no `.devlocal`, archive, binary, download, collector evidence, gap audit, response review, or transient render is tracked

### Requirement: Direct migration and release policy names capability availability
Documentation SHALL describe one direct SDK migration from Multica `0.4.42`
to `0.4.43`, exact target/source/bounds, additive public fields, starter input,
legacy normalization, status-sort semantics, non-SDK fresh checkout, and atomic
rollback. It SHALL state that the retained surface supports `0.4.42`, while an
explicit conversation-starter mutation requires CLI `0.4.43`. It SHALL not
require an intermediate SDK release.

#### Scenario: Consumer action is explicit
- **WHEN** a caller reads migration and compatibility guidance
- **THEN** it can distinguish always-compatible retained calls, `0.4.43`-only explicit starter mutation, legacy unknown values, and the exclusive `0.4.44` ceiling

#### Scenario: Rollback is contract-atomic
- **WHEN** target acceptance cannot be satisfied
- **THEN** approved contract, generated runtime, public models/resources, tests, and docs are reverted together rather than publishing a mixed target claim

#### Scenario: Live verification remains gated
- **WHEN** authorized prepared `0.4.43` credentials are unavailable
- **THEN** live status is reported separately and all mandatory offline/source-backed gates remain required
