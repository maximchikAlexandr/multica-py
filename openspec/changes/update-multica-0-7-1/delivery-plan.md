## Delivery contract

- Change: `update-multica-0-7-1`
- Planning base: `f3c41027b89550731e52335e6bea42eeb7b4e905`
- Upstream baseline: Multica `0.7.0` at `dbdbb299164347586e2650bb67684a490726a798`
- Upstream target: Multica `0.7.1` release `425269384` at `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`
- Estimate source of truth: the root planning issue properties `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours`; this file intentionally contains no numeric estimate total.
- Planning authority: proposal, design, delta specs, and tasks in this change. Operational status and assignee state remain in Multica, not OpenSpec.

## E2E decision

`e2e_required=true`.

Lower-level table-driven tests can prove mappings, decoding, standard errors, and invalid wire shapes, but they cannot prove the reviewed cross-component settlement, concurrency, and atomic-refresh behavior against a real `0.7.1` CLI/server/database/filesystem boundary. The owner also requires independent exact-revision evidence. One focused repository-native script is the smallest sufficient live layer; it reuses the project-described isolated test repository and `multica-test` profile/daemon and does not introduce another runner.

The test repository URL and private stand coordinates SHALL be read at execution time from the current project description and environment as `TEST_REPOSITORY_URL` and stand-specific parameters. They SHALL NOT be copied into Git, logs, screenshots, or public comments. The primary Multica profile, daemon, containers, server, workspace, token, and credentials SHALL NOT be used.

## Verification matrix

