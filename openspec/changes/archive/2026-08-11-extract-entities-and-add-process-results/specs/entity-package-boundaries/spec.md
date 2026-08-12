## ADDED Requirements

### Requirement: Canonical bound entity package
The SDK SHALL define `_BoundEntity` in `multica_py.entities._base` and SHALL define every bound entity subclass in a dedicated module under `multica_py.entities`. The canonical bound entity set SHALL be exactly `Agent`, `Autopilot`, `AutopilotRun`, `Comment`, `CommentThread`, `Issue`, `TaskRun`, `Label`, `Project`, `Skill`, `Squad`, `Workspace`, and `WorkspaceMember`. No module under `multica_py.resources` or `multica_py.models` SHALL define `_BoundEntity` or a subclass of it.

#### Scenario: Every bound entity has canonical module ownership
- **WHEN** the canonical bound entity classes are inspected
- **THEN** each class has a `multica_py.entities.*` defining module and inherits the one `_BoundEntity` defined by `multica_py.entities._base`

#### Scenario: Resource modules contain no bound entity definitions
- **WHEN** the Python classes defined by `multica_py.resources.*` are inspected
- **THEN** none is `_BoundEntity` or a `_BoundEntity` subclass

#### Scenario: Private base remains private
- **WHEN** `multica_py.__all__` and `multica_py.entities.__all__` are inspected
- **THEN** `_BoundEntity` is absent while the 13 canonical entity classes are available from `multica_py.entities`

### Requirement: Entity and resource responsibilities remain separated
Entity modules SHALL own immutable domain fields, serialization/detachment behavior, lazy relations, and entity-scoped domain actions. Resource modules SHALL own CLI argument construction, `Command` plans, transport execution, wire decoding, and service or collection operations. An attached entity action SHALL delegate through its originating `MulticaClient` resource and SHALL NOT directly construct CLI argv, invoke subprocess transport, or decode wire output.

#### Scenario: Entity action delegates to its resource
- **WHEN** an attached entity action such as `Issue.add_comment`, `Agent.set_skills`, or `Project.add_local_directory` runs
- **THEN** the action reaches the originating client's resource command path with unchanged arguments and result behavior

#### Scenario: Detached entity fails before I/O
- **WHEN** a detached entity invokes an action or relation that requires a client
- **THEN** it raises the existing `DetachedEntityError` before command construction or subprocess execution

#### Scenario: Resource operation returns canonical entity
- **WHEN** a resource operation or wire converter produces a bound domain object
- **THEN** the result is an instance of the canonical class from `multica_py.entities` and retains the originating client binding

### Requirement: Entity references do not create avoidable resource coupling
Runtime and type-checking references to bound entity classes SHALL resolve from `multica_py.entities` modules rather than importing sibling resource modules. Pure relation-state adapters—helpers that only create or update relation state from already decoded entity/value data and do not own a client, construct `Command`/CLI argv, invoke transport, or decode raw wire payloads—SHALL live in the entity layer or existing neutral internal/model infrastructure. Command-construction and wire-adaptation adapters—helpers that build `Command`/CLI argv, invoke or prepare transport, or adapt raw wire output for a relation—SHALL remain private methods on the resource service that owns the operation, and entity loaders SHALL reach them through the bound client's resource. These adapter categories are mutually exclusive. A resource-to-resource import SHALL remain only when one resource composes or delegates to another resource service, not solely to name or construct a bound entity, so that importing any public entity or resource module completes without a circular-import failure.

#### Scenario: Entity-only imports bypass sibling resources
- **WHEN** resource, model, decoder, and wire modules reference an entity type or pure relation state without invoking another resource service
- **THEN** the reference resolves from `multica_py.entities` and no sibling resource import is required

#### Scenario: Pure relation-state adapters stay resource-neutral
- **WHEN** a relation helper only creates or updates state from already decoded values
- **THEN** it is defined in an entity or neutral internal/model module and has no client, `Command`/argv, transport, or raw-wire-decoding dependency

#### Scenario: Command and wire adapters stay with the owning resource
- **WHEN** a relation loader needs CLI command construction, transport preparation, or raw-wire adaptation
- **THEN** the adapter is a private method on the owning resource service, the entity loader invokes it through the bound client, and the entity module does not import a resource at runtime

#### Scenario: Legitimate nested resources remain composable
- **WHEN** a resource owns a nested service such as issue comments, issue metadata, agent skills, project resources, or squad members
- **THEN** the service composition remains in the resource layer and continues to use the same client configuration and transport

#### Scenario: Package import graph is cycle-safe
- **WHEN** each `multica_py.entities.*`, `multica_py.resources.*`, `multica_py._internal.wire_models`, and `multica_py._internal.decoders` module is imported in a fresh interpreter
- **THEN** every import succeeds without relying on a pre-established import order

### Requirement: Entity import compatibility preserves class identity
The package root SHALL continue exporting all existing canonical bound entity names. Each existing `multica_py.resources.<domain>` entity import path SHALL remain as a compatibility re-export of the canonical entity class, not as a wrapper, subclass, or duplicate definition. Serialization, equality, hashing, `repr`, relation behavior, and all existing public method signatures SHALL remain unchanged by the relocation.

#### Scenario: Root import identity is unchanged
- **WHEN** a consumer imports an entity from `multica_py` and the same entity from `multica_py.entities`
- **THEN** both names are the identical class object

#### Scenario: Resource-module compatibility import is identical
- **WHEN** a consumer imports an existing entity name from its former `multica_py.resources.*` module
- **THEN** it is the identical canonical class from `multica_py.entities`

#### Scenario: Existing entity behavior survives relocation
- **WHEN** the pre-change bound-entity contract suite exercises construction, decoding, equality, hashing, repr, serialization, detach, relations, actions, and typing
- **THEN** observable values, errors, commands, and annotations remain unchanged except for the class defining-module path
