## ADDED Requirements

### Requirement: Issue updated-time filters are paired and stable across pages
`issues.list` SHALL accept `updated_since` and `updated_until` only as a pair of RFC3339 timestamps, SHALL require `updated_since < updated_until`, and SHALL emit the corresponding CLI flags unchanged on every page request.

#### Scenario: Valid half-open updated interval
- **WHEN** a caller supplies valid RFC3339 bounds with `updated_since < updated_until`
- **THEN** the SDK SHALL emit both flags and decode the normal issue page

#### Scenario: Missing, malformed, or reversed bounds
- **WHEN** one bound is omitted, either bound is not RFC3339, or `updated_since >= updated_until`
- **THEN** the SDK SHALL raise validation before transport executes

### Requirement: Attachment paths remain literal repeatable values
Issue create, update, and comment attachment inputs SHALL emit one flag per supplied path and SHALL treat commas as literal path characters rather than separators. Existing omission, ordering, and external-file validation SHALL remain.

#### Scenario: Literal comma path
- **WHEN** a caller supplies two paths and one contains a comma
- **THEN** the SDK SHALL emit two attachment flags and SHALL preserve the comma-containing path byte-for-byte

### Requirement: Comment projections preserve endpoint-specific fields
Roots-only comment list projections SHALL decode optional `resolution_id`, `resolution_content`, and `resolution_content_truncated`. Default, flat, recent, and thread projections SHALL tolerate omission and SHALL NOT synthesize those fields. Existing open enum and tombstone behavior SHALL remain.

#### Scenario: Roots-only resolution summary
- **WHEN** a roots-only summary or since response includes resolution projection fields
- **THEN** the SDK SHALL preserve their values and truncation state

#### Scenario: Non-roots projection omits resolution fields
- **WHEN** a default, flat, recent, or thread response omits resolution projection fields
- **THEN** the SDK SHALL decode the existing row without inventing a resolution

### Requirement: Changed retained response models remain forward-compatible
The SDK SHALL adapt the changed retained responses as follows: task-run rows accept optional integer `credits_micros`; attachment results accept optional integer `width` and `height`; projects accept nullable `creator_type` and `creator_id`; runtime definitions accept nullable integer `max_concurrent_tasks`; user profiles accept nullable or older-server-omitted `whats_new_seen_version`; workspace list rows accept optional RFC3339 `pinned_at` and preserve pinned-first order. Each model SHALL retain all previously supported fields, nullability, omission, timestamps, open values, pagination, and bound relations.

#### Scenario: Old and new wire rows decode
- **WHEN** each affected decoder receives a baseline row without the new field and a target row with null or a valid target value
- **THEN** both rows SHALL decode with the prior public fields unchanged and the new field represented accurately

#### Scenario: Invalid and unknown values fail or remain open as specified
- **WHEN** a changed field has an invalid wire type or an existing open enum receives an unknown string
- **THEN** invalid types SHALL raise the existing decode error and open enum values SHALL round-trip without closing the vocabulary

### Requirement: Runtime concurrency presence semantics are distinct
The existing runtime update input SHALL distinguish omitted `max_concurrent_tasks` as retain, an integer from 1 through 50 as set, and explicit `None` as clear to unlimited. Runtime response `null` SHALL mean unlimited.

#### Scenario: Retain, set, and clear
- **WHEN** callers respectively omit the field, supply an in-range integer, or supply explicit `None`
- **THEN** the SDK SHALL preserve distinct absent, integer, and null transport states and decode the resulting nullable response

#### Scenario: Invalid concurrency value
- **WHEN** a caller supplies a boolean, zero, a negative integer, or an integer greater than 50
- **THEN** the SDK SHALL reject the value before transport executes

### Requirement: Issue retry becomes run-targeted after explicit approval
After approval of this breaking change, the SDK SHALL remove the false public mapping from `issues.rerun(issue)` to hidden/deprecated `issue rerun` and SHALL expose `issues.rerun_task(run_id, *, issue=None, fresh=False) -> TaskRun` using public `issue rerun-task`. It SHALL preserve run-id prefix scoping through optional issue identity, SHALL emit `--fresh` only when requested, and SHALL decode the returned task row. No implementation SHALL begin before the human gate approves this migration.

#### Scenario: Run-targeted retry
- **WHEN** an approved caller retries a run with optional issue scope and `fresh=True`
- **THEN** the SDK SHALL invoke `issue rerun-task <run-id> --issue <issue> --fresh --output json` and return the decoded task row

#### Scenario: Legacy issue-targeted call is not silently emulated
- **WHEN** a caller attempts the removed issue-targeted retry contract after the approved breaking release
- **THEN** the SDK SHALL provide no false mapping to a run-targeted command and migration documentation SHALL direct the caller to supply a run id

### Requirement: New upstream groups remain deferred
Workflow, project-workflow, view, runtime-concurrency management, comment steering, daemon watchdog/force, interactive assignee-picker, hidden probe commands, and skill-history/restore surfaces SHALL NOT enter the public SDK in this change. Existing comment add without steering and existing process-control behavior SHALL remain supported.

#### Scenario: Contract surface audit
- **WHEN** the approved contract and public resource exports are inspected
- **THEN** no operation, signature, response, enum, or model for a deferred surface SHALL appear
