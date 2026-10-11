## Delivery contract

- `delivery_mode`: `single_wp_no_dag`
- `planning_issue`: `MYL-424`
- `change_id`: `fix-issue-properties-and-local-stdin`
- `graph_revision`: `1`
- `approved_base`: `39700e7e7316489646ace220838674d055654699`
- `estimate_authority`: custom properties `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours` on MYL-424; numeric totals are intentionally not duplicated in this artifact.
- `estimate_basis`: remaining active developer effort for one experienced developer familiar with this Python SDK, without AI acceleration. Confidence is medium and calibration is uncalibrated. The exact code paths, public contracts, existing property loader, standard-library process boundary, test harness, and close local test analogues are inspectable; uncertainty is concentrated in spawned-I/O ownership, cross-platform pipe behavior, timeout races, and full-suite repair. Tests were not run to manufacture estimating evidence.

The authoritative estimate selects one execution unit. This package therefore contains exactly one work package covering every OpenSpec task. Operational status and assignee are intentionally absent from this planning artifact.

## WP-01 — Restore typed Issue properties and deadlock-safe local stdin

- `id`: `WP-01`
- `task_coverage`: `1.1`, `1.2`, `2.1`, `2.2`, `3.1`, `3.2`, `3.3`, `4.1`, `4.2`
- `deliverable`: One coherent compatibility-preserving SDK correction in which raw issue property projections stay separate from the name-keyed typed relation, synchronous local execution services all three pipes under timeout, spawned initial stdin never blocks handle return, and focused real-process evidence proves exact data preservation and bounded failure behavior.
- `owned responsibility scope`: issue projection and bound relation initialization; local subprocess communication and handle-owned I/O lifecycle; directly related resource, lifecycle, conformance, component and fixture coverage; strict specification and repository verification. Directly related tests, fixtures, documentation, snapshots, and service files are included when required to satisfy the tasks.
- `critical shared files`: `src/multica_py/entities/issues.py`, `src/multica_py/_internal/issue_wires.py` if projection preservation requires it, `src/multica_py/_internal/processes.py`, `src/multica_py/execution/local.py`, `tests/unit/resources/test_issues.py`, `tests/unit/test_process_lifecycle.py`, `tests/unit/execution/test_conformance.py`, `tests/component/test_process_contract.py`, and `tests/fixtures/child_process.py`.
- `contract_surface`: ordinary `issues.list/get` raw UUID-to-JSON projections; bound `Issue.properties` as `LazyMapping[str, PropertyValue]` keyed by name; resolved-row eager snapshots; `ExecutionRequest.stdin`; synchronous timeout/cancellation/process-group cleanup; `LocalExecutor.spawn`; `LocalProcessHandle` buffered/streaming ownership, wait, close, and collection-timeout retry; exact stdout/stderr bytes and exit code.
- `definition_of_done/evidence`: every listed OpenSpec task is completed exactly once; raw-map list/get regressions load typed property rows without per-item issue gets and preserve serialization; above-capacity real-process cases prove successful three-channel exchange, bounded timeout cleanup, non-blocking spawn, exact-once input, complete buffered output, and timeout retry; focused tests, strict OpenSpec, Ruff, mypy source/tests, complete non-live pytest with live exclusion, and `make pr` pass with exact commands/exits recorded; no production dependency, unrelated behavior, transient report, or visual HTML is added.
- `parallel_safety`: one executor owns both corrections and their shared process fixtures, so lifecycle semantics and verification evidence are integrated once without conflicting writers or partial handoffs.

## Coverage proof

`WP-01` covers tasks `1.1–1.2`, `2.1–2.2`, `3.1–3.3`, and `4.1–4.2` exactly once. No task is omitted or assigned to another work package.
