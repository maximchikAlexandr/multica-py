## ADDED Requirements

### Requirement: Accepted history migrates without rewrite or silent reuse

Verification SHALL preserve immutable composition and accepted WP-01/02/03 SHAs,
prove the new planning revision descends from accepted integration
`9b5d112830831f9e727b35f4936f923ec9429cc7`, and distinguish the original
composition planning parent from the new final `VERIFIED_PLANNING_SHA`. The old
WP-04 blocked attempt and every old ACCEPT marker SHALL NOT be treated as
acceptance under the new graph revision. Before resumed implementation,
verification SHALL prove exactly one newly created or idempotently recovered
replacement is the only nonterminal direct child, retains the exact
implementation parent with `stage=null`, and carries the all-covering
`single_wp_no_dag` contract without stage, dependency, frontier, or DAG fields.
MYL-576 and MYL-577 SHALL be terminal duplicates of that replacement. Accepted
historical children SHALL remain terminal so completion of the replacement can
close parent fan-in.

#### Scenario: Accepted history is reconciled

- **WHEN** the revised implementation contract, direct child set, and candidate history are checked
- **THEN** immutable composition parents, accepted WP SHAs, current integration ancestry, and both planning identities match their declared roles; exactly one replacement is the sole unstaged nonterminal child under the exact parent; MYL-576 and MYL-577 are its cancelled duplicates; and no obsolete child can prevent final children-done fan-in

#### Scenario: An old result is reused silently

- **WHEN** a result or ACCEPT from the prior graph revision is offered as evidence for revised remaining tasks
- **THEN** acceptance fails until the revised package is executed and independently accepted on the new exact input

### Requirement: Remaining upgrade coverage is closed and table-driven

Every affected revised scenario and all 196 supported response work items SHALL
map to a frozen case-table row, existing sufficient assertion, accepted-history
regression, or explicit non-surface decision. Repeated coverage SHALL extend
existing tables rather than create a parallel framework.

#### Scenario: Coverage reconciliation runs

- **WHEN** contract, test discovery, accepted-history records, and exclusions are compared
- **THEN** every item has exactly one decision and sufficient positive, negative, fixture, documentation, or non-surface evidence

### Requirement: Offline release gates are deterministic and sufficient

The exact candidate SHALL pass composition/accepted-history ancestry, final
OpenSpec equality to the new verified planning revision, strict source-link and
contract validation, deterministic render, generated freshness, focused
unit/resource/component/contract tests, complete non-live tests, type, lint,
package build/import, documentation, and forbidden-content checks in GitHub CI.

#### Scenario: A deterministic gate detects drift

- **WHEN** ancestry, accepted-history regression, final OpenSpec equality, a second render, generated check, source link, lower-level assertion, package import, or forbidden-content audit differs
- **THEN** release readiness fails until the approved source or handwritten implementation is reconciled

#### Scenario: GitHub CI evaluates the candidate

- **WHEN** the implementation revision is published for review
- **THEN** ordinary CI runs the named offline checks against that exact SHA without live credentials or stand dependencies

### Requirement: Local E2E and image evidence are not required

The delivery SHALL set `e2e_required=false` because every revised observable
result is fully asserted at deterministic source, contract, fake-CLI, component,
package, or CI boundaries and no visible-output requirement remains.

#### Scenario: The stand is unavailable

- **WHEN** verification is planned or executed without the project stand
- **THEN** no live fixture is invented and the complete named offline gate set remains mandatory

#### Scenario: Evidence is published

- **WHEN** final verification is reported
- **THEN** commit, accepted-history, planning, CI, command, exit-code, assertion, limitation, and cleanup evidence is published in Multica without screenshots, terminal captures, live logs, private endpoints, or credentials
