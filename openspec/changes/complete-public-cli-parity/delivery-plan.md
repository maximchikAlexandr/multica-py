## Delivery contract

- `delivery_mode`: `dag`
- Planning issue: `MYL-303`
- OpenSpec change: `complete-public-cli-parity`
- Approved base: `d1b5f0e154c5587eca4cebd8bd2a6d39ae3d4d06`
- Estimate authority: planning-issue properties `Estimate, hours`,
  `Estimate min, hours`, and `Estimate max, hours`. The estimate covers
  remaining work for one experienced developer familiar with Python SDK and
  CLI contract tooling, without AI acceleration. Confidence is medium and the
  estimate is uncalibrated because no comparable measured execution history is
  available. Material uncertainty comes from the unresolved absolute
  CLI-to-SDK inventory, interactive transport behavior, response-variant
  breadth, and strict cross-inventory closure. Tests were not run for the
  estimate.
- Numeric totals are intentionally stored only in the authoritative issue
  properties. The `Estimate, hours` property exceeds the multi-WP threshold.
- Topology rule: stages are topological layers, not WIP limits. Stage 2 first
  corrects A1–A10 in two disjoint fronts; stage 3 is the mandatory task `3.8`
  regression gate. No new-family task may begin before WP-04 completes. Stage 4
  is the next parallel frontier, whose siblings have disjoint production and
  family-test write zones. Shared registries, exports, client wiring, broad
  operation tables, documentation, and packaging integration are reserved for
  WP-07.
- Scope rule: each WP owns the stated responsibility rather than an exhaustive
  file allowlist. Directly related tests, fixtures, snapshots, and local docs
  are included unless assigned to an active sibling below.

### Stage map

| WP | Stage | Direct `depends_on` |
|---|---:|---|
| WP-01 | 1 | none |
| WP-02 | 2 | WP-01 |
| WP-03 | 2 | WP-01 |
| WP-04 | 3 | WP-02, WP-03 |
| WP-05 | 4 | WP-04 |
| WP-06 | 4 | WP-04 |
| WP-07 | 5 | WP-05, WP-06 |
| WP-08 | 6 | WP-07 |

## WP-01 — Closed inventory, approved contract, and shared primitives

- `stage`: 1
- `depends_on`: none
- OpenSpec task coverage: `1.1`–`1.8`, `2.1`–`2.8`, `4.1`–`4.4`.
- Deliverable: a complete source/help-reconciled public CLI inventory with no
  relevant unresolved pattern; a strict approved-contract schema and reviewed
  target contract that closes every inventory row; deterministic generated
  bindings; and the shared safe-content, daemon-options, terminal-process, and
  wire-presence primitives needed by later resource work.
- Owned responsibility scope: `contracts/sdk-contract.json`;
  `tools/upstream_contract/`; `scripts/upstream_contract.py`; generated approved
  SDK projection; contract/inventory tests and source-linked evidence schemas;
  shared command, executor, base-resource, redaction, staging, sentinel, and
  common-model primitives. Downloaded binaries, upstream checkouts, collector
  output, and transient renders remain outside Git.
- Critical shared files: this WP exclusively owns approved-contract schema/data,
  generated binding output, `resources/_base.py`, `_internal/commands.py`,
  executor/transport extensions, shared safe-content types, and their focused
  tests until completion. Later WPs consume these contracts without editing
  them except through the integration owner WP-07.
- Contract surface: stable inventory IDs and dispositions; operation/input/
  response/field catalogs; dynamic factory and alias reconciliation; safe
  content protocol; daemon launch options; terminal-capable command mode;
  generated binding APIs.
- Definition of done/evidence: pinned source and recursive binary help agree;
  every public row has one allowed evidence-backed disposition; no relevant
  extractor review item is unresolved; strict contract tests reject omissions,
  stale deferrals, duplicates, and direct evidence promotion; two renders are
  byte-identical; focused type/style tests for shared primitives pass.
- Parallel-safety rationale: predecessor by design. It freezes every shared
  contract and primitive before correction work begins, preventing successors
  from racing on schema, generation, transport, or content semantics.

## WP-02 — System and organization A1–A10 corrections

- `stage`: 2
- `depends_on`: WP-01
- OpenSpec task coverage: `3.1`, `3.2`, `3.3`, `3.6`, `3.7`.
- Deliverable: truthful daemon/auth transports and variants, corrected
  attachment upload/download/path/bytes behavior, every CLI-supported
  project-resource variant, and corrected squad membership argv and results.
- Owned responsibility scope: daemon, auth, attachment, project-resource, and
  squad-member resource/model modules; their native response, exact-argv,
  process, cleanup, and family-local regression fixtures and tests.
- Critical shared files excluded: no edits to approved contract/generator,
  shared command/base primitives, client construction, package exports, global
  operation tables, broad fake-CLI registries, docs, or packaging manifests.
  WP-03 exclusively owns issue/comment corrections while this WP is active.
- Contract surface: actual daemon status/disk variants and absence semantics;
  lifecycle/text auth and daemon behavior; attachment metadata and cleanup;
  project-resource reference variants; squad member identity, role, and result
  mappings.
