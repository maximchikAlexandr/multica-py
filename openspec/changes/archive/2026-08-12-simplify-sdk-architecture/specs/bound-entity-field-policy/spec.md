## ADDED Requirements

### Requirement: Msgspec declarations govern bound-entity field policy
Every `_BoundEntity` subclass SHALL derive its public serialized fields and private runtime fields from `msgspec.structs.fields()` metadata. A field whose declared Python name starts with `_` or whose encoded name starts with `_` SHALL be private runtime state; every other declared field SHALL be public. `_client` SHALL remain private. `_PUBLIC_FIELDS` and the global `_RUNTIME_FIELDS` registry SHALL be removed rather than retained as parallel policy sources.

#### Scenario: Public fields drive value behavior
- **WHEN** equality, hashing, repr, `to_dict`, `from_dict`, `to_json`, or `from_json` processes a bound entity
- **THEN** it uses the derived public field set, preserves declaration order and encoded-name conversion, and excludes client/relation runtime fields

#### Scenario: Private relation field stays outside snapshots
- **WHEN** an entity declares `_comments`, `_issues`, or another underscore-prefixed msgspec field and its relation is loaded
- **THEN** that field is accepted by `_set_runtime` but is absent from equality, hashing, repr, and serialized output

#### Scenario: Unsupported runtime name is rejected
- **WHEN** `_set_runtime` receives a name not declared as a private field on that concrete entity and not declared as an approved public runtime overlay
- **THEN** it raises `AttributeError` without modifying runtime state

### Requirement: Constructor seeds are derived without a registry
Private constructor seeds SHALL be identified from fields whose Python name is public but whose encoded msgspec name starts with `_`. Construction, decoding, rebind, detach, and relation seeding SHALL preserve the current seed semantics without `_RUNTIME_INIT_FIELDS` or a replacement global/class registry.

#### Scenario: Hidden issue context remains constructible
- **WHEN** a comment thread or task-run value is built with a public constructor seed encoded as `_issue_id`
- **THEN** the seed remains available to its relation loader, stays absent from the public serialized snapshot, and detach/rebind behavior is unchanged

#### Scenario: Aggregate relation seeds remain presence-aware
- **WHEN** an autopilot is decoded with present `triggers` or `subscribers` constructor seeds
- **THEN** the corresponding relations are seeded exactly as before, while omitted seeds remain unloaded

### Requirement: Public runtime overlays are an explicit narrow exception
The derived policy SHALL allow a minimal explicit exception only for `AutopilotRun.trigger_payload` and `AutopilotRun.result`, whose normalized immutable JSON values currently live in runtime state. The exception SHALL be named locally to the bound-entity base or `AutopilotRun`; it SHALL NOT be a general field-policy registry or extension protocol.

#### Scenario: Autopilot JSON overlays remain immutable and public
- **WHEN** `trigger_payload` or `result` contains nested mutable input structures
- **THEN** the exposed value, equality, hashing, repr, and serialization use the normalized immutable snapshot and preserve existing round trips

#### Scenario: No unrelated public field becomes an overlay
- **WHEN** the field policy is inspected across all bound entities
- **THEN** only `AutopilotRun.trigger_payload` and `AutopilotRun.result` are public runtime overlays
