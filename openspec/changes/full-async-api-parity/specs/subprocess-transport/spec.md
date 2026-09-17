## ADDED Requirements

### Requirement: Async command execution reuses executor contracts
Asynchronous command execution SHALL reuse the existing `CommandExecutor`, `CliTransport`, `ExecutionRequest`, command-step modes, process semaphore, compatibility check, staging, output capture, redaction, decoding, and cleanup contracts. Blocking plan execution SHALL be offloaded through the Python standard library; executor implementations SHALL NOT require a duplicate async protocol.

#### Scenario: Local and remote backends gain the same async surface
- **WHEN** `Command.run_async()` executes against local, SSH, or microsandbox-backed client configuration
- **THEN** it invokes that backend's existing synchronous executor contract outside the event-loop thread

#### Scenario: Composite command cleanup is preserved
- **WHEN** an asynchronously executed multi-step command succeeds, fails, times out, or its awaiter is cancelled
- **THEN** plan-owned staging and output resources follow the existing `Command.run()` finalization contract, including cleanup after the underlying execution finishes

#### Scenario: Transport exceptions retain identity
- **WHEN** async execution encounters a classified CLI failure, timeout, missing executable, invalid decoding, or backend failure
- **THEN** it raises the same public exception class and diagnostic data as synchronous execution of the same plan
