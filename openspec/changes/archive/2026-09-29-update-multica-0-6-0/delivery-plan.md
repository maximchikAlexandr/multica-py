## Delivery contract

- `delivery_mode`: `dag`
- `planning_issue`: `MYL-342`
- `change_id`: `update-multica-0-6-0`
- `graph_revision`: `4`
- `approved_base`: `c1842ae2dfcd0cc5e739b7785d3209d5e72d01ed`
- `estimate_authority`: custom properties `Estimate, hours`, `Estimate min, hours`
  and `Estimate max, hours` on the planning issue; numeric totals are intentionally
  not duplicated in this artifact.
- `estimate_basis`: remaining active developer effort for one experienced developer
  familiar with this Python SDK, without AI acceleration. Confidence is medium and
  calibration is uncalibrated: refreshed code and close local extension points are
  inspectable, while the 196-entrypoint contract reconciliation, wakeup-v2 presence
  matrix, stderr cursor and likely full-gate repair loops have no comparable measured
  execution history. Tests were not run to manufacture estimating evidence.
- `stage_mapping`: `WP-01 -> 1`, `WP-02 -> 2`, `WP-03 -> 2`, `WP-04 -> 3`.

The authoritative estimate selects DAG delivery. Stage 2 is a real parallel
frontier: both siblings consume WP-01 outputs read-only and own disjoint mutable
files. WP-02 owns wakeup-specific modules; WP-03 is the single writer for
`src/multica_py/_internal/wire_models.py` and all other agent/issue/comment/PR/MCP
focused paths. WP-04 exclusively owns every aggregate seam after the join.

## WP-01 — Refreshed 0.6.0 contract foundation

- `id`: `WP-01`
- `stage`: `1`
- `task_coverage`: `1.1`, `1.2`, `1.3`, `1.4`, `1.5`
- `depends_on`: none
- `deliverable`: One validated approved contract based on exact refreshed main,
  including provenance, all command/response dispositions and mappings, vectors,
  compatibility policy and deterministic generated projection.
- `owned responsibility scope`: `contracts/sdk-contract.json`; required schema,
  validator and generator support under `contracts/schema/` and
  `tools/upstream_contract/`; `src/multica_py/_generated/approved_sdk.py`; private
  contract-generation checks. Evidence manifests and binaries remain untracked.
- `critical shared files`: contract and generated module are immutable inputs to all
  stage-2 WPs; only WP-01 writes them.
- `contract surface`: exact baseline/target identities; 205-node dispositions;
  193 approved operations; 196 response entrypoints with 18 changed/178 unchanged;
  input/output gates, mappings, vectors and source/test references.
- `definition_of_done/evidence`: validate succeeds; two renders are byte-identical;
  generated check succeeds; baseline PR #95 operations have no duplicate promotion;
  no evidence or transient output is tracked.
- `parallel_safety`: sole stage-1 predecessor centralizes every contract decision
  before handwritten siblings start.

## WP-02 — Existing wakeup resource v2

- `id`: `WP-02`
- `stage`: `2`
- `task_coverage`: `2.1`, `2.2`, `2.3`, `2.4`
- `depends_on`: `WP-01`
- `deliverable`: Existing wakeup resource/models support six evolved baseline pairs
  plus four target-only lifecycle pairs with exact validation, response presence and
  private focused evidence.
- `owned responsibility scope`: `src/multica_py/resources/issue_wakeups.py`,
  `src/multica_py/models/issue_wakeups.py`, and wakeup-private tests/fixtures/helpers.
  It SHALL NOT edit aggregate model exports, operation tables, public inventories,
  shared contract fixtures or consumer docs.
- `critical shared files`: none mutable with stage-2 siblings. WP-01 contract and
  generated binding are read-only; aggregate seams belong to WP-04.
- `contract surface`: existing create/update/list/get/disable/events v2 fields;
  seven condition families; deadlines/timeouts/fire limits; trigger/delete/checkin/
  runs results; local versus server validation; open values and no extra retry.
- `definition_of_done/evidence`: private tests prove all ten eager/command pairs,
  exact argv/results, replacement semantics, response presence, omitted target cap,
  checkin ownership boundaries, malformed values and ambiguous-failure no-retry.
