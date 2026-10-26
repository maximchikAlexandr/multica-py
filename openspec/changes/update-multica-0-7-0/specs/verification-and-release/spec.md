## ADDED Requirements

### Requirement: Accepted PR 101 coverage remains a release gate

Verification SHALL prove the composition commit has exact PR #101 head as first
parent, the Plan-Verifier-approved planning SHA as second parent, exact
integration target `a96eecf3e12a88dd7b4d56e1aafae3285fb0990c` in its ancestry,
the published OpenSpec subtree unchanged, and accepted PR #101 behavior intact
before remaining `0.7.0` adaptations are accepted.

#### Scenario: Baseline reconciliation runs

- **WHEN** the composition and consolidated candidate are checked against their exact parents, OpenSpec input, and accepted PR #101 public signatures, canonical vectors, fixtures, and generated bindings
- **THEN** both parent identities and integration ancestry match, the OpenSpec subtree is byte-identical, and every retained behavior matches or has an explicit source-pinned `0.7.0` adapt decision

### Requirement: Remaining upgrade coverage is closed and table-driven

Every affected remaining-delta scenario and all 196 supported response work
items SHALL map to a frozen case-table row, existing sufficient assertion, or
explicit retained/non-surface decision. Repeated coverage SHALL extend existing
tables rather than create a parallel framework.

#### Scenario: Coverage reconciliation runs

- **WHEN** contract and test discovery compare target decisions with test references
- **THEN** every item has exactly one decision and sufficient positive, negative, fixture, and documentation coverage

### Requirement: Offline release gates are deterministic and sufficient

The exact candidate SHALL pass baseline ancestry/preservation, strict source-link
audit, contract validation, deterministic render, generated freshness, focused
unit/resource/component/contract tests, complete non-live tests, type, lint,
package build/import, documentation, and forbidden-content checks in GitHub CI.

#### Scenario: A deterministic gate detects drift

- **WHEN** ancestry, a second render, generated check, source link, lower-level assertion, package import, or forbidden-content audit differs
- **THEN** release readiness fails until the approved source or handwritten implementation is reconciled

#### Scenario: GitHub CI evaluates the candidate

- **WHEN** the implementation revision is published for review
- **THEN** ordinary CI runs the named offline checks against that exact SHA without live credentials or stand dependencies

### Requirement: Local E2E and image evidence are not required

The delivery SHALL set `e2e_required=false` because every remaining observable
result is fully asserted at deterministic contract, fake-CLI, component, package,
or CI boundaries and no visible output requirement remains.

#### Scenario: The stand is unavailable

- **WHEN** verification is planned or executed without the project stand
- **THEN** no live fixture is invented and the complete named offline gate set remains mandatory

#### Scenario: Evidence is published

- **WHEN** final verification is reported
- **THEN** commit, CI, command, exit-code, and assertion evidence is published in Multica without screenshots, terminal captures, live logs, private endpoints, or credentials
