## Delivery contract

- Change: `update-multica-0-11-1`
- Planning issue: `MYL-670` (`01a1fc4f-716c-7121-9d93-d6d5583a971d`)
- Planning base: `b268e3bec0436fe51727fda50583344f57663284`
- Upstream baseline: Multica `0.7.1` at `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`
- Upstream target: Multica `0.11.1` release `451169000` at `e1fe10d6694848e35dd1aa00e08cd11d93e545ac`
- Estimate source of truth: root planning issue properties `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours`; this file intentionally contains no numeric O/M/P/E totals.
- Planning authority: proposal, design, delta specs, tasks, and this delivery contract. Live status and assignees remain in Multica.
- Human gate: no implementation child, implementation code, or implementation PR is authorized until explicit approval.

## E2E decision

`e2e_required=false`.

No material acceptance result requires a real backend, database, browser, persistent identity, interactive terminal, or visible-output capture. The change governs deterministic SDK contract data, explicit argv/body mappings, typed response decoding, presence/error policy, compatibility, documentation, and packaging. Existing contract validation, frozen operation tables, fake-CLI component boundaries, controlled pagination/content/error fixtures, type checks, package checks, and ordinary CI can prove every changed scenario at a sufficient lower layer.

The repository's generic live suite is pinned to a separately prepared older target and is neither extended nor required. The project test stand URL from project context is therefore not used. No task-specific script, profile, daemon, container, database, port, credential, fixture account, or local E2E attempt is planned. This is a sufficiency decision, not a claim that a live `0.11.1` run passed.

No before/after image is required because the Python SDK change does not alter human-facing terminal tables, logs, progress, summaries, or browser UI. Exact argv and decoded results are machine-observable contract data. There is no renderer readiness gate, ANSI/TTY claim, image filename, or capture cleanup requirement.

## Verification matrix

| Case ID | OpenSpec requirement / scenario | Verification gap / local E2E decision | OpenAPI operation or schema | Local test script | Independent Tester steps | CI disposition / test or job | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| V111-01 | exact provenance; mixed provenance fails | Lower-level contract validation is sufficient; no live gap | None; CLI/source contract | None | Inspect full commit URLs and mutate one identity in an isolated fixture | `make contract`; `contract-check` | release/tree/archive/executable/version identity and full source pins match; mutation fails before render | Sanitized command/exit/file links in Multica; no image |
| V111-02 | 263 help nodes and five source-only names close exactly | Contract inventory and negative mutation prove closure | None | None | Compare approved counts/dispositions with issue dossier; inspect source-only rows | `tests/unit/test_upstream_contract.py`; `tests/contract/test_sdk_contract.py` | 209 baseline, 263 target, 55 added, one removed, 31 changed; five source-only decisions exact; zero pending/duplicate | Count/assertion summary in Multica; no image |
| V111-03 | 196 response rows receive one verdict | Registry validation and source audit are sufficient | Reviewed CLI JSON envelopes, not OpenAPI | None | Sample every changed family and verify full registry completeness assertion | contract/unit tests plus `scripts/audit_source_links.py` | 102 changed, 94 unchanged, unique old/target full-commit sources and SDK/test/doc action | Source/file links and assertion summary; no image |
| V111-04 | deterministic approved-contract generation | Double render/check proves the production boundary | None | None | Run check twice from clean checkout and inspect Git diff | `make contract`; `contract-check` | byte-identical generated projection; evidence path cannot affect output; clean diff | Commands/exits and exact SHA; no generated JSON committed beyond approved functional outputs |
| V111-05 | legacy rerun migrates to `rerun-task` | Existing operation/canonical-vector tables close the gap | `issues.rerun` SDK operation | None | Construct command through public API and inspect exact plan; inspect absence of old binding | `tests/cases/operations.py`, operation/resource/contract tests | public signature/result retained; exact `issue rerun-task <id>` argv; no public `issue rerun` fallback | Exact argv assertion and code links; no image |
| V111-06 | new families remain deferred/non-surface | Public discovery and forbidden-symbol checks are sufficient | None | None | Inspect package exports, resource inventory, approved dispositions, and docs | public-surface/contract tests | no chat-wakeup, inbox, issue-status, view/workflow, batch/delete/linking, project-management, or runtime-concurrency symbols | Inventory assertion summary; no image |
| V111-07 | squad assignees and payload conditions | Existing frozen tables plus fake CLI prove mapping/validation | Autopilot/issue/trigger CLI JSON | None | Exercise public command construction with valid squad/conditions and invalid constraints | operation cases, autopilot model/trigger resource tests | discriminator/identity preserved; ordered mapping exact; omission differs from empty; invalid fails before I/O | Sanitized expected/actual assertion summary; no image |
| V111-08 | optional `run_outcome`, `daemon_id`, and open values | Typed wire/model tests are sufficient | Task/run/runtime/profile JSON schemas | None | Decode present/omitted/null/unknown/malformed fixtures from public paths | issue/autopilot/system model and resource tests | approved presence policy; unknown valid open value retained; malformed type raises output-shape error; no machine fallback | Fixture/code links; no image |
| V111-09 | literal text, stdin/file LF rule, NUL sanitization | Content helper, resource, and fake-CLI component checks prove distinct boundaries | Issue/workspace/user/comment CLI mutations | None | Inspect exact argv/stdin for literal backslashes, multiline, empty/omitted, and NUL cases | content/resource/component tests | literal inline text; one trailing LF rule; explicit empty vs omission; target sanitization not confused with local argv NUL rejection | Text assertion summary only; no terminal render or PNG |
| V111-10 | changed pagination and workspace `pinned_at` ordering | Controlled page fixtures close the interaction gap | Reviewed list envelopes | None | Traverse multi-page fixtures through public collection APIs and inspect list-only fields | collection/page/resource/component tests | no duplicates/skips; correct terminal condition; optional RFC3339 decode; pinned-first order; non-list responses omit projection | Fixture/code links; no image |
| V111-11 | reviewed 400/409/413 errors and skill atomicity | Fake CLI and filesystem fixtures are sufficient | Standard error envelope | None | Trigger each fixture through public operations and inspect sanitized exception/prior state | transport-error/resource/component tests | typed status/code/message; generic unknown fallback; no retry/private detail; 413 preserves prior complete skill bundle | Assertion summary; no raw stderr/private payload attachment |
| V111-12 | compatibility floor/target/ceiling | Existing compatibility preflight tests are sufficient | CLI version JSON | None | Exercise boundary versions and one operation-level gate from clean checkout | `make compat`; `compatibility` matrix | floor `0.6.2`; maximum tested `0.11.1`; strict rejection at `0.11.2`; intermediate SDK release not required | Commands/exits and matrix links; no image |
| V111-13 | docs/package claims match contract | Typed documentation and artifact inspection are sufficient | Distribution metadata | None | Compare migration/API/changelog/generated constants and inspect wheel/sdist contents | docs contract tests; `make package`; `package-test` | direct migration and rollback coherent; deferred families absent; generated runtime packaged; transient evidence excluded | Package workflow/commit/file links; no binary attachment required |
| V111-14 | full release gate and exact revision | Existing CI is required for any suite expected over ten minutes | None | None | From fresh checkout verify remote SHA, run focused checks, inspect CI jobs and clean tree | `lint`, `types`, `quality`, `compatibility`, `contract-check`, `package-test` | all required jobs refer to candidate SHA; local/remote equality; no split suite; no untracked evidence | PR/commit/CI links, commands/exits, limitations, cleanup in Multica; no image |