- Definition of done/evidence: source-linked native regressions for A1–A5 and
  A8–A10 pass through the public family methods; unsupported output flags are
  absent; exact positional/flag mappings, cleanup, redaction, Ruff, and mypy
  checks pass in the owned scope.
- Parallel-safety rationale: writes only system and organization correction
  modules plus local tests. It does not touch WP-03's issue/comment modules or
  the shared test and integration zones reserved for WP-04/WP-07.

## WP-03 — Comment and pagination A1–A10 corrections

- `stage`: 2
- `depends_on`: WP-01
- OpenSpec task coverage: `3.4`, `3.5`.
- Deliverable: recent comments decode as truthful flat root/reply records with
  identity and content intact, and exact root/reply cursor stderr parsing
  preserves pagination, folding, and compact controls.
- Owned responsibility scope: issue-comment resource, wire/public model, cursor
  parser, and family-local native payload/stderr fixtures and regression tests.
- Critical shared files excluded: no edits to WP-01 foundation files, WP-02
  system/organization modules, client/export wiring, global operation tables,
  broad component registries, docs, or package metadata.
- Contract surface: flat comment records, root/reply identity, content,
  cursor/pagination signals, folding, and compact behavior.
- Definition of done/evidence: A6–A7 native payload and stderr fixtures pass
  through public methods; grouping occurs only where wire evidence requires it;
  malformed cursor/data cases fail without silent defaults; focused Ruff and
  mypy checks pass.
- Parallel-safety rationale: owns only issue-comment corrections and local
  tests, disjoint from WP-02's system/organization correction zone.

## WP-04 — Mandatory A1–A10 regression gate

- `stage`: 3
- `depends_on`: WP-02, WP-03
- OpenSpec task coverage: `3.8`.
- Deliverable: one reviewable gate proving every A1–A10 correction together
  before any new resource family or family expansion starts.
- Owned responsibility scope: focused cross-correction public-operation unit,
  component, decoder, exact-argv, and type-check orchestration and evidence.
  Repairs remain within the completed correction owners' scopes and are
  serialized here; no new-family code is permitted.
- Critical shared files: this WP may assemble only the focused A1–A10 test
  selection and evidence. It does not add client wiring, package exports,
  general operation cases, broad docs, or new-family fixtures reserved for
  later WPs.
- Contract surface: the combined corrected public behavior for A1–A10 and the
  explicit pass/fail boundary that unlocks new-family work.
- Definition of done/evidence: all focused public unit/component/decoder/argv
  regressions and relevant mypy checks for A1–A10 pass from a clean tree; the
  evidence identifies the tested SHA; no task from sections 5–7 has started.
- Parallel-safety rationale: barrier by design. It joins both stage-2 correction
  fronts and must complete before the stage-4 frontier can open.

## WP-05 — System and organization family completion

- `stage`: 4
- `depends_on`: WP-04
- OpenSpec task coverage: `5.1`–`5.4`, `5.9`, `6.1`, `6.4`, `6.7`, `6.8`,
  `7.1`–`7.4`, `7.6`.
- Deliverable: native repository checkout and runtime-profile operations;
  agent env/skill, workspace, and squad mutations; complete system,
  organization, daemon, auth, project, runtime, and agent inputs and response
  projections.
- Owned responsibility scope: daemon, auth, attachment, repository, runtime,
  runtime-profile, maintenance/update, login/setup, agent and nested env/skills,
  workspace/member, squad/member, project/project-resource, system/version
  resource and model modules; their family-local tests and fixtures. Property,
  autopilot, issue, comment, chat, wakeup, skill-file, and user-profile modules
  belong to WP-06 while both are active.
- Critical shared files excluded: no edits to approved contract/generator,
  shared primitives, client/package exports, global operation tables, broad
  component registries, documentation, or packaging manifests; WP-07 owns
  those integrations.
- Contract surface: checkout and runtime-profile results; secret-safe agent env;
  workspace/squad/project inputs; daemon launch controls; human-local auth;
  complete daemon/runtime/agent/organization records and presence semantics.
- Definition of done/evidence: assigned B/C/D mappings have source-linked
  canonical, presence, redaction, process, cleanup, and negative cases; raw
  secrets never appear in ordinary models; family-local tests, Ruff, and mypy
  pass without changing WP-06's zone.
- Parallel-safety rationale: after the A1–A10 gate, this WP owns only
  system/organization families and local tests, disjoint from WP-06's
  issue/content/automation families.

## WP-06 — Issue, content, and automation family completion

- `stage`: 4
- `depends_on`: WP-04
- OpenSpec task coverage: `5.5`–`5.8`, `6.2`, `6.3`, `6.5`, `6.6`, `7.5`,
  `7.7`, `7.8`.
- Deliverable: issue timeline; complete chat and wakeup families; trigger URL
  rotation; issue/comment/autopilot/skill/user inputs; and complete trigger,
  property, comment, acknowledgement, and remaining nested projections.
