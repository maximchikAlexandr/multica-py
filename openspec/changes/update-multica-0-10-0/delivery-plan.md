## Delivery contract

- Change: `update-multica-0-10-0`
- Planning issue: `MYL-666`
- Planning base: `b268e3bec0436fe51727fda50583344f57663284`
- Planning base tree: `6fb22297ab62a86b591dc058fdc7a03b107c97fd`
- Upstream baseline: Multica `0.7.1` at `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`
- Upstream target: Multica `0.10.0` release `446890529` at `2fcb424b72b024f65161809081009063846ea44d`
- Development repository: `https://github.com/maximchikAlexandr/multica-py`
- Estimate source of truth: root planning issue properties `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours`; this file intentionally contains no numeric estimate totals.
- Planning authority: proposal, design, delta specs, and tasks in this change. Operational status and assignees remain in Multica.

## E2E decision

`e2e_required=true`.

Unit/contract/fake-CLI tests are sufficient for deterministic argv, validation, wire decoding, generation, and documentation, but they cannot prove the combined target executable, SDK subprocess, isolated authentication/profile, membership-only private visibility, no-body cancellation, and destructive-conflict behavior. One focused repository-native script, `scripts/e2e_multica_010.py`, closes that gap against the project test stand. It uses public SDK operations, `multica-test`, a dedicated test profile/daemon, disposable resources, and failure-safe cleanup. It accepts environment-specific bindings as parameters and never embeds private URLs, hostnames, tokens, or personal data.

The independent Tester also performs fresh manual public actions and inspects outputs and remote state; invoking the script twice is not an independent walkthrough. The existing GitHub exact-PR-head live workflow is updated by Implementer to require observed CLI `0.10.0`. Tester does not edit product tests or fixtures.

No before/after PNG is required: the change does not alter human-facing terminal tables, logs, progress, summaries, browser UI, or Mac-specific rendered output. Genuine machine-readable text and state observations provide the relevant evidence. If implementation unexpectedly changes visible output, verification is blocked until equivalent baseline/candidate text and real PNG captures are planned and produced with an available renderer.

## Verification matrix

| Case ID | OpenSpec requirement / scenario | Verification gap and E2E decision | Public boundary / schema | Local script | Independent Tester actions | CI disposition / job | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| V100-01 | Exact provenance; `209→246`; `196/196`; deterministic generation | Lower-level checks are sufficient; no live case | Approved contract and generated projection | None | Compare exact identities, dispositions, response count, source links, and two render digests from a fresh checkout | Extend existing contract/required checks | Exact commits/digests/counts; zero pending; second render identical; check mode clean | Commands, exit codes, contract/commit links, digests; no image |
| V100-02 | Retained additive fields; omitted/null/present/malformed; open values | Lower-level decode tables are sufficient | Existing wire/public models and page types | None | Inspect table mapping and run focused decode/model tests | Existing test job with extended tables | Legacy omission decodes; null semantics preserved; malformed present values fail; valid unknown tokens survive | Focused test output and file/commit links; no image |
| V100-03 | Private membership, project activity/archive/list pagination, subscriber delivery | Real authorization and omission require the isolated stand | Public project/issue/subscriber SDK calls and target CLI JSON | `scripts/e2e_multica_010.py --case private-project` | Create disposable private project and member/non-member identities in the test workspace; compare member get/list with privileged non-member not-found/omission; inspect `has_more`, activity/archive, `project_covered`, and delivery fields; remove resources | Extend exact-PR-head live smoke where protected fixture identities exist; otherwise local E2E remains authoritative for auth boundary | No private disclosure; correct list envelope/order/presence; subscriber inheritance exact; cleanup confirmed | Sanitized JSON projections, command/exit record, tested SHA, MR/commit links; no image |
| V100-04 | `rerun-task` resume/fresh migration | Real task lifecycle and result require target process/backend | Public issue/task-run SDK operation and `issue rerun-task` CLI | `scripts/e2e_multica_010.py --case rerun-task` | Create a disposable run, invoke one approved resume/fresh path independently, inspect identity/result ordering, and confirm removed issue-targeted command is not used | Extend live smoke with disposable task fixture; unit/component rows remain mandatory | Exact task/run identity; mode selector correct; typed result; negative missing/conflicting inputs fail before I/O; cleanup confirmed | Sanitized task/run IDs, outputs, commands, exit codes, links; no image |
| V100-05 | Literal inline/file/stdin/empty/omitted text and metadata escaping | Real subprocess and server persistence require target CLI | Public issue/comment/update and metadata SDK calls | `scripts/e2e_multica_010.py --case text-metadata` | Use disposable records and equivalent literal-backslash/multiline/empty/omitted fixtures; read state back through a separate public call; test slash/percent/space/Unicode metadata keys; delete fixtures | Existing fake-CLI tests plus focused live case | Exact stored text; at most one trailing LF removed; omission preserves prior value; escaped key round-trips as one key; no path injection | Sanitized before/action/after text, hashes, commands, exit codes, links; no image |
| V100-06 | No-body `499`; archived-project `409`; bounded runtime-delete conflicts | Real status/body/process behavior requires target backend; destructive cases need fail-closed observation | Public SDK exception surface and target process exit | `scripts/e2e_multica_010.py --case errors` | Trigger only disposable, pre-authorized cancellation/conflict fixtures; inspect typed exception and unchanged remote state; do not retry; verify cleanup handle before deletion | Extend exact-PR-head live smoke only for safely reproducible fixtures; fake-CLI error tests always run | `499` maps without JSON-shape failure; `409`/runtime conflicts map typed diagnostics; no retry/follow-up mutation; secrets redacted | Sanitized exception class/message, process exit, state assertions, cleanup record, links; no image |
| V100-07 | Webhook filter constraints; deferred surfaces; docs/package/forbidden content | Lower-level pre-I/O and repository audits are sufficient | Existing builders, exports, docs, wheel/sdist | None | Run invalid cases and inspect fake CLI received no command; inspect valid argv and public export inventory; audit packages | Existing required/package jobs with extended fixtures | Requires/conflicts exact; valid repeated values exact; deferred methods absent; docs consistent; evidence/HTML absent from package | Test/package output and file/commit links; no image |

