## ADDED Requirements

### Requirement: Target request presence maps to exact CLI channels
Every adapted operation SHALL map reviewed values to the exact target positional, flag, stdin/file, JSON-body, query, header, multipart, or local-process channel and SHALL preserve omission separately from explicit null, empty string, zero, and false values.

#### Scenario: Omitted patch input is not emitted
- **WHEN** a caller omits a presence-sensitive optional value
- **THEN** command construction SHALL omit its target token or body member and SHALL not substitute a default

#### Scenario: Explicit empty, zero, false, and null are retained
- **WHEN** the approved target accepts an explicit empty string, zero, false, or null
- **THEN** command construction SHALL emit the exact reviewed representation and SHALL not collapse it to omission

#### Scenario: Imperative constraint fails before transport
- **WHEN** inputs violate an approved requires, conflicts-with, exactly-one, at-least-one, required-together, conditional-range, or custom constraint
- **THEN** validation SHALL fail before invoking the CLI and SHALL identify the governed inputs

### Requirement: Target text channels preserve literal content
Issue, project, workspace, comment, and other reviewed text-bearing operations SHALL preserve target literal inline content and file/stdin trailing-newline behavior without decoding backslash escape sequences.

#### Scenario: Inline backslashes remain literal
- **WHEN** inline text contains backslash sequences
- **THEN** the target command SHALL receive those characters literally rather than converting them to control characters

#### Scenario: File and stdin preserve multiline content
- **WHEN** text is supplied through an approved file or stdin channel
- **THEN** all content SHALL be preserved except the one target-defined trailing LF normalization, and explicit empty content SHALL remain distinct from omission

### Requirement: Target cancellation and replay errors retain shared decoding
The shared transport SHALL preserve reviewed target 499 cancellation, 409 revision/replay conflicts, 413 size failures, and retained standard command failures for every adapted operation.

#### Scenario: Client cancellation is typed
- **WHEN** the target returns status 499 through a governed command
- **THEN** the SDK SHALL raise the existing sanitized typed command error and SHALL not decode a partial success model

#### Scenario: Conflict payload remains sanitized and inspectable
- **WHEN** a revision or idempotency conflict returns the reviewed standard payload
- **THEN** the typed error SHALL preserve approved status/code/message fields and SHALL redact secrets through the shared boundary
