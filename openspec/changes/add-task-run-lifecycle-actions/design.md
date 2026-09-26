## Context

`TaskRun` is a frozen bound entity produced by `IssueResource.runs()` and retains both its originating `MulticaClient` and inherited `issue_id`. It already owns the `messages` relation and `stream_events()`. Status refresh is currently available only indirectly: streaming calls the private `_refresh_run()` helper, which eagerly loads `IssueResource.runs(issue_id)` and selects the matching run. Cancellation already exists as the governed `IssueResource.cancel_task_command(task_id, *, issue_id=None, options=None)` operation and returns `ActionResult[None]`.

The neighboring `Issue` and `Project` entities establish the continuation pattern: a bound eager method delegates to an argument-identical `*_command()` method, command construction performs no I/O, per-operation options flow to the root resource, detached entities fail before transport, and returned entities are new immutable snapshots. The new surface must reuse those seams and must not create a second run resource or lifecycle abstraction.

## Goals / Non-Goals

**Goals:**

- Expose `refresh`/`refresh_command` and `cancel`/`cancel_command` directly on bound `TaskRun`.
- Preserve exact root-command argv, `OperationOptions`, result types, binding, exceptions, and lazy command inspection.
- Return a new bound run from refresh and leave the original frozen snapshot unchanged after both actions.
- Keep the governed bound-operation inventory, tests, and public documentation exact.

**Non-Goals:**

- No `TaskHandle`, run lookup resource, wait/poll helper, terminal-state predicate, async/streaming addition, or creation/correlation API.
- No change to `Issue.runs`, `TaskRun.messages`, or `TaskRun.stream_events` semantics.
- No new upstream command, approved SDK-contract operation, transport, wire model, dependency, or persistence behavior.

## Decisions

### Decision 1: Refresh through the existing issue-runs command plan

`TaskRun.refresh_command(*, options=None)` SHALL require the bound client and inherited `issue_id`, build `client.issues.runs_command(issue_id, options=options)`, and map its result to the row whose `id` exactly equals `self.id`. The selected row is already bound by `IssueResource.runs_command`; it is returned as a new `TaskRun`. If a successful page omits the target, the mapper SHALL raise `ProtocolError`, matching the existing streaming refresh contract.

The implementation SHOULD extract one pure selector shared by `_refresh_run()` and the new command mapper so eager streaming and inspectable refresh cannot drift. `refresh()` remains only `return self.refresh_command(options=options).run()`.

Alternative considered: add `IssueResource.get_run()` or reload an arbitrary page through a new CLI operation. Rejected because no single-run upstream command exists, `issue.runs` is already the governed discovery path, and GitHub issue #52 explicitly excludes another lookup API.

### Decision 2: Cancel through the existing cancellation action

`TaskRun.cancel_command(*, options=None)` SHALL require the bound client and delegate to `client.issues.cancel_task_command(self.id, issue_id=self.issue_id, options=options)`. The optional inherited issue ID is forwarded when present and omitted when absent, preserving the root operation's supported addressing contract. `cancel()` SHALL run that command and return its existing `ActionResult[None]` unchanged.

Cancellation SHALL NOT refresh or mutate the run. A caller that needs current state performs an explicit subsequent `refresh()`.

Alternative considered: automatically return the refreshed run after cancellation. Rejected because it changes the established action result, adds an unrequested second subprocess, obscures command inspection, and introduces a race-dependent composite operation.

### Decision 3: Treat the methods as governed bound aliases, not new root operations

The four public methods SHALL be declared in the explicit bound-operation inventory used by discovery tests. Their signatures contain only keyword-only `options: OperationOptions | None = None`; eager and command forms differ only by return annotation. Canonical root operation counts and `contracts/sdk-contract.json` SHALL remain unchanged because both underlying CLI operations are already approved.

Focused table-driven tests SHALL cover exact previews, zero construction I/O, option forwarding, eager/command equivalence, new-snapshot binding, missing-run `ProtocolError`, detached refresh/cancel failure, missing refresh issue context, optional cancel issue context, propagated root command failures, and preservation of messages/run discovery behavior.

Alternative considered: add duplicate canonical operations for the bound aliases to the approved upstream contract. Rejected because that contract identifies CLI operations; the repository already models bound aliases separately and duplicate entries would overstate upstream coverage.

### Decision 4: Document explicit lifecycle composition only

Public documentation SHALL show `fresh_run = run.refresh()`, inspectable command execution, `result = run.cancel()`, and explicit `run.cancel(); run = run.refresh()`. It SHALL continue directing message reads through `run.messages` and SHALL not imply waiting, terminal interpretation, verification, or orchestration policy.

Alternative considered: document polling examples as part of this change. Rejected because polling policy and terminal interpretation are explicit non-goals.

## Risks / Trade-offs

- [Refresh scans the issue's run page because no direct run-get command exists] → Reuse the current governed path and exact-ID selector; do not invent an API or silently return another row.
- [A run may disappear between snapshots] → Raise `ProtocolError` on a successful response that omits the requested ID, consistent with streaming behavior.
- [Cancellation acknowledgement does not imply a refreshed state] → Preserve `ActionResult[None]` and document the explicit refresh step.
- [Bound-operation discovery is closed and can fail when methods are added] → Update the single explicit declaration/table and its exactness tests in the same implementation task.
- [The active `unify-sdk-operation-contracts` change also governs operation conventions] → Keep this change additive, use the current post-normalization `Page`/`ActionResult` APIs, and avoid modifying root operation contracts or response conventions.

## Migration Plan

This is an additive SDK surface change with no data migration. Implement the bound adapters and shared selector, extend table-driven verification and documentation, then run strict OpenSpec and the repository's normal offline gates. Rollback removes the four bound methods and their declarations/tests/docs; the underlying root resource APIs remain intact.

## Open Questions

None. The source issue and existing root command contracts determine the lifecycle surface and error behavior.
