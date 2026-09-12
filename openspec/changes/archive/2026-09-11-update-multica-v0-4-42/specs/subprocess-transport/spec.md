## ADDED Requirements

### Requirement: Target CLI failures retain exact typed mappings

Against the exact `0.4.42` source and binary, the transport SHALL preserve
reviewed success, validation, authentication, not-found, conflict/revision,
rate-limit, transport, and local-process failure mappings. Classification SHALL
use stable exit codes, HTTP diagnostics, and reviewed localized prefixes only;
it SHALL preserve the actual reported exit code and actionable redacted detail.
Unknown diagnostics SHALL remain `CommandExecutionError` rather than being
guessed into a semantic class.

#### Scenario: Validation and conflict remain distinct
- **WHEN** target CLI validation or revision-conflict fixtures fail
- **THEN** they raise the approved distinct exception types with exact exit/payload behavior and no retry advice replaces upstream detail

#### Scenario: Authentication not-found and rate limits are classified
- **WHEN** reviewed target diagnostics represent authentication failure, missing resources, or rate limiting
- **THEN** each maps to its approved SDK exception and retains safe actionable detail

#### Scenario: Transport and local-process failures are not response errors
- **WHEN** executable absence, timeout, malformed structured output, or local process-control failure occurs
- **THEN** each follows its existing transport/output/process exception contract rather than an HTTP semantic mapping

#### Scenario: Removed and secret-bearing paths stay safe
- **WHEN** obsolete Plugin commands are absent or retained agent/autopilot secret channels fail
- **THEN** Plugin errors are not exposed as supported operations and all retained secrets remain absent from preview, exception strings, streams, attributes, and reprs

### Requirement: Presence-sensitive target argv is preserved byte-for-byte

Command construction SHALL preserve the target distinction among omitted,
null/None, empty string, zero, and false for every reviewed update operation.
It SHALL enforce mutually exclusive inline/file/stdin content, custom-env, MCP
config, and secret channels before transport. New target flags SHALL use the
existing shell-free plan and immutable config snapshot.

#### Scenario: Omission matrix is exact
- **WHEN** table-driven update cases exercise omitted, null, empty, zero, and false values
- **THEN** complete expected argv and transport calls match the target mapping without truthiness collapse

#### Scenario: Exclusive channels fail before I/O
- **WHEN** more than one reviewed content, config, or secret channel is present
- **THEN** construction raises the documented validation error and performs zero executor calls
