## ADDED Requirements

### Requirement: Multi-value property definitions remain open and typed by value shape
Property definition `type` SHALL remain an open string and SHALL decode `multi_text` and `multi_url` without a new closed enum. `PropertyValue.value` SHALL accept the existing scalar values plus an immutable ordered tuple of strings for these multi-value types.

#### Scenario: New property definitions decode without enum closure
- **WHEN** property catalog output contains `type="multi_text"` or `type="multi_url"`
- **THEN** the definition preserves that exact type string and introduces no new public enum

#### Scenario: Multi-value rows preserve order and duplicates
- **WHEN** a resolved property row contains `value=["a","b","a"]`
- **THEN** the public value is `("a","b","a")` in the same order

### Requirement: Issue property writes support legacy strings and JSON arrays
`IssuePropertyResource.set` and `set_command` SHALL continue accepting a string unchanged for legacy comma-separated input and SHALL additionally accept `tuple[str, ...]`. A tuple SHALL be encoded as a compact JSON array in the single `--value` argument. The SDK MUST reject non-string tuple members before transport and MUST NOT split, trim, sort, or deduplicate either representation.

#### Scenario: Legacy comma-separated input is preserved
- **WHEN** a caller sets `value="one,two"`
- **THEN** argv contains the exact single value `one,two`

#### Scenario: JSON-array input is deterministic
- **WHEN** a caller sets `value=("one","two,three","one")`
- **THEN** argv contains one `--value` argument equal to `["one","two,three","one"]`

#### Scenario: Empty collection is explicit
- **WHEN** a caller sets `value=()`
- **THEN** argv contains one `--value` argument equal to `[]` rather than omitting the flag

#### Scenario: Invalid collection fails locally
- **WHEN** a tuple contains a non-string member
- **THEN** command construction raises a typed validation error and performs zero transport calls

### Requirement: Multi-value decoding distinguishes null, empty, and malformed data
Resolved property rows SHALL decode JSON `null` as `None`, an empty JSON array as `()`, and a string array as an ordered tuple. Arrays containing non-string items and object values for `multi_text` or `multi_url` MUST fail closed as malformed output. Existing scalar property kinds SHALL retain their current scalar behavior.

#### Scenario: Null and empty remain distinct
- **WHEN** otherwise identical rows contain `null` and `[]`
- **THEN** their public values are respectively `None` and `()`

#### Scenario: Malformed multi-value output fails closed
- **WHEN** a multi-value row contains an object or a non-string array element
- **THEN** decoding raises the existing malformed-output exception with no lossy coercion
