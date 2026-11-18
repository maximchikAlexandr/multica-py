## ADDED Requirements

### Requirement: Literal text and presence-safe input channels
Changed text-taking operations SHALL preserve inline text literally, SHALL preserve file/stdin content except one trailing LF, and SHALL distinguish omission, explicit empty content, and an explicitly false stdin selector before invoking the CLI.

#### Scenario: Inline backslashes remain literal
- **WHEN** a caller supplies inline text containing backslashes or escape-looking sequences
- **THEN** command construction SHALL pass those characters literally without backslash decoding

#### Scenario: File and stdin multiline content is preserved
- **WHEN** a caller supplies multiline content through the approved file or stdin channel
- **THEN** the SDK SHALL preserve the content except one trailing LF according to the target contract

#### Scenario: Omitted and empty inputs differ
- **WHEN** a field is omitted, explicitly empty, or its stdin selector is explicitly false
- **THEN** argv/stdin construction SHALL preserve the proven distinction and SHALL NOT overwrite stored text for the omitted or false-selector case

### Requirement: Typed cancellation, privacy, archive, and destructive errors
The shared transport/error boundary SHALL decode proven target `499` cancellation without a response body, private-resource not-found behavior, archived-project `409`, and bounded runtime-delete conflicts without unsafe retry or mutation follow-up.

#### Scenario: Cancellation has no body
- **WHEN** the CLI reports cancellation status `499` with an empty body
- **THEN** the SDK SHALL raise the existing typed cancellation error and SHALL NOT misclassify it as malformed JSON

#### Scenario: Archived project mutation fails closed
- **WHEN** a target operation reports the proven archived-project conflict
- **THEN** the SDK SHALL raise the mapped typed conflict and SHALL NOT retry or issue a second mutation

#### Scenario: Runtime delete conflict is bounded
- **WHEN** runtime deletion reports a target-defined bounded conflict or confirmation failure
- **THEN** the SDK SHALL preserve the typed diagnostic, perform no destructive follow-up, and redact sensitive process data

### Requirement: Metadata paths and webhook filters fail closed
Metadata keys SHALL be encoded as a single escaped path segment, and webhook filter inputs SHALL satisfy all target required/conflicting/presence rules before transport.

#### Scenario: Metadata key cannot alter the path
- **WHEN** a metadata key contains slashes, percent sequences, spaces, or Unicode
- **THEN** the SDK SHALL produce the proven escaped path argument and SHALL NOT let the key introduce another path segment

#### Scenario: Invalid webhook filters do not invoke the CLI
- **WHEN** webhook filter selectors are missing a required companion or contain a forbidden combination
- **THEN** the SDK SHALL raise validation before process creation and record no command invocation

#### Scenario: Valid webhook filters preserve literal values
- **WHEN** webhook filter inputs satisfy the target rules
- **THEN** the SDK SHALL emit each destination and repeated value exactly as proven by the approved mapping