## Script and environment contract

- Implementer owns `scripts/e2e_multica_010.py` and any directly related safe fixtures/tests. The script uses the repository's Python/pytest conventions and public SDK only; it does not add a runner framework.
- Entry command template: `uv run python scripts/e2e_multica_010.py --case <case> --candidate-sha <full-sha> --cli multica-test --profile <isolated-profile> --output-dir <run-owned-dir>`.
- Required parameterized inputs: test server/workspace identifiers, dedicated profile/daemon handle, disposable actor/resource identifiers, candidate product SHA, test-code SHA, and output directory. Secret values are read through the test context and never printed.
- Readiness gate: clean exact candidate checkout; remote SHA equality; script/test-code revision recorded; `multica-test version --output json` reports `0.10.0`; executable resolves to the isolated test installation; profile/server/workspace differ from primary values; dedicated daemon is healthy; focused offline checks pass; run-owned output directory is empty; cleanup permissions are confirmed.
- The script writes compact sanitized projections with scenario, candidate SHA, test-code SHA, CLI version, command identifier, exit status, assertions, and cleanup state. It excludes environment dumps, tokens, cookies, private hostnames, personal data, binaries, and unrelated logs.
- Each case creates unique disposable resources, records exact resource IDs only in access-controlled evidence, and registers cleanup immediately after creation. Failure-safe cleanup runs on success, assertion failure, interruption, and partial setup. Runtime deletion is attempted only for the script-owned validated runtime handle.
- A case is PASS only when all assertions and cleanup pass at the recorded product revision. A changed product revision requires impact assessment and rerun only for affected cases; unresolved impact leaves the case unverified.

## CI and ownership contract

- Implementer extends existing unit/contract/component/package tables and `.github/workflows/live-smoke.yml` (or its current repository-equivalent path) as OpenSpec tasks 4.1–4.4. Tester verifies coverage and does not modify these files.
- CI resolves an open same-repository PR head, checks out its full SHA, revalidates it before and after the run, observes CLI `0.10.0`, limits credentials to the protected test environment, and uploads only a sanitized allowlist.
- Automated local suites expected to exceed or reaching ten minutes are stopped without splitting and run unsplit in GitHub Actions at the published exact revision. Manual Tester walkthroughs are not subject to that automated-suite limit.
- Normal development results, test scripts, fixtures, generated product files, and real commits stay in Git. Real logs, outputs, diagnostic JSON, SHA/hash evidence, screenshots, command transcripts, and assertion results are attached only in Multica.

## Independent evidence and cleanup

Tester publishes one final Multica comment containing the candidate SHA, test-code SHA, observed CLI version, scenario outcomes, exact commands and exit codes, assertion summary, CI/MR/commit/file links, cleanup result, and no-image rationale. Relevant sanitized output files are attached to that comment and read back to prove accessibility. The comment contains no numerical planning estimate.

Cleanup removes disposable stand resources, run-owned local output, and dedicated transient daemon state while preserving the evidence MR/branch/commits. It does not close/merge the MR or delete its branch without separate authorization. Missing readiness, required auth isolation, target CLI identity, cleanup capability, or evidence read-back blocks verification rather than downgrading E2E.

