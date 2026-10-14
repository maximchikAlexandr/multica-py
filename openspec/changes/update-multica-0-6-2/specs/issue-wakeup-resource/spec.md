## ADDED Requirements

### Requirement: Wakeup responses expose recoverable last-error diagnostics

`IssueWakeup` SHALL expose nullable `last_error`. The shared decoder for create, get, list, update, and disable SHALL preserve the target diagnostic string, explicit null, and legacy omission without changing wakeup command signatures or page behavior.

#### Scenario: Supported wakeup operations round-trip last error
- **WHEN** create, get, list, update, or disable returns a wakeup with a non-null `last_error`
- **THEN** the corresponding typed result preserves the exact diagnostic string

#### Scenario: Null and legacy omission are compatible
- **WHEN** target output returns `last_error: null` or legacy output omits the field
- **THEN** the typed model exposes `None` without a decode failure

### Requirement: Recoverable pull-request diagnostics clear after recovery

The SDK SHALL preserve each of the three reviewed recoverable pull-request condition diagnostics while its condition is pending and SHALL expose `None` after upstream recovery clears `last_error`. The SDK SHALL NOT reinterpret a pending diagnostic as terminal disablement.

#### Scenario: Pending condition remains observable
- **WHEN** a pull-request condition produces any reviewed recoverable pending diagnostic
- **THEN** get/list and subsequent mutation results preserve that diagnostic while the wakeup remains recoverable

#### Scenario: Recovery clears stale diagnostic
- **WHEN** the condition later becomes healthy and upstream clears `last_error`
- **THEN** the next decoded wakeup exposes `None` and does not retain a client-side cached error
