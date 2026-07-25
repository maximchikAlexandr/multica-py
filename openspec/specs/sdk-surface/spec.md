## ADDED Requirements

### Requirement: Synchronous resource client
The SDK MUST expose one synchronous `MulticaClient` with stateless domain resources and immutable typed models.
#### Scenario: Resource calls remain stateless
- **WHEN** a consumer calls a resource method
- **THEN** no model performs hidden I/O or Active Record persistence.
<!-- Source IDs: 001:FR-001,FR-002,FR-003,FR-004,FR-005 -->

### Requirement: Public resource surface
The SDK MUST retain every public resource method present in the canonical operation table.
#### Scenario: Public methods have canonical rows
- **WHEN** a public resource method exists
- **THEN** one canonical operation row covers it.
<!-- Source IDs: 001:FR-018–FR-031,005:FR-019–FR-025 -->

### Requirement: Closed public types
The SDK MUST use immutable `msgspec` models and closed public enums or primitive unions without public `Any`.
#### Scenario: Structured output stays closed and typed
- **WHEN** structured output is decoded
- **THEN** it is a typed model or documented closed primitive.
<!-- Source IDs: 001:FR-033–FR-039 -->

### Requirement: Distribution boundary
The distribution MUST remain `multica-py`, import as `multica_py`, include `py.typed`, and import without a CLI.
#### Scenario: Clean installation imports without a CLI
- **WHEN** installed cleanly
- **THEN** `import multica_py` succeeds before a CLI invocation.
<!-- Source IDs: 001:FR-006A–FR-006D,FR-047–FR-050B -->
