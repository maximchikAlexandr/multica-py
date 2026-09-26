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
- Topology rule: stages are topological layers, not WIP limits. Stage 2 is the
  parallel frontier; its siblings have disjoint production and family-test
  write zones. Shared registries, exports, client wiring, broad operation
  tables, documentation, and packaging integration are reserved for WP-05.
- Scope rule: each WP owns the stated responsibility rather than an exhaustive
  file allowlist. Directly related tests, fixtures, snapshots, and local docs
  are included unless assigned to an active sibling below.

### Stage map

| WP | Stage | Direct `depends_on` |
|---|---:|---|
| WP-01 | 1 | none |
| WP-02 | 2 | WP-01 |
| WP-03 | 2 | WP-01 |
| WP-04 | 2 | WP-01 |
| WP-05 | 3 | WP-02, WP-03, WP-04 |
| WP-06 | 4 | WP-05 |

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
  tests until completion. Stage-2 WPs consume these contracts without editing
  them.
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
  contract and primitive before family implementations begin, preventing
  siblings from racing on schema, generation, transport, or content semantics.

## WP-02 — System, local-process, attachment, repository, and runtime parity

- `stage`: 2
- `depends_on`: WP-01
- OpenSpec task coverage: `3.1`, `3.2`, `3.6`, `5.1`, `5.9`, `6.7`, `6.8`,
  `7.1`, `7.2`.
- Deliverable: truthful daemon/auth transports and variants, corrected
  attachment upload/download/path/bytes behavior, native repository checkout,
  complete runtime-profile operations, complete daemon/update/login controls,
  and expanded daemon/runtime models.
- Owned responsibility scope: daemon, auth, attachment, repository, runtime,
  runtime-profile, maintenance/update, login, setup, and system/version resource
  and model modules; family-local unit/decoder/process fixtures and tests.
- Critical shared files excluded: no edits to the approved contract/generator,
  common command/base primitives, client construction, package `__init__`
  exports, global `tests/cases/operations.py`, broad component fake-CLI
  registries, docs, or packaging manifests; WP-05 owns those integrations.
- Contract surface: exact JSON/text/path/bytes/spawn/terminal modes; daemon
  status and disk-report variants; attachment result metadata; checkout result;
  runtime-profile models; daemon launch options; version aliases; human-local
  auth safeguards.
- Definition of done/evidence: source-linked native A1–A4/A8–A9 fixtures pass
  through public family methods; unsupported output flags are absent; exact
  checkout and runtime-profile argv/presence cases pass; secrets are redacted;
  cleanup/cancellation are proven; family tests, Ruff, and mypy pass.
- Parallel-safety rationale: writes only system/local-process family modules and
  family-local tests after WP-01 freezes shared primitives. It does not touch
  organization or issue/content family zones owned by WP-03/WP-04.

## WP-03 — Agent, workspace, squad, project, and property parity

- `stage`: 2
- `depends_on`: WP-01
- OpenSpec task coverage: `3.3`, `3.7`, `5.2`–`5.4`, `6.1`, `6.4`, `7.3`,
  `7.4`, `7.6`.
- Deliverable: all CLI-supported project-resource variants, corrected squad
  membership argv, agent env and additive skills, workspace and squad mutation
  families, complete agent/project inputs, and full agent/workspace/squad/
  project/project-resource records.
- Owned responsibility scope: agent and nested agent env/skills modules;
  workspace and workspace-member modules; squad and squad-member modules;
  project, project-resource, and property modules; corresponding entity/wire/
  public models and family-local tests/fixtures.
- Critical shared files excluded: the same WP-01 and WP-05 shared files listed
  above. Autopilot trigger/property-display integration assigned to WP-04 is
  not edited here unless a pre-agreed family-neutral model landed in WP-01.
- Contract surface: secret-safe agent env access; atomic skill add; workspace
  create/update/invite; squad CRUD/member/activity; project/resource variant
  inputs; complete record presence/redaction semantics.