## Test code and ownership

Implementer owns all required edits to contract schema/data, generator, generated projection, source links, resources, models, wire adapters, tests, fixtures, fingerprints, docs, package assertions, and existing CI workflows. Tester does not edit implementation tests or fixtures; Tester independently inspects their coverage, executes the agreed focused checks, verifies CI/package results, and reports findings.

No new local E2E script is created. Existing automatic checks remain in their current paths and runners. Product implementation, test/fixture updates, and generated functional outputs are committed according to their natural results. Real logs, diagnostic JSON, hashes, command transcripts, provenance read-outs, and assertion reports are published only in Multica, not Git.

## Readiness, execution, evidence, and cleanup

Before independent verification, assert: exact candidate SHA is published; local and remote SHAs match; contract target/source links are exact; generated check mode is clean; focused checks pass; required CI jobs point to the candidate; and no `.devlocal` or diagnostic evidence is tracked. Automated local suites expected to exceed ten minutes run unsplit in GitHub Actions; if a local owned suite reaches ten minutes, stop only that process and retain the partial result as non-PASS context.

Tester uses a fresh checkout of the candidate SHA, performs the V111-01 through V111-14 public/contract inspections and focused commands, and records each PASS/FAIL against that exact revision. A later product revision requires impact assessment and rerun of affected cases; unresolved impact leaves the case unverified. A second invocation of the same test is not a manual check.

The final Multica comment SHALL include PR/commit/file/CI links, exact candidate SHA, commands, exit codes, material assertions, limitations, no-live/no-image rationale, and cleanup status. Comment and attachment read-back SHALL confirm accessibility. Private URLs, hostnames, profiles, credentials, tokens, personal data, environment dumps, raw logs, and diagnostic JSON SHALL not be published or committed.

Cleanup removes run-owned build/test output and any isolated test checkout or environment while preserving the evidence branch, PR, commits, CI links, and Multica attachments. Merge, PR closure, branch deletion, and deletion of durable evidence require separate authority.

## Ponytail full scope audit

