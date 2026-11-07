## Delivery contract

- Change: `update-multica-0-8-1`
- Planning base: `b268e3bec0436fe51727fda50583344f57663284`
- Upstream baseline: Multica `0.7.1` at `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`
- Upstream target: Multica `0.8.1` release `436353568` at `b1ea927def6490c43bedff537b6f4ed9a47fa828`
- Test repository: `https://github.com/maximchikAlexandr/multica-py`
- Estimate source of truth: root planning issue properties `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours`; this file intentionally contains no numeric estimate total.
- Planning authority: proposal, design, delta specs, tasks, and this delivery contract. Operational status and assignees remain in Multica.
- Implementation gate: human approval of the explicit run-targeted retry break is required before any production or test edit.

## E2E decision

`e2e_required=false`.

No material acceptance result requires a task-specific live interaction. The change governs deterministic SDK argv, pre-transport validation, approved-contract projection, and JSON decoding. Existing table-driven unit/contract tests, fake-CLI component cases, packaging checks, and `.github/workflows/ci.yml` can prove every changed scenario with controlled old/new/invalid rows. The protected live-smoke workflow is pinned to an older CLI and does not provide a suitable `0.8.1` acceptance boundary; changing or invoking it would add unrelated scope rather than close a remaining gap.

No test script, fixture repository, stand profile, daemon, backend, database, port, credential, browser walkthrough, or automatic E2E runner is created. The isolated project stand documented by the project remains unused. Existing test and CI paths are extended only where the matrix requires them.

No before/after PNG is required because the specified change does not alter terminal tables, logs, progress, summaries, or browser UI. If implementation changes visible output, verification stops for a planning revision that defines equivalent baseline/candidate text and actual Mac PNG renders through bundled `scripts/render_terminal.swift` from `openspec-e2e-testing`.

## Verification matrix

| Case ID | OpenSpec requirement/scenario | Verification gap / local E2E decision | Public boundary / schema | Local test script | Independent Tester steps | CI disposition / job | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| V081-01 | Exact lineage, closed 225-node inventory, 196 responses, sole generator input | Contract/source checks close the gap; no live case | `contracts/sdk-contract.json`, generated projection | None; existing `scripts/upstream_contract.py` and source-link audit | Compare exact identities, counts, dispositions, repeated-render result, and clean Git | Extend contract checks in CI quality/contract gates | Exact provenance; `193+15+17=225`; one removed row; 196 verdicts; deterministic bytes | Commands, exits, exact SHA, contract/source links in Multica; no image |
| V081-02 | Paired updated-time filters and stable paging | Exact argv and transport-not-called tables are sufficient | `issues.list`, `IssueListFilter`, issue pages | None; extend existing issue resource tables | Inspect valid, missing, malformed, equal, reversed, and paged cases; run focused nodes | Existing unit/contract/component jobs | Both flags present unchanged; invalid pairs fail before transport | Test/file links and assertion summary; no image |
| V081-03 | Literal repeatable attachments; deferred steering guard | Fake CLI proves argv and public-surface guard proves deferral | Issue create/update and comment add bindings | None; extend existing `ArgvCase`/`CommandCase` rows | Inspect comma path and multiple-order rows plus absence of steering API | Existing non-live jobs | One flag per path; comma preserved; deferred signatures absent | Test/file links and assertions; no image |
| V081-04 | Projection-specific comment resolution | Old/new/invalid decoder rows are sufficient | Direct/flat/thread/recent comment projections | None; extend comment decoder/operation cases | Compare roots-only summary/since with other projections and run focused cases | Existing contract/component jobs | Roots fields preserved; other modes omit; tombstones/open enums retained | Fixture/test links and assertions; no image |
| V081-05 | Approved run-targeted retry replacement | Public boundary and fake CLI fully express migration; no live task needed | `issues.rerun_task`, task row decoder, public exports | None; extend issue resource and contract tables after approval | Inspect legacy removal, exact argv, scoped prefix, fresh flag, task decode, docs | Existing unit/contract/component jobs | No false issue mapping; exact run id/options; TaskRun result | API/migration/test links; no image |
| V081-06 | Task credits and attachment dimensions | Shared decoder fixtures are sufficient | Task-run usage and attachment result models | None; extend existing model matrices | Run old/new/null/omitted/invalid rows for both entrypoint families | Existing contract jobs | Additive fields accurate; all retained fields unchanged; invalid types fail | Fixture/test links and assertions; no image |
| V081-07 | Project creator, runtime concurrency, profile version, workspace pinning | Controlled model/input/order fixtures close every gap | Project, runtime, user profile, workspace list models | None; extend existing model/resource tables | Trace all 13 affected entrypoints, presence states, list-only projection, order | Existing unit/contract/component jobs | Old/new rows decode; open values retained; runtime absent/null/int distinct; pinned order stable | Fixture/test links and assertions; no image |
| V081-08 | Deferred groups and no silent expansion | Contract/public-export invariants are sufficient | Operation catalog and public package exports | None; extend existing public invariants | Compare added CLI evidence with approved operation/export inventory | Existing contract job | No workflow/view/project-workflow/concurrency-management/steering/process-control API | Contract/test links and assertions; no image |
| V081-09 | Repository gates, docs, package, exact-SHA publication | Existing CI is sufficient; long local suite moves unsplit to CI | Makefile, CI workflow, built wheel/sdist | None; existing repository commands | Fresh checkout; run focused checks; inspect linked CI/package/docs; verify remote SHA | `lint`, `types`, `quality`, compatibility, contract, package jobs as applicable | OpenSpec strict, Ruff, mypy, offline tests, live exclusion, docs/package, clean Git, SHA equality | Commands/exits and commit/MR/file/CI links in Multica; no raw log/image |

