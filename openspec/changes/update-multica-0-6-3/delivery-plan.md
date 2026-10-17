## Delivery Contract

- Task key: `MYL-495`
- Change: `update-multica-0-6-3`
- Approved code base: `a96eecf3e12a88dd7b4d56e1aafae3285fb0990c`
- Upstream baseline: Multica `0.6.1` at `2ea01ae4ef55de4310b99af192d2dbd367832883`
- Upstream target: Multica `0.6.3` at `18fa9f728a9e25f2465df2789631edb2a75442ad`
- Implementation is blocked until explicit human approval. Draft PR #101 and PR #103 are neither a base nor a dependency.
- The authoritative weighted, optimistic, and pessimistic hour totals live only in the planning issue properties `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours`. This file records qualitative confidence and evidence without duplicating totals.

## E2E Decision

`e2e_required=true`.

Offline contract, unit, component, type, package, and deterministic-generation gates are sufficient for provenance, exact argv, strict decoding, redaction, and artifact cleanliness. Local/live E2E remains necessary for three behaviors that depend on a real Multica 0.6.3 server/CLI transaction: multi-value property persistence, workflow-aware status/project/assignee/run outcomes, and the actual visible project/daemon output used for before/after evidence.

Test-code repository: `https://github.com/maximchikAlexandr/multica-py`. The isolated stand, CLI profile, daemon, database, ports, authenticated frontend URL, and credentials SHALL come from the private project environment; public Git files SHALL use parameters such as `MULTICA_TEST_*` and MUST NOT contain private hostnames or personal data.

## Verification Matrix

| Case ID | OpenSpec requirement/scenario | Verification gap / local E2E decision | OpenAPI operation/schema | Local test script | Independent Tester steps | CI disposition / job | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| C01 | Upstream Contract: provenance, inventories, exclusions, deterministic generation | No local E2E; source-aware validation and exact closure are stronger and reproducible offline | Not applicable; CLI approved-contract boundary | Existing `scripts/upstream_contract.py`, `scripts/audit_source_links.py`, contract tests | Inspect pinned source/ref inputs, run validate/render twice/check/audit at candidate SHA, compare bytes and tracked content | Extend existing `contract-check` and offline quality jobs | Exact release identities; 209 nodes; 4/0/3 delta; 196 responses; 56/140 verdicts; no excluded public symbols; identical render bytes | Multica comment: commands, exit codes, candidate SHA, hashes, concise assertion results; no image |
| C02 | Property Resource: legacy and JSON-array writes; ordered/duplicate/null/empty decode | Local E2E required because CLI/server persistence and resolved-property projection cannot be proved by fake CLI alone | Existing issue/property CLI JSON contracts; no repository OpenAPI artifact | Extend `tests/live/test_smoke.py` using public SDK; no second harness | In an isolated workspace create uniquely named `multi_text` and `multi_url` definitions, create an issue, set legacy string then tuple values containing comma/duplicate/empty cases, reload through property list and resolved issue projection, unset, and inspect final state | Offline rows in `quality`; protected `live-smoke` after human approval | One mutation per set; exact order and duplicates; comma remains one item only in JSON-array path; null and empty remain distinct; cleanup succeeds | Captured baseline/candidate text plus `property-multi-before.png` and `property-multi-after.png`; command/exit/assertion log in Multica only |
| C03 | Project Workflow Compatibility: UUID/null, validation conflict, status remap, handoff, partial update | Local E2E required because authoritative workflow transaction spans server persistence and run/assignment behavior | Existing project/issue CLI JSON contracts; workflow-management HTTP endpoints explicitly excluded | Extend `tests/live/test_smoke.py` with prepared named/default workflow projects and public SDK calls | Using disposable projects/issues in the isolated stand, read default and named workflow projects; create/update/status/move an issue; observe one invalid-status conflict, one compatible remap, and resulting project/status/assignee/run state; independently inspect issue/project through CLI or UI, not by rerunning pytest | Offline fixture rows in `quality`; protected `live-smoke` after human approval | UUID and null/legacy decode; one command per mutation; no client retry; returned state equals independent read; unrelated project fields survive partial update; handoff is not duplicated | `workflow-before.txt`, `workflow-after.txt`, `workflow-before.png`, `workflow-after.png`; Multica-only command/exit/assertion records and image attachments |
| C04 | SDK Surface: daemon `cli_commit` full/legacy output | Focused local E2E and image required for changed read output; legacy absence is covered offline with fixture | `daemon status --output json` | Existing live smoke plus a small public-SDK assertion in `tests/live/test_smoke.py` | On macOS capture equivalent baseline 0.6.1 and candidate 0.6.3 daemon-status text at fixed width/locale; verify candidate full commit and public SDK field; do not stop/restart the primary daemon | Offline decoder rows in `quality`; candidate identity check in protected `live-smoke` | Baseline omission/empty normalizes to `None`; candidate exact full SHA; no lifecycle mutation | `daemon-status-061.txt`, `daemon-status-063.txt`, `daemon-status-061.png`, `daemon-status-063.png` rendered from actual text |
| C05 | SDK Surface and Wakeup: diagnostics, stable redaction, upload partial effects | No local fault injection; existing fake CLI/component transport gives deterministic error body, call count, side-effect, and redaction assertions without risking real data | Existing wakeup/upload CLI result and error envelopes | Existing unit/component transport, wakeup, attachment and redaction tests | Inspect fixtures against pinned 0.6.3 source, run focused tests, verify sanitized public exception and exact one-call behavior | Extend `quality`; no live-only case | Safe stable text retained; secrets/backend stack/private hosts absent; upload is not retried; partial side effect explicit | Multica comment with focused test command, exit code, source links and assertions; no image |
| C06 | Verification and Release: direct docs, package, rollback, one-SHA gates | No local E2E beyond C02–C04; build/package/CI checks are authoritative | Not applicable | Existing Makefile, packaging tests and CI workflows | At exact candidate SHA run full offline command set, inspect wheel/sdist/tracked file lists, compare docs/contract/generated version claims, and confirm clean tree | Existing `lint`, `types`, `quality`, `compatibility`, `contract-check`, package/release gates; extend fixtures only | All commands pass at same SHA; no live nodes in offline collection; no evidence/private content in Git/package; version interval and exclusions agree | Multica comment with SHA, commands, exit codes, package filenames/hashes, MR/commit/file links; no image |

