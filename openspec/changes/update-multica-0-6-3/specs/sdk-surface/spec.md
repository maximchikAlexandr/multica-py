## ADDED Requirements

### Requirement: Daemon status exposes compatible CLI commit identity
`DaemonStatus` SHALL expose `cli_commit: str | None`. A 0.6.3 full commit SHA SHALL be preserved exactly; empty string, JSON null, or field omission from compatible older output SHALL normalize to `None` without changing daemon-status command construction.

#### Scenario: Full target commit decodes
- **WHEN** daemon status output contains the full target commit
- **THEN** `cli_commit` equals `18fa9f728a9e25f2465df2789631edb2a75442ad`

#### Scenario: Legacy output remains compatible
- **WHEN** daemon status output omits `cli_commit` or emits an empty/null value
- **THEN** `cli_commit is None` and all existing fields retain their prior decoding

### Requirement: Reviewed 0.6.3 errors preserve stable public boundaries
Wakeup diagnostics, attachment upload failures, and stable redacted HTTP 500 messages SHALL map through existing exception and redaction paths. The SDK MUST preserve actionable stable text and MUST NOT expose backend internals, credentials, private hostnames, or stack traces.

#### Scenario: Stable server failure is safe
- **WHEN** a reviewed 0.6.3 command returns a stable redacted server error
- **THEN** the existing public command exception contains the safe message, exit status, and command context without backend detail leakage

#### Scenario: Upload failure is not retried
- **WHEN** an upload step fails after a prior issue mutation
- **THEN** the SDK reports the existing partial-side-effect boundary and performs no automatic retry

### Requirement: Additive target fields do not create unrelated APIs
The SDK SHALL add only approved fields and adapters required by the 0.6.3 contract. It MUST NOT expose workflow-management endpoints, daemon autostart commands, or daemon-claim-only project workflow data as public operations.

#### Scenario: Public discovery remains governed
- **WHEN** public resources, symbols, signatures, operation cases, and approved bindings are compared
- **THEN** only approved additive fields appear and no excluded operation is discoverable
