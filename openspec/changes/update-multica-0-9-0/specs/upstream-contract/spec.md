## ADDED Requirements

### Requirement: Multica 0.9.0 provenance is exact
The approved contract SHALL record the direct baseline Multica `0.7.1` commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0` and target stable `0.9.0` release `444052572` at commit `8cd8a2db978d532d8627c78cd29f05deab6c6f17`, including the reviewed archive and executable identities.

#### Scenario: Target identity is accepted
- **WHEN** contract validation reads the `0.9.0` provenance
- **THEN** the release, tag commit, archive SHA-256 `107cfffef0ff871388d9ec7110f664f6e90392cf9bba92b0bdea672d7fa9f343`, executable SHA-256 `2c11ee05872013453fab87872188ccaea3af4f81d3f6cb5848c57726ae4eaa10`, platform, architecture, and version output SHALL match the approved values

#### Scenario: Evidence cannot promote behavior
- **WHEN** collector, binary-help, response-review, or source-only evidence contains an operation absent from the approved contract
- **THEN** generation SHALL leave public SDK behavior unchanged

### Requirement: Direct command inventory is completely reconciled
The approved contract SHALL account exactly once for all 236 target command nodes, including 28 additions, one removal, 18 changed nodes, and every source-only command name, with a reviewed `retain`, `adapt`, `remove`, `defer`, or `not_sdk_surface` disposition.

#### Scenario: Changed command mapping is complete
- **WHEN** a retained or adapted node is validated
- **THEN** its positional arity, local and inherited flags, defaults, aliases or deprecation, required and conflict rules, presence semantics, `RunE` or helper destination, pinned source, and positive and negative tests SHALL be present

#### Scenario: Optional families remain deferred
- **WHEN** validation reaches issue-status, workflow, project-workflow, view, project-member, runtime-concurrency, issue-delete, hidden, unattached-environment, daemon-control, or UI-only candidates
- **THEN** no public SDK method SHALL be generated for that candidate by this change

### Requirement: Baseline response review is closed
The contract SHALL contain 196 unique baseline response-entrypoint verdicts, comprising 88 changed and 108 unchanged rows, with `response_review_complete=true` and no pending verdict.

#### Scenario: Response row is traceable
- **WHEN** a response entrypoint is validated
- **THEN** its pinned source, envelope, model action, error action, fixture action, documentation action, and changed or unchanged rationale SHALL be present

#### Scenario: Duplicate or pending response row fails
- **WHEN** a response entrypoint is missing, duplicated, or pending
- **THEN** strict contract validation SHALL fail before rendering

### Requirement: Compatibility and rendering follow the reviewed target
The generated compatibility metadata SHALL retain the existing supported floor, set `0.9.0` as the maximum tested CLI, use the reviewed exclusive next-version ceiling, and render only from the approved contract.

#### Scenario: Rendering is byte stable
- **WHEN** the approved contract is validated and rendered twice from identical inputs
- **THEN** the committed runtime projection and every transient relative output SHALL be byte-identical

#### Scenario: Unreviewed version is outside the tested interval
- **WHEN** a client reports a CLI at or above the approved exclusive ceiling
- **THEN** the existing compatibility policy SHALL warn or reject it without claiming that version was tested
