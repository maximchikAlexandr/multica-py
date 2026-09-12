## Delivery topology

This plan compiles every task in `tasks.md` exactly once into seven work
packages. `depends_on` contains direct predecessors only. Stage numbers are
topological levels, not WIP limits or live status. Each responsibility scope
includes directly related tests, fixtures, snapshots, documentation, generated
support files, and maintenance files unless an active sibling owns them.

| Stage | Work packages |
|---:|---|
| 1 | WP-01 |
| 2 | WP-02, WP-03, WP-04, WP-05 |
| 3 | WP-06 |
| 4 | WP-07 |

## WP-01 — Exact provenance and contract foundation

- `id`: `WP-01`
- `stage`: `1`
- `depends_on`: none
- `task_coverage`: `1.1`, `1.2`, `1.3`, `1.4`, `1.5`
- `deliverable`: A human-reviewed `contracts/sdk-contract.json` that pins
  `0.4.42`, encodes every approved/deferred/removed disposition, separates
  archive from executable identities, and passes strict validation against the
  exact target source.
- `owned responsibility scope`: Upstream/release verification inputs and
  ignored evidence workflow; `contracts/sdk-contract.json`; contract schema and
  validator changes strictly required by the reviewed metadata; source-link and
  inventory audit inputs. Critical shared files owned here are
  `contracts/sdk-contract.json`, `contracts/schema/**`,
  `tools/upstream_contract/contract.py`, and the ignored reconciliation
  registries. No production SDK resource/model implementation belongs here.
- `contract surface`: Target/release/compatibility metadata, operation and
  response IDs, source refs, mappings, five-state presence, constraints,
  adapters, canonical vectors, removals, and deferrals consumed by every later
  package.
- `DoD / evidence`: Old/target source SHAs and release IDs resolve; archive and
  binary digests independently match; Cobra totals equal 199/189 and union
  classification 166/21/2/12; response registry has 173 unique entries with
  51/122 split and no missing target URL; strict contract validation exits 0;
  tracked-file audit contains no evidence/transient output.
- `parallel-safety rationale`: This is the sole foundation writer and has no
  sibling. Stage-2 packages consume its frozen contract and MUST route any
  material contract correction through a planning revision rather than editing
  this shared surface concurrently.

## WP-02 — Core response models and adapters

- `id`: `WP-02`
- `stage`: `2`
- `depends_on`: `WP-01`
- `task_coverage`: `2.1`, `2.2`, `2.3`, `2.4`, `2.5`
- `deliverable`: Presence-correct immutable Issue, Comment, Agent, and TaskRun
  decoding for target and supported legacy payloads.
- `owned responsibility scope`: Core domain/entity and private-wire modules for
  issues, comments, agents, and task runs; their decoder adapters; focused model
  and envelope fixtures/tests. Critical write zones include
  `src/multica_py/entities/issues.py`, `entities/comments.py`,
  `entities/agents.py`, corresponding private wire/decoder modules, and
  model-focused test resources. It does not edit resource argv builders,
  Plugin/autopilot modules, central transport classification, global exports,
  generated contract files, or docs.
- `contract surface`: Public field names/types, nested conversation starters,
  missing/null/value normalization, timestamp and integer precision, immutable
  arbitrary JSON, and removed TaskRun projections.
- `DoD / evidence`: Legacy/compact/current/malformed frozen case tables pass;
  no silent defaults, float conversion, mutable JSON, obsolete TaskRun fields,
  or extra transport calls remain; mypy passes for the owned modules/tests.
- `parallel-safety rationale`: Its writes are confined to response
  model/wire/decoder zones. WP-03 owns request resources, WP-04 owns
  Plugin/autopilot/global-removal zones, and WP-05 owns transport/errors, so
  Stage-2 siblings have no critical shared-file writes.

## WP-03 — Skill and issue query compatibility

