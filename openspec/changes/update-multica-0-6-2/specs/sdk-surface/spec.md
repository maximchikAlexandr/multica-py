## ADDED Requirements

### Requirement: Daemon status exposes CLI commit without fabrication

`DaemonStatus` SHALL expose `cli_commit` as an optional string. A full target commit SHALL remain exact, an explicit empty string SHALL remain empty, and a missing legacy field SHALL decode as `None`. The SDK SHALL NOT derive or replace the value from `cli_version`.

#### Scenario: Full commit is preserved
- **WHEN** daemon status returns a full CLI commit SHA
- **THEN** `DaemonStatus.cli_commit` equals that exact SHA

#### Scenario: Empty and missing commits remain distinct
- **WHEN** target output contains `cli_commit: ""` versus legacy output omits `cli_commit`
- **THEN** the model exposes `""` versus `None` and neither case falls back to the CLI version

### Requirement: Retained operations adopt 0.6.2 behavior without duplicate APIs

The existing upload, issue search, project update, and command-error public methods SHALL retain their signatures and result categories while adopting the reviewed `0.6.2` behavior. Issue search SHALL accept digit-prefixed keys and preserve cancellation behavior. Project update SHALL keep `Unset` as omission, explicit `None` as the approved clear where nullable, and existing revision/concurrency controls. Redacted internal-server errors SHALL expose only stable safe diagnostics.

#### Scenario: Digit-prefixed issue lookup is retained in search
- **WHEN** issue search receives a query matching a digit-prefixed issue key
- **THEN** the existing typed page operation returns the decoded match without a new search method

#### Scenario: Cancellation remains typed
- **WHEN** the target search path reports cancellation
- **THEN** the existing transport/error boundary reports the reviewed cancellation failure without returning a partial success page

#### Scenario: Project omission and null remain distinct under concurrency
- **WHEN** a project update omits a field versus explicitly clears an approved nullable field with the expected revision
- **THEN** argv preserves those distinct states and a revision conflict remains the existing typed conflict error

#### Scenario: Internal errors remain redacted
- **WHEN** the target CLI reports an HTTP 500 response whose backend text is redacted
- **THEN** the SDK raises the existing typed command error with safe stable detail and does not require or expose raw backend text

### Requirement: Daemon autostart is absent from the public SDK

The Python daemon resource SHALL NOT expose enable, disable, or status methods for daemon autostart in this change.

#### Scenario: Public surface audit excludes autostart
- **WHEN** public exports, resource methods, generated bindings, and canonical operation cases are audited
- **THEN** no daemon-autostart symbol is present and ordinary daemon start, stop, restart, status, logs, and disk usage remain unchanged except for `cli_commit`
