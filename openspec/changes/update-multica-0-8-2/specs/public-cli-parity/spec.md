## ADDED Requirements

### Requirement: Every approved 0.8.2 operation records exact CLI semantics
Each supported or adapted operation SHALL record positional arity, command path, aliases/deprecation, local and inherited flags, defaults, destination mapping, normalized constraints, response adapter, and source provenance.

#### Scenario: Presence-sensitive inputs are reviewed
- **WHEN** a flag distinguishes omitted, null, empty, zero, or false values
- **THEN** the public signature and approved mapping represent every accepted state and reject unsupported states before process execution

#### Scenario: Imperative validation is normalized
- **WHEN** pinned source uses `Flags().Changed`, conditionals, or helper validation
- **THEN** the contract records the exact requires, conflict, together, range, enum, or custom-validator rule with positive and negative table-driven cases

### Requirement: Legacy issue rerun is replaced by run-targeted rerun
The SDK SHALL remove the false issue-targeted rerun mapping and SHALL expose the public `issue rerun-task <run-id>` operation with optional issue-scoped short-prefix resolution, `fresh` presence, and a typed task-row result.

#### Scenario: Full run identifier reruns safely
- **WHEN** a caller supplies a full run identifier without issue scope
- **THEN** exact argv invokes `issue rerun-task <run-id> --output json` and returns the reviewed task projection

#### Scenario: Short run prefix requires issue scope
- **WHEN** a caller supplies a short run prefix without `issue_id`
- **THEN** validation fails before transport and the migration documentation directs callers away from issue-targeted rerun

#### Scenario: Fresh rerun disables reuse
- **WHEN** `fresh=True` is supplied
- **THEN** exact argv contains `--fresh` once and the operation retains the target task-row response

### Requirement: CLI-backed additions have reviewed dispositions
Issue statuses, project members, workflows and project workflows, saved views, and runtime concurrency SHALL be supported as typed CLI-backed resources; `environment`, daemon force/watchdog controls, hidden commands, and UI-only changes SHALL remain deferred or non-SDK surface as recorded in the contract.

#### Scenario: Approved additions are generated and bound
- **WHEN** a caller accesses an approved new resource
- **THEN** explicit client/resource methods use reviewed argv, validation, decoding, options, and errors without runtime registry dispatch or direct HTTP access

#### Scenario: Deferred process controls remain absent
- **WHEN** generation inspects attached-but-ungrouped `environment` or daemon process-control flags
- **THEN** no public SDK method is emitted and documentation records the upstream exposure or safety decision required for a future change

### Requirement: Mandatory compatibility repairs remain distinct from additions
The contract and migration documentation SHALL distinguish required repairs to retained behavior from optional newly approved resource families.

#### Scenario: A new family cannot mask an incomplete repair
- **WHEN** any mandatory rerun, search, attachment, PR auto-complete, response, authorization, or compatibility repair is unresolved
- **THEN** release validation fails even if every newly approved resource family passes its own tests

