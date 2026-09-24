## ADDED Requirements

### Requirement: Multica 0.5.2 upgrade coverage is table-driven
Offline verification SHALL cover exact `0.5.1` and `0.5.2` release, source,
archive, executable, checksum, and version JSON provenance; both 201-node public
command inventories; all 167 supported response entrypoints; duplicate issue
snapshots; task supplement metadata; atomic create-time properties; docs,
packaging, and `[0.4.42,0.5.3)` compatibility. Repeated cases SHALL extend the
repository's existing frozen dataclass tables and shared fixtures. No mandatory
offline gate SHALL require a backend or network.

#### Scenario: Duplicate matrix is exhaustive
- **WHEN** issue fixtures exercise legacy omission, explicit null, a valid object, malformed objects, missing original behavior, status changes, list/get/create/update/children/search, and bound-operation paths
- **THEN** values, presence, failures, pagination, labels, metadata, properties, binding, and subprocess counts match the approved contract

#### Scenario: Supplement matrix is exhaustive
- **WHEN** agent-task and task-run fixtures exercise omitted and open capability, omitted/empty/ordered IDs, omitted/true/false permission, malformed values, and existing usage/result/error/failure members
- **THEN** both projections preserve exact values, presence, order, and unchanged legacy behavior

#### Scenario: Property matrix covers every type and failure boundary
- **WHEN** create cases exercise all property types, names and UUIDs, repeat order, eager/command/project-bound parity, duplicate, malformed, empty, archived, `__none__`, comparison, capability, canonical JSON, atomicity, and post-create mismatch paths
- **THEN** exact argv, validation timing, one-create behavior, returned snapshots, and zero fallback property calls match the approved contract

#### Scenario: Excluded surface remains absent
- **WHEN** negative inventories inspect public operations, symbols, resources, methods, enums, retries, generated mappings, and canonical vectors
- **THEN** task-supplement and duplicate mutations, comment receipt fields, issue timeline actions, and create attachment paths are absent

### Requirement: Complete upstream audits are reproducible for 0.5.2
Release acceptance SHALL reproduce the `201→201` command audit with exactly
three changed help nodes and all five source-only names classified, plus the
167-entrypoint response audit with `response_review_complete=true`. Strict
validation SHALL require exact source links, unique work-item coverage,
dispositions, normalized mappings, and no unresolved evidence.

#### Scenario: Command and response totals are exact
- **WHEN** contract, provenance, and source-link checks run at the delivery SHA
- **THEN** the approved totals, changed/unchanged rows, source-only classifications, mappings, source URLs, and test references match exactly

#### Scenario: Deterministic render has one authoritative input
- **WHEN** the approved contract is rendered twice to isolated destinations
- **THEN** relative paths and bytes are identical and collector or audit evidence is not read as production input

### Requirement: Direct 0.5.1 to 0.5.2 migration and rollback are atomic
README, API, compatibility, migration, changelog, live-target, and release
documentation SHALL describe one direct `0.5.1` to `0.5.2` migration, exact
target/source/bounds, new read projections, atomic property creation, retained
legacy behavior, deferred surfaces, and rollback. It SHALL state that retained
operations keep their existing minimums while new fields and atomic properties
require CLI `0.5.2`; it SHALL not require an intermediate SDK delivery.

#### Scenario: Consumer action and version gates are explicit
- **WHEN** a caller reads migration and compatibility guidance
- **THEN** it can distinguish retained older-CLI calls, `0.5.2`-only fields and properties, omission semantics, deferred operations, and the exclusive `0.5.3` ceiling

#### Scenario: Rollback restores one coherent contract
- **WHEN** target acceptance cannot be satisfied
- **THEN** approved contract, generated runtime, public models/resources, tests, docs, and package claims revert together to the prior `0.5.1` state

#### Scenario: Live verification remains gated
- **WHEN** an authorized prepared `0.5.2` target is unavailable
- **THEN** live status is reported separately and every mandatory offline and source-backed gate remains required

### Requirement: Offline quality and packaging gates remain strict and clean
Release acceptance SHALL run strict OpenSpec validation; approved-contract
validate, render, and check against pinned target source; deterministic double
render; source-link audit; focused unit, contract, and component suites; Ruff
check and format check; `mypy src`; `mypy tests`; complete
`pytest -m "not live"`; collect-only verification with no live nodes; build;
isolated package validation; and `git diff --check`. The final tracked tree and
packages SHALL contain no archives, binaries, `.devlocal`, collector/audit
evidence, or transient render output.

#### Scenario: Every mandatory offline gate passes
- **WHEN** the implementation is prepared for delivery
- **THEN** every named command exits zero at the same exact SHA and collect-only output contains no `tests/live` node

#### Scenario: Distribution contains only approved artifacts
- **WHEN** wheel, source distribution, tracked files, and ignored evidence paths are audited
- **THEN** generated compatibility, exports, docs, and included files match the approved contract and no forbidden evidence artifact is shipped or tracked
