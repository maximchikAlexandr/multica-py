## Delivery topology

This plan compiles every checkbox in `tasks.md` exactly once into six atomic
work packages. `depends_on` lists direct predecessors only. Stages are
topological levels, not WIP limits or live status. Each owned responsibility
scope includes directly related tests, fixtures, snapshots, documentation,
generated support, and maintenance files unless an active sibling owns them.

| Stage | Work packages |
|---:|---|
| 1 | WP-01 |
| 2 | WP-02 |
| 3 | WP-03 |
| 4 | WP-04 |
| 5 | WP-05 |
| 6 | WP-06 |

## WP-01 — Provenance and contract foundation

- `id`: `WP-01`
- `stage`: `1`
- `depends_on`: none
- `task_coverage`: `1.1`, `1.2`, `1.3`, `1.4`
- `deliverable`: A human-reviewed `contracts/sdk-contract.json` pinned to exact
  `0.4.43`, with complete command/response reconciliation, approved additive
  mappings, compatibility interval, and independently verified identities.
- `owned responsibility scope`: Implementation-base proof; ignored
  release/source/binary evidence; command/response reconciliation;
  `contracts/sdk-contract.json`; strictly required contract schema/validator;
  source-link and inventory audit inputs. Critical shared files are
  `contracts/sdk-contract.json`, `contracts/schema/**`,
  `tools/upstream_contract/contract.py`, and ignored review registries. It owns
  no public model/resource implementation.
- `contract surface`: Exact target/release/bounds, operation and response IDs,
  source refs, starter destination/presence/constraints, response schemas,
  canonical vectors, sort/error decisions, retained operations, and non-SDK
  checkout disposition.
- `DoD / evidence`: Base contains approved `0.4.42`; release/tag/archive/
  executable identities resolve independently; command totals are `189/189`
  with three help changes and no topology changes; 163 unique response rows
  split `4/159`; strict pinned-source contract validation exits zero; tracked
  evidence audit is clean.
- `parallel-safety rationale`: Sole foundation writer. Every later package
  consumes its frozen contract; a material contract or dependency correction
  requires planning revision instead of a concurrent sibling edit.

## WP-02 — Agent conversation-starter input

- `id`: `WP-02`
- `stage`: `2`
- `depends_on`: `WP-01`
- `task_coverage`: `2.1`, `2.2`, `2.3`
- `deliverable`: Exact typed create/update starter input with deterministic
  omit/set/clear argv and complete pre-I/O validation coverage.
- `owned responsibility scope`: `src/multica_py/resources/agents.py`; starter
  validation/encoding helpers colocated with that resource; agent mutation
  argv, command, component, and static-type cases. Critical shared case-table
  rows for agent create/update belong here. It excludes issue activity models,
  relation/streaming code, transport classification, contract/generated files,
  global counts, and final docs.
- `contract surface`: Four public signatures, tuple/`Unset`, one JSON flag,
  tuple order, empty-list semantics, item type, count, trim, 80/4000 code-point
  limits, `0.4.43` explicit-use availability, and zero-I/O failures.
- `DoD / evidence`: Signature/type discovery agrees; omission preserves old
  argv; `()` emits exact `[]`; valid JSON is stable; every invalid and boundary
  table row has complete expected argv or zero executor calls; focused mypy and
  tests pass.
- `parallel-safety rationale`: No package runs concurrently at this stage.
  WP-02 may extend shared `tests/cases/operations.py` agent rows, then hands the
  completed fixture state to WP-03 through the direct dependency chain.

## WP-03 — Presence-aware task and usage responses

- `id`: `WP-03`
- `stage`: `3`
- `depends_on`: `WP-02`
- `task_coverage`: `3.1`, `3.2`, `3.3`, `3.4`
- `deliverable`: Immutable legacy/current decoding for cancellation actors,
  tri-state output truncation, timestamps, and exact issue-usage coverage
  counts across eager, command, lazy, and streaming paths.
- `owned responsibility scope`: `src/multica_py/models/issue_activity.py`,
  `entities/issues.py`, private task/run-message wire adapters, semantic
  run-event raw-message handling, task/message relations, and their focused
  decoder/relation/streaming/usage/type fixtures. Critical zones include
  `_internal/wire_models.py`, task-run entity fields, and model-focused test
  modules. It excludes agent mutation request code, central transport/status
  fixtures, approved/generated contract, global registries, and final docs.
- `contract surface`: Actor shape and open type; absence/null/malformed rules;
  truncation unknown/false/true; received timestamp fidelity; exact nonnegative
  counters; legacy count independence; immutable nested input JSON; unchanged 37 relations
  and call counts.
- `DoD / evidence`: Legacy, current, malformed, future actor, exact integer,
  timestamp, streamed raw-message, duplicate-difference, and divergent-count
  frozen rows pass; no value is defaulted or converted through float; owned
  mypy passes.
