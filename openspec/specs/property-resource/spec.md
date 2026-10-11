# property-resource Specification

## Purpose
TBD - created by archiving change update-multica-v0-4-28. Update Purpose after archive.
## Requirements
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

### Requirement: Issue property query options use the target CLI contract

The existing property catalog and issue property value operations SHALL remain
unchanged. `issues.get` SHALL additionally support opt-in property resolution.
`issues.list` SHALL additionally support an ordered fields allowlist,
repeatable property predicates, opt-in property resolution, and property sort
using the target command destinations and validations. The default list/get
projection SHALL continue returning the raw property UUID map.

#### Scenario: Property resolution is opt-in
- **WHEN** issue get or list is called with `resolve_properties=True`
- **THEN** argv emits `--resolve-properties` once and the decoder returns the reviewed name/type/value/display projection

#### Scenario: Raw property map remains default
- **WHEN** property resolution is omitted or false
- **THEN** argv omits the flag and the existing raw UUID-keyed property map remains unchanged

#### Scenario: Same and different property names compose correctly
- **WHEN** list receives `Impact=High`, `Impact=Medium`, and `Environment=prod`
- **THEN** all three flags are emitted in order, the two Impact values represent OR, and Environment composes with them as AND

#### Scenario: Unset sentinel and reserved operators are enforced
- **WHEN** a predicate uses `Name=__none__` versus `Name>=Value`, `Name<=Value`, or `Name!=Value`
- **THEN** the unset sentinel is accepted and each reserved comparison spelling is rejected before transport

#### Scenario: Property sorting is constrained
- **WHEN** list sorting names a reviewed sortable property versus an archived or unsortable property
- **THEN** the reviewed form reaches `--sort property:<name-or-id>` and unsupported forms fail with the documented validation behavior

### Requirement: Issue field projection preserves partial-row typing

The issue-list `fields` option SHALL use the target allowlist and SHALL return
partial list rows without constructing falsely complete Issue entities.
Required identity fields used by binding and pagination SHALL remain available,
and omission of unrequested fields SHALL remain distinct from explicit null.

#### Scenario: Fields are emitted deterministically
- **WHEN** a caller supplies an ordered nonempty fields selection
- **THEN** the exact reviewed `--fields` encoding is emitted once and unsupported or duplicate-invalid selections fail before transport

#### Scenario: Partial rows do not invent values
- **WHEN** a valid projection omits optional IssueSummary fields
- **THEN** decoding preserves absence according to the reviewed projection model and relation binding performs no per-item get
