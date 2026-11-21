## ADDED Requirements

### Requirement: Changed retained operations preserve typed presence and errors
All 102 changed supported work items SHALL be adapted through the existing resource, entity, model, wire, decoder, transport-error, and command-plan seams. Optional fields and inputs SHALL distinguish omission, explicit null, explicit empty, and supplied values; open upstream enums SHALL preserve unknown valid strings; closed SDK enums SHALL reject unknown values before I/O.

#### Scenario: Optional target field is omitted or null
- **WHEN** a reviewed target response omits an optional field or supplies explicit null
- **THEN** the approved model SHALL apply the row-specific presence policy without inventing a value or collapsing omission into an explicit write

#### Scenario: Unknown open enum value arrives
- **WHEN** a target-owned open value has the approved wire type but is not yet known to the SDK
- **THEN** decoding SHALL preserve it without closed-enum rejection

#### Scenario: Reviewed error is returned
- **WHEN** a changed operation returns an approved 400, 409, or 413 standard-error shape
- **THEN** the existing sanitized typed exception boundary SHALL preserve approved status/code/message fields without retrying or leaking private backend detail

### Requirement: Assignees, conditions, outcomes, and machine binding are explicit
Existing autopilot, issue, wakeup, runtime, runtime-profile, project-resource, and task/run models and operations SHALL represent reviewed squad assignees, webhook payload conditions, optional `run_outcome`, and `daemon_id` machine binding through their existing public families and presence policies.

#### Scenario: Squad is the assignee
- **WHEN** an approved autopilot or issue operation receives or returns a squad assignee
- **THEN** the SDK SHALL preserve the `squad` discriminator and canonical identity without coercing it to agent or member

#### Scenario: Payload conditions are supplied
- **WHEN** a supported webhook/autopilot trigger operation receives reviewed payload conditions
- **THEN** command and eager forms SHALL produce the same exact ordered mapping, reject malformed constraints before transport, and preserve omission separately from an empty set

#### Scenario: Run outcome is absent or present
- **WHEN** an approved task/run response omits, nulls, or supplies `run_outcome`
- **THEN** the SDK SHALL apply the reviewed optional/open-value policy and malformed wire types SHALL fail with the existing output-shape error

#### Scenario: Runtime profile is machine-bound
- **WHEN** a reviewed runtime or profile operation receives or returns `daemon_id`
- **THEN** the SDK SHALL preserve the approved identifier, omission, and compatibility semantics without inventing cross-machine fallback

### Requirement: Text channels preserve target semantics and sanitize NUL input
Supported issue, workspace, user-profile, comment, and related text mutations SHALL preserve literal inline text, preserve file/stdin content except the target's single trailing-LF rule, distinguish omission from explicit empty input, and match target NUL sanitization before validation, comparison, and persistence where the reviewed operation applies it.

#### Scenario: Inline backslashes are literal
- **WHEN** a supported inline text argument contains backslash sequences
- **THEN** the SDK SHALL pass literal text and SHALL NOT decode escape sequences locally

#### Scenario: File or stdin carries multiline text
- **WHEN** a supported file/stdin channel supplies multiline text
- **THEN** content SHALL remain byte/text equivalent except for the reviewed removal of one trailing LF

#### Scenario: NUL-bearing issue text is submitted
- **WHEN** issue create/update title, title-base, description, or description-base contains NUL according to the target handler's reviewed scope
- **THEN** the resulting command/response behavior SHALL match target sanitization and tests SHALL distinguish sanitized equality, validation, and persistence from local argv rejection

### Requirement: Pagination and workspace ordering remain source-governed
Changed list operations SHALL preserve their reviewed pagination envelope, cursor/offset semantics, filter destinations, and ordering. Workspace list SHALL decode optional RFC3339 `pinned_at` and retain pinned-first ordering, while get/create/update SHALL not fabricate that list-only projection.

#### Scenario: Changed page traverses
- **WHEN** a changed list operation returns multiple pages or a terminal page
- **THEN** the SDK SHALL preserve every item once, advance according to the approved pagination strategy, and stop on the reviewed terminal condition

#### Scenario: Workspace membership is pinned
- **WHEN** workspace list returns `pinned_at`
- **THEN** the SDK SHALL decode the optional timestamp and preserve target pinned-first ordering without adding it to non-list responses

### Requirement: Skill budget failures preserve the existing operation boundary
Existing skill import, refresh, and file operations SHALL retain their public methods while applying target size/write limits and the approved 413 error through existing typed errors and atomic bundle behavior.

#### Scenario: Skill write exceeds the target budget
- **WHEN** a supported skill operation returns the reviewed 413 standard error
- **THEN** the SDK SHALL raise the approved typed command error, expose only sanitized fields, and preserve any previously complete bundle

### Requirement: Changed contracts extend existing architecture only
Implementation SHALL reuse the approved contract schema, generator, explicit resource methods, wire structs, decoders, shared error mapping, frozen operation cases, and existing CI workflows. It SHALL NOT add a second transport, runtime registry, version-specific resource layer, dependency, generator, or public family.

#### Scenario: Implementation surface is inspected
- **WHEN** the final diff is reviewed
- **THEN** every production addition SHALL trace to a requirement or unique compatibility risk and SHALL use an existing seam, while deferred families and speculative abstractions remain absent
