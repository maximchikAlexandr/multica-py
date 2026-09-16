## ADDED Requirements

### Requirement: Multica 0.4.44 direct-patch compatibility is verified end to end
Offline verification SHALL cover exact `0.4.43`/`0.4.44` release, source,
archive, executable, and version JSON provenance; both 189-node public command
inventories; all 163 unique response entrypoints; comment tombstones and
keep-replies deletion; custom lifecycle projection; Triage parent presence;
docs, packaging, and `[0.4.42,0.4.45)` bounds. Repeated cases SHALL extend
existing frozen dataclass tables and shared fixtures. No mandatory offline gate
SHALL require a backend or network.

#### Scenario: Command and response audits are exhaustive
- **WHEN** contract and source-link gates inspect the direct-patch review
- **THEN** they prove 189/189 command nodes with zero topology or flag deltas, one transport adaptation, and 163 unique response rows split into 30 changed and 133 unchanged

#### Scenario: Comment matrix is presence-sensitive and non-destructive
- **WHEN** fixtures exercise omitted and valid deletion time, empty live content, tombstones with replies, null/malformed/wrong-type times, target deletion, and pre-support 404
- **THEN** public values, failures, exact argv, descendant preservation, and zero fallback calls match the approved contract

#### Scenario: Issue matrix pins lifecycle and Triage semantics
- **WHEN** fixtures exercise four custom phases, built-in keys, projection omission, malformed name/category, and Triage omitted/same/null/foreign parent cases alongside ordinary issue controls
- **THEN** decoded values, standard errors, exact argv, and authoritative no-partial-write state match the approved contract

#### Scenario: Full offline and package gates pass
- **WHEN** implementation is ready for delivery
- **THEN** strict OpenSpec, pinned-source contract validate, two-render byte equality, contract check, source-link audit, focused suites, Ruff format/check, mypy for source/tests/scripts/tools, full non-live pytest with coverage, live-node exclusion, build, and package validation all exit zero

#### Scenario: Git tracks no transient evidence
- **WHEN** repository files and final status are audited
- **THEN** no `.devlocal`, archive, binary, download, collector evidence, gap audit, response review, or transient render is tracked

### Requirement: Direct migration and release policy names safe-delete availability
Documentation SHALL describe one direct SDK migration from Multica `0.4.43`
to `0.4.44`, exact target/source/bounds, comment deletion time, keep-replies
semantics, lifecycle projection, Triage parent rejection, retained behavior,
non-SDK changes, and atomic rollback. It SHALL state that retained operations
support CLI `0.4.42` while safe comment deletion requires CLI `0.4.44`. It SHALL
not require a separate intermediate SDK release.

#### Scenario: Consumer action is explicit
- **WHEN** a caller reads migration and compatibility guidance
- **THEN** it can distinguish retained older-CLI calls, `0.4.44`-only safe deletion, omitted tombstone data, custom lifecycle projection, Triage errors, and the exclusive `0.4.45` ceiling

#### Scenario: Rollback is contract-atomic
- **WHEN** target acceptance cannot be satisfied
- **THEN** approved contract, generated runtime, public models/resources, tests, docs, and package claims are reverted together rather than publishing a mixed target claim

#### Scenario: Live verification remains gated
- **WHEN** authorized prepared `0.4.44` credentials are unavailable
- **THEN** live status is reported separately and every mandatory offline/source-backed gate remains required