- Owned responsibility scope: issue and nested comment/timeline/wakeup modules;
  chat; autopilot and trigger; property; skill and skill-file; user-profile
  content resources/models; their family-local tests and fixtures.
- Critical shared files excluded: no edits to WP-01 shared foundations,
  WP-05 system/organization modules, client/package exports, global operation
  tables, broad component registries, documentation, or package metadata.
- Contract surface: timeline and chat envelopes; wakeup replacement, re-enable,
  retry, and loop rules; trigger secret opt-in; safe content channels; comment
  supplements, properties, acknowledgements, and nested-field completeness.
- Definition of done/evidence: assigned B/C/D items have canonical, presence,
  redaction, pagination, failure, and native-shape cases; no raw argv replaces a
  typed public family; family-local tests, Ruff, and mypy pass without changing
  WP-05's zone.
- Parallel-safety rationale: after the A1–A10 gate, this WP owns only
  issue/content/automation families and local tests, disjoint from WP-05's
  system/organization families.

## WP-07 — Cross-family integration, canonical proof chain, and migration docs

- `stage`: 5
- `depends_on`: WP-05, WP-06
- OpenSpec task coverage: `6.9`, `8.1`–`8.5`.
- Deliverable: all family work wired into one public client/package, every
  global/inherited input reconciled, one closed canonical operation/response/
  export/package proof chain, broad component coverage, and complete user-facing
  coverage and migration documentation.
- Owned responsibility scope: `client.py`, package/model/resource export files,
  shared public discovery and `tests/cases/operations.py`, broad component
  fake-CLI registries, bound-surface/inventory/package tests, README/API/
  CLI-coverage/compatibility/service/migration/changelog/examples, and any
  integration-only fixture or snapshot.
- Critical shared files: exclusive owner of all cross-family registries,
  canonical case tables, client wiring, top-level exports, broad docs, and
  package manifests. Family modules remain owned by their completed predecessor;
  integration fixes in those modules are coordinated sequentially in this WP.
- Contract surface: `MulticaClient` resource access, public `__all__`, bound
  relations, operation-case bijection, transport method registry, documented
  coverage dimensions, compatibility and migration claims.
- Definition of done/evidence: public discovery equals approved typed inventory;
  every CLI-executing method has one canonical exact argv/transport/result row;
  all global/inherited flags have typed equivalent or presentation disposition;
  broad fake-CLI paths pass; docs and package exports match signatures; no
  unknown allowlist exists.
- Parallel-safety rationale: starts only after both stage-4 siblings finish, so
  it can update shared registries once without merge races or duplicate client/
  export wiring.

## WP-08 — Exact-SHA release verification and evidence handoff

- `stage`: 6
- `depends_on`: WP-07
- OpenSpec task coverage: `8.6`–`8.8`.
- Deliverable: one clean exact implementation SHA with all mandatory offline,
  contract, deterministic-generation, source-link, type, style, test, coverage,
  build, packaging, dependency, and tracked-content gates passing; optional
  prepared-live status reported separately.
- Owned responsibility scope: final verification evidence and only directly
  necessary repair changes discovered by those gates, including related tests,
  fixtures, generated freshness, docs, and package metadata. It does not expand
  product scope or choose a new disposition.
- Contract surface: final approved contract/runtime byte consistency, package
  contents, compatibility metadata, release commands, and delivery SHA.
- Definition of done/evidence: strict OpenSpec and pinned-source contract
  validation pass; deterministic renders match; Ruff, mypy, full non-live
  pytest/coverage, live-node exclusion, build, wheel/sdist tests, dependency and
  content audits pass; Git is clean; no evidence binary/source checkout/report,
  secret, or visual HTML is tracked or packaged; optional live result is clearly
  separated.
- Parallel-safety rationale: terminal integration gate. It follows WP-07 and
  serializes any final repair against the complete tree; no sibling writes exist.

## Coverage audit

Every task in `tasks.md` is assigned exactly once:

- WP-01: `1.1`–`1.8`, `2.1`–`2.8`, `4.1`–`4.4`.
- WP-02: `3.1`, `3.2`, `3.3`, `3.6`, `3.7`.
- WP-03: `3.4`, `3.5`.
- WP-04: `3.8`.
- WP-05: `5.1`–`5.4`, `5.9`, `6.1`, `6.4`, `6.7`, `6.8`, `7.1`–`7.4`,
  `7.6`.
- WP-06: `5.5`–`5.8`, `6.2`, `6.3`, `6.5`, `6.6`, `7.5`, `7.7`, `7.8`.
- WP-07: `6.9`, `8.1`–`8.5`.
- WP-08: `8.6`–`8.8`.

Stage 2 (`WP-02`, `WP-03`) is the correction frontier. Stage 3 (`WP-04`)
joins it and proves A1–A10 before any section-5 task begins. Stage 4 (`WP-05`,
`WP-06`) is the new-family frontier. Both frontiers have disjoint production
write zones and family-local tests; critical shared integration files are
isolated in predecessor WP-01 or successor WP-07.