## Delivery topology

`delivery_mode=dag` because the authoritative `Estimate, hours` property is above the topology threshold and the work has two genuine non-conflicting parallel fronts. Exact estimate totals exist only in the root issue properties.

Estimate basis: remaining work from planning base for one experienced developer familiar with the Python/SDK stack, without AI acceleration. Confidence is medium and calibration is uncalibrated: the package and implementation seams are inspectable, but the breadth of target response adaptations, live authorization fixtures, and review repair is material. Evidence includes the `42,448`-line approved contract, `196` response entrypoints, existing resource/wire/test seams, prior upgrade commits, and the current live workflow. No tests were run for estimation.

Stage mapping (to be copied to each WP child issue): `WP-1 -> 1`, `WP-2 -> 2`, `WP-3 -> 2`, `WP-4 -> 3`, `WP-5 -> 3`, `WP-6 -> 4`, `WP-7 -> 5`. Stages are consecutive topological layers; no live status or assignee is stored here.

### WP-1 — Approved contract foundation

- Tasks: `1.1`, `1.2`, `1.3`, `1.4`, `1.5`.
- Stage: `1`.
- Depends on: none.
- Deliverable: one reviewed `0.7.1` to `0.10.0` approved contract and byte-stable generated projection with complete command/response dispositions.
- Owned responsibility: `contracts/sdk-contract.json`, `src/multica_py/_generated/approved_sdk.py`, directly related generator validation/render/source-link fixtures, and contract-specific tests. Critical shared contract/projection files are frozen for downstream WPs after this WP.
- Contract surface: exact provenance/compatibility; `209→246` command registry; `196/196` response registry; retained/adapted/removed/deferred/not-SDK-surface policy; generated operation/type identifiers and source/test references.
- DoD/evidence: contract validate/render/check; second render byte equality; exact counts/digests/source links; no evidence-driven generation; focused contract tests; reviewable commit.
- Parallel safety: foundation is intentionally exclusive because all downstream model, command, test, and documentation work consumes its stable identifiers and decisions.

### WP-2 — Response models and privacy projections

- Tasks: `2.1`, `2.2`, `2.3`, `2.4`.
- Stage: `2`.
- Depends on: `WP-1`.
- Deliverable: backward-compatible public/wire/entity adaptation for target response fields, project privacy/activity/pagination, and subscriber delivery.
- Owned responsibility: `src/multica_py/models/**`, `src/multica_py/entities/**`, relevant `_internal/*_wires.py` and decoders, model/decode/presence tests and fixtures. It does not edit resource command builders, shared transport/errors, consolidated operation tables, or CI.
- Contract surface: field names/types; omitted/null/present/malformed policy; open value handling; page `has_more`; private get/list omission; `project_covered` and delivery semantics.
- DoD/evidence: focused model/wire tests cover every changed field state and older-server fixture; no private disclosure; mypy/Ruff for owned paths; no edits to the frozen approved contract.
- Parallel safety: runs beside `WP-3`; its write zone is model/entity/wire decoding, while `WP-3` owns command/transport seams.

### WP-3 — Command migration and transport safety

- Tasks: `3.1`, `3.2`, `3.3`, `3.4`, `3.5`.
- Stage: `2`.
- Depends on: `WP-1`.
- Deliverable: explicit run-targeted rerun API plus literal/presence-safe text, metadata/webhook validation, and typed cancellation/archive/runtime-delete errors.
- Owned responsibility: `src/multica_py/resources/**`, `src/multica_py/_internal/transport.py`, `src/multica_py/exceptions.py`, public exports needed by rerun-task, and focused argv/transport/error tests. It does not edit model/entity/wire files owned by `WP-2`, consolidated operation tables, docs, or CI.
- Contract surface: `rerun_task[_command]` signature and result; exact argv/stdin channels; path escaping; webhook constraints; `499`/`404`/`409` and bounded destructive conflict mapping; no issue-to-run inference.
- DoD/evidence: positive/negative command rows; invalid calls prove no process invocation; typed error/redaction/no-retry assertions; mypy/Ruff for owned paths; no legacy issue-rerun alias.
- Parallel safety: runs beside `WP-2` with disjoint production seams; any required wire-type addition is agreed through the WP-1 contract and landed by `WP-2` before integration.

### WP-4 — Consolidated tests, CI, and E2E script

