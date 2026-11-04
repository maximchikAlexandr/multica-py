## ADDED Requirements

### Requirement: Workflow resources use typed open contracts
`MulticaClient` SHALL expose a workflow resource implementing reviewed
list/get/create/update/delete and handoff-set operations, while
`ProjectResource` SHALL expose workflow get/set operations. Workflow, step,
handoff, mapping-plan, and conflict result models SHALL preserve target JSON
fields and use open strings for server-owned status, handler, actor, and
transition vocabularies. File-backed instructions and steps SHALL remain file
inputs and SHALL not expose file contents in command previews or errors.

#### Scenario: Workflow list and get decode future values
- **WHEN** a valid target payload contains an unknown future status key, handler kind, or transition label
- **THEN** typed decoding succeeds and preserves the exact string

#### Scenario: Create and update preserve optional fields
- **WHEN** description, steps file, or mappings are omitted, explicitly cleared where supported, empty, or populated
- **THEN** command construction emits only the reviewed representation and validation rejects unsupported null or empty forms before I/O

#### Scenario: Mapping conflict remains structured
- **WHEN** workflow assignment dry-run or set returns a reviewed conflict plan
- **THEN** the SDK decodes the plan and does not collapse it into a generic success or retry the mutation

### Requirement: Runtime concurrency is typed and bounded
`RuntimeResource` SHALL expose `concurrency` and `concurrency_command` for
`runtime concurrency <runtime-id> <limit|none>`. A limit SHALL be an exact
integer from `1` through `50`; `None` SHALL emit `none`; booleans, floats,
strings, zero, and out-of-range integers SHALL fail before I/O. Runtime
definition payloads SHALL add `max_concurrent_tasks: int | None` with omitted
legacy and explicit null both decoding to `None` and malformed values failing.

#### Scenario: Concurrency limit is set
- **WHEN** a caller supplies a valid integer limit
- **THEN** exact argv carries the integer and the returned runtime definition preserves that value

#### Scenario: Concurrency limit is cleared
- **WHEN** a caller supplies `None`
- **THEN** exact argv carries `none` and the returned runtime definition decodes a null limit as `None`

#### Scenario: Invalid concurrency is zero-I/O
- **WHEN** a caller supplies an invalid type or value
- **THEN** validation raises a typed error before preview execution or subprocess I/O

### Requirement: Task usage credits preserve integer precision
The shared task-usage slice used by agent tasks and issue runs SHALL expose
`credits_micros: int | None`. Omitted and explicit null SHALL decode to `None`;
zero and positive integers SHALL be preserved exactly; booleans, floats,
strings, negative values when rejected upstream, and malformed container shapes
SHALL fail typed decoding according to the approved contract.

#### Scenario: Credits are absent or null
- **WHEN** a legacy or target payload omits credits or emits JSON null
- **THEN** decoding succeeds with `credits_micros is None`

#### Scenario: Credits preserve exact magnitude
- **WHEN** a payload contains zero or a large valid integer credit value
- **THEN** decoding preserves that integer without floating-point conversion or currency inference

### Requirement: Comment steering is explicit and receipt-preserving
Issue comment add SHALL accept ordered repeatable `steer` run identifiers and a
`steer_active` boolean using the target CLI flags. Steering SHALL be mutually
exclusive with attachments and SHALL preserve the existing content/file/stdin
exclusivity. Successful comment decoding SHALL preserve trigger/steering
outcomes, including queued, coalesced, deferred, blocked, and steered states,
without treating receipt state as an exception.

#### Scenario: Selected runs are steered in caller order
- **WHEN** a caller supplies multiple valid run identifiers
- **THEN** argv contains one `--steer` per identifier in caller order and the comment result preserves returned outcomes

#### Scenario: Steering and attachments conflict before I/O
- **WHEN** steering and any attachment are supplied together
- **THEN** command construction raises before filesystem or subprocess access

#### Scenario: Active steering is distinct from explicit steering
- **WHEN** `steer_active=True` is supplied without explicit run identifiers
- **THEN** argv contains only `--steer-active` and the SDK does not expand active runs locally

### Requirement: Forced daemon stop remains an upstream safety operation
Daemon stop SHALL accept `force: bool = False` and emit `--force` only when
true. The SDK SHALL delegate shutdown, timeout, daemon PID/profile validation,
and exact-child termination to the reviewed CLI command; it SHALL not implement
local process discovery, signal delivery, or cleanup fallback.

#### Scenario: Default stop remains graceful
- **WHEN** daemon stop is called without force
- **THEN** argv is unchanged from the accepted graceful operation

#### Scenario: Forced stop uses one reviewed flag
- **WHEN** daemon stop is called with `force=True`
- **THEN** argv adds only `--force` and reviewed timeout, mismatch, and cleanup failures remain sanitized command failures

### Requirement: Target limits and diagnostics adapt existing operations
Issue workflow status errors, literal issue attachment paths, property value
limits, skill file limits, skill source failures, repository stale-checkout
warnings, foreign-chat privacy, and run-message permission behavior SHALL adapt
their existing public operations and shared exception/result contracts. The SDK
SHALL not add a second validator framework, retry layer, or diagnostic model
when existing typed errors and result fields are sufficient.

#### Scenario: Boundary tables cover both sides
- **WHEN** property, skill-file, or skill-source boundary fixtures exercise the reviewed accepted and rejected values
- **THEN** exact thresholds and target error codes are asserted through existing table-driven tests

#### Scenario: Repository warning does not claim freshness
- **WHEN** repository checkout succeeds from a stale cache and the CLI emits the reviewed warning
- **THEN** the path result remains usable while documentation and tests prevent a false current-state claim

#### Scenario: Privacy behavior remains fail closed
- **WHEN** foreign-chat, run-message, or task-list access is denied or redacted
- **THEN** typed errors/results expose only reviewed public fields and do not reveal private identity, URL, host, path, credentials, or backend detail
