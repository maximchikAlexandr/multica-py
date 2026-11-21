## ADDED Requirements

### Requirement: Multica 0.11.1 parity decisions are complete and review-gated
The SDK SHALL maintain a closed target inventory for Multica `0.11.1` in which every public help node and every separately reconciled source-only name has one explicit scope decision. Extractor discovery SHALL NOT itself authorize a public method, model, enum, or compatibility claim.

#### Scenario: Inventory closure is exact
- **WHEN** target help and source-only inventories are compared with approved decisions
- **THEN** every identity SHALL have exactly one disposition and every promoted mapping SHALL name its existing or approved public symbol, response, tests, and documentation

#### Scenario: New families remain deferred
- **WHEN** public discovery is inspected after the upgrade
- **THEN** chat wakeups, inbox, issue batch/delete/PR linking, issue-status, view, workflow, project archive/restore/member/workflow, runtime concurrency, and other candidate-only families SHALL expose no new public SDK symbol

### Requirement: Legacy issue rerun migrates to the target command
The existing public `IssueResource.rerun(issue_id)` and `rerun_command(issue_id)` behavior SHALL invoke target command `issue rerun-task <issue-id>` while preserving the existing typed signature and `ActionResult[None]` response contract. The removed public `issue rerun` command SHALL NOT remain as an argv fallback.

#### Scenario: Existing SDK call uses the replacement command
- **WHEN** a caller constructs or executes `issues.rerun(issue_id)` against the target contract
- **THEN** exact argv SHALL contain `issue rerun-task <issue-id>` and the existing action result SHALL decode

#### Scenario: Legacy command is absent
- **WHEN** approved bindings, generated projection, canonical vectors, docs, and public discovery are inspected
- **THEN** no governed argv SHALL invoke public `issue rerun`, while hidden source compatibility `rerun` remains `not_sdk_surface`

### Requirement: Deferred and non-SDK behavior cannot leak through related operations
UI-only behavior, daemon internals, hidden commands, claim-only fields, root wiring, and server functionality without a reviewed supported CLI entrypoint SHALL remain `not_sdk_surface` or `defer` as approved and SHALL NOT be inferred from a related supported operation.

#### Scenario: Related server behavior is discovered
- **WHEN** target source exposes a server route, internal command, or response field without an approved SDK entrypoint
- **THEN** contract validation SHALL require an explicit defer or non-surface row and public inventory SHALL remain unchanged
