## Delivery contract

- Change: `update-multica-0-7-1`
- Planning base: `f3c41027b89550731e52335e6bea42eeb7b4e905`
- Upstream baseline: Multica `0.7.0` at `dbdbb299164347586e2650bb67684a490726a798`
- Upstream target: Multica `0.7.1` release `425269384` at `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`
- Estimate source of truth: the root planning issue properties `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours`; this file intentionally contains no numeric estimate total.
- Planning authority: proposal, design, delta specs, and tasks in this change. Operational status and assignee state remain in Multica, not OpenSpec.

## E2E decision

`e2e_required=false`.

The owner has authoritatively declined additional infrastructure. No material acceptance result requires a task-specific live interaction: the change governs SDK argument mappings, validation, response decoding, compatibility, deterministic generation, and documentation. Existing frozen tables, contract checks, fake-CLI component tests, controlled lifecycle/concurrency fixtures, packaging checks, and non-live CI can prove every changed scenario at a sufficient lower layer. The plan therefore adds no verification script, repository URL, profile, daemon, backend, database, port, credential, or runner, and it does not claim live-server proof.

Independent exact-revision evidence remains required. Tester verifies the scenario-to-test mapping, runs focused lower-level checks from a fresh checkout, and confirms the published remote SHA and CI evidence. The repository's pre-existing generic live facilities remain outside this change and are neither extended nor required.

## Verification matrix

| Case ID | Requirement / scenario | Verification decision | Public boundary / schema | Existing check and independent Tester actions | CI disposition | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|
| V071-01 | Upstream provenance, 209 commands, 196 responses, deterministic projection | Contract/source checks are sufficient | Approved contract and generated projection; no OpenAPI operation | Contract validate/render/check and source-link audit; Tester compares exact identities and repeated-render assertions | Extend existing contract job to target `0.7.1` | Exact commits/release/digests; 209/209 inventory; 196 unique verdicts; clean render | Commands, exits, SHA, and links in Multica; no image |
| V071-02 | Wakeup `blocked` create/update/get/list/events and validation negatives | Frozen operation/response tables plus fake-CLI component rows are sufficient | Existing wakeup request/result/error models | Tester inspects and runs the focused table/component nodes | Existing non-live jobs | Exact `blocked` mappings on five response paths; invalid combinations fail before transport | Test paths, command, exit, assertions; no image |
| V071-03 | Agent allowed/reserved/retained/omitted/empty `custom_args` | Request/error/response fixtures fully express the contract | Existing agent create/update and standard error envelope | Tester inspects and runs operation, body, decoder, and error cases | Existing non-live jobs | Ordered allowed values; typed reserved error; omission differs from empty; retained response state | Test paths, command, exit, assertions; no image |
| V071-04 | Autopilot success, blocked settlement, retry chain, nullable legacy data | Controlled lifecycle fixtures are sufficient and deterministic | Existing autopilot run page and task/issue relations | Tester traces fixture states and runs focused relation/decoder tests | Existing non-live jobs | Task id retained; blocked is not false failure; retry linkage/order; legacy null | Fixture/test links and assertions; no image |
| V071-05 | Search overflow text and workflow-assignee preservation | Fake-CLI request/response cases prove SDK behavior; no live backend claim is needed | Existing issue search/update and issue model | Tester inspects emitted query and decoded response assertions and runs focused component rows | Existing non-live jobs | Query remains text; normal page decodes; assignee identity is preserved | Test paths, command, exit, assertions; no image |
| V071-06 | Concurrent project-resource partial updates and omission/null | Controlled interleaving component fixture is the lowest sufficient layer | Existing project resource update/get models | Tester inspects the interleaving schedule and final projection, then runs the focused component case | Existing non-live jobs | Both accepted partial changes converge; omitted fields remain; explicit null clears only its field | Fixture/test links and assertions; no image |
| V071-07 | Portable/atomic skill bundles, binary skip, remote failures, prior-bundle preservation | Filesystem and transport fixtures deterministically cover all branches | Existing skill import/refresh/files models and standard errors | Tester inspects bundle fixtures and runs table/component cases | Existing non-live jobs | Portable success; unsafe rejection; binary omission; typed failures; prior bundle unchanged | Fixture/test links and assertions; no binary/log dump or image |
| V071-08 | Open process-cleanup `failure_reason` and `result` | Known/unknown/invalid wire fixtures are sufficient | Existing issue-run and agent-task projections | Tester compares both decoder paths and runs focused tests | Existing non-live jobs | Known values preserved on both paths; future valid values decode; invalid types fail | Test paths, command, exit, assertions; no image |
| V071-09 | Offline, typing, lint, docs, packaging, exact-SHA delivery | Repository and CI gates are sufficient | Makefile, CI workflows, package artifacts | Tester checks published SHA, scenario coverage, and linked CI from a fresh checkout | Run focused gates locally; move any suite expected to exceed or reaching ten minutes unsplit to GitHub Actions | OpenSpec strict, contract, source links, tests, mypy, Ruff, docs, package, live collection, clean Git all pass | Commands/exits and CI/MR/commit/file links in Multica; no diagnostic files committed |

