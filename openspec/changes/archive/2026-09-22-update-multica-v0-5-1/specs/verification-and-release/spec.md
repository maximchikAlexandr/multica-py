## ADDED Requirements

### Requirement: Multica 0.5.1 upgrade coverage is table-driven
Offline unit, contract, and component coverage SHALL extend existing frozen
case tables and shared fixtures for present, omitted/legacy, and malformed
`wakeup_id` and `call_id` payloads. Coverage SHALL verify the `AgentTask`
projection from `agents.tasks`, the `TaskRun` projection from `issues.runs`,
run-message sequence ordering, serialization/presence behavior,
complete argv and transport calls, and unchanged legacy payloads without adding
duplicate test helpers or a parallel case framework.

#### Scenario: Present and omitted matrices cover every adapted entrypoint
- **WHEN** the focused model, resource, contract, and component suites run
- **THEN** `agents.tasks` (`AgentTask`), `issues.runs` (`TaskRun`), and `issues.run_messages` each have present and omitted/legacy proof and malformed types fail at the protocol boundary

#### Scenario: Deferred surface has a negative inventory guard
- **WHEN** public method, operation, generated symbol, and documentation inventories are audited
- **THEN** no `issue wakeup` entrypoint is present and all seven CLI nodes remain explicit deferred rows in the approved contract

### Requirement: Complete upstream audits are reproducible
Offline audit fixtures SHALL reproduce 194 baseline and 201 target public help
nodes, seven additions, zero removals/renames/moves, two changed existing nodes,
164 approved operation IDs, and 167 supported response entrypoints with
`response_review_complete=true`. Exactly three response entrypoints SHALL be
classified changed and 164 unchanged.

#### Scenario: Command and response totals agree
- **WHEN** the gap and response audits are rerun against the pinned baseline and target source snapshots
- **THEN** all command, operation, and response totals and dispositions equal the approved contract with no unresolved source-only name

#### Scenario: Source links stay pinned and resolvable
- **WHEN** source-link audit checks every changed, retained, deferred, and non-SDK decision
- **THEN** every link targets either baseline commit `2df765a3c8f39789c9fb76316378bcffc20d22d9` or target commit `f41fae6b08fb734afcbd13205c0b3203dd0bc9c6` and resolves to the reviewed symbol or range

### Requirement: Direct migration and package claims are atomic
README, API reference, migration guide, changelog, live-test preparation, and
package assertions SHALL describe one direct `0.5.0` to `0.5.1` upgrade. They
SHALL state the `[0.4.42,0.5.2)` reviewed interval, maximum-tested `0.5.1`,
optional correlation-field behavior, deferred wakeup family, and non-SDK
runtime-profile disposition. No intermediate SDK release SHALL be introduced.

#### Scenario: Documentation teaches the supported delta only
- **WHEN** a maintainer or caller reads upgrade documentation
- **THEN** they can distinguish the two supported optional fields from deferred wakeup operations and can identify the exact target and compatibility gate

#### Scenario: Package metadata agrees with generated runtime
- **WHEN** the built wheel and source distribution are inspected
- **THEN** their generated target, compatibility assertions, exports, and documentation match the approved `0.5.1` contract and contain no review-only evidence

### Requirement: Release gates remain offline and clean
The delivery SHALL pass strict OpenSpec validation, approved-contract
validate/render/check against the pinned target source, two byte-identical
renders, source-link audit, Ruff check and format check, `mypy src`, `mypy
tests`, `pytest -m "not live"`, non-live collect-only verification, focused
unit/contract/component tests, build and package validation, and `git diff
--check` without backend or network access. Live smoke SHALL remain separately
gated and SHALL only decode prepared `0.5.1` responses. Tracked files SHALL
exclude downloaded archives, binaries, `.devlocal`, collector evidence, audit
outputs, and transient renders.

#### Scenario: Complete offline gate succeeds
- **WHEN** the implementation is ready for delivery
- **THEN** every required offline command exits zero at one clean exact commit and collect-only output contains no `tests/live/*` node

#### Scenario: Transient evidence is not promoted
- **WHEN** tracked files and package contents are audited
- **THEN** only approved contract, deterministic runtime, implementation, tests, fixtures, specs, and documentation are present and all evidence/download/render paths remain untracked
