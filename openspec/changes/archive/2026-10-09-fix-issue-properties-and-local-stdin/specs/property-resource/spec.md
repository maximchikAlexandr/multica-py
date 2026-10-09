## ADDED Requirements

### Requirement: Raw issue property projections remain separate from the typed relation

The SDK SHALL preserve the ordinary `issues.list` and `issues.get` UUID-to-value property projection as raw issue projection data and SHALL NOT use that projection as the loaded value of `Issue.properties`. When the projection is not a complete set of resolved property rows, the bound `Issue.properties` relation SHALL load through `issues.properties.list` and SHALL expose a `LazyMapping` keyed by property name whose values are `PropertyValue` instances.

#### Scenario: Ordinary list row loads typed properties

- **WHEN** `issues.list` returns an issue containing `{"properties":{"p1":"high"}}` and the caller evaluates `issue.properties.all()`
- **THEN** the SDK invokes `issue property list <issue-id> --output json` and returns the resulting `PropertyValue` under its property name rather than exposing `"p1": "high"` as the relation

#### Scenario: Ordinary get result loads typed properties

- **WHEN** `issues.get` returns an issue containing a raw UUID-keyed property map and the caller evaluates `issue.properties.all()`
- **THEN** the SDK loads the same authoritative typed relation without treating any raw string, number, boolean, null, array, or object value as a `PropertyValue`

#### Scenario: Resolved property rows remain an eager relation snapshot

- **WHEN** an issue response contains complete resolved property rows with property id, name, type, and value
- **THEN** `issue.properties.all()` returns name-keyed `PropertyValue` instances from that projection without issuing a redundant property-list command

#### Scenario: Raw projection compatibility is retained separately

- **WHEN** an ordinary or fields-selected issue response contains the UUID-keyed property projection
- **THEN** the issue projection and serialization retain that raw JSON data while the typed `Issue.properties` relation remains independently loadable
