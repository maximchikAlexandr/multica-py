## ADDED Requirements

### Requirement: Multica 0.6.0 coverage extends merged tables
Offline verification SHALL extend existing contract, provenance, operation,
response, model, resource, compatibility and documentation tables. It SHALL cover
all four added/six changed commands, every approved mapping and boundary, all 18
changed response entrypoints, and explicit proof for 178 unchanged entrypoints.
The 29 operations introduced by PR #95 SHALL be tested as retained/adapted baseline
surface; a duplicate operation case hierarchy or fixture framework SHALL NOT be
introduced.

#### Scenario: Positive and negative vectors cover every changed rule
- **WHEN** contract and focused suites run
- **THEN** each added/changed input and response rule has source-linked success/failure evidence and invalid inputs fail at their specified ownership boundary

#### Scenario: Baseline operations are not duplicated
- **WHEN** public discovery, canonical cases and contract rows are compared
- **THEN** every approved public method has exactly one canonical row and merged PR #95 methods have no second implementation path

#### Scenario: Shared models do not leak entrypoint semantics
- **WHEN** tasks, comments, MCP or wakeup models are shared across operations
- **THEN** cursor, supplements, agent count, v2 fields and error behavior remain limited to approved entrypoints

### Requirement: Complete upstream audits are reproducible
Maintainer evidence SHALL reproduce release/checksum/binary identities, exact SDK
baseline identities, direct source comparison, all 205 command nodes, source-only
classifications, gap decisions and all 196 response entrypoints. Tracked files and
distributions SHALL exclude archives, executables, source checkouts, `.devlocal`,
collector/audit output, caches and transient render paths.

#### Scenario: Reproduced evidence agrees
- **WHEN** pinned audit inputs are regenerated outside version control
- **THEN** provenance, dispositions, mappings and 18/178 response verdicts agree with the approved contract or validation fails

#### Scenario: Evidence remains outside delivery
- **WHEN** Git and built contents are audited
- **THEN** no forbidden evidence, binary, checkout, cache or transient artifact is present

### Requirement: Direct migration and rollback are coherent
README, API, CLI coverage, compatibility, migration, contributing, service-usage
and release guidance SHALL describe one direct upgrade from approved `0.5.3` to
maximum-tested `0.6.0`, the exclusive `0.6.1` ceiling, preserved PR #95 baseline,
adapted/supported behavior, exclusions, attachment partial-side-effect handling and
separate live policy. Contract, generated projection, handwritten code, fixtures,
docs and package claims SHALL roll back together to baseline `c1842ae2…`.

#### Scenario: Consumer guidance matches code and contract
- **WHEN** public docs and inventories are compared
- **THEN** wakeup evolution, cursor, attachments, 18 changed responses, compatibility and exclusions agree exactly

#### Scenario: Rollback restores refreshed baseline
- **WHEN** any provenance, render, source-link, model, test or package gate fails
- **THEN** all `0.6.0` behavior and claims revert together without removing PR #95 baseline behavior

### Requirement: Offline quality and package gates remain strict
Delivery SHALL pass strict OpenSpec; approved-contract validate, deterministic
double render and check; pinned source-link audit; focused contract/resource/model/
compatibility suites; Ruff check/format; mypy source and tests; complete non-live
pytest and non-live collect-only with no live nodes; build; isolated package
validation; diff checks; and Git/package forbidden-content audits. Live validation
SHALL be reported separately and SHALL NOT be fabricated or required by offline
acceptance.

#### Scenario: Complete offline gate passes
- **WHEN** implementation is presented for review
- **THEN** every required offline, typing, lint, build, package, determinism, source-link and content-audit command exits successfully

#### Scenario: Live evidence is explicit
- **WHEN** prepared-target smoke is unavailable or not selected
- **THEN** offline acceptance reports live status as not run and makes no backend contact