- Definition of done/evidence: A5/A10 native and exact-argv regressions pass;
  B2–B12 and relevant C/D mappings have family-local canonical and negative
  cases; raw custom env never appears in ordinary Agent reads; resource variants
  preserve labels and identity; family tests, Ruff, and mypy pass.
- Parallel-safety rationale: organization-domain modules do not overlap the
  system/runtime zone or issue/content zone. Shared discovery and exports wait
  for WP-05.

## WP-04 — Issue, comment, chat, wakeup, autopilot, skill, and content parity

- `stage`: 2
- `depends_on`: WP-01
- OpenSpec task coverage: `3.4`, `3.5`, `5.5`–`5.8`, `6.2`, `6.3`, `6.5`,
  `6.6`, `7.5`, `7.7`, `7.8`.
- Deliverable: correct flat recent-comment and cursor behavior; issue timeline;
  complete chat and wakeup families; trigger URL rotation; issue/comment/
  autopilot/skill/user input parity; and complete trigger/property/comment/
  acknowledgement response projections.
- Owned responsibility scope: issue and nested comment/timeline/wakeup modules;
  chat modules; autopilot and trigger modules; skill and skill-file modules;
  user-profile content modules; their entity/wire/public models and family-local
  tests/fixtures.
- Critical shared files excluded: the WP-01 foundation and WP-05 integration
  zones. Shared resource/client registration is represented by local modules
  and deferred to WP-05.
- Contract surface: root/reply identity, cursor and folding signals, timeline
  envelopes, wakeup replacement/re-enable/retry/loop rules, chat ordering,
  trigger secret opt-in, content channels, comment supplements and
  acknowledgements.
- Definition of done/evidence: A6–A7 and D17 native fixtures retain identity and
  content; all B13–B16 and assigned C/D items have canonical, presence,
  redaction, pagination, and failure cases; no raw argv substitutes for typed
  families; family tests, Ruff, and mypy pass.
- Parallel-safety rationale: owns only issue/content/automation families and
  local tests. It does not write system/runtime or organization-domain modules.

## WP-05 — Cross-family integration, canonical proof chain, and migration docs

- `stage`: 3
- `depends_on`: WP-02, WP-03, WP-04
- OpenSpec task coverage: `3.8`, `6.9`, `8.1`–`8.5`.
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
  broad fake-CLI paths pass; docs and package exports match signatures; focused
  A1–A10 suite passes together; no unknown allowlist exists.
- Parallel-safety rationale: starts only after all stage-2 siblings finish, so
  it can update shared registries once without merge races or duplicate client/
  export wiring.

## WP-06 — Exact-SHA release verification and evidence handoff

- `stage`: 4
- `depends_on`: WP-05
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
- Parallel-safety rationale: terminal integration gate. It follows WP-05 and
  serializes any final repair against the complete tree; no sibling writes exist.

## Coverage audit

Every task in `tasks.md` is assigned exactly once:

- WP-01: `1.1`–`1.8`, `2.1`–`2.8`, `4.1`–`4.4`.
- WP-02: `3.1`, `3.2`, `3.6`, `5.1`, `5.9`, `6.7`, `6.8`, `7.1`, `7.2`.
- WP-03: `3.3`, `3.7`, `5.2`–`5.4`, `6.1`, `6.4`, `7.3`, `7.4`, `7.6`.
- WP-04: `3.4`, `3.5`, `5.5`–`5.8`, `6.2`, `6.3`, `6.5`, `6.6`, `7.5`,
  `7.7`, `7.8`.
- WP-05: `3.8`, `6.9`, `8.1`–`8.5`.
- WP-06: `8.6`–`8.8`.

The only execution frontier with multiple independent packages is stage 2
(`WP-02`, `WP-03`, `WP-04`). Their production write zones and family-local
tests are disjoint; all critical shared integration files are isolated in
predecessor WP-01 or successor WP-05.
