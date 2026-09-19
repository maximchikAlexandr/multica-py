## Estimate basis

The authoritative weighted estimate and scenario bounds are stored only in the
planning issue custom properties `Estimate, hours`, `Estimate min, hours`, and
`Estimate max, hours`. The estimate covers remaining active developer work for
one experienced developer familiar with the Python stack, without AI
acceleration; unattended waits, approval queues, and unavailable live-target
access are excluded. Confidence is medium and calibration is unavailable.

Evidence includes the complete OpenSpec package, clean base
`bc1c1609963b219ffcb2f9466f33aa3434f570a6`, current contract/generator,
resource and wire-model extension points, table-driven test infrastructure, and
the recently delivered `0.4.44` analogue. Uncertainty is concentrated in
manual 194-node/163-entrypoint reconciliation, presence-sensitive task fields,
the remove-refresh fallback, effective-model validation, and cross-inventory
repair. Tests were not run to manufacture timing evidence.

## Delivery topology

The issue estimate property is above the multi-package threshold. This plan
compiles every checkbox in `tasks.md` exactly once into six atomic work
packages. `depends_on` lists direct predecessors only. Stages are topological
levels, not WIP limits or live status. Each responsibility scope includes
directly related tests, fixtures, snapshots, docs, generated support, and
maintenance files unless an active sibling owns them.

| Stage | Work packages |
|---:|---|
| 1 | WP-01 |
| 2 | WP-02, WP-03, WP-04 |
| 3 | WP-05 |
| 4 | WP-06 |

## WP-01 — Provenance and contract foundation

- `id`: `WP-01`
- `stage`: `1`
- `depends_on`: none
- `task_coverage`: `1.1`, `1.2`, `1.3`, `1.4`, `1.5`
- `deliverable`: A human-reviewed `contracts/sdk-contract.json` pinned to exact
  `0.5.0`, with complete command/response reconciliation, public decisions,
  compatibility bounds, and independently verified identities.
- `owned responsibility scope`: Implementation-base proof; ignored release,
  source, binary, collector, gap, and response evidence; 189-to-194 command and
  163-response reconciliation; `contracts/sdk-contract.json`; strictly needed
  schema/validator changes; source-link and inventory audit inputs. Critical
  shared files are `contracts/sdk-contract.json`, `contracts/schema/**`,
  `tools/upstream_contract/**`, `scripts/audit_source_links.py`, and provenance
  fixtures. It owns no public resource/entity implementation.
- `contract surface`: Exact release/tag/digests/bounds; operation and response
  IDs; source refs; public names/types; presence and constraint policy; exact
  vectors; compatibility gates; retained operations; non-SDK dispositions.
- `DoD / evidence`: Base contains the approved `0.4.44` delivery; identities
  resolve independently; inventory proves 189 baseline, 194 target, five added,
  zero removed/renamed/moved, six changed responses and 157 unchanged; strict
  pinned-source validation exits zero; tracked evidence audit is clean.
- `parallel-safety rationale`: Sole foundation writer. All Stage-2 packages
  consume its frozen contract; material contract or dependency correction
  requires planning revision rather than a concurrent sibling edit.

## WP-02 — Comment update

- `id`: `WP-02`
- `stage`: `2`
- `depends_on`: `WP-01`
- `task_coverage`: `2.1`, `2.2`
- `deliverable`: A text-only, optimistic eager/lazy comment-update API with
  exact revision validation, typed response, and no implicit merge or retry.
- `owned responsibility scope`: `src/multica_py/resources/issue_comments.py`;
  comment-specific generated bindings; comment update operation cases;
  comment-focused decoder/resource/component/transport fixtures. It excludes
  label/skill files, task/agent/runtime implementation, approved contract,
  global registries and counts, final documentation, and packaging.
- `contract surface`: `issues.comments.update`; nonblank ID; body text channel;
  positive non-boolean keyword-only revision; canonical vector positional args
  `(comment_id, body)` plus keyword argument `expected_revision=3`; exact argv;
  Comment response; `0.5.0` gate; stale conflict; unchanged attachments; mention
  retrigger; one-call behavior.
- `DoD / evidence`: Eager/lazy success, exact argv, all invalid revisions,
  canonical keyword binding, target response, stale conflict, attachment
  preservation, retrigger evidence, and zero read/merge/retry cases pass in
  existing table-driven layers.
- `parallel-safety rationale`: Runs with WP-03 and WP-04 after WP-01. Its
  production writes stay inside comment resource paths; centralized error code
  belongs to WP-04 and shared inventories belong later to WP-05.

## WP-03 — Label and skill-label surface

- `id`: `WP-03`
- `stage`: `2`
- `depends_on`: `WP-01`
- `task_coverage`: `2.3`, `2.4`, `3.1`, `3.2`, `3.3`, `3.4`
- `deliverable`: One coherent typed label model supporting issue/skill scope,
  description presence, skill label operations, and one public
  `Skill.labels: LazyCollection[Label]` that is preloaded for list results,
  unloaded for detail results, and invalidated after mutations.
- `owned responsibility scope`: `src/multica_py/entities/labels.py`,
  `entities/skills.py`, `resources/labels.py`, `resources/skills.py`, a new
  skill-label resource module, relevant enums/wires, and label/skill-specific
  unit/contract/component/relation fixtures. It excludes comment paths,
  task/agent/runtime paths, approved/generated contract files, global case
  registries and counts, final docs, and packaging.
