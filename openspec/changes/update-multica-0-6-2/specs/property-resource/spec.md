## ADDED Requirements

### Requirement: Multi-text and multi-URL definitions remain open and option-less

The property catalog SHALL accept and decode `multi_text` and `multi_url` definitions while retaining `PropertyDefinition.type` as a forward-compatible string. Creating either type SHALL reject a present nonempty options collection before transport and SHALL preserve the existing definition envelope.

#### Scenario: List-property definitions decode
- **WHEN** property get or list returns a `multi_text` or `multi_url` definition
- **THEN** the frozen definition preserves the exact type string and uses no select options

#### Scenario: List-property options fail before I/O
- **WHEN** create is called for `multi_text` or `multi_url` with one or more options
- **THEN** validation raises before transport

### Requirement: Multi-value property input is discriminated, canonical, and bounded

`IssuePropertyResource.set` and `set_command` and create-time `IssuePropertyAssignment` SHALL expose the same keyword-only `property_type` discriminator. The discriminator SHALL be omitted or exactly `multi_text` or `multi_url`. A string or string sequence intended as a list property SHALL require the matching discriminator; a sequence without it, an unsupported discriminator, a discriminator with a scalar non-string value, or null SHALL fail before I/O. Omitting the discriminator SHALL preserve the existing scalar-string input contract.

For discriminated input, the SDK SHALL parse target comma-form strings or JSON string-array strings, accept Python string sequences, stably de-duplicate by first occurrence, validate by the declared type before command construction, and serialize one compact JSON string array. A list value SHALL contain 1 through 20 strings; `multi_text` items SHALL be nonblank and at most 2000 characters; `multi_url` items SHALL be HTTP(S) URLs of at most 2048 characters. Removal SHALL remain the separate unset operation.

#### Scenario: Discriminated sequence input uses JSON without comma ambiguity
- **WHEN** a caller supplies `property_type="multi_text"` or `property_type="multi_url"` with sequence items including a comma or an item beginning with `[`
- **THEN** the command emits one compact JSON string array and preserves item text and first-occurrence order

#### Scenario: Discriminated string forms are parsed before I/O
- **WHEN** a caller supplies a matching list-property discriminator with a valid comma-form or JSON-array string
- **THEN** the SDK parses and validates the declared list type before command construction and emits one canonical compact JSON string array

#### Scenario: Legacy scalar string remains compatible
- **WHEN** a caller supplies a string and omits `property_type`
- **THEN** the existing scalar/raw string behavior is preserved without claiming local list-property validation

#### Scenario: Missing or conflicting discriminator fails before I/O
- **WHEN** a caller supplies a string sequence without `property_type`, supplies a discriminator outside `multi_text|multi_url`, or combines a list discriminator with a scalar non-string value
- **THEN** both direct set and create-time assignment reject the input before transport or command-plan construction

#### Scenario: Bounds and element validation fail before I/O
- **WHEN** a list is empty, exceeds 20 unique items, contains blank or overlong text, contains a non-HTTP(S) or overlong URL, contains a non-string item, or is null
- **THEN** validation fails before transport and no unset is inferred

### Requirement: Multi-value decoding is typed and isolated from metadata

Resolved `multi_text` and `multi_url` property rows SHALL decode their values to immutable tuples of strings. Scalar property types and issue metadata SHALL retain their existing value types; the global metadata value alias SHALL NOT be widened to collections.

#### Scenario: Resolved rows preserve immutable list values
- **WHEN** issue property list or a resolved issue projection returns a list-property row
- **THEN** `PropertyValue.value` is the ordered immutable string tuple for that row

#### Scenario: Malformed list rows fail explicitly
- **WHEN** a list-property row contains a scalar, object, null, or a collection with a non-string item
- **THEN** decoding raises the existing typed output error instead of coercing or discarding content

### Requirement: Multi-value filtering and display are literal

An issue-list property predicate for `multi_text` or `multi_url` SHALL compare one complete stored element exactly. Property list display values SHALL return stored strings as-is and SHALL NOT resolve member-like strings to actor names.

#### Scenario: Filter matches one exact element
- **WHEN** a list property filter contains one valid text or URL element
- **THEN** the SDK emits one property predicate token for that entire element and does not split it as a list assignment

#### Scenario: Member-shaped text remains text
- **WHEN** a multi-text display value resembles a member reference
- **THEN** the decoded display value remains the original stored string without actor resolution
