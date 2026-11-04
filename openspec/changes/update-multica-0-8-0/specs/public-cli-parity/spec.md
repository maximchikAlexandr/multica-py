## ADDED Requirements

### Requirement: Approved 0.8.0 public commands have one typed SDK owner
Every supported target command SHALL map to one canonical eager SDK operation
and an argument-identical lazy `*_command()` operation through the existing CLI
transport. The public method, resource location, result decoder, validation,
contract record, generated inventory, tests, and documentation SHALL agree.

#### Scenario: Newly approved command families are discoverable
- **WHEN** public operation discovery runs after the upgrade
- **THEN** workflow lifecycle and handoff, project workflow get/set, runtime concurrency, issue rerun-task, comment steering, and forced daemon stop each have one canonical typed owner

#### Scenario: Existing commands remain closed
- **WHEN** the target inventory is compared with public SDK discovery
- **THEN** every retained operation keeps its owner and every approved adaptation is represented without duplicate aliases or raw-command-only gaps

### Requirement: Workflow commands preserve upstream identity and presence
The SDK SHALL support workflow list/get/create/update/delete and handoff set,
plus project workflow get/set. Workflow references SHALL accept the reviewed
UUID, full prefix, exact name, and default forms; provider-owned status keys
and handler kinds SHALL remain open strings. Update omission, explicit null,
file inputs, repeatable mappings, dry-run results, and structured conflicts
SHALL retain their distinct target semantics.

#### Scenario: Workflow update requires an explicit change
- **WHEN** a workflow update is constructed with every field omitted
- **THEN** validation fails before CLI execution rather than inventing a no-op mutation

#### Scenario: Project reset uses explicit default
- **WHEN** project workflow set receives the reviewed `default` selection
- **THEN** argv sends that exact selection, target behavior clears the project override, and the typed result preserves the resolved workflow state

#### Scenario: Handoff replacement preserves unspecified fields
- **WHEN** handoff set changes only a reviewed handler or instruction field
- **THEN** the SDK emits the exact selected flags and relies on the target command's read-modify-replace behavior without fabricating unavailable fields

### Requirement: Rerun migration targets task runs explicitly
The SDK SHALL remove `IssueResource.rerun` and `rerun_command`, which map the
hidden legacy `issue rerun` command and empty action response. It SHALL add
`rerun_task` and `rerun_task_command` for public `issue rerun-task <run-id>`,
with optional issue scope and fresh execution, returning the canonical typed
task-run result. No compatibility shim SHALL silently change old return types.

#### Scenario: Scoped rerun resolves one task
- **WHEN** a caller reruns a full run UUID or short prefix with an issue scope
- **THEN** exact argv carries `--issue`, optional `--fresh`, and JSON output and the result decodes as a task run

#### Scenario: Obsolete rerun imports and methods are absent
- **WHEN** public discovery and migration tests inspect the issue resource
- **THEN** the legacy rerun pair and its generated inventory row are absent and documentation names `rerun_task` as the replacement

### Requirement: Task-only and hidden surfaces remain excluded
Quick-create `--assignee-picker`, Cobra root nodes, hidden `probe-runtimes`,
hidden legacy rerun, UI/desktop/provider-only behavior, and server routes without
a reviewed public CLI operation SHALL be recorded as deferred or
`not_sdk_surface` and SHALL NOT create public SDK symbols.

#### Scenario: Exclusions cannot leak into generation
- **WHEN** generated discovery and forbidden-symbol assertions run
- **THEN** excluded nodes have contract evidence but no public method, model, enum, or export
