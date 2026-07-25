## ADDED Requirements

### Requirement: CLI-only transport
The SDK MUST invoke Multica through one shell-free controlled subprocess transport.
#### Scenario: Resource calls use the controlled subprocess
- **WHEN** a resource runs a command
- **THEN** exact argv, cwd, profile, workspace, environment, stdin, and timeout reach that transport.
<!-- Source IDs: 001:FR-006–FR-010,FR-015 -->

### Requirement: Managed process lifecycle
The SDK MUST expose managed processes with bounded concurrency, timeout cancellation, escalation, and descendant cleanup.
#### Scenario: Timed processes clean up descendants
- **WHEN** the timeout process case expires
- **THEN** parent and descendant are absent.
<!-- Source IDs: 001:FR-016–FR-017B,005:FR-004–FR-006,006:FR-008–FR-010 -->

### Requirement: Decode and diagnostics
The SDK MUST decode supported structured output, map reliable failures to typed errors, and redact secrets from diagnostics.
#### Scenario: Failures expose typed redacted diagnostics
- **WHEN** malformed output or nonzero exit occurs
- **THEN** the diagnostic has redacted command context and the documented error type.
<!-- Source IDs: 001:FR-011–FR-014,FR-040–FR-044 -->