| Case ID | Requirement / scenario | Gap and local E2E decision | Public boundary / schema | Script and independent Tester actions | CI disposition | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|
| V071-01 | Upstream provenance, 209 commands, 196 responses, deterministic projection | No live gap; contract/source checks are sufficient | Approved contract and generated projection; no OpenAPI operation | Script preflight records candidate SHA and `multica-test version`; Tester independently compares them with the delivery contract | Extend `contract-check` source checkout to target `0.7.1`; run validate/render/check and source-link audit | Exact commits/release/digests; 209/209 inventory; 196 unique verdicts; clean render | Sanitized preflight text and manifest attached in Multica; no image |
| V071-02 | Wakeup `blocked` create/update/get/list/events and validation negatives | Local E2E selected for real condition persistence and event observation; negative matrix remains lower-level | Existing CLI-backed wakeup resource; request/result/error models | `scripts/verify_multica_071.py --case wakeup-blocked` creates disposable issue/wakeup, updates and reads it, then observes event state; Tester independently creates one blocked condition and inspects get/list/events | Add unit/contract/component rows for all paths, invalid state, missing dependency, and conflicts; live smoke covers one positive lifecycle | Exact `blocked` round-trip on five response paths; invalid combinations fail before transport; cleanup removes wakeup/issues | Sanitized JSON/text per action, commands, exit codes, SHA; no image because table/log output is unchanged |
| V071-03 | Agent allowed/reserved/retained/omitted/empty `custom_args` | Local E2E selected for authoritative provider-reserved rejection and retained server state; exhaustive forms remain lower-level | Existing agent create/update and standard error envelope | Script uses a disposable agent/provider fixture for allowed, reserved, omitted, empty, and runtime-retain paths; Tester independently executes the reserved and retain paths | Extend existing operation/component cases; live smoke covers reserved error and retained state only when the stand has the safe provider fixture | Ordered allowed values; standard sanitized reserved error; omission differs from empty array; runtime change retains args | Sanitized result/error JSON and final agent projection; no image |
| V071-04 | Autopilot create-issue success, blocked settlement, retry chain, nullable legacy data | Local E2E selected for real task/issue/run settlement; malformed/legacy variants remain fixtures | Existing autopilot run page and task/issue relations | Script triggers disposable create-issue autopilot fixtures for success and blocked settlement and records task/run linkage; failure/retry uses a deterministic test fixture supported by the stand; Tester independently inspects run history and issue state | Extend contract/unit relations for all variants; protected live smoke covers one success and one blocked settlement | Emitted task id retained; blocked issue is not false run failure; retry order/linkage preserved; legacy null remains `None` | Sanitized run/issue/task projections and links; no image |
| V071-05 | Search overflow text and workflow-assignee preservation | Local E2E selected for backend parsing and workflow resolution; cheaper checks cannot prove server behavior | Existing issue search/update and issue model | Script searches an out-of-int4 decimal string and applies a disposable workflow-resolved update; Tester repeats public calls and inspects returned/current assignee | Add focused component rows; live smoke covers both public calls | Normal page instead of conversion error; returned and persisted assignee are unchanged | Sanitized query/result and before/after identity values; no PNG because human-facing output is unchanged |
| V071-06 | Concurrent project-resource partial updates and omission/null | Local E2E selected because real optimistic concurrency/database merge semantics are the requirement | Existing project resource add/update/get models | Script creates one disposable resource and coordinates two distinct partial updates, then a clear/omit case; Tester independently reads final resource and verifies both writes | Add deterministic component regression with controlled interleaving; live smoke executes one isolated convergence case | No lost unrelated fields; both accepted changes converge; null clears only the named field; omission preserves | Sanitized initial/update/final JSON, ordering and exit codes; no image |
| V071-07 | Portable/atomic skill bundles, binary skip, remote failures, prior-bundle preservation | Local E2E selected for filesystem/acquisition/atomic replacement; all failure codes use controlled stand fixtures | Existing skill import/refresh/files models and standard errors | Script creates a disposable skill and controlled remote bundles for valid, unsafe path, binary, 400/413/502/503/504, and failed refresh; Tester independently inspects files before/after one success and one failed refresh | Add table-driven unit/component cases for every path/status; live smoke runs valid bundle and prior-preservation cases | Complete success; unsafe paths rejected; binary omitted; exact typed failures; old bundle byte-identical after every failure | Sanitized bundle listing, content hashes, error summaries, final cleanup record; no binary/log dump and no image |
| V071-08 | Open process-cleanup `failure_reason` and `result` | Local observation selected only when the isolated stand can deterministically produce the reviewed cleanup outcome; otherwise the required contract fixtures remain the acceptance evidence and the gap is reported, not fabricated | Existing issue-run and agent-task projections | Script records a naturally emitted deterministic cleanup outcome from a disposable task; Tester independently compares issue-run and agent-task paths | Add known/unknown/invalid wire cases to both paths; no extra live attempt if the readiness fixture is unavailable | Exact known values on both paths; unknown valid values decode; invalid types fail | Sanitized task projections and provenance; no image |
| V071-09 | Offline, typing, lint, docs, packaging, exact-SHA delivery | No additional local E2E; repository/CI gates are sufficient | Makefile, CI workflows, package artifacts | Tester checks published SHA and linked CI; no second suite replay | Run focused gates locally; run any suite expected to exceed or reaching ten minutes unsplit in GitHub Actions on the published SHA | OpenSpec strict, contract, source links, tests, mypy, Ruff, docs, package, live collection, clean Git all pass | Commands/exit codes and CI/MR/commit/file links in Multica; no diagnostic files committed |

## Script and environment contract

- Implementer owns `scripts/verify_multica_071.py` and any directly related committed fixtures. It SHALL use the repository's Python/SDK conventions and existing test helpers where applicable, accept case selection and execution parameters, fail closed on readiness mismatch, and avoid a parallel validation framework.
- Entry command: `uv run python scripts/verify_multica_071.py --cli multica-test --repository "$TEST_REPOSITORY_URL" --candidate-sha "$CANDIDATE_SHA" --output "$EVIDENCE_DIR"` with a disposable case namespace. Actual values are supplied only in the isolated test context.
- Readiness SHALL prove exact candidate SHA, CLI `0.7.1`, isolated profile and daemon identity, isolated repository checkout, dedicated database/ports where applicable, empty disposable namespace, and focused offline prerequisites before consuming a live attempt.
- The script SHALL emit only sanitized scenario JSON/text, a manifest containing product revision, test-code revision, commands, exit codes, assertion outcomes, and content hashes, plus a cleanup record. Environment dumps, tokens, profiles, private hostnames, raw logs, binaries, and unrelated state are forbidden.
- Failure-safe cleanup SHALL remove only disposable wakeups, issues, agents, autopilots, project resources, skills, checkout state, database state, and ports created by the case namespace. It SHALL never stop or mutate the primary Multica daemon or containers.

## Independent Tester contract