- `contract surface`: Label resource type and description; create/list/update
  mapping and clear presence; `skills.labels.list/add/remove`; resolver fence;
  remove-refresh fallback; one `Skill.labels: LazyCollection[Label]` contract;
  list-payload preload without transport; detail lazy loading; invalidation;
  strict nested decoding.
- `DoD / evidence`: Issue/skill, omit/set/clear, empty/populated/malformed,
  exact argv, resolver mismatch, add/list/remove success, detach-refresh
  fallback, list-preload zero-call behavior, detail one-load behavior, cache
  reuse/invalidation, stable public type, and unbound failures pass; skill
  detail wire contract remains unchanged.
- `parallel-safety rationale`: Sole owner of the shared Label model and all
  skill-label code. Its write zone does not overlap WP-02 or WP-04; shared
  exports and inventory integration wait for WP-05.

## WP-04 — Task, agent, runtime, and error adaptations

- `id`: `WP-04`
- `stage`: `2`
- `depends_on`: `WP-01`
- `task_coverage`: `4.1`, `4.2`, `4.3`, `4.4`, `4.5`
- `deliverable`: Presence-correct task deltas, fail-fast OMP validation, and
  safe structured runtime-delete conflicts through the centralized boundary.
- `owned responsibility scope`: Task/agent wire and public models;
  `resources/agents.py`, `resources/runtimes.py`; centralized reviewed
  error/transport fields; task/agent/runtime-specific unit, contract, component,
  and error fixtures. It excludes comment and label/skill production paths,
  approved/generated contract files, global registries/counts, final docs, and
  packaging.
- `contract surface`: Task issue-state presence; open failure reasons;
  create/update effective-model validation across runtime changes; exact argv;
  no partial mutation; empty delete success; optional structured blockers;
  legacy/plain conflict; no cascade/retry.
- `DoD / evidence`: Absent versus known-empty delta, changed fields, malformed
  shapes, `runtime_access_denied`, future reasons, complete OMP combinations,
  runtime swap/clear, no transport on invalid input, structured/plain/malformed
  conflicts, and no cascade/retry pass in table-driven tests.
- `parallel-safety rationale`: Runs with WP-02 and WP-03 after WP-01. It is the
  sole Stage-2 owner of shared exception/transport changes; WP-02 consumes the
  existing conflict boundary and does not edit it.

## WP-05 — Generated, inventory, documentation, and package integration

- `id`: `WP-05`
- `stage`: `3`
- `depends_on`: `WP-02`, `WP-03`, `WP-04`
- `task_coverage`: `5.1`, `5.2`, `5.3`, `5.4`
- `deliverable`: One integrated generated runtime, exact global inventories,
  direct migration documentation, and package metadata consistent with all
  domain implementations and the frozen contract.
- `owned responsibility scope`: `src/multica_py/_generated/**`; public exports;
  global operation/canonical/variant/legacy/response/relation tables and counts,
  including `tests/cases/**` and `tests/component/resources/cases.py`; cross-
  domain integration fixtures; `docs/**`, README, examples, changelog;
  compatibility, packaging, release, and source-link assertions. It may
  reconcile predecessor-focused files because all siblings are complete.
- `contract surface`: Deterministic approved projection; exact public,
  operation, response, relation, and case inventories; `[0.4.42,0.5.1)` and
  operation gates; every new/presence/error decision; direct migration;
  checksum roles; non-SDK exclusions; atomic rollback.
- `DoD / evidence`: Two renders match byte-for-byte; validate/render/check and
  source-link audit exit zero; global sets and counts are exact without
  allowlists; docs and package assertions agree; tracked tree contains no
  transient evidence.
- `parallel-safety rationale`: Sole Stage-3 integrator after all domain
  siblings. Shared generated, registry, export, documentation, count, and
  packaging files therefore have one owner.

## WP-06 — Final verification and delivery evidence

- `id`: `WP-06`
- `stage`: `4`
- `depends_on`: `WP-05`
- `task_coverage`: `6.1`, `6.2`, `6.3`, `6.4`, `6.5`
- `deliverable`: Reproducible acceptance evidence at one clean exact SHA with
  mandatory offline/package gates and separately reported gated-live status.
- `owned responsibility scope`: Full-repository verification, narrowly scoped
  final fixes, evidence summary, final diff/status audit, and delivery SHA. It
  may update directly related code, tests, fixtures, docs, or support files
  because no sibling remains; product-scope or contract/topology changes return
  to planning revision.
- `contract surface`: Complete OpenSpec acceptance; contract/generated
  equality; public/package API; compatibility; source pins; offline/live
  separation; presence and no-retry guarantees; tracked-artifact policy; exact
  delivery identity.
- `DoD / evidence`: Strict OpenSpec/contract/source gates, focused suites,
  Ruff, mypy source/tests/scripts/tools, full non-live pytest/coverage,
  live-node exclusion, build, and package validation exit zero; authorized live
  result or unavailable environment is separate; final diff is scoped and tree
  is clean at the recorded SHA.
- `parallel-safety rationale`: Terminal package with no concurrent sibling;
  broad correction is safe only after WP-05 completes.

## Coverage and frontier audit

Work-package task sets are disjoint and their union is exactly `1.1-1.5`,
`2.1-2.4`, `3.1-3.4`, `4.1-4.5`, `5.1-5.4`, and `6.1-6.5`. Every task is
covered once. The parallel frontier is Stage 2 (`WP-02`, `WP-03`, `WP-04`);
all three depend directly on `WP-01`, own non-conflicting production domains,
and defer shared registries/exports/docs to `WP-05`. `WP-05` depends directly
on all three siblings, and `WP-06` depends directly on `WP-05`.
