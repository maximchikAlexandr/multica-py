## MODIFIED Requirements

### Requirement: Decode and diagnostics
The SDK MUST decode supported structured output, map reliable failures to typed errors, and redact secrets from diagnostics.
Classified failures MUST preserve actionable upstream detail. A raw HTTP `409`,
the stable `v0.4.28` localized conflict prefixes,
and the localized generic conflict fallback SHALL map to `ConflictError` even
though upstream has no conflict-specific process exit code. Known validation
failures SHALL map to `ValidationError` through exit code `5`, raw HTTP
`400`/`422`, the stable localized validation prefixes, or an explicitly reviewed
local CLI validation marker. A classified exception's `str(exc)` SHALL contain
the redacted nonempty upstream detail from stderr (or stdout when stderr is
empty); the exception SHALL retain redacted `stdout`, `stderr`, redacted argv,
and the documented reported exit code. The actual argv SHALL be supplied only
to the executed subprocess invocation and SHALL NOT be retained in exception
attributes, reprs, or previews. When no safe detail exists, the existing
generic command-failed message SHALL remain the fallback. `--server-config` inline JSON SHALL be a collected secret.
`--server-config-file` path SHALL NOT be a secret. `--credential-file` path
SHALL NOT be a secret; plugin Remote MCP stdin and credential-file **contents**
SHALL be collected into `secret_values`. The SDK SHALL NOT add a plaintext
`--credential` flag. A `--credential*` key match MUST NOT redact the file path.

#### Scenario: Failures expose typed redacted diagnostics
- **WHEN** malformed output or nonzero exit occurs
- **THEN** the diagnostic has redacted command context and the documented error type.

#### Scenario: Failures retain redacted streams
- **WHEN** malformed output or a nonzero CLI exit occurs
- **THEN** the diagnostic retains captured redacted streams without exposing secrets

#### Scenario: Conflict detail reaches str of exception
- **WHEN** the CLI emits `Request conflict: <server detail>` for an HTTP `409`
- **THEN** the SDK raises `ConflictError`, `str(exc)` contains the actionable server detail, and generic retry advice does not replace it

#### Scenario: Localized and raw conflicts classify consistently
- **WHEN** stderr contains the pinned English or Chinese conflict prefix, the pinned generic conflict fallback, or a raw `returned 409` diagnostic
- **THEN** classification returns `ConflictError` while preserving the actual process exit code when no semantic conflict exit code exists

#### Scenario: Validation detail reaches str of exception
- **WHEN** a server-side invalid thinking-level or other HTTP `400`/`422` response reaches the SDK through exit `5` or a pinned validation prefix
- **THEN** the SDK raises `ValidationError` and `str(exc)` contains the actionable redacted upstream reason

#### Scenario: Reviewed local validation is classified
- **WHEN** `v0.4.28` rejects max concurrency through its reviewed local CLI validation message before an HTTP request
- **THEN** the SDK raises `ValidationError` with that message rather than an unclassified `CommandExecutionError`

#### Scenario: Detail redaction precedes message construction
- **WHEN** upstream detail, stdout, stderr, or argv contains a collected secret
- **THEN** the secret is absent from `str(exc)`, exception attributes, reprs,
  redacted argv, and command preview while the actual argv passed to the
  subprocess still receives the real value

#### Scenario: Empty diagnostics use the generic fallback
- **WHEN** a classified or unclassified failure has no nonempty safe stderr or stdout detail
- **THEN** `str(exc)` uses the existing redacted command-failed fallback and no detail is fabricated

#### Scenario: MCP and plugin credentials are redacted
- **WHEN** a workspace MCP add uses inline `--server-config` JSON or plugin Remote MCP configure uses credential-file or stdin contents
- **THEN** the inline JSON and credential bytes are absent from `str(exc)`, redacted argv, and preview while `--server-config-file` and `--credential-file` paths remain visible

#### Scenario: Credential file path is not treated as a secret
- **WHEN** `collect_secret_values` sees `--credential-file <path>` or `--server-config-file <path>`
- **THEN** the path is not added as a secret; file or stdin contents are collected when those channels carry credentials or config JSON