- Tasks: `4.1`, `4.2`, `4.3`, `4.4`.
- Stage: `3`.
- Depends on: `WP-2`, `WP-3`.
- Deliverable: complete cross-surface operation/fake-CLI tables, exact-head CLI `0.10.0` live workflow, and the safe repository-native E2E script.
- Owned responsibility: `tests/cases/**`, `tests/component/**`, cross-surface `tests/unit/**`, safe E2E fixtures, `scripts/e2e_multica_010.py`, and `.github/workflows/live-smoke.yml` or current equivalent. Direct tests already owned by predecessor WPs are extended only where consolidation requires one shared table.
- Contract surface: public-operation completeness; canonical/noncanonical case mapping; live workflow authorization/SHA contract; script parameters, sanitized artifact schema, readiness, and cleanup.
- DoD/evidence: every changed contract row maps to a case; fake CLI sees no invalid invocation; workflow tests prove exact-head and `0.10.0`; script self-checks prove parameter validation/sanitization/cleanup without contacting the stand during implementation tests.
- Parallel safety: runs beside `WP-5`; it owns tests/scripts/CI while `WP-5` owns prose documentation only.

### WP-5 — Compatibility and migration documentation

- Tasks: `5.1`.
- Stage: `3`.
- Depends on: `WP-2`, `WP-3`.
- Deliverable: consistent compatibility, API, migration, coverage, changelog, contribution, packaging, and release documentation.
- Owned responsibility: `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/**`, and directly related documentation checks. It does not edit product code, tests, generated files, workflow YAML, or OpenSpec planning artifacts.
- Contract surface: target/support envelope; rerun-task migration; retained adaptations; deferred families; E2E/CI usage and evidence boundaries.
- DoD/evidence: source-link and docs checks pass; examples name only approved public APIs; no private stand values or unsupported method claims; documentation commit is independently reviewable.
- Parallel safety: prose-only write zone is disjoint from the tests/scripts/CI owned by `WP-4`.

### WP-6 — Integrated repository verification

- Tasks: `5.2`, `5.3`, `5.4`.
- Stage: `4`.
- Depends on: `WP-4`, `WP-5`.
- Deliverable: one consolidated checked revision with all required offline, typing, lint, contract, docs, package, and CI evidence ready for independent verification.
- Owned responsibility: integration fixes across directly related code/tests/docs when a required gate exposes a defect, verification command records, and normal publication of the exact candidate revision. It does not broaden scope or alter planning topology.
- Contract surface: strict OpenSpec and approved-contract gates; operation completeness; live-test collection isolation; package contents/imports; ten-minute local automated-suite rule; exact remote SHA.
- DoD/evidence: all focused gates pass; full non-live suite passes locally within limit or unsplit in CI at exact SHA; forbidden artifacts absent; local/remote candidate SHA equality recorded.
- Parallel safety: integration is serialized after both stage-3 deliverables to avoid competing repair commits and to verify one consolidated revision.

### WP-7 — Independent stand verification and delivery evidence

- Tasks: `6.1`, `6.2`, `6.3`, `6.4`.
- Stage: `5`.
- Depends on: `WP-6`.
- Deliverable: independent target-stand verdict and a read-back-verified Multica evidence comment/attachments for the exact published revision.
- Owned responsibility: isolated Tester profile/daemon/stand resources, execution of the committed script, fresh manual public actions, sanitized evidence staging outside Git, cleanup, and evidence publication. Tester does not edit product code/tests/fixtures or merge/close/delete delivery refs.
- Contract surface: readiness gate; V100-03 through V100-06 live cases; exact product/test-code/CLI identities; PASS/FAIL assertions; cleanup; no-image rationale; evidence accessibility.
- DoD/evidence: readiness passes; required script/manual cases have explicit outcomes; disposable resources and transient files are cleaned; MR/branch/commits preserved; final comment and attachments are read back; unresolved gaps are reported without claiming PASS.
- Parallel safety: final external verification is serialized on the exact consolidated SHA and cannot start from intermediate sibling revisions.

## Coverage and frontier audit

Every OpenSpec task is owned exactly once: `1.1–1.5` by `WP-1`; `2.1–2.4` by `WP-2`; `3.1–3.5` by `WP-3`; `4.1–4.4` by `WP-4`; `5.1` by `WP-5`; `5.2–5.4` by `WP-6`; `6.1–6.4` by `WP-7`. Direct dependencies contain no transitive-only edges.

Executable frontiers are: stage 1 `{WP-1}`; stage 2 `{WP-2, WP-3}`; stage 3 `{WP-4, WP-5}`; stage 4 `{WP-6}`; stage 5 `{WP-7}`. Two stages contain independent parallel work with non-conflicting primary write zones, so the graph is not a linear chain and remains eligible for DAG delivery.
