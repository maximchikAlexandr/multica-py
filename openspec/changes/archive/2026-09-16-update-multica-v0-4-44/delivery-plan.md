## Delivery topology

This plan compiles every checkbox in `tasks.md` exactly once into five atomic
work packages. `depends_on` lists direct predecessors only. Stages are
topological levels, not WIP limits or live status. Each owned responsibility
scope includes directly related tests, fixtures, snapshots, documentation,
generated support, and maintenance files unless an active sibling owns them.

| Stage | Work packages |
|---:|---|
| 1 | WP-01 |
| 2 | WP-02, WP-03 |
| 3 | WP-04 |
| 4 | WP-05 |

## WP-01 — Provenance and contract foundation

- `id`: `WP-01`
- `stage`: `1`
- `depends_on`: none
- `task_coverage`: `1.1`, `1.2`, `1.3`, `1.4`
- `deliverable`: A human-reviewed `contracts/sdk-contract.json` pinned to exact
  `0.4.44`, with complete command/response reconciliation, approved comment and
  issue decisions, compatibility bounds, and independently verified identities.
- `owned responsibility scope`: Implementation-base proof; ignored baseline
  and target release/source/binary evidence; 189-node and 163-row
  reconciliation; `contracts/sdk-contract.json`; strictly required contract
  schema/validator changes; source-link and inventory audit inputs. Critical
  shared files are `contracts/sdk-contract.json`, `contracts/schema/**`,
  `tools/upstream_contract/contract.py`, and ignored review registries. It owns
  no public comment/issue implementation.
- `contract surface`: Exact target/release/bounds; operation and response IDs;
  source refs; tombstone type/presence; delete availability/error policy;
  lifecycle projection; Triage parent presence; canonical vectors; retained
  operations; non-SDK dispositions.
- `DoD / evidence`: Base contains the approved `0.4.43` contract; identities
  resolve independently; command totals are `189/189` with zero public shape
  changes and one transport adaptation; 163 unique response rows split
  `30/133`; strict pinned-source validation exits zero; tracked evidence audit
  is clean.
- `parallel-safety rationale`: Sole foundation writer. WP-02 and WP-03 consume
  its frozen contract; any material contract or dependency correction requires
  planning revision rather than a concurrent sibling edit.

## WP-02 — Comment tombstones and safe deletion

- `id`: `WP-02`
- `stage`: `2`
- `depends_on`: `WP-01`
- `task_coverage`: `2.1`, `2.2`, `2.3`
- `deliverable`: One presence-correct comment model and one fail-closed
  keep-replies delete path, with complete focused decoding and behavior proof.
- `owned responsibility scope`: `src/multica_py/entities/comments.py`;
  comment-specific parts of `src/multica_py/_internal/wire_models.py`;
  `src/multica_py/resources/issue_comments.py`; comment-focused decoder,
  resource, relation, command, and component fixtures. Critical focused files
  include comment rows in `tests/contract/test_issue_models.py` and directly
  related comment test modules. It excludes issue wire/resource behavior,
  `tests/unit/resources/test_issues.py`, approved/generated contract files,
  global case registries, final docs, and packaging.
- `contract surface`: `deleted_at` public/wire type; omitted/present/null/
  malformed policy; tombstone identity/content/replies; all comment response
  adapters; unchanged Python signature/argv; `0.4.44` delete availability;
  centralized plain-text 404 failure; zero fallback.
- `DoD / evidence`: Live, empty-live, tombstone, descendants, malformed values,
  all list/add/reply paths, target delete, pre-support 404, complete argv, and
  zero-fallback frozen cases pass; focused mypy passes.
- `parallel-safety rationale`: Runs concurrently with WP-03 only after WP-01.
  Its production and focused-test ownership excludes issue projection/update
  files and every global registry owned later by WP-04.

## WP-03 — Issue lifecycle and Triage semantics

- `id`: `WP-03`
- `stage`: `2`
- `depends_on`: `WP-01`
- `task_coverage`: `3.1`, `3.2`, `3.3`
- `deliverable`: Retained legacy lifecycle projection and presence-sensitive,
  atomic Triage parent-update behavior across eager/command and bound/unbound
  paths.