## Local Scripts, Fixtures, and Ownership

- Implementer owns all repository test changes: table rows, fake CLI payloads, provenance fixtures, any focused additions to `tests/live/test_smoke.py`, CI workflow updates, and product-generated artifacts. Tester SHALL NOT edit these files.
- Reuse the repository's pytest/fake-CLI/live-smoke infrastructure. Do not add a new E2E runner, snapshot dependency, browser automation framework, or committed evidence directory.
- C02 fixtures require disposable property definitions and an issue namespace unique to the run. C03 requires prepared disposable projects for default and named workflows plus disposable issues/runs. C04 requires separate baseline and target executables/profiles; it MUST NOT restart or stop the workspace's primary daemon.
- Each live script SHALL record the product candidate SHA, test-code SHA, exact CLI version/commit, selected profile, sanitized resource identifiers, command, exit status, and cleanup result. It MUST fail before assertions if the observed CLI is not exact 0.6.3.
- Setup and cleanup SHALL use the isolated test profile/daemon and failure-safe `try/finally` fixtures. Cleanup removes disposable server data and local stand state while preserving the evidence branch, MR, commits, and Multica attachments.

## Independent Walkthrough and Images

- Tester uses a fresh checkout of the test repository and the dedicated isolated stand. The SDK candidate and test code revisions SHALL be recorded separately when they differ.
- C02 independent action is a CLI/SDK round trip followed by a separate property-list/resolved-issue read. C03 independent action is a public mutation followed by a separate CLI or UI state inspection. C04 independent action is an actual daemon-status read with no lifecycle mutation. Merely rerunning automated tests is insufficient.
- For every changed Mac-visible output, capture actual UTF-8 text for baseline and candidate under the same locale, terminal width, output mode, fixture, and sanitized labels. Render those captured text files to PNG with the bundled `scripts/render_terminal.swift` from `openspec-e2e-testing`. Label PNGs as renders of captured output, not terminal screenshots.
- ANSI color, TTY-only progress, and interactive states are out of capture scope unless the command genuinely emits them under the selected mode; redirection limitations SHALL be stated in the evidence comment.
- Images and source text retain the tested output language. The plan and Tester-authored explanation remain English. Missing mandatory before/after text or PNG blocks completion of C02, C03, or C04.

## Evidence Publication and Cleanup