- `parallel_safety`: writes only wakeup-specific modules and private evidence; it
  does not touch agent/issue or comment/PR/MCP sibling zones.

## WP-03 — Shared-wire response adapters

- `id`: `WP-03`
- `stage`: `2`
- `task_coverage`: `3.1`, `3.2`, `3.3`, `3.4`, `4.1`, `4.2`, `4.3`
- `depends_on`: `WP-01`
- `deliverable`: One coherent focused adapter set implements agent-task pagination,
  issue attachments/timeline, seven comment projections, linked pull requests and
  workspace MCP semantics through the shared wire layer with private evidence and
  no cross-entrypoint leakage.
- `owned responsibility scope`: sole ownership of
  `src/multica_py/_internal/wire_models.py`; agent-task and issue resource/entity
  paths including `src/multica_py/resources/issues.py`; comment, linked-PR and
  workspace-MCP resource/entity/model paths; narrow command-plan/transport support
  required for successful-stderr and timeout behavior; all focused tests, fixtures
  and helpers for tasks 3.1–4.3. It SHALL NOT edit wakeup modules, aggregate
  registries, public inventories or docs.
- `critical shared files`: WP-03 is the only stage-2 writer of
  `src/multica_py/_internal/wire_models.py`, including `_TaskRunWire`, task decoding,
  `_CommentWire`, `comment_from_wire` and linked-PR/MCP wire projections. WP-02 does
  not edit that file. Aggregate seams remain read-only until WP-04.
- `contract surface`: validated task limit/before and exact successful-stderr
  cursor; issue-run non-leakage; ordered attachments, timeout and partial errors;
  open timeline actions; immutable comment supplements; required PR target status;
  workspace-list-only MCP agent count with zero distinct from omission.
- `definition_of_done/evidence`: private tests independently prove cursor/task
  presence, attachment validation/failures, timeline open values, comment dual
  projection, PR future-open states, MCP omission/zero and entrypoint non-leakage;
  the DoD requires no WP-02 symbols or mutable output.
- `parallel_safety`: owns the complete shared-wire response cluster as one writer.
  Its files and focused tests do not overlap WP-02 wakeup-specific modules/tests;
  both consume only read-only WP-01 bindings.

## WP-04 — Shared integration, docs and release gates

- `id`: `WP-04`
- `stage`: `3`
- `task_coverage`: `5.1`, `5.2`, `5.3`
- `depends_on`: `WP-02`, `WP-03`
- `deliverable`: One coherent, documented, package-clean direct upgrade whose
  aggregate inventories and complete offline evidence agree with contract and code.
- `owned responsibility scope`: aggregate/root exports; shared operation, contract,
  provenance and compatibility tables; public inventories; cross-WP fixtures;
  README and API/CLI coverage/compatibility/contributing/migration/service-usage/
  releasing docs; full-gate repairs, package/content audits and final evidence.
- `critical shared files`: exclusively owns every shared export, registry, inventory,
  docs and integration seam after all predecessors complete. Product scope or
  contract changes require planning revision rather than integration-time choice.
- `contract surface`: exact 205/193/196 inventories, 18/178 response verdicts, no
  duplicate baseline surface, direct compatibility/rollback, package contents and
  complete offline/live-status claims.
- `definition_of_done/evidence`: strict OpenSpec; contract validate/render/check;
  source-link audit; focused/compatibility/full non-live suites and collect-only;
  Ruff; mypy source/tests; build and isolated package validation; Git/package
  forbidden-content audit all succeed with commands and exit codes recorded.
- `parallel_safety`: starts only after both stage-2 WPs and is the sole writer
  of shared seams, so no sibling has a hidden dependency or conflicting write zone.

## Coverage proof

Every OpenSpec task is assigned exactly once:

- WP-01: `1.1–1.5`
- WP-02: `2.1–2.4`
- WP-03: `3.1–3.4`, `4.1–4.3`
- WP-04: `5.1–5.3`

Stages are consecutive. Every predecessor has a lower stage. Stage 2 contains two
independent WPs, providing a genuine parallel execution frontier.
