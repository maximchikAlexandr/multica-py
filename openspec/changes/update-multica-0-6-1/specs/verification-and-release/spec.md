## ADDED Requirements

### Requirement: Multica 0.6.1 coverage extends existing tables
Offline verification SHALL extend the existing approved operation, response,
model, resource, compatibility and documentation tables. Complete expected argv
SHALL cover `duplicate_of` omission and all valid direct/bound status/update
forms. Negative cases SHALL cover blank references, cancelled-only policy,
content/attachment conflicts, zero transport/upload on conflict and the
server-without-field compatibility error. No parallel fixture framework or
duplicate canonical operation row SHALL be introduced.

#### Scenario: Positive vectors prove exact command shape
- **WHEN** unit and contract tables exercise the four adapted entrypoints
- **THEN** each expected argv includes exact flag order and `--output json`, with omission represented by complete baseline argv

#### Scenario: Negative vectors fail at the owned boundary
- **WHEN** invalid status, content, attachment or response-field cases execute
- **THEN** local conflicts perform zero I/O and the CLI-owned compatibility failure performs one mutation with no SDK retry

### Requirement: Complete command and response audits are reproducible
Maintainer evidence SHALL reproduce the stable release identities, exact SDK
baseline, 205-node command inventory, two adapted-node mappings and the full
196-entrypoint response audit with nine changed and 187 unchanged semantics.
Every source link SHALL be commit-pinned. The dynamic-checkin parser defect SHALL
be explicitly reproduced and closed by pinned source/help evidence without
changing the approved inventory.

#### Scenario: Reproduced evidence agrees
- **WHEN** collect, source-aware validate, render and check run against pinned inputs
- **THEN** provenance, inventories, mappings and response verdicts agree with the approved contract or the gate fails

#### Scenario: Evidence remains outside delivery
- **WHEN** Git and built distributions are audited
- **THEN** no collector output, archive, executable, source checkout, `.devlocal`, transient render or visual HTML is tracked or packaged

### Requirement: Direct migration, documentation and rollback remain coherent
README, API, CLI coverage, compatibility, migration, contributing, service-usage
and releasing guidance SHALL describe one direct upgrade from `0.6.0` to `0.6.1`,
the interval `[0.6.0,0.6.2)`, four adapted issue entrypoints, nine changed response
semantics, compatible open/numeric behavior and excluded target features. Contract,
generated projection, handwritten code, fixtures, tests and docs SHALL roll back
together to exact baseline `48745d2fe9e80ee9c027293ef22971ff5723f5f5`.

#### Scenario: Consumer guidance matches contract and code
- **WHEN** public docs, signatures, inventories and fixtures are compared
- **THEN** duplicate transitions, compatibility, quota/usage/checkout semantics and exclusions agree exactly

#### Scenario: Rollback restores the exact SDK baseline
- **WHEN** any provenance, generation, source-link, test or package gate fails
- **THEN** all `0.6.1` behavior and claims revert together without removing reviewed `0.6.0` behavior

### Requirement: Offline quality and package gates remain strict
Delivery SHALL pass strict OpenSpec validation; approved-contract collect,
source-aware validate, deterministic double render and check; pinned source-link
audit; focused unit/contract/component/compatibility tests; Ruff check and format;
mypy source and tests; complete non-live pytest and collect-only with no live
nodes; build, sdist, wheel, isolated import/package validation; diff cleanliness;
and Git/package forbidden-content audits. Live validation SHALL remain a separate
explicit gate and SHALL NOT be fabricated by offline acceptance.

#### Scenario: Complete offline gate passes
- **WHEN** implementation is presented for review
- **THEN** every required offline, typing, lint, build, package, determinism, source-link and content-audit command exits successfully

#### Scenario: Live status is explicit
- **WHEN** a prepared live target is unavailable or not selected
- **THEN** acceptance records live validation as not run and performs no hidden backend contact
