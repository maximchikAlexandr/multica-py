## ADDED Requirements

### Requirement: Closed async parity inventory
Offline verification SHALL derive the expected async surface from the existing public I/O and command inventory plus explicit client, relation, and managed-process lifecycle declarations. Every in-scope synchronous operation SHALL have exactly one `_async` counterpart with an equivalent normalized signature and resolved return type, and every out-of-scope local operation SHALL have none. No allowlist SHALL hide missing or extra async methods.

#### Scenario: Async inventory is complete
- **WHEN** public resource and bound entity methods are discovered
- **THEN** every command-executing eager method has a corresponding async method and every async method maps back to one synchronous command-executing method

#### Scenario: Typing remains closed
- **WHEN** mypy checks source, tests, overloads, and public exports
- **THEN** async APIs resolve to the existing concrete public result types without `Any`, broad object returns, or a duplicate async model type

### Requirement: Async behavior is verified offline
Offline tests SHALL prove command equivalence, event-loop responsiveness, standard gather composition, shared concurrency limits, cancellation boundaries, result and exception parity, relation cache/coalescing behavior, managed-process cleanup, documentation examples, and unchanged synchronous behavior. Tests SHALL use the standard library and pytest with existing table-driven cases and shared fixtures before adding new test structures.

#### Scenario: Sync and async cases share operation evidence
- **WHEN** canonical operation cases execute both styles against equivalent fake executor responses
- **THEN** they assert identical complete argv, mode, stdin, timeout, decode result, exception, cache effect, and subprocess count

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
