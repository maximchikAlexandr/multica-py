## MODIFIED Requirements

### Requirement: Offline quality and release
CI MUST run Ruff, configured mypy, offline pytest, statement and branch coverage, contract check, package validation, and approved release validation through `uv`. Coverage acceptance MUST include named gates for process lifecycle code and individually selected critical resource modules so that aggregate package coverage cannot conceal their regression.

#### Scenario: Pull requests run offline quality and release checks
- **WHEN** a pull request runs
- **THEN** job outcomes, not workflow-text tests, decide acceptance.

#### Scenario: Critical coverage zones are enforced
- **WHEN** offline coverage is checked
- **THEN** each configured critical zone independently satisfies both its statement and branch threshold and a missing zone or threshold fails the gate

### Requirement: Focused process and offline checks
Offline tests MUST use stdlib and pytest, keep exact argv assertions including operations with dynamic temporary paths, retain exactly three real-process cases, and use deterministic synchronization or subprocess test doubles for additional lifecycle branches.

#### Scenario: Offline checks keep focused process cases
- **WHEN** the process module is collected
- **THEN** IDs are `bytes-env`, `text-stdin`, and `timeout-tree-cleanup`.

#### Scenario: Dynamic argv remains exact
- **WHEN** an operation creates a temporary file or directory path
- **THEN** only the declared dynamic argv position is normalized and the complete remaining argv, transport method, stdin, and timeout are compared exactly