| Planned addition | Requirement or unique risk | Existing seam | Why the current state is insufficient |
|---|---|---|---|
| Contract/provenance refresh | Exact 263-node and 196-response closure | `contracts/sdk-contract.json`, `tools/upstream_contract/`, `scripts/upstream_contract.py` | Current data and hard validation are pinned to `0.7.1` and assert no changed response rows |
| Rerun command migration | Target removes public `issue rerun` | `IssueResource.rerun`, generated binding, canonical operation cases | Existing exact argv invokes the removed command |
| Input and text adaptations | 31 changed help nodes and target content semantics | explicit resource methods, `_internal/content.py`, presence sentinels | Current mappings/fixtures encode the old flags and text behavior |
| Response/model adaptations | 102 changed response rows, including optional/open fields | private wire structs, explicit adapters, frozen/public models | Current models and response registry do not represent the reviewed target deltas |
| Error and pagination regressions | Reviewed 400/409/413 and changed page/order behavior | shared transport exceptions, page models, fake-CLI component fixtures | Existing cases cannot prove the new target error shapes and traversal/order contracts |
| Test and evidence expansion | Every changed/retained row requires an oracle | `tests/cases/operations.py`, fingerprints, unit/contract/component suites | Existing closure asserts the `0.7.1` inventory and zero changed response rows |
| Documentation/package/CI refresh | Direct migration, exact source checkout, distribution truthfulness | current docs, packaging tests, `contract-check`, package workflows | Current claims and CI source preparation target `0.7.1` |

No second generator, registry, transport, versioned resource layer, dependency, public candidate family, live runner, screenshot flow, or intermediate-release delivery phase survives this audit. Tests, fixtures, generated projection, docs, and CI changes remain only where they close a named requirement or regression risk.

## Estimate contract

The mandatory `estimate-openspec` assessment measures remaining active developer-hours for one experienced developer familiar with Python, msgspec, pytest, and this repository, without AI acceleration. Exact optimistic, weighted, and pessimistic totals are authoritative only in the root planning issue properties named in the delivery contract.

Confidence is medium and calibration is uncalibrated. Evidence is strong for the current architecture, exact target dossier, frozen operation cases, contract validator/renderer, and CI/package seams. Uncertainty remains coupled across the large response registry: a shared wire/presence correction can move several domain rows together, target text sanitization crosses local and server boundaries, and preserving the older compatibility floor may expose repairs beyond the direct target fixtures. Tests were not run for the estimate; source, tests, workflows, OpenSpec artifacts, and the approved contract were inspected.

The estimate covers contract/provenance reconciliation, command/input adaptation, typed response/error/pagination work, table-driven and focused component coverage, documentation/package/CI updates, integration repair, and independent-verification preparation. It excludes unattended CI time, approval queues, human response delay, implementation scheduling, new deferred families, live infrastructure, and persistent-data migration. A scope decision to publish any deferred family, close target-owned enums, add a transport, or drop/preserve a materially different compatibility envelope invalidates the estimate.

## Delivery topology

`delivery_mode=dag`.

The estimate property exceeds the multi-WP threshold. The graph has one real parallel execution frontier: after the approved contract and product adaptation are stable, test/fixture closure and documentation/CI preparation can proceed independently with disjoint critical write zones. Final release/evidence work fans in from both. Stages are topological layers, not WIP limits.

Stage mapping: `WP-01-contract-foundation -> 1`, `WP-02-product-adaptation -> 2`, `WP-03-test-closure -> 3`, `WP-04-docs-ci -> 3`, `WP-05-release-evidence -> 4`.

Every OpenSpec task is covered exactly once below. Directly related tests, fixtures, snapshots, docs, generated files, and service files follow the owning WP unless an active sibling explicitly owns them.

### WP-01-contract-foundation

- **Stage:** 1
- **Depends on:** none
- **Task coverage:** 1.1–1.6, exactly once.
- **Deliverable:** one validated approved-contract foundation containing exact target provenance, complete command/source-only/response decisions, compatibility policy, validator closure, and deterministic generated projection.
- **Owned responsibility scope:** `contracts/sdk-contract.json`; contract schema/loader/validator/renderer; source-link audit integration; generated projection; directly coupled contract/unit/mutation fixtures.
- **Critical shared files:** `contracts/sdk-contract.json`, `tools/upstream_contract/contract.py`, `scripts/upstream_contract.py`, `src/multica_py/_generated/approved_sdk.py`.
- **Contract surface:** 263 help nodes, five source-only identities, 196 response rows, exact provenance, compatibility bounds, approved-contract-only generation.
- **DoD / evidence:** strict contract validation closes exact counts and identities; full-commit links pass audit; render/check is byte-stable across two renders; generated projection is clean; review evidence remains untracked.
- **Parallel-safety rationale:** foundation is the sole stage-1 writer to shared contract/generated files and precedes every consumer.

