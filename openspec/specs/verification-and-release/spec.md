## ADDED Requirements

### Requirement: Offline quality and release
CI MUST run Ruff, configured mypy, offline pytest, coverage, contract check, package validation, and approved release validation through `uv`.
#### Scenario: Pull requests run offline quality and release checks
- **WHEN** a pull request runs
- **THEN** job outcomes, not workflow-text tests, decide acceptance.
<!-- Source IDs: 001:FR-051–FR-059C,005:FR-011–FR-017 -->

### Requirement: Canonical operation coverage
Every public SDK method MUST have exactly one canonical success operation row with complete transport behavior.
#### Scenario: Public methods have canonical operation coverage
- **WHEN** `discovered_public_methods` is compared to `{case.sdk_method for case in OPERATION_CASES if case.is_canonical}`
- **THEN** the sets are equal, with 111 unique canonical methods, 135 unique case IDs, and 24 noncanonical variants.
<!-- Source IDs: 001:FR-060–FR-066,004:FR-004–FR-008,FR-017,006:FR-011–FR-013 -->

### Requirement: Focused process and offline checks
Offline tests MUST use stdlib and pytest, keep exact argv assertions, and retain exactly three real-process cases.
#### Scenario: Offline checks keep focused process cases
- **WHEN** the process module is collected
- **THEN** IDs are `bytes-env`, `text-stdin`, and `timeout-tree-cleanup`.
<!-- Source IDs: 004:FR-006,FR-015,FR-016,005:FR-002,FR-005,FR-006,006:FR-009 -->

### Requirement: Prepared-target live smoke
Live smoke MUST run separately against a prepared CLI/profile/workspace and clean uniquely named resources through the SDK.
#### Scenario: Prepared targets run live smoke
- **WHEN** live smoke is selected
- **THEN** five fixed scenarios run without backend provisioning or direct HTTP.
<!-- Source IDs: 003:FR-001,FR-002,FR-007,FR-014,FR-022,FR-029,FR-030 -->

### Requirement: Maintainer documentation
Documentation MUST describe CLI installation/authentication, compatibility, and approved upstream review.
#### Scenario: Maintainers can follow approved upstream review
- **WHEN** a maintainer follows it
- **THEN** they validate, collect, render, and check without a promotion state machine.
<!-- Source IDs: 001:FR-067–FR-075 -->