- Tester SHALL work from a fresh checkout/profile context at the published candidate SHA and SHALL not edit implementation, CI tests, fixtures, or the verification script.
- Tester SHALL run the readiness gate once, execute the focused script, then independently perform representative public actions for V071-02 through V071-08 and inspect returned SDK objects plus final server/filesystem state. A second script invocation is not an independent walkthrough.
- PASS is case-specific and records candidate SHA, test-code SHA, material fixtures, commands, exit codes, assertions, and cleanup. A new candidate SHA requires impact assessment and rerunning only affected cases; uncertain impact leaves the case unverified.
- No before/after PNG is required because the planned change does not alter visible terminal tables, logs, progress, summaries, or browser UI. If implementation unexpectedly changes visible output, verification SHALL stop and require a planning revision that adds actual baseline/candidate text and Mac PNG capture via the bundled `scripts/render_terminal.swift` from `openspec-e2e-testing`.
- The final Multica comment SHALL include normal development MR/commit/file links, script/result commit separation when each has a distinct durable result, CI links, and sanitized evidence attachments. Tester SHALL read the comment back and confirm attachments are accessible. Actual results, logs, diagnostic JSON, hashes, commands, provenance, and images remain Multica-only.
- Cleanup SHALL preserve the evidence branch, MR, commits, CI links, and Multica attachments. It SHALL NOT close, merge, or delete the branch without separate authorization.

## Verification ownership

- Implementer owns OpenSpec tasks 1.1–6.3, including product code, approved contract, generated projection, lower-level tests/fixtures, CI workflow changes, documentation, verification script, and exact-SHA publication.
- Independent Tester owns execution and evidence for task 6.4 and reports findings without modifying implementation artifacts.
- Planning verification and implementation approval remain separate gates; this package does not authorize implementation.

## Estimate basis

The authoritative totals are stored only in the root planning issue properties. The estimate covers remaining work for one experienced developer familiar with the Python/CLI stack, without AI acceleration, from base `f3c41027b89550731e52335e6bea42eeb7b4e905` through the specified implementation, tests, documentation, exact-revision verification, and likely review repairs. It excludes unattended CI time, approval queues, and external blocking.

Confidence is medium and calibration is unavailable: acceptance is explicit, affected source/tests and a close `0.7.0` upgrade analogue are inspectable, but no comparable developer-hour history exists and several corrections require real server lifecycle/concurrency fixtures. Tests were not run for estimation. The main uncertainty is the effort to encode the already-reviewed command/response dossier in the large approved contract, deterministic stand support for autopilot/skill failure cases, and repair cycles from the full offline/package gates.

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

### WP-5 — Integration, documentation, exact-SHA E2E, and release evidence

- `stage`: 3
- `depends_on`: WP-2, WP-3, WP-4
- OpenSpec task coverage: 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4
- Deliverable: coherent documentation and CI, one focused isolated verification script, all repository gates, exact-SHA publication, and independent Tester evidence.
- Owned responsibility scope: compatibility/API/migration/coverage/changelog/contributing/release docs, CI workflows, `scripts/verify_multica_071.py`, directly related script fixtures, cross-domain integration tests/helpers, publication proof, and Tester evidence coordination. After predecessors complete, this package may make necessary integration repairs across their areas and records those repairs explicitly.
- Contract surface: documented compatibility/migration; CI target source and protected live CLI version; readiness and cleanup parameters; sanitized evidence schema; exact candidate SHA; Multica attachment/read-back contract.
- Definition of done/evidence: focused and full required gates pass under the ten-minute/CI policy; local and remote SHA match; independent case evidence and cleanup are attached/read back in Multica; no private data, raw diagnostics, or transient evidence is committed; branch/MR remain unmerged and preserved.
- Parallel-safety rationale: this final integrator starts only after all domain siblings close, so documentation, CI, shared helpers, and cross-domain repairs cannot race active sibling writes.

## Frontier validation

- Stage 1 frontier: WP-1 only, because shared contract/generated authority must be established once.
- Stage 2 frontier: WP-2, WP-3, and WP-4 are mutually independent and may run concurrently with disjoint production/test ownership.
- Stage 3 frontier: WP-5 integrates the completed siblings and performs publication/evidence work.

The graph therefore contains a real three-way parallel frontier. WIP limits are operational Manager policy and are not encoded as additional dependencies or stages.
