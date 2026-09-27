## Delivery Contract

- Task key: `MYL-305`
- OpenSpec change: `add-task-run-lifecycle-actions`
- Approved base: `origin/main` at `d1b5f0e154c5587eca4cebd8bd2a6d39ae3d4d06`
- Delivery mode: `single_wp_no_dag`
- Estimate source: the authoritative `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours` properties on the root planning issue
- Estimate basis: remaining active developer effort for one experienced developer familiar with this Python SDK, without AI acceleration; unattended CI/approval time is excluded
- Confidence: high
- Calibration: evidence-based but uncalibrated against historical effort records

The estimate is supported by inspected current implementations of `TaskRun`, `_refresh_run`, `IssueResource.runs_command`, and `IssueResource.cancel_task_command`; established `Issue` and `Project` continuation methods; the closed bound-operation discovery tables; nearby table-driven tests; documentation seams; and repository delivery gates. The main uncertainty is repair effort after the full gate, not architecture or upstream behavior.

The authoritative estimate property selects `single_wp_no_dag`. This contract therefore contains exactly one work package covering every OpenSpec task. It has no dependency, stage, frontier, or DAG metadata.

## WP-01 — Add Minimal TaskRun Lifecycle Actions

**Task coverage:** `1.1`, `1.2`, `1.3`, `2.1`, `2.2`, `2.3`, `2.4`, `3.1`, `3.2`.

**Deliverable:** A review-ready implementation in which bound `TaskRun` supports inspectable refresh and cancel command pairs over the existing root issue resource plans, with exact immutable result/error semantics, governed public-surface declarations, focused table-driven proof, updated documentation, and all required repository gates passing.

**Owned responsibility scope:**

- Bound task-run lifecycle implementation and shared exact-ID refresh selection in `src/multica_py/entities/issues.py`.
- Directly related operation inventories and table-driven unit/contract/type-check fixtures, including supporting snapshots or count assertions required by those inventories.
- Public API and service-usage documentation for the lifecycle actions.
- OpenSpec task completion and delivery evidence for this change.
- No changes to the canonical root operation inventory, `contracts/sdk-contract.json`, transport, wire models, dependencies, or unrelated resource behavior unless an observed gate proves a directly caused consistency fix is required; any product-contract expansion requires a planning revision.

**Contract surface:**

- `TaskRun.refresh_command(*, options=None) -> Command[TaskRun]` reuses `IssueResource.runs_command`, requires bound client plus inherited issue context, selects the exact run ID, and raises `ProtocolError` if a successful page omits it.
- `TaskRun.refresh(*, options=None) -> TaskRun` runs the inspectable command and returns a newly bound immutable snapshot.
- `TaskRun.cancel_command(*, options=None) -> Command[ActionResult[None]]` reuses `IssueResource.cancel_task_command`, forwards inherited issue context when present, and preserves task-ID-only addressing otherwise.
- `TaskRun.cancel(*, options=None) -> ActionResult[None]` runs the inspectable command without implicit refresh or snapshot mutation.
- `Issue.runs`, `TaskRun.messages`, and `TaskRun.stream_events` remain behaviorally and structurally unchanged.

**Definition of done and evidence:**

- Every covered checkbox in `tasks.md` is completed once, with no scope left for another WP.
- Exact command previews and transport calls prove default and operation-option forms; command construction proves zero I/O.
- Positive cases prove exact refreshed-row selection, originating-client binding, action result type, eager/command equivalence, and original snapshot immutability.
- Negative cases prove detached and missing-context boundaries, optional cancellation context, missing-run `ProtocolError`, and unmodified root exception propagation without retries or extra calls.
- Closed bound-operation and public-signature inventories accept exactly the four new methods while canonical root-operation contract checks remain unchanged.
- API/service documentation shows direct and command forms, explicit refresh after cancellation, unchanged message access, and no orchestration helpers.
- Strict OpenSpec validation, focused tests, Ruff, mypy, non-live collection and suite, build/package validation, and repository `make pr` complete successfully with exact command/exit evidence and no transient tracked artifacts.

**Parallel-safety rationale:** This is intentionally one indivisible implementation package. Runtime methods, closed inventory declarations, focused tests, and documentation describe one small public contract and are likely to touch the same high-contention files; splitting them would create coordination overhead and temporary invariant failures without an independent deliverable.
