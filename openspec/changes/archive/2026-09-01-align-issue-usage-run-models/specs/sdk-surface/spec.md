## ADDED Requirements

### Requirement: Typed issue activity preserves reviewed CLI projections
The typed issue API SHALL preserve reviewed assignee, usage, and task-run projections returned by supported Multica CLI versions. Missing optional legacy fields SHALL retain documented compatibility defaults, while present reviewed fields SHALL NOT silently become `None` or `0`.

#### Scenario: Scalar issue assignee is preserved
- **WHEN** an issue response contains matching non-null `assignee_id` and `assignee_type` scalar fields without a nested assignee
- **THEN** the public issue assignee contains that identifier and type

#### Scenario: Nested legacy assignee is preserved
- **WHEN** an issue response contains the supported nested assignee projection without scalar assignee fields
- **THEN** the public issue assignee contains the nested identifier and type

#### Scenario: Matching assignee projections agree
- **WHEN** an issue response contains nested and scalar assignee projections with the same identifier and type
- **THEN** the public issue assignee contains that common value

#### Scenario: Conflicting assignee projections fail closed
- **WHEN** nested and scalar assignee projections disagree or only one member of the scalar pair is present
- **THEN** decoding raises `OutputShapeError` and does not select one projection silently

#### Scenario: Current issue usage categories are preserved
- **WHEN** issue usage JSON contains task or run count plus input, output, cache-read, and cache-write token counts
- **THEN** every present count is exposed separately with its exact integer value and cache-read is not silently folded into an undocumented total

#### Scenario: Legacy issue usage remains decodable
- **WHEN** a supported legacy usage response contains only legacy fields
- **THEN** those fields retain their documented values and absent current fields use documented optional compatibility defaults rather than fabricated measurements

#### Scenario: Current task-run context is preserved
- **WHEN** an issue run response contains reviewed runtime, work directory, privacy-safe relative work directory, result, or failure fields
- **THEN** the public typed task run exposes every present reviewed field without leaking a private wire model