- `id`: `WP-03`
- `stage`: `2`
- `depends_on`: `WP-01`
- `task_coverage`: `3.1`, `3.2`, `3.3`, `3.4`, `3.5`, `3.6`
- `deliverable`: Backward-compatible default skill/issue behavior plus explicit
  target content, projection, property query, sort, and bounded pagination
  options.
- `owned responsibility scope`: Skill and issue resource argv builders,
  property-filter/projection validation, skill-file relation behavior, issue
  list/search page adapters, and their table-driven argv/command/relation/
  component/type fixtures. Critical zones include
  `src/multica_py/resources/skills.py`, `resources/issues.py`,
  `entities/skills.py`, issue pagination helpers, and directly corresponding
  test resources. It does not edit core Issue/TaskRun field declarations,
  Plugin/autopilot/global exports, transport classifier, approved contract, or
  final docs/count constants.
- `contract surface`: `--with-content`, `--resolve-properties`, `--fields`,
  repeatable `--property`, property sort, limit `1..100`, OR/AND/`__none__`,
  reserved operators, partial-row decoding, truthful `has_more`, and bounded
  failure behavior. Deferred timeline/trigger/active-sibling methods remain
  absent.
- `DoD / evidence`: Complete valid/default/invalid expected-argv rows pass;
  construction is zero-I/O; omission/content projections remain distinct;
  pagination terminates on false `has_more` and fails on malformed/repeated/
  no-progress pages; existing default API results remain unchanged.
- `parallel-safety rationale`: The package owns skill/issue request and paging
  files only; response field adapters, removals/global exports, and centralized
  transport files are owned by other Stage-2 siblings.

## WP-04 — Plugin and autopilot breaking removals

- `id`: `WP-04`
- `stage`: `2`
- `depends_on`: `WP-01`
- `task_coverage`: `4.1`, `4.2`, `4.3`, `4.4`, `4.5`
- `deliverable`: A target-compatible public surface with the complete Plugin
  API and autopilot priority inputs removed, and a 37-relation inventory with
  stable surviving IDs.
- `owned responsibility scope`: Plugin resource/model files and deletion;
  autopilot create/update resources; Workspace plugin relation state;
  `MulticaClient` resource registration; package/resource/model exports;
  public discovery and removal/type fixtures. Critical shared files exclusively
  owned in Stage 2 are `src/multica_py/client.py`, package `__init__.py` files,
  registry files, `entities/workspaces.py`, `resources/autopilots.py`, and
  Plugin modules. Generated output and final global counts belong to WP-06.
- `contract surface`: Removed `plugins.*` operations and symbols, removed
  autopilot `priority` parameters/flags, unchanged remaining autopilot
  presence, `Workspace.plugins` absence, and stable R35-R38 identifiers.
- `DoD / evidence`: Import/signature/discovery/argv negative tests prove no
  Plugin or priority shim remains; remaining autopilot cases pass; relation
  discovery equals 37 with no allowlist; no unsupported replacement is added.
- `parallel-safety rationale`: This package alone owns global public
  registration/export files during Stage 2. Other siblings must defer any
  necessary export reconciliation to WP-06, preventing concurrent writes.

## WP-05 — Target error and presence matrix

- `id`: `WP-05`
- `stage`: `2`
- `depends_on`: `WP-01`
- `task_coverage`: `5.1`, `5.2`, `5.3`, `5.4`
- `deliverable`: One redaction-safe transport-boundary classifier and complete
  five-state/exclusive-channel negative matrix aligned to `0.4.42`.
- `owned responsibility scope`: Central transport error classification,
  diagnostic/redaction and secret collection, shared validation helpers needed
  for presence/channel constraints, and focused transport/process/error tests.
  Critical zones include `src/multica_py/transport.py`, `exceptions.py`,
  command-plan redaction helpers, and corresponding transport/component test
  files. It does not edit domain resources/models, global exports, the approved
  contract, or docs.