## Script, artifact, and CI contract

- No task-specific local E2E script or generated evidence file is permitted. Implementer extends existing test tables, fixtures, fake-CLI component rows, contract checks, and CI only.
- Product test code and necessary fixtures belong in the normal implementation commits. If a verified Git utility itself creates a functional commit, preserve it and link it without renaming it for evidence conventions.
- Automated local suites follow the ten-minute policy. A suite predicted to exceed or reaching ten minutes is stopped only for its owned process and run unsplit in GitHub Actions on the exact published revision; it is not split to evade the limit.
- Commands, exit codes, assertion summaries, exact SHAs, MR/commit/file/CI links, and applicable image attachments are published in Multica and read back. Raw logs, diagnostic JSON, hashes, provenance dumps, environment dumps, private hosts, personal data, and screenshots are not committed.
- JSON enters Git only when it is an actual product contract/fixture or generated functional result under test, never merely as execution evidence.

## Independent Tester contract

- Tester uses a fresh checkout at the published candidate SHA and does not edit implementation, CI tests, fixtures, or documentation.
- Tester maps V081-01 through V081-09 to concrete tests and assertions, executes focused lower-level commands, inspects deterministic fixtures and source/contract links, and verifies exact-revision CI. A second invocation of the same automatic test is not treated as an independent manual check.
- PASS is case-specific and records candidate SHA, material fixtures, test paths, commands, exit codes, assertions, and links. A new SHA requires impact assessment and rerunning only affected cases; uncertain impact leaves the case unverified.
- The final Multica comment contains normal development MR/commit/file links, CI links, sanitized evidence, and applicable attachments, followed by read-back. Cleanup removes only run-owned local diagnostics while preserving branch, MR, commits, CI, and Multica evidence; it does not close, merge, or delete the branch.

## Verification ownership

- Implementer owns tasks 1.1 through 6.2, including approved contract, generated projection, production code, all lower-level tests/fixtures, CI adjustments, documentation, packaging, and publication proof.
- Independent Tester owns tasks 6.3 and 6.4, executing and publishing evidence without editing product or verification artifacts.
- Plan Verifier owns planning acceptance. Human approval of the breaking retry contract remains a separate gate before implementation assignment.

## Estimate basis

The authoritative totals are stored only in the root planning issue properties. The estimate covers remaining work for one experienced developer familiar with the Python/CLI stack, without AI acceleration, from the exact planning base through implementation, required tests, documentation, package verification, publication, and likely review repairs. It excludes unattended CI duration, approval queues, meetings, and external blocking.

Confidence and calibration are documented without duplicating numeric totals. Tests were not run for planning or estimation.

Confidence is medium and calibration is unavailable. Acceptance is explicit, current code and close prior upgrade artifacts are inspectable, and all affected paths use established patterns. Material uncertainty remains in the large approved-contract edit, the cross-cutting response fixtures, the public retry removal/migration, and likely repair cycles across public-surface, typing, packaging, and source-link gates. There is no comparable developer-hour history, so the estimate is uncalibrated. The primary drivers are:

- contract and architecture: closing the complete command/response dossier and updating the sole generator input without admitting deferred surfaces;
- implementation and verification: preserving old/new/null/omitted/open-value behavior across several shared models and their bound relations;
- delivery: migrating a breaking public method, updating documentation/package evidence, and absorbing exact-revision review fixes.

The estimate excludes unattended CI duration, the human approval queue, and external outages. It becomes invalid if the human gate approves any currently deferred command group, retains issue-targeted retry through a new compatibility mechanism, changes the effective base, or requires live `0.8.1` stand evidence.

## Delivery topology

`delivery_mode=dag` because the authoritative `Estimate, hours` property exceeds the single-package threshold and a genuine parallel frontier exists after the shared contract/generated foundation. Dependencies are direct only, task coverage is complete and non-overlapping, and stages are consecutive topological layers.

Stage mapping: `WP-1 -> 1`, `WP-2 -> 2`, `WP-3 -> 2`, `WP-4 -> 2`, `WP-5 -> 3`.

### WP-1 — Approved contract and generated foundation