- `owned responsibility scope`: `src/multica_py/_internal/issue_wires.py`;
  issue-specific parts of `src/multica_py/entities/issues.py` and
  `src/multica_py/resources/issues.py`; issue lifecycle/update decoder,
  resource, command, and component fixtures. Critical focused files include
  `tests/unit/resources/test_issues.py` and directly related issue test modules.
  It excludes comment wire/entity/resource code,
  `tests/contract/test_issue_models.py` while WP-02 is active, approved/generated
  contract files, global case registries, final docs, and packaging.
- `contract surface`: Open status strings and existing `IssueStatus`;
  unstarted/started/done/closed legacy categories; built-in status behavior;
  projection/name omission and failures; parent omit/set/clear; Triage
  same/null/foreign 400; standard code/message; atomic no-partial-write proof.
- `DoD / evidence`: Four custom phases, every built-in, omission, malformed
  projection/name, exact argv, Triage omitted/same/null/foreign, ordinary issue
  controls, combined updates, authoritative refetch, and all four SDK forms pass;
  no lifecycle enum is added; focused mypy passes.
- `parallel-safety rationale`: Runs concurrently with WP-02 only after WP-01.
  Its production and focused-test ownership excludes all comment paths and
  shared registries, so sibling write-zones do not overlap.

## WP-04 — Generated, documentation, and inventory integration

- `id`: `WP-04`
- `stage`: `3`
- `depends_on`: `WP-02`, `WP-03`
- `task_coverage`: `4.1`, `4.2`, `4.3`, `4.4`
- `deliverable`: One integrated generated runtime, exact global inventories,
  direct migration documentation, and package metadata consistent with both
  domain packages and the approved contract.
- `owned responsibility scope`: `src/multica_py/_generated/**`; global
  operation/canonical/legacy/response tables and counts, including
  `tests/cases/operations.py` and `tests/component/resources/cases.py`; public
  exports/registries; cross-package integration fixtures; `docs/**`, README,
  examples, changelog; packaging, release, compatibility, and source-link
  assertions. It may reconcile earlier focused files because both predecessors
  are complete.
- `contract surface`: Deterministic approved projection; exact public,
  operation, response, relation, and case inventories; `[0.4.42,0.4.45)`;
  `0.4.44` safe-delete availability; tombstone/lifecycle/Triage semantics;
  checksum roles; non-SDK decisions; atomic migration/rollback.
- `DoD / evidence`: Two renders match byte-for-byte; validate/render/check and
  source-link audit exit zero; global sets/counts are exact without allowlists;
  docs and package assertions agree; tracked tree contains no transient data.
- `parallel-safety rationale`: Sole Stage-3 integrator after both Stage-2
  siblings. Shared generated, registry, documentation, count, and packaging
  files therefore have one owner.

## WP-05 — Final verification and delivery evidence

- `id`: `WP-05`
- `stage`: `4`
- `depends_on`: `WP-04`
- `task_coverage`: `5.1`, `5.2`, `5.3`, `5.4`, `5.5`
- `deliverable`: Reproducible acceptance evidence at one clean exact SHA with
  mandatory offline/package gates and separately reported gated-live status.
- `owned responsibility scope`: Full-repository verification, narrowly scoped
  final fixes, evidence summary, final diff/status audit, and delivery SHA. It
  may update directly related code, tests, fixtures, docs, or support files
  because no sibling remains; product-scope or contract/DAG changes return to
  planning revision.
- `contract surface`: Complete OpenSpec acceptance, contract/generated
  equality, public/package API, compatibility, source pins, offline/live
  separation, no-fallback behavior, tracked-artifact policy, and exact delivery
  identity.
- `DoD / evidence`: Strict OpenSpec/contract/source gates, focused suites,
  Ruff, mypy source/tests/scripts/tools, full non-live pytest/coverage,
  live-node exclusion, build, and package validation exit zero; authorized live
  result or unavailable environment is separate; final diff is scoped and tree
  is clean at the recorded SHA.
- `parallel-safety rationale`: Terminal package with no concurrent sibling;
  broad correction is safe only after WP-04 completes.

## Coverage audit

Work-package task sets are disjoint and their union is exactly `1.1-1.4`,
`2.1-2.3`, `3.1-3.3`, `4.1-4.4`, and `5.1-5.5`. Every task is covered once.
The only parallel frontier is Stage 2 (`WP-02`, `WP-03`); both depend directly
on `WP-01`, `WP-04` depends directly on both, and `WP-05` depends directly on
`WP-04`.