## Script and environment contract

- No task-specific E2E script or environment contract is created. No test-repository or stand-specific parameter is an input to this change.
- Implementer SHALL extend only existing test tables, fixtures, fake-CLI/component cases, repository commands, and CI jobs needed by the matrix. No new runner, target-discovery layer, credential path, profile, daemon, database, port, or external service is allowed.
- Automated local suites follow the ten-minute policy. Long suites run unsplit in GitHub Actions on the published exact revision; this is CI execution, not local E2E.
- Commands, exit codes, assertion summaries, exact SHAs, and links are published in Multica. Raw logs, diagnostic JSON, hashes, screenshots, environment dumps, private hostnames, and credentials are not committed.

## Independent Tester contract

- Tester SHALL work from a fresh checkout at the published candidate SHA and SHALL not edit implementation, CI tests, or fixtures.
- Tester SHALL independently map V071-01 through V071-09 to concrete tests/assertions, run the focused lower-level commands, inspect the deterministic fixtures and state projections, and verify linked CI. This evidence SHALL not be described as a live stand result.
- PASS is case-specific and records candidate SHA, test paths, commands, exit codes, assertions, and CI links. A new candidate SHA requires impact assessment and rerunning only affected cases; uncertain impact leaves the case unverified.
- No before/after PNG is required because the planned change does not alter visible terminal tables, logs, progress, summaries, or browser UI. If implementation unexpectedly changes visible output, verification SHALL stop and require a planning revision that adds actual baseline/candidate text and Mac PNG capture via the bundled `scripts/render_terminal.swift` from `openspec-e2e-testing`.
- The final Multica comment SHALL include normal development MR/commit/file links, natural test/result commit separation when each has a distinct durable result, CI links, and sanitized evidence attachments. Tester SHALL read the comment back and confirm attachments are accessible. Actual results, logs, diagnostic JSON, hashes, commands, provenance, and images remain Multica-only.
- No mutable live test data is created. Cleanup removes only run-owned local diagnostic output while preserving the evidence branch, MR, commits, CI links, and Multica attachments; it SHALL NOT close, merge, or delete the branch without separate authorization.

## Verification ownership

- Implementer owns OpenSpec tasks 1.1–6.3, including product code, approved contract, generated projection, lower-level tests/fixtures, CI workflow changes, documentation, and exact-SHA publication.
- Independent Tester owns execution and evidence for task 6.4 and reports findings without modifying implementation artifacts.
- Planning verification and implementation approval remain separate gates; this package does not authorize implementation.

## Estimate basis

The authoritative totals are stored only in the root planning issue properties. The estimate covers remaining work for one experienced developer familiar with the Python/CLI stack, without AI acceleration, from base `f3c41027b89550731e52335e6bea42eeb7b4e905` through the specified implementation, tests, documentation, exact-revision verification, and likely review repairs. It excludes unattended CI time, approval queues, and external blocking.

Confidence is medium and calibration is unavailable: acceptance is explicit, affected source/tests and a close `0.7.0` upgrade analogue are inspectable, but no comparable developer-hour history exists. Tests were not run for estimation. The main uncertainty is the effort to encode the already-reviewed command/response dossier in the large approved contract, model deterministic lifecycle/concurrency and skill-failure fixtures at existing lower layers, and absorb repair cycles from the full offline/package gates.

## Delivery topology

`delivery_mode=dag` because the authoritative `Estimate, hours` property exceeds the single-package threshold and the graph has a genuine parallel stage after one shared contract foundation. Task coverage is complete and non-overlapping; dependencies below are direct only. Stages are consecutive topological layers, and Manager SHALL copy the exact `wp_id -> stage` mapping to child issue `stage` fields.

Stage mapping: `WP-1 -> 1`, `WP-2 -> 2`, `WP-3 -> 2`, `WP-4 -> 2`, `WP-5 -> 3`.

### WP-1 — Approved contract and generated foundation

- `stage`: 1
- `depends_on`: none
- OpenSpec task coverage: 1.1, 1.2, 1.3, 1.4, 1.5
- Deliverable: one validated `0.7.1` approved contract, complete command/response reconciliation, generated projection, and central operation/fixture metadata that downstream resource work consumes.
- Owned responsibility scope: `contracts/sdk-contract.json`, contract schema/validation/render/source-link tooling as required, `src/multica_py/_generated/approved_sdk.py`, central generated operation/vector metadata, and directly related contract tests/fixtures. This scope owns critical shared contract and generated files for the graph.
- Contract surface: exact upstream/release/binary identities; preserved minimum and new ceiling; 209 command dispositions; four changed help mappings; 196 response verdicts; deterministic generated bindings and validators.
- Definition of done/evidence: contract validate/render/check and source-link audit are clean; repeated render is byte-stable; generated operation completeness remains exact; no review evidence or `.devlocal` artifact is tracked.
- Parallel-safety rationale: this predecessor centralizes every shared contract/generated write before resource siblings begin, preventing concurrent edits to the largest conflict surface.

