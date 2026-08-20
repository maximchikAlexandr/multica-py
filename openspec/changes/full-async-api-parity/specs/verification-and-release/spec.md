## ADDED Requirements

### Requirement: Closed async parity inventory
Offline verification SHALL derive the expected async surface from the actual merged v0.4.28 public I/O and command inventory plus explicit client, relation, managed-process lifecycle, and run-message declarations. Before implementation, one canonical-accounting decision SHALL be recorded and applied consistently: either (A) structurally exclude `_async` from the existing synchronous consumer, retain its 194/321 baseline, and keep the two `list_messages` pairs in separate bound evidence, or (B) add the new synchronous `list_messages` methods to canonical rows and update all derived counts and repository instructions. Every in-scope synchronous operation SHALL then have exactly one `_async` counterpart with an equivalent normalized signature and resolved return type, and every out-of-scope local operation SHALL have none. No allowlist SHALL hide missing or extra async methods, options A and B SHALL NOT be mixed, and async symbols SHALL NOT enter the approved upstream contract or generated descriptors.

#### Scenario: Async inventory is complete
- **WHEN** public resource and bound entity methods are discovered
- **THEN** every command-executing eager method, including both run `list_messages` methods, has a corresponding async method and every async method maps back to one synchronous command-executing method or an explicitly declared relation/client/process primitive

#### Scenario: Canonical accounting is internally consistent
- **WHEN** the existing canonical consumer and the async parity gate run after the decision is recorded
- **THEN** option A preserves 194/321 with structural `_async` exclusion and separate `list_messages` evidence, or option B includes the new synchronous rows and updates every derived counter; either option excludes `_async` from approved upstream contract/descriptors

#### Scenario: v0.4.28 compatibility boundary remains fixed
- **WHEN** compatibility constants, docs, contract provenance, and async tests are inspected
- **THEN** they consistently preserve the supported interval `[0.4.28, 0.4.29)`

#### Scenario: Run message pair has canonical evidence
- **WHEN** table-driven bound-entity cases discover `TaskRun` and `AutopilotRun` message listing
- **THEN** sync and async evidence asserts the same signature, complete command plan, result tuple, validation/error, binding, subprocess count, and unchanged `.messages` cache state in the location selected by the canonical-accounting decision

#### Scenario: Typing remains closed
- **WHEN** mypy checks source, tests, overloads, and public exports
- **THEN** async APIs resolve to the existing concrete public result types without `Any`, broad object returns, or a duplicate async model type

### Requirement: Async behavior is verified offline
Offline tests SHALL prove command equivalence, event-loop responsiveness, standard gather composition, shared concurrency limits, cancellation boundaries, result and exception parity, command-backed and loader-only relation cache/coalescing behavior, managed-process cleanup, documentation examples, and unchanged synchronous behavior. Tests SHALL use the standard library and pytest with existing table-driven cases and shared fixtures before adding new test structures.

#### Scenario: Sync and async cases share operation evidence
- **WHEN** canonical operation cases execute both styles against equivalent fake executor responses
- **THEN** they assert identical complete argv, mode, stdin, timeout, decode result, exception, cache effect, and subprocess count

#### Scenario: Merged v0.4.28 cases use current shared fixtures
- **WHEN** async parity covers Plugin, Property, MCP, Issue Property, Skill refresh/search, and their bound actions and relations
- **THEN** it reuses the current canonical tables/consumer and shared execution fixtures for filesystem, credential/config stdin/file, redaction, staging/cleanup, binding, and cache-invalidation evidence without a parallel allowlist

#### Scenario: Event-loop progress is deterministic
- **WHEN** a fake executor blocks an async SDK call under deterministic synchronization
- **THEN** an event-loop task progresses before the executor is released without timing-only sleeps

#### Scenario: Full offline gate remains green
- **WHEN** the change is ready for delivery
- **THEN** OpenSpec validation, Ruff check and format check, `mypy src`, `mypy tests`, contract checks, package validation, and `pytest -m "not live"` all pass without a backend or network

### Requirement: Async workflows are documented
Primary public documentation SHALL show equivalent sync and async resource, entity-action, command, gather, relation, client-lifecycle, and managed-process workflows. It SHALL state the cancellation boundary and SHALL NOT imply that cancelling an awaiter necessarily terminates an already-started executor operation.

#### Scenario: Consumer can choose execution style
- **WHEN** a consumer reads the public API and service-usage documentation
- **THEN** matching examples identify where to use synchronous calls, `_async` methods, `Command.run_async()`, `asyncio.gather()`, and async context management
