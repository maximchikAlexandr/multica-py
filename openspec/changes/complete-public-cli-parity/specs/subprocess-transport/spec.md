## ADDED Requirements

### Requirement: Transport mode follows the concrete CLI contract
Each approved operation SHALL select JSON decode, text, bytes, buffered
process, streaming process, foreground process, or interactive terminal mode
from reviewed source/help behavior. A resource SHALL NOT append `--output json`
unless that leaf or an inherited public flag supports it, and SHALL NOT claim a
structured model for human-oriented stderr or lifecycle-only behavior.

#### Scenario: Unsupported output flag is rejected before approval
- **WHEN** an approved argv template contains `--output json`
- **THEN** contract validation proves the flag exists on the effective public command and that its JSON path matches the declared decoder

#### Scenario: Text and lifecycle operations stay truthful
- **WHEN** auth logout, daemon stop/restart, native checkout, or another reviewed operation emits text, a path, or process lifecycle rather than JSON
- **THEN** the public method uses the matching transport/result contract and does not fabricate structured success

### Requirement: Interactive and foreground operations use supported process entrypoints
Guided setup, token-prompt login, daemon foreground/restart, streaming logs,
and any other public interactive or foreground operation SHALL use a controlled
process or terminal-capable entrypoint with the same executor, configuration,
redaction, timeout, cancellation, semaphore, and preview boundaries as other
commands.

#### Scenario: Interactive behavior is not forced through buffered decode
- **WHEN** a public operation requires caller input or a live terminal
- **THEN** its approved command returns the supported managed/interactive process abstraction and no buffered JSON decoder is selected

### Requirement: Safe content and secret channels materialize at execution
Typed inline/file/stdin inputs SHALL preserve preview safety and exact execution
bytes. Secret values or secret-file contents SHALL be collected for diagnostic
redaction only at execution; file paths SHALL remain visible unless the path is
itself secret. Caller-owned streams SHALL not be closed by the SDK.

#### Scenario: File and stdin content do not leak
- **WHEN** agent environment, comment, skill, skill-file, or profile content is supplied through a safe content input
- **THEN** preview omits secret contents, execution sends exact reviewed bytes through the correct channel, and errors redact collected secret values

### Requirement: Native output adapters preserve metadata
Adapters for text/path/bytes operations SHALL retain any structured metadata the
CLI emits alongside the primary value. Attachment downloads SHALL preserve
identifier, filename, path, and size while download-bytes reads the reviewed
path only after successful decode and cleans SDK-owned temporary content.

#### Scenario: Attachment object becomes a typed download result
- **WHEN** the CLI emits `{id, filename, path, size}` for a download
- **THEN** the SDK decodes that object, returns the typed metadata for path mode, and uses its path for byte mode without expecting a JSON string