- Tester publishes one final Multica comment with exact candidate/test SHAs; commands and exit codes; assertion results; provenance; MR, commit, and file links; and all required PNG attachments. Tester SHALL read the posted comment back and verify attachment presence.
- Actual logs, diagnostic JSON, hashes, raw outputs, screenshots/renders, private hostnames, credentials, and personal data SHALL remain out of Git and GitHub. Sanitize evidence before publication without changing the asserted semantic values.
- GitHub retains only ordinary development outputs: implementation, tests, fixtures, required scripts, generated product code/docs, and their commits. If a tested Git utility itself creates a functional commit, preserve that commit unchanged and link it; do not create an evidence-only commit.
- Cleanup removes disposable stand resources and local evidence staging files after successful publication/read-back. It SHALL NOT close or merge the MR, delete the evidence branch, or remove evidence commits without separate authorization.

## Estimate Basis

The estimate covers the full remaining implementation from the approved base through mandatory offline acceptance and the planned independent verification/repair work. It assumes one experienced developer familiar with Python, msgspec, pytest, and this repository, without AI acceleration. Confidence and calibration are recorded here after the estimate property read-back; numeric totals remain issue-property-only.

Confidence is **medium** and calibration is **uncalibrated**. Evidence is strong for the existing contract generator, wire/resource patterns, table-driven tests, CI jobs, and exact acceptance criteria. Uncertainty is concentrated in the breadth of the 209-node/196-response contract reconciliation, the exact server-owned workflow handoff fixtures, and likely repair iterations across strict closure and package gates. Tests were not run for estimation. The estimate becomes invalid if workflow-management or daemon-autostart public APIs enter scope, the compatibility minimum changes, the target upstream commit moves, or implementation starts from either draft PR instead of the approved base.

## Work Package Topology

`delivery_mode=dag`. The authoritative `Estimate, hours` property exceeds the multi-WP threshold, and stage 2 contains three genuinely independent packages. Stages are consecutive topological layers; WIP policy is operational and is not encoded as extra dependencies.

Stage mapping: `WP-01 -> 1`, `WP-02 -> 2`, `WP-03 -> 2`, `WP-04 -> 2`, `WP-05 -> 3`.

### WP-01 — Approved Contract Foundation

- Stage: `1`
- OpenSpec task coverage: `1.1`, `1.2`, `1.3`, `1.4`
- Depends on: none
- Deliverable: one strict, source-pinned 0.6.3 approved contract and deterministic generated runtime foundation, including exact inventory/response closure and exclusions.
- Owned responsibility scope: `contracts/sdk-contract.json`, `contracts/schema/`, contract validator/renderer code in `scripts/upstream_contract.py`, source-link audit inputs, contract-specific mutation/provenance tests, and `src/multica_py/_generated/approved_sdk.py`. Directly related fixtures/docs are included unless assigned below.
- Critical shared files: this WP exclusively owns the approved contract, schema, renderer, and generated runtime until accepted. Downstream WPs consume these files and SHALL NOT edit them concurrently.
- Contract surface: release/tag/asset/binary provenance; `[0.6.0,0.6.4)` compatibility; 209 CLI nodes; 196 response items; generated signatures/types/mappings; explicit `defer`/`not_sdk_surface` decisions.
- DoD/evidence: strict contract validation against pinned target source; negative mutation cases; double-render byte equality; generated freshness; source-link audit; exact count/disposition assertions; clean diff limited to planning-approved product files.
- Parallel-safety rationale: foundation is intentionally serialized because every runtime package consumes the same approved generated contract.

### WP-02 — Multi-value Properties

- Stage: `2`
- OpenSpec task coverage: `2.1`, `2.2`, `3.1`
- Depends on: `WP-01`
- Deliverable: backward-compatible typed multi-value property definitions, writes, decoding, and focused automated coverage.
- Owned responsibility scope: property models/types, `resources/properties.py`, `resources/issue_properties.py`, property projection adapters, and property-focused unit/component/contract cases and fixtures. Related tests and docs local to this behavior are included.
- Critical shared files: SHALL NOT edit the approved contract/generated runtime, project/issue workflow implementation, daemon/diagnostic implementation, `tests/cases/operations.py`, general public-discovery tables, CI workflows, live smoke, or cross-cutting docs owned by WP-05.
- Contract surface: open property type strings; `str | tuple[str, ...]` set input; compact JSON-array argv; scalar/null/empty/ordered/duplicate/malformed decode behavior; unchanged raw projection boundary.
- DoD/evidence: table-driven complete argv and decoder rows; zero-I/O invalid tuple tests; legacy comma-string regression; mypy/ruff/focused pytest success; no new dependency or fixture framework.
- Parallel-safety rationale: writes are confined to property runtime/test paths and do not overlap WP-03 or WP-04.

### WP-03 — Project Workflow Compatibility

