## ADDED Requirements

### Requirement: Server cancellation is represented without a body
The transport SHALL classify the reviewed server cancellation outcome as status `499` with no response body and SHALL not require JSON decoding to identify cancellation.

#### Scenario: Cancellation has no body
- **WHEN** the CLI reports the reviewed cancellation status and no payload
- **THEN** the SDK SHALL raise the standard cancellation error with command context and SHALL not replace it with an output-shape failure

#### Scenario: Other nonzero exits remain errors
- **WHEN** a retained operation exits nonzero for a reason other than reviewed cancellation
- **THEN** the SDK SHALL preserve the standard command-error classification, stderr sanitization, and exit code

### Requirement: Runtime update failure is not false success
The runtime update operation SHALL classify a non-zero update result as failure even when progress or informational text was emitted.

#### Scenario: Runtime update exits nonzero
- **WHEN** the runtime update process emits text and exits nonzero
- **THEN** eager execution SHALL raise the standard command error and command preview SHALL remain passive

#### Scenario: Runtime update succeeds
- **WHEN** the runtime update process exits zero with the reviewed result shape
- **THEN** the SDK SHALL return the typed update result without inferring success from text alone

### Requirement: Changed file and stdin paths preserve literal transport behavior
Retained attachment and comment operations SHALL preserve literal argv, explicit file or stdin channels, prevalidation, and failure-safe cleanup under the `0.9.0` command contract.

#### Scenario: Literal user content is not shell evaluated
- **WHEN** content contains spaces, quotes, shell metacharacters, or option-like prefixes
- **THEN** the SDK SHALL pass each reviewed argument or stdin payload literally through the existing process transport

#### Scenario: Temporary input is cleaned after failure
- **WHEN** a file-backed operation fails after local preparation
- **THEN** run-owned temporary input SHALL be removed while caller-owned files and published evidence remain unchanged
