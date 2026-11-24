## ADDED Requirements

### Requirement: Removed issue rerun is replaced by reviewed rerun-task
The target public SDK SHALL remove the obsolete `issues.rerun` operation and its resource/bound methods and SHALL expose the target `issue rerun-task` behavior as `issues.rerun_task` with matching eager and command-building methods on the existing issue resource and bound issue.

#### Scenario: Replacement operation emits exact target command
- **WHEN** a caller invokes `rerun_task` with any approved optional inputs
- **THEN** the SDK SHALL emit the exact reviewed `issue rerun-task` argv, preserve omission versus explicit values, and decode the approved target result

#### Scenario: Removed operation is absent
- **WHEN** public exports, generated bindings, operation cases, documentation, and bound issue methods are inspected
- **THEN** `issues.rerun` and `rerun` SHALL be absent and SHALL NOT target a hidden compatibility command

#### Scenario: Replacement failures remain typed
- **WHEN** the target refuses rerun-task because the issue/task state or input is invalid
- **THEN** the SDK SHALL raise the existing sanitized typed command error with the reviewed status and payload

### Requirement: Every target command has an explicit SDK disposition
Every target help node, changed baseline node, removed node, hidden node, and source-only name SHALL have exactly one `support`, `adapt`, `retain`, `remove`, `defer`, or `not_sdk_surface` decision in the approved inventory.

#### Scenario: Deferred families remain unavailable
- **WHEN** public SDK discovery runs after the upgrade
- **THEN** deferred chat-wakeup, Inbox, issue batch/status-management, project member/overview/progress/workflow-management, quick-action, View, Workflow, `doc`, and `environment` families SHALL NOT appear as public resources or methods

#### Scenario: Adapted operations preserve existing names
- **WHEN** a changed target command already belongs to an approved SDK operation
- **THEN** the existing public operation name SHALL remain stable unless this change explicitly names a replacement

#### Scenario: Discovery equals the approved operation set
- **WHEN** canonical public method discovery and generated inventory checks run
- **THEN** they SHALL equal the approved supported/retained/adapted operation rows with no allowlist, duplicate, or ungoverned method
