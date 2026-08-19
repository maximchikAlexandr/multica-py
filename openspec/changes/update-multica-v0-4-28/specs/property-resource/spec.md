## ADDED Requirements

### Requirement: Workspace property catalog is a public resource

The SDK SHALL expose `MulticaClient.properties` for tagged `v0.4.28`
`property list|get|create|update|archive|unarchive`. List SHALL support
`--include-archived`. Create SHALL require nonblank `name` and `type`. Accepted
documented types are `text`, `number`, `select`, `multi_select`, `date`,
`checkbox`, `url`, `actor`, and `multi_actor`; unknown future types SHALL decode
without a closed-enum failure. Repeatable `--option` SHALL be emitted only when
the caller supplies options; actor types SHALL reject a present option tuple
before transport. Update SHALL use `Unset` for omitted fields because upstream
uses `Flags().Changed`. A present empty icon string SHALL emit `--icon ""` when
source treats that as clear.

#### Scenario: List can include archived definitions
- **WHEN** `properties.list(include_archived=True)` runs
- **THEN** argv contains `property list --include-archived --output json` and each row decodes to a frozen property definition

#### Scenario: Actor create rejects select options
- **WHEN** create is called with `type="actor"` and a nonempty `options` tuple
- **THEN** construction raises `ValueError` before transport

#### Scenario: Select create repeats options
- **WHEN** create is called with `type="select"` and `options=("Ready", "Blocked:#ff0000")`
- **THEN** argv contains repeatable `--option` flags in caller order

#### Scenario: Update presence is distinct from empty icon
- **WHEN** update omits icon versus passes `icon=""`
- **THEN** omitted icon emits no `--icon` flag and present empty icon emits `--icon ""`

### Requirement: Issue property values are distinct from metadata

`IssueResource` SHALL expose nested `IssuePropertyResource` at
`client.issues.properties` (eager list/set/unset mapping to
`issue property list|set|unset`), registered like `issues.metadata` /
`IssueMetadataResource` in `RESOURCE_SPECS` and `_NESTED_RESOURCE_ATTRS`.
Set SHALL require `--name` and `--value`. Unset
SHALL require `--name`. Bound `Issue.properties` SHALL load through
`issues.properties.list` as a `LazyMapping` keyed by property name. Actor and
multi-actor values SHALL pass through `--value` in the reviewed CLI form; the
SDK SHALL NOT merge these keys into `Issue.metadata` or `MetadataValue`.

#### Scenario: Issue property list is a mapping
- **WHEN** `issue.properties.all()` loads
- **THEN** transport receives `issue property list <issue-id> --output json` and keys remain property names with typed values

#### Scenario: Set emits name and value flags
- **WHEN** `issues.properties.set(issue_id, name="Reviewer", value="member:...")` runs
- **THEN** argv is `issue property set <issue-id> --name Reviewer --value <value> --output json`

#### Scenario: Unset does not send a value
- **WHEN** unset runs
- **THEN** argv contains `--name` and does not contain `--value`

#### Scenario: Metadata remains a separate relation
- **WHEN** `Issue.metadata` and `Issue.properties` are both loaded
- **THEN** they use `issue metadata list` and `issue property list` respectively and do not share decoded types