### WP-02-product-adaptation

- **Stage:** 2
- **Depends on:** `WP-01-contract-foundation`
- **Task coverage:** 2.1–2.5 and 3.1–3.5, exactly once.
- **Deliverable:** existing SDK operations, models, adapters, pagination, content, and errors implement every approved changed row while deferred families remain absent.
- **Owned responsibility scope:** `src/multica_py/resources/`, `src/multica_py/entities/`, `src/multica_py/models/`, `src/multica_py/_internal/`, public exports, and narrowly coupled implementation fixtures needed to develop the product behavior.
- **Critical shared files:** issue/autopilot/workspace/runtime/profile/skill resources and models; wire adapters; shared content, decoder, and transport-error modules.
- **Contract surface:** rerun-task migration; squad/payload inputs; optional/open outcomes; machine binding; literal/file/stdin/NUL text semantics; page/order behavior; 400/409/413 errors; skill atomicity.
- **DoD / evidence:** exact public signatures and command plans match the approved contract; changed wire fixtures decode with correct presence; invalid inputs fail before I/O; sanitized errors and generic fallback remain stable; no candidate-family symbol or new architecture appears.
- **Parallel-safety rationale:** product source is owned by one WP after the contract foundation, avoiding cross-domain adapter conflicts.

### WP-03-test-closure

- **Stage:** 3
- **Depends on:** `WP-02-product-adaptation`
- **Task coverage:** 4.1–4.4, exactly once.
- **Deliverable:** complete frozen-table, fingerprint, unit, contract, and fake-CLI component coverage for all approved changes and retained invariants.
- **Owned responsibility scope:** `tests/cases/`, `tests/unit/`, `tests/contract/`, `tests/component/`, and directly related fake-CLI fixtures/snapshots; no docs or workflow edits.
- **Critical shared files:** operation cases and literal fingerprints, SDK-contract tests, domain model/resource tests, transport/content/page component fixtures.
- **Contract surface:** canonical vectors, exact argv, response/presence matrices, pagination, typed errors, public discovery, eager/command parity, deferred-family absence.
- **DoD / evidence:** V111-02 through V111-12 lower-level mappings are assertion-complete; fixture/fingerprint closure is exact; focused commands pass on one candidate revision; findings name missing rows rather than weakening completeness checks.
- **Parallel-safety rationale:** writes only test and fixture zones while stage sibling WP-04 owns docs/workflows; production source is frozen at the predecessor.

### WP-04-docs-ci

- **Stage:** 3
- **Depends on:** `WP-02-product-adaptation`
- **Task coverage:** 5.1–5.2, exactly once.
- **Deliverable:** coherent direct-migration/package documentation and exact-target CI source preparation using existing workflows.
- **Owned responsibility scope:** `docs/`, `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, packaging documentation/claims, and `.github/workflows/` contract/package preparation; no implementation or test-case edits.
- **Critical shared files:** compatibility/API/migration/coverage/release docs and `.github/workflows/ci.yml` exact target checkout.
- **Contract surface:** direct `0.7.1` to `0.11.1` migration and rollback, compatibility interval, rerun replacement, deferred families, exact source checkout, package claims.
- **DoD / evidence:** docs agree with approved/generated contract; no unsupported family or moving source link is claimed; existing CI fetches the exact target revision; package claims remain evidence-clean.
- **Parallel-safety rationale:** docs/workflow write zone is disjoint from WP-03 test/fixture zone, so both stage-3 WPs can proceed concurrently.

### WP-05-release-evidence

- **Stage:** 4
- **Depends on:** `WP-03-test-closure`, `WP-04-docs-ci`
- **Task coverage:** 5.3–5.4 and 6.1–6.4, exactly once.
- **Deliverable:** one clean, published, fully gated candidate with independent exact-revision verification and durable Multica evidence.
- **Owned responsibility scope:** final cross-tree reconciliation, required gate repairs, package/CI results, Git publication, independent verification handoff, Multica evidence/read-back, and failure-safe cleanup. Directly related repairs return to the owning area within this fan-in WP; no active sibling remains.
- **Critical shared files:** cross-cutting only as required to repair final gate failures; all prior WP outputs are inputs.
- **Contract surface:** strict OpenSpec/contract/source/test/type/lint/compat/package gates, unsplit CI policy, V111 matrix closure, local/remote SHA equality, evidence privacy and durability.
- **DoD / evidence:** every V111 case is PASS or blocks delivery at one exact published SHA; required CI/package jobs point to that SHA; remote equals local; repository is clean; Multica comment/attachment read-back succeeds; diagnostics are removed and durable Git/evidence records are preserved.
- **Parallel-safety rationale:** fan-in begins only after both stage-3 siblings complete; it is the sole final integrator and evidence owner.
