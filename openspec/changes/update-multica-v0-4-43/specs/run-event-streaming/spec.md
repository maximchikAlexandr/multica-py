## ADDED Requirements

### Requirement: Streaming preserves run-message truncation metadata
Semantic streaming SHALL retain the complete immutable `RunMessage`, including
tri-state `output_truncated`, as every message-backed event's `raw_message`.
Event classification and semantic `output`/`content` fields SHALL remain
unchanged; the SDK SHALL NOT infer completeness from message type, terminal run
status, quiet reads, or absence of the field.

#### Scenario: Truncated output remains inspectable
- **WHEN** a streamed tool-result row has `output_truncated=true`
- **THEN** the semantic event retains its existing output projection and its `raw_message.output_truncated` is `True`

#### Scenario: Legacy unknown remains unknown
- **WHEN** a streamed legacy row omits `output_truncated`
- **THEN** its `raw_message.output_truncated` is `None` and streaming does not describe the output as complete

#### Scenario: Duplicate detection includes truncation state
- **WHEN** the same sequence is observed again with a different `output_truncated` value
- **THEN** the existing complete-message duplicate check raises `OutputShapeError`
