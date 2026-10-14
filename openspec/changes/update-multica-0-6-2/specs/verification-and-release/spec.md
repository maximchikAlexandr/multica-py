## ADDED Requirements

### Requirement: Multica 0.6.2 coverage extends existing case tables

Verification SHALL extend the existing frozen unit, contract, and component case tables for every changed `0.6.2` contract. It SHALL cover list-property JSON and comma forms, ambiguity, bounds, de-duplication, text and URL validation, null/unset, exact-element filtering, literal display values, daemon commit full/empty/missing states, wakeup diagnostic round trips and recovery, upload interruption, digit-prefix and cancellation search, project omission/null concurrency, and redacted server errors.

#### Scenario: Changed behavior has positive and negative rows
- **WHEN** the affected case tables are inspected
- **THEN** each changed mapping, decoder, validator, and error path has precise expected argv/result/error assertions without duplicate one-off test functions

#### Scenario: Legacy compatibility remains covered
- **WHEN** legacy `0.6.1` payloads omit newly introduced fields
- **THEN** focused fixtures prove compatible decoding without fabricated target values

### Requirement: Complete inventories and source links are release gates

Release verification SHALL prove all 209 target CLI nodes and all 196 supported response entrypoints reconcile with the approved manifest. Every changed source reference SHALL use a full pinned commit SHA, and a source-link audit SHALL reject mutable or unresolved references.

#### Scenario: Missing inventory coverage blocks release
- **WHEN** a target CLI node, supported response entrypoint, required semantic dimension, or changed/unchanged manifest row lacks a reviewed disposition
- **THEN** verification fails before packaging or release approval

#### Scenario: Mutable source reference blocks release
- **WHEN** an approved changed contract row cites a branch, abbreviated commit, or unresolved line target
- **THEN** the source-link audit fails

### Requirement: Repository and packaging gates remain offline-first

The implementation SHALL pass focused affected tests, the full non-live suite, non-live collection audit, Ruff check and format check, mypy for source and tests, approved-contract validate/render/check and freshness assertions, strict OpenSpec validation, documentation contract checks, source-link audit, wheel/sdist build, artifact packaging tests, and import verification before a CLI invocation. Live smoke SHALL remain separately credential-gated and SHALL NOT weaken offline acceptance.

#### Scenario: Offline suite excludes live tests
- **WHEN** the non-live suite and collect-only audit run
- **THEN** no `tests/live/*` node is collected and all affected offline layers are present

#### Scenario: Generated runtime is reproducible
- **WHEN** contract render and check run from the approved input
- **THEN** the committed generated runtime is fresh and no review-only evidence file appears in Git

#### Scenario: Distribution artifacts preserve public changes
- **WHEN** wheel and sdist are built and tested
- **THEN** the target compatibility metadata, new model fields, list-property typing, and `py.typed` are present and importable before CLI execution

### Requirement: Migration documentation is direct and bounded

Documentation SHALL describe one direct `0.6.1` to `0.6.2` upgrade, the `0.6.3` exclusive ceiling, list-property input and output semantics, daemon commit and wakeup diagnostic presence, changed error behavior, and the explicit daemon-autostart deferral. It SHALL NOT claim that review evidence is production input or that autostart is supported.

#### Scenario: User guidance matches the approved contract
- **WHEN** API, compatibility, service usage, CLI coverage, migration, changelog, contributing, and release documents are checked
- **THEN** examples and claims agree with actual signatures, types, version gates, and deferred scope

### Requirement: Local E2E is not required for structured SDK deltas

This change SHALL use deterministic lower-level and existing gated coverage instead of a new local E2E stand because no changed human-facing table, log, progress view, browser UI, or otherwise untestable cross-component interaction remains. No before/after image SHALL be required for product verification.

#### Scenario: Every scenario maps to sufficient non-E2E evidence
- **WHEN** the delivery verification matrix is reviewed
- **THEN** each affected scenario maps to contract, unit, component, packaging, documentation, or existing gated live-smoke evidence with no unresolved local interaction gap