- Stage: `2`
- OpenSpec task coverage: `2.3`, `2.4`, `3.2`
- Depends on: `WP-01`
- Deliverable: additive project workflow identity plus authoritative, single-attempt workflow-aware issue write behavior and focused coverage.
- Owned responsibility scope: project wire/entity/resource paths, existing issue create/status/update/project-move adapters where a bounded change is required, and project/workflow-focused unit/component fixtures and tests. Related tests and docs local to this behavior are included.
- Critical shared files: SHALL NOT edit the approved contract/generated runtime, property paths, daemon/diagnostic paths, `tests/cases/operations.py`, CI workflows, live smoke, or cross-cutting docs owned by WP-05.
- Contract surface: nullable/omitted `workflow_id`; unchanged public issue method signatures and argv; server-returned status remap, assignee and run state; one-attempt conflict propagation; project partial-update presence.
- DoD/evidence: UUID/null/legacy decode and serialization; success/conflict/remap/handoff/partial-update table cases; exact transport call counts; focused mypy/ruff/pytest success; no workflow-management API or client-side mapper.
- Parallel-safety rationale: writes are confined to project/issue workflow runtime and dedicated tests, disjoint from property and daemon/diagnostic ownership.

### WP-04 — Daemon Identity and Safe Diagnostics

- Stage: `2`
- OpenSpec task coverage: `2.5`, `2.6`, `3.3`
- Depends on: `WP-01`
- Deliverable: compatible daemon CLI commit decoding and reviewed wakeup/upload/server diagnostic behavior through existing safe exception boundaries.
- Owned responsibility scope: daemon status model/decoder/resource tests, wakeup/attachment/transport/redaction implementation only where required, and their focused unit/component fixtures/tests. Related tests and docs local to this behavior are included.
- Critical shared files: SHALL NOT edit the approved contract/generated runtime, property paths, project/workflow paths, `tests/cases/operations.py`, CI workflows, live smoke, or cross-cutting docs owned by WP-05.
- Contract surface: full/empty/null/omitted `cli_commit`; safe stable messages; redaction; upload partial-side-effect boundary; exact one-call/no-retry behavior; retained wakeup lifecycle.
- DoD/evidence: full-SHA and legacy decoder cases; source-linked diagnostic/error fixtures; leakage assertions; exact call counts; focused mypy/ruff/pytest success; no daemon lifecycle mutation in tests.
- Parallel-safety rationale: daemon/wakeup/transport-redaction paths and fixtures are separate from WP-02 and WP-03 write zones.

### WP-05 — Integration, Documentation, CI, and Acceptance

- Stage: `3`
- OpenSpec task coverage: `3.4`, `3.5`, `4.1`, `4.2`, `5.1`, `5.2`
- Depends on: `WP-02`, `WP-03`, `WP-04`
- Deliverable: integrated public closure, protected live coverage, coherent documentation/package claims, all offline gates at one clean SHA, and an independently executable evidence handoff after human approval.
- Owned responsibility scope: shared public discovery/canonical operation tables including `tests/cases/operations.py`; cross-cutting response/compatibility/package assertions; `.github/workflows/`; `tests/live/`; README and `docs/`; package/export checks; final integration repairs; verification scripts/fixtures not owned by predecessors.
- Critical shared files: this WP is the sole writer for shared canonical tables, CI/live workflow, and cross-cutting documentation. It may repair predecessor-owned code only after those WPs are accepted and no sibling remains active.
- Contract surface: exact public symbol/operation/response closure; excluded surfaces absent; target CLI identity gate; direct migration and rollback claims; offline/live separation; evidence publication contract.
- DoD/evidence: all task 5.1 commands pass at one clean candidate SHA; live nodes excluded offline; build and isolated wheel/sdist tests pass; Git/package audits exclude evidence; after human approval Tester completes C02–C04, posts commands/assertions/links and mandatory images to Multica, verifies attachment read-back, and cleans the stand without closing/merging/deleting the evidence branch.
- Parallel-safety rationale: this is the sole join package because it owns intentionally shared integration files and must consume all three stage-2 deliverables before final closure.

## Coverage and Frontier Check

Every OpenSpec task `1.1` through `5.2` appears exactly once above. Direct dependencies only are listed: WP-05 depends on the three stage-2 deliverables and inherits WP-01 transitively. The executable frontiers are `{WP-01}`, `{WP-02, WP-03, WP-04}`, and `{WP-05}`, so the DAG has a real parallel frontier and does not collapse into a linear chain.