### WP-2 — Wakeup and agent retained behavior

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 2.1, 2.2, 2.3, 2.4
- Deliverable: `blocked` issue-state wakeups and provider-owned agent `custom_args` behavior implemented through existing resources with complete positive/negative tables.
- Owned responsibility scope: issue-wakeup and agent resource/model adapters plus their unit/contract/component cases and directly related fixtures. It SHALL consume, not rewrite, WP-1 contract/generated outputs.
- Contract surface: wakeup create/update/get/list/events open state; condition dependency/conflict validation; agent JSON-body omission/empty distinction; standard reserved-argument errors; retained arguments on runtime change.
- Definition of done/evidence: focused wakeup and agent test matrices pass with exact argv/body/decoder/error assertions; public signatures and open-value semantics remain backward-compatible.
- Parallel-safety rationale: write zones are confined to wakeup/agent modules and their domain tests, disjoint from WP-3 autopilot/task and WP-4 issue/project/skill zones.

### WP-3 — Autopilot settlement and task outcomes

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 3.1, 3.2, 3.3, 3.4
- Deliverable: corrected create-issue autopilot settlement and forward-compatible process-cleanup decoding across existing run/task paths.
- Owned responsibility scope: autopilot wire/model/resource/relation paths, task-run and agent-task decoding for cleanup outcomes, and their focused unit/contract fixtures. Shared general issue-resource behavior belongs to WP-4; central contract/generated metadata belongs to WP-1.
- Contract surface: nullable and malformed `task_id`; success/blocked/failure-retry ordering; open `failure_reason` and `result` values on both task response paths.
- Definition of done/evidence: table/focused tests prove every lifecycle and wire-shape scenario without synthetic task identities or closed enums.
- Parallel-safety rationale: autopilot/task decoder and fixture ownership is distinct from WP-2 and WP-4; any unavoidable shared test helper change is deferred to WP-5 after siblings finish.

### WP-4 — Issue, project-resource, and skill corrections

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 4.1, 4.2, 4.3, 4.4, 4.5
- Deliverable: issue parsing/assignment regressions, atomic concurrent project-resource updates, and portable all-or-nothing skill bundle behavior with typed remote failures.
- Owned responsibility scope: issue search/update adapters, project-resource adapters/models, skill import/refresh/files adapters, their controlled component fixtures, and domain-specific tests. It SHALL not edit WP-1 contract/generated files or WP-2/WP-3 domain modules.
- Contract surface: search string preservation; returned assignee identity; omitted/null partial-update semantics; portable paths; binary exclusion; complete bundle replacement; 400/413/502/503/504 standard errors; prior-bundle retention.
- Definition of done/evidence: deterministic component interleavings and table cases prove no lost fields or partial bundles and preserve existing public models/methods.
- Parallel-safety rationale: the three related server-correctness areas share component-test patterns but no sibling production write zone; grouping them avoids cross-WP fixture contention.

### WP-5 — Integration, documentation, exact-SHA verification, and release evidence

- `stage`: 3
- `depends_on`: WP-2, WP-3, WP-4
- OpenSpec task coverage: 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4
- Deliverable: coherent documentation and CI, complete scenario-to-test mapping, all repository gates, exact-SHA publication, and independent Tester evidence.
- Owned responsibility scope: compatibility/API/migration/coverage/changelog/contributing/release docs, CI workflows, cross-domain integration tests/helpers, publication proof, and Tester evidence coordination. After predecessors complete, this package may make necessary integration repairs across their areas and records those repairs explicitly.
- Contract surface: documented compatibility/migration; non-live CI gates; focused lower-level commands and assertions; exact candidate SHA; Multica attachment/read-back contract.
- Definition of done/evidence: focused and full required gates pass under the ten-minute/CI policy; local and remote SHA match; every changed scenario maps to a sufficient deterministic check; independent case evidence is attached/read back in Multica without a live-server claim; no private data, raw diagnostics, or transient evidence is committed; branch/MR remain unmerged and preserved.
- Parallel-safety rationale: this final integrator starts only after all domain siblings close, so documentation, CI, shared helpers, and cross-domain repairs cannot race active sibling writes.

## Frontier validation

- Stage 1 frontier: WP-1 only, because shared contract/generated authority must be established once.
- Stage 2 frontier: WP-2, WP-3, and WP-4 are mutually independent and may run concurrently with disjoint production/test ownership.
- Stage 3 frontier: WP-5 integrates the completed siblings and performs publication/evidence work.

The graph therefore contains a real three-way parallel frontier. WIP limits are operational Manager policy and are not encoded as additional dependencies or stages.
