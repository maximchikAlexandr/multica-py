## ADDED Requirements

### Requirement: Approved 0.11.0 adaptations preserve typed presence semantics
The SDK SHALL implement every approved changed response row with explicit
present, omitted, null, malformed, and open-enum behavior. This SHALL include
squad autopilot assignees, webhook payload conditions, optional
`run_outcome`, runtime-profile `daemon_id`, project privacy/activity/archive
fields, subscriber delivery, and skill bundle-limit errors.

#### Scenario: Optional target field is omitted
- **WHEN** a legacy-compatible response omits an approved optional target field
- **THEN** decoding succeeds with the documented omission state and does not invent a value

#### Scenario: Open enum receives a valid unknown token
- **WHEN** an open-policy field contains a syntactically valid unknown target token
- **THEN** the token survives decoding and public projection without coercion

#### Scenario: Malformed changed field is returned
- **WHEN** a changed field violates its approved wire type or required relation
- **THEN** decoding fails with the existing typed malformed-response boundary

### Requirement: Legacy issue rerun is replaced by task-identity rerun
The public legacy `issue rerun` mapping SHALL be removed. The SDK SHALL expose
the approved `issue rerun-task` operation using explicit task identity and the
reviewed resume/fresh mode contract, with a typed result and no issue-derived
task inference or compatibility alias.

#### Scenario: Task rerun succeeds
- **WHEN** a caller supplies a task identity and exactly one approved rerun mode
- **THEN** the SDK emits the exact reviewed argv and returns the typed rerun result

#### Scenario: Legacy rerun surface is inspected
- **WHEN** public symbols, documentation, and generated operation inventory are inspected
- **THEN** no callable legacy issue-rerun alias or mapping remains

#### Scenario: Rerun mode is missing or conflicting
- **WHEN** a caller supplies no mode or conflicting modes
- **THEN** validation fails before any process invocation

### Requirement: Changed command inputs preserve literal and constrained behavior
Inline description, content, and context values SHALL preserve literal
backslashes. File channels SHALL preserve UTF-8 multiline content with the
reviewed trailing-newline behavior. Metadata keys SHALL be path-escaped exactly,
and webhook filter, squad-assignee, runtime-profile, and destructive-operation
constraints SHALL be validated before I/O.

#### Scenario: Literal inline text is submitted
- **WHEN** an approved inline text argument contains backslashes and escape-like sequences
- **THEN** exact literal text reaches the CLI without SDK interpretation

#### Scenario: File text is submitted
- **WHEN** an approved file channel reads a UTF-8 multiline file
- **THEN** the exact content reaches the CLI with only the contractually required single trailing newline

#### Scenario: Invalid cross-field constraint is submitted
- **WHEN** squad, webhook, runtime-profile, or destructive inputs violate an approved requires, conflicts, or exactly-one rule
- **THEN** a typed local validation error is raised with zero process invocations

### Requirement: Target errors retain safety and redaction
The transport and resource layers SHALL map approved no-body `499`
cancellation, private-resource not-found, archived-project `409`, bounded
runtime-delete conflict, and skill aggregate-budget `413` responses to typed
errors. They SHALL NOT retry cancellation or conflict responses, expose secrets,
or initiate destructive follow-up.

#### Scenario: No-body cancellation is returned
- **WHEN** a target CLI operation exits with the approved empty `499` cancellation shape
- **THEN** the SDK raises the typed cancellation error without a JSON-shape error or retry

#### Scenario: Bounded destructive conflict is returned
- **WHEN** runtime deletion or project mutation returns an approved conflict
- **THEN** the SDK exposes sanitized bounded details and performs no cascade, retry, or second mutation

#### Scenario: Skill bundle exceeds the aggregate limit
- **WHEN** skill write input receives the approved `413` response
- **THEN** the SDK raises the typed size-limit error without leaking payload content

### Requirement: Deferred families remain absent
Chat wakeups, inbox, issue batch/delete/pull-request linking, issue-status,
view, workflow, project-management additions, and other commands classified
`defer` SHALL remain outside the public SDK surface until a separate approved
change defines their naming and compatibility policy.

#### Scenario: Package surface is audited
- **WHEN** public exports, resource methods, generated operations, and documentation are compared with dispositions
- **THEN** no deferred family is publicly callable or documented as supported