- `contract surface`: Semantic exception taxonomy, raw exit/payload retention,
  actionable redacted detail, generic unknown fallback, executable/malformed/
  timeout/process boundaries, omission/null/empty/zero/false, and exclusive
  inline/file/stdin/config channels.
- `DoD / evidence`: Table-driven target diagnostic fixtures map exactly;
  unknown cases remain generic; all preview/repr/exception streams are secret
  safe; valid actual subprocess argv remains unchanged; invalid combinations
  perform zero executor calls.
- `parallel-safety rationale`: Central transport/error files are isolated from
  the response, request, and removal write zones assigned to its Stage-2
  siblings.

## WP-06 — Generated, documentation, and inventory integration

- `id`: `WP-06`
- `stage`: `3`
- `depends_on`: `WP-02`, `WP-03`, `WP-04`, `WP-05`
- `task_coverage`: `6.1`, `6.2`, `6.3`, `6.4`, `6.5`, `6.6`
- `deliverable`: One integrated contract-generated runtime, exact global
  inventories, direct migration documentation, and packaging/release metadata
  consistent with the completed production surface.
- `owned responsibility scope`: Generated runtime files; global canonical and
  legacy count constants; cross-resource registries not finalized in Stage 2;
  API/compatibility/migration/contributor/release docs, README/examples/
  changelog; packaging/release and source-link audit assertions. It owns resolution of
  cross-package integration conflicts after all predecessors complete. Critical
  files include `src/multica_py/_generated/**`, global operation tables/counts,
  `docs/**`, `README.md`, `CHANGELOG.md`, packaging tests, and audit scripts.
- `contract surface`: Deterministic projection from approved contract, exact
  public/canonical/relation inventories, `[0.4.42,0.4.43)`, migration/removal/
  deferral policy, checksum roles, and package exports as observed after WP-04.
- `DoD / evidence`: Two renders match byte-for-byte; validate/render/check and
  source-link audit exit 0; every global set/count is exact with no allowlist;
  docs contain correct executable collector digest and direct migration;
  package tests agree with removed files/exports; tracked-tree audit is clean.
- `parallel-safety rationale`: This is the sole Stage-3 integrator and starts
  only after every Stage-2 writer completes, so shared generated, registry,
  documentation, and count files have one owner.

## WP-07 — Final verification and delivery evidence

- `id`: `WP-07`
- `stage`: `4`
- `depends_on`: `WP-06`
- `task_coverage`: `7.1`, `7.2`, `7.3`, `7.4`, `7.5`
- `deliverable`: Reproducible acceptance evidence at one clean exact SHA,
  including all mandatory offline/package gates and separately reported gated
  live status.
- `owned responsibility scope`: Full-repository verification, narrowly scoped
  final fixes, proof logs/summary, and clean-tree/diff audit after integration.
  It owns any directly related final fix because no sibling remains active, but
  a product-scope or contract-dependency change requires a planning revision.
- `contract surface`: The complete OpenSpec acceptance surface, approved
  contract and generated-runtime equality, package/public API, source pins,
  offline/live separation, and exact delivery SHA.
- `DoD / evidence`: Strict OpenSpec and contract gates, focused tests, Ruff,
  format, mypy source/tests/scripts, full non-live pytest/coverage, live-node
  exclusion, build, and package validation exit 0; authorized live-negative
  result is recorded or its missing environment is stated separately; final
  diff contains no deferred API or transient artifact; worktree is clean at the
  recorded SHA.
- `parallel-safety rationale`: It is the terminal package with no concurrent
  sibling. Its broad corrective scope is safe only after WP-06 completes and
  does not encode WIP or assignee state in the DAG.

## Coverage audit

The work-package task sets are disjoint and their union is exactly:
`1.1-1.5`, `2.1-2.5`, `3.1-3.6`, `4.1-4.5`, `5.1-5.4`, `6.1-6.6`, and
`7.1-7.5`. No task is omitted or assigned to more than one package.