- `stage`: 1
- `depends_on`: none
- OpenSpec task coverage: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1
- Deliverable: one validated `0.8.1` approved contract with closed CLI/response manifests, compatibility metadata, source/test references, and a deterministic generated projection consumed by every downstream package.
- Owned responsibility scope: `contracts/sdk-contract.json`; strictly required contract schema/validator/render/source-link tooling; `src/multica_py/_generated/approved_sdk.py`; central generated operation/vector metadata; directly related contract fixtures and tests. These are the graph's critical shared files.
- Contract surface: exact release/source/binary lineage; `209 -> 225` command accounting; 196 response verdicts; compatibility interval; retry replacement metadata; deferred-surface exclusions; generated signatures, bindings, validators, responses, and source references.
- Definition of done/evidence: contract schema and pinned-source validation, diff classification, source-link audit, two byte-identical renders, check-mode freshness, operation completeness, and clean Git evidence boundaries.
- Parallel-safety rationale: every shared contract/generated write is centralized before domain work begins, preventing sibling races in the largest conflict surface.

### WP-2 — Issue inputs, comments, and retry migration

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 2.1, 2.2, 2.3, 2.4, 2.5
- Deliverable: paired updated-time filters, literal attachments, roots-only resolution projection, approved run-targeted retry, and public-surface deferral guards through existing issue/comment resources.
- Owned responsibility scope: issue and comment resource/input/wire/model paths; issue/comment operation cases; focused public-surface and migration tests; directly related fixtures and docs fragments. It consumes and does not rewrite WP-1 contract/generated outputs.
- Contract surface: RFC3339 interval validation; exact repeatable attachment argv; projection-specific resolution fields; `rerun_task` signature/TaskRun result; absence of steering and other deferred issue APIs.
- Definition of done/evidence: focused exact-argv, transport-not-called, old/new/invalid decode, public export, bound behavior, and migration tests pass with no false issue-targeted retry.
- Parallel-safety rationale: issue/comment production and test zones are distinct from WP-3 task/attachment models and WP-4 project/runtime/profile/workspace models.

### WP-3 — Task usage and attachment result extensions

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 3.1, 3.2
- Deliverable: additive task credit usage and image dimension decoding across all affected retained entrypoints.
- Owned responsibility scope: shared task-run usage and attachment result wire/model adapters; agent-task, issue-run, upload, and upload-bytes decoder tables; domain-specific fixtures and tests. It does not edit issue retry/comment paths or WP-4 domains.
- Contract surface: optional integer `credits_micros`; optional image `width`/`height`; baseline omission; retained tokens/costs/timestamps/result/error/pagination; invalid wire types.
- Definition of done/evidence: all three task/attachment response families pass old/new/null-or-omitted/invalid matrices and public compatibility invariants.
- Parallel-safety rationale: its shared models and fixtures do not overlap the production write zones owned by WP-2 or WP-4; central contract/generated metadata remains read-only.

### WP-4 — Project, runtime, profile, and workspace projections

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 3.3, 3.4, 3.5, 3.6
- Deliverable: creator identity, nullable runtime concurrency with presence-aware update input, profile version state, and list-only workspace pinning/order through existing resource/model patterns.
- Owned responsibility scope: project, runtime, user-profile, and workspace resource/entity/wire/model paths plus their focused relation, operation, decode, ordering, and validation tables. It consumes WP-1 outputs and does not edit WP-2 or WP-3 domains.
- Contract surface: seven project-returning paths; three runtime paths with unset/int/null semantics; two profile paths; workspace-list-only `pinned_at`; bound relations and open values.
- Definition of done/evidence: old/new/null/omitted/unknown/invalid matrices, runtime range and transport-not-called negatives, list-order assertions, and bound public invariants pass.
- Parallel-safety rationale: the four related model families share established projection patterns while remaining file-disjoint from the other stage-2 packages.

### WP-5 — Integration, documentation, package, and exact-SHA evidence

- `stage`: 3
- `depends_on`: WP-2, WP-3, WP-4
- OpenSpec task coverage: 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.4
- Deliverable: one coherent scenario-to-test map, complete documentation/package/CI gates, exact-SHA publication, integration repairs, and independent Tester evidence.
- Owned responsibility scope: cross-domain case tables/helpers after siblings complete; compatibility/API/migration/coverage/changelog/release docs; CI workflows when required; package verification; publication proof; Multica evidence coordination. It may make necessary integration repairs across completed predecessor areas and records them explicitly.
- Contract surface: all V081 cases; test-layer sufficiency; deferred-surface documentation; package contents; exact local/remote SHA; CI and independent evidence/read-back contract.
- Definition of done/evidence: focused and required repository gates pass under the ten-minute/CI rule; every scenario maps to a concrete assertion; package/docs are consistent; remote SHA equals verified SHA; independent evidence is attached and read back in Multica with no live claim or committed diagnostics.
- Parallel-safety rationale: integration begins only after all stage-2 siblings finish, so shared helpers, documentation, CI, and cross-domain fixes cannot race active sibling writes.

## Frontier validation

- Stage 1 frontier: WP-1 only, establishing the single shared contract/generated authority.
- Stage 2 frontier: WP-2, WP-3, and WP-4 are mutually independent with disjoint production and domain-test write zones.
- Stage 3 frontier: WP-5 integrates completed siblings and performs delivery/evidence work.

The graph therefore has a real three-way parallel frontier. WIP remains an operational Manager policy and is not encoded as dependencies or extra stages.