- `parallel-safety rationale`: WP-03 starts only after WP-02 completes. It may
  extend the repository-standard shared `tests/cases/operations.py` and
  `tests/unit/resources/test_issues.py` fixtures sequentially; no active
  sibling can write either file.

## WP-04 — Retained semantic compatibility

- `id`: `WP-04`
- `stage`: `4`
- `depends_on`: `WP-03`
- `task_coverage`: `4.1`, `4.2`, `4.3`
- `deliverable`: Target-pinned status ordering and 404/500 behavior with exact
  retained-surface and non-SDK negative proof.
- `owned responsibility scope`: Status-sort semantic fixtures; centralized
  transport diagnostic fixtures/classifier changes only if target evidence
  requires them; retained-operation/discovery assertions; fresh-checkout
  negative audit. Critical zones include transport-focused tests,
  `tests/unit/resources/test_issues.py` status cases, and non-SDK inventory
  assertions. It excludes agent request cases, activity models/wires/relations,
  contract/generated output, global count reconciliation, and final docs.
- `contract surface`: Server-side category ordering and direction; unchanged
  sort argv; reviewed 404 not-found versus 500 internal failure; redaction;
  malformed-output separation; all 160 operations retained; absent typed checkout.
- `DoD / evidence`: Canonical/custom/direction and unrelated-sort cases pass;
  404 and 500 map distinctly with safe detail; malformed success output remains
  an `OutputShapeError`; discovery has no fresh-checkout API and no retained
  operation drift.
- `parallel-safety rationale`: WP-04 starts only after WP-03 completes. Its
  status and retained-operation additions to `tests/cases/operations.py` and
  `tests/unit/resources/test_issues.py` therefore follow, rather than overlap,
  WP-02 and WP-03 writes. Final global reconciliation remains in WP-05.

## WP-05 — Generated, documentation, and inventory integration

- `id`: `WP-05`
- `stage`: `5`
- `depends_on`: `WP-04`
- `task_coverage`: `5.1`, `5.2`, `5.3`, `5.4`
- `deliverable`: One integrated generated runtime, exact global inventories,
  direct migration documentation, and package/release metadata consistent with
  all implemented target behavior.
- `owned responsibility scope`: `src/multica_py/_generated/**`; global
  operation/canonical/legacy tables and counts; public exports/registries;
  cross-package integration fixes; `docs/**`, README, examples, changelog;
  packaging, release, compatibility, and source-link assertions. Critical
  shared files include generated runtime, global case inventories,
  `docs/compatibility.md`, `docs/migration.md`, and package audit scripts.
- `contract surface`: Deterministic approved projection; exact public,
  operation, response, relation, and case inventories; `[0.4.42,0.4.44)`;
  `0.4.43` starter availability; additive-model semantics; checksum roles;
  non-SDK disposition; atomic migration/rollback.
- `DoD / evidence`: Two renders match byte-for-byte; validate/render/check and
  source-link audit exit zero; global sets/counts are exact without allowlists;
  docs and package assertions agree; tracked tree contains no transient.
- `parallel-safety rationale`: Sole Stage-5 integrator after the serialized
  domain chain. Shared generated, registry, documentation, count, and
  packaging files therefore have one owner.

## WP-06 — Final verification and delivery evidence

- `id`: `WP-06`
- `stage`: `6`
- `depends_on`: `WP-05`
- `task_coverage`: `6.1`, `6.2`, `6.3`, `6.4`, `6.5`
- `deliverable`: Reproducible acceptance evidence at one clean exact SHA with
  mandatory offline/package gates and separately reported gated-live status.
- `owned responsibility scope`: Full-repository verification, narrowly scoped
  final fixes, evidence summary, final diff/status audit, and delivery SHA. It
  may update directly related tests, fixtures, docs, or support files because
  no sibling remains; product-scope or contract/DAG changes return to planning.
- `contract surface`: Complete OpenSpec acceptance, contract/generated
  equality, package/public API, compatibility, source pins, offline/live
  separation, tracked-artifact policy, and exact delivery identity.
- `DoD / evidence`: Strict OpenSpec/contract/source gates, focused suites,
  Ruff, mypy source/tests/scripts/tools, full non-live pytest/coverage,
  live-node exclusion, build, and package validation exit zero; authorized live
  result or unavailable environment is separate; final diff is scoped and tree
  is clean at the recorded SHA.
- `parallel-safety rationale`: Terminal package with no concurrent sibling;
  broad correction is safe only after WP-05 completes.

## Coverage audit

Work-package task sets are disjoint and their union is exactly `1.1-1.4`,
`2.1-2.3`, `3.1-3.4`, `4.1-4.3`, `5.1-5.4`, and `6.1-6.5`. Every task is
covered once and every dependency listed above is direct.
