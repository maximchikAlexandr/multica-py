## Why

`TaskRun` is the canonical bound snapshot for a concrete issue execution, but callers must leave that entity to refresh its state or cancel it. Adding the two existing lifecycle operations to the bound surface makes execution control consistent with the SDK's immutable-entity and inspectable-command conventions without introducing a broader orchestration abstraction.

## What Changes

- Add `TaskRun.refresh()` and `TaskRun.refresh_command()` as bound adapters over the existing issue-runs lookup, returning a newly bound `TaskRun` snapshot without mutating the original.
- Add `TaskRun.cancel()` and `TaskRun.cancel_command()` as bound adapters over `IssueResource.cancel_task`, returning `ActionResult[None]` without mutating the original snapshot.
- Preserve `OperationOptions`, command inspection, typed errors, inherited issue context, and the current `Issue.runs` and `TaskRun.messages` behavior.
- Extend the governed bound-operation inventory, table-driven tests, and public documentation for the new methods.
- Keep polling, waiting, terminal-state helpers, new run lookup APIs, new lifecycle types, and orchestration semantics out of scope.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdk-surface`: Add the minimal public `TaskRun` refresh and cancellation method pairs with the established options, return, exception, command-inspection, and immutable-snapshot contracts.
- `bound-resource-relations`: Govern the two bound lifecycle actions as adapters over existing issue resource command plans while preserving run discovery and message relations.
- `verification-and-release`: Require exact signature, argv, result binding, immutability, detached-context, operation-inventory, documentation, and regression coverage for the new bound methods.

## Impact

- Public API: `multica_py.entities.issues.TaskRun` gains four methods; no existing signature or return type changes.
- Implementation: the bound entity delegates to existing `IssueResource.runs_command` and `IssueResource.cancel_task_command` behavior; no transport, dependency, wire model, or upstream command is added.
- Verification: existing bound-operation tables and issue-resource tests gain rows/cases, with unchanged offline repository gates.
- Documentation: TaskRun lifecycle examples and the bound-operation inventory describe explicit refresh-after-cancel behavior.
