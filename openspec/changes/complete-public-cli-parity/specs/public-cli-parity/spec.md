## ADDED Requirements

### Requirement: Public CLI parity has a closed inventory
The SDK SHALL maintain one reviewed inventory for the pinned Multica `v0.5.3`
CLI that covers every public runnable leaf, positional input, local and inherited
behavior-affecting flag, output variant, nested emitted field, mutation
acknowledgement, pagination contract, error contract, and required transport.
The inventory SHALL include dynamically registered leaves and aliased flag sets.

#### Scenario: Every public leaf is accounted for
- **WHEN** pinned source registration and recursive binary help are reconciled
- **THEN** every public runnable leaf and its effective inputs occur exactly once in the inventory

#### Scenario: Dynamic registrations remain visible
- **WHEN** a factory or helper registers commands or aliases that literal extraction cannot resolve
- **THEN** the inventory records the resolved commands from source and help evidence and retains a reviewed provenance link

### Requirement: Dispositions are explicit and evidence-backed
Every inventory item SHALL have exactly one disposition: `typed`,
`typed-equivalent`, `transport`, `presentation-only`, or
`outside-public-scope`. `typed-equivalent` SHALL cite the public SDK operation
and prove equivalent inputs, timing, side effects, outputs, and errors.
`transport` SHALL name the supported process or terminal entrypoint.
`presentation-only` SHALL prove that the item changes representation only.
`outside-public-scope` SHALL cite evidence that the node is hidden/internal or
the field is server-only and never emitted by the public CLI.

#### Scenario: Public uncertainty blocks completion
- **WHEN** any public item remains `partial`, `unknown`, deferred, unreviewed, or lacks required evidence
- **THEN** strict contract validation and release acceptance fail

#### Scenario: Generic raw argv is not typed parity
- **WHEN** a public domain capability is reachable only through `client.cli.command_command(...)`
- **THEN** the item remains incomplete unless the inventory classifies it as a genuinely transport-only operation

### Requirement: Parity covers behavior and data rather than method names
Typed parity SHALL preserve positional arity, input destinations, five-state
presence where applicable, constraints, atomic timing, output envelope,
field type and presence, ordering, pagination, redaction, exit behavior, and
process lifecycle. Matching names or raw environment escape hatches SHALL NOT
prove parity.

#### Scenario: Equivalent operation is proven semantically
- **WHEN** an existing SDK method is proposed as coverage for a CLI operation or flag
- **THEN** source-linked tests prove equivalent mapping, side effects, response, errors, and lifecycle before the inventory closes

#### Scenario: Presentation aliases avoid duplicate APIs
- **WHEN** aliases, help parents, `--full-id`, table-only grouping, or an equivalent presentation control is reviewed
- **THEN** the inventory records its existing equivalent or presentation disposition without creating a duplicate domain method

### Requirement: Scope exclusions cannot hide public capabilities
Hidden internal commands, test-only registrations, and server fields never
emitted by the CLI SHALL remain outside scope. Public interactive operations,
foreground or streaming modes, text or byte outputs, and public data-bearing
flags SHALL remain in scope even when they do not map to a JSON domain model.

#### Scenario: Interactive setup receives transport coverage
- **WHEN** guided setup or another public interactive leaf is inventoried
- **THEN** it maps to a supported terminal/process entrypoint with lifecycle and error semantics rather than an invented JSON model

#### Scenario: Hidden daemon probe remains excluded
- **WHEN** `daemon probe-runtimes` is reconciled
- **THEN** its hidden status and source evidence justify `outside-public-scope` and no typed public SDK operation is added
