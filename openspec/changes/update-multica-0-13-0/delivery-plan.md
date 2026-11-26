## Delivery contract

- Change: `update-multica-0-13-0`
- Planning issue: `MYL-674`
- Base: `b268e3bec0436fe51727fda50583344f57663284`
- Target upstream: Multica `0.13.0`, release `457951728`, commit `35b54a3742bb51bdf5ffa688655367ec98044862`
- Estimate source: planning-issue properties `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours`; numeric totals intentionally live only in those properties.
- Estimate basis: remaining active developer work from this exact base to all acceptance criteria, one experienced project-familiar developer without AI acceleration; medium confidence because code seams and complete upstream audit are available, while the accumulated response/mapping volume and live privacy/access behavior create bounded uncertainty. Tests were not run while estimating.
- Delivery mode: `dag`; the `Estimate, hours` property exceeds the single-WP threshold and stages 2 and 3 each contain genuinely independent write-safe fronts.

## Ponytail gates

Before design, the change was reduced to existing contract, generator, resource/model/wire, frozen-case, documentation, and CI seams. No new runtime dependency, generator, resource hierarchy, blocker graph cache, closed upstream enum registry, or test framework is planned.

After the E2E plan, the live scope remains only the interactions lower-level checks cannot prove: hidden blocker counts/privacy, authoritative graph failures, `leader|direct` handoff round-trip, task document attribution/access, and rerun-task replacement. All other cases stay in existing lower-level tables and CI. The existing `scripts/e2e/verify_multica_test.py` harness is extended; no parallel runner or evidence/cleanup framework is introduced. Each production, test/evidence, and WP addition has a unique requirement/risk and an existing seam identified in `design.md`.

## E2E decision

`e2e_required=true` because real backend authorization and lifecycle state determine whether hidden blocker counts leak identities, whether cycle/cross-workspace constraints hold, whether `leader|direct` handoff round-trips, and whether task document attribution is omitted or rejected for an unauthorized caller. Fake CLI and contract fixtures can prove SDK mapping but cannot prove these integrated access/lifecycle outcomes. No broader command sweep is permitted.

Test repository URL source: active project description resource `https://github.com/maximchikAlexandr/multica-py`. The stand is the project-described isolated `multica-py-e2e-062` compose project with its fixed PostgreSQL, frontend port `14002`, API port `19082`, and primary wrapper `multica-test`; these values define the test boundary and are never replaced by the primary Multica profile, daemon, containers, or data. Tester SHALL acquire an exclusive stand lease, use a fresh `<tester-checkout>` at the candidate SHA, and receive two wrapper-owned, non-personal test identities in the same test workspace: `<primary-test-cli>` (the existing `multica-test`) and `<restricted-test-cli>` (a stand-operator provisioned wrapper with a distinct profile and daemon). Wrapper names/paths, identity IDs, profile/daemon handles, Basic Auth, and server URL are material inputs supplied out of band and recorded only as sanitized labels/hashes; no secret enters Git or evidence.

Readiness SHALL fail closed before mutation unless the checkout SHA, both CLI versions, wrapper/profile/daemon separation, two distinct test identity IDs, common test workspace, exclusive compose/DB/port lease, stand health, output directory outside Git, and capture renderer are all proven. The harness does not provision identities, profiles, daemons, database, ports, or the stand. If `<restricted-test-cli>` or the lease is unavailable, E2E-01P and E2E-03D remain blocked; they are not downgraded to single-identity PASS. The fixed stand database is never reset or accessed directly: reset means case-specific deletion/archive of every recorded test-owned resource, followed by read-back; failed cleanup blocks completion and leaves sanitized resource IDs for operator recovery.

### Scenario-to-check matrix

OpenAPI is `N/A` for every row: this repository wraps a CLI subprocess and contains no OpenAPI document or generated HTTP client. The authoritative interface/schema references are therefore exact CLI nodes plus response IDs in `contracts/sdk-contract.json` and its generated Python projection. “Extend” below means the Implementer adds rows/assertions to the named existing path; the Tester only verifies them.

| Ref | Exact requirement / scenario | CLI boundary and contract schema | Verification disposition, workflow job, test path, assertion | Live case |
|---|---|---|---|---|
| UC-1 | Approved upstream contract is pinned and complete / Exact release identity is retained | `multica version --output json`; release/compatibility schema | `.github/workflows/ci.yml` `contract-check`; `tests/contract/test_sdk_contract.py`; assert exact release/tag/commit/archive/executable/version hashes and prior lineage | none; lower-level sufficient |
| UC-2 | Approved upstream contract is pinned and complete / Complete command disposition is closed | all `277` target help nodes plus removed `issue rerun`; command registry | `contract-check`; `tests/contract/test_sdk_contract.py` + `scripts/audit_source_links.py`; assert exact node set, one disposition and zero pending | none |
| UC-3 | Approved upstream contract is pinned and complete / Complete response review is closed | `196` response registry rows | `contract-check`; `tests/contract/test_sdk_contract.py`; assert exact row set, old/target source URLs and zero pending | none |
| UC-4 | Approved contract alone generates production artifacts / Generated output is reproducible | `validate/render/check`; generated projection schema | `contract-check`; `tests/unit/test_development_harness.py`; render twice and assert byte equality/clean tree | none |
| UC-5 | Approved contract alone generates production artifacts / Unknown extraction pattern fails closed | extractor review-item schema | `contract-check`; `tests/contract/test_sdk_contract.py`; mutation fixture asserts validation failure and no generated promotion | none |
| UC-6 | Compatibility is direct and bounded / Supported and unsupported versions are classified | `multica version`; compatibility metadata | `.github/workflows/ci.yml` `compatibility`; existing compat-marked cases plus `tests/component/test_service_safety.py`; assert retained floor, `0.13.0` accepted and `>=0.13.1` rejected | none |
| SDK-1 | Issue blockers preserve identity, kind, count, and privacy / Visible blocker collections decode | `issue get/list/search/create/update`; `issue` / `issue_list_page` | `.github/workflows/ci.yml` `quality`; extend `tests/contract/test_issue_models.py` and existing operation tables; assert order, `manual|stage`, `closed`, binding and no hydration | E2E-01V |
| SDK-2 | Issue blockers preserve identity, kind, count, and privacy / Older omission remains compatible | same issue reads; legacy `issue` fixtures | `compatibility`; `tests/contract/test_baseline_specs.py` + `test_issue_models.py`; assert omitted arrays/count defaults without unrelated drift | none |
| SDK-3 | Issue blockers preserve identity, kind, count, and privacy / Hidden blockers do not leak | `issue get`; `issue` | `quality` fixture asserts count/visible mismatch and no synthesized ID; backend visibility remains unprovable offline | E2E-01P |
| SDK-4 | Issue blockers preserve identity, kind, count, and privacy / Malformed blocker payload fails typed decoding | issue response decoder; `issue` | `quality`; `tests/contract/test_issue_models.py`; wrong array/id/count/via shapes raise `OutputShapeError`, no partial entity | none |
| SDK-5 | Issue blocker mutations enforce local and authoritative constraints / Valid mutation has exact transport and invalidation | `issue create --blocked-by`, `issue update --blocked-by/--remove-blocked-by`; `issue` | `quality`; `tests/unit/resources/test_operations.py` + `tests/component/resources/cases.py`; exact argv/result and scoped invalidation | E2E-01V |
| SDK-6 | Issue blocker mutations enforce local and authoritative constraints / Local failures avoid transport | same writes; local validator | `quality`; existing issue unit case tables; assert blank/type/self/max-100 raises locally with zero transport | none |
| SDK-7 | Issue blocker mutations enforce local and authoritative constraints / Authoritative graph failures remain typed | same writes; standard error schema | `quality` fake-CLI rows assert typed/redacted error/no cache; real cycle/cross-workspace/hidden enforcement requires backend | E2E-01G |
| SDK-8 | Removed issue rerun has one migration target / Replacement executes exact target command | `issue rerun-task <run-id> [--issue] [--fresh]`; task row | `quality`; `tests/unit/resources/test_operations.py` + component cases; exact argv/presence/task decode/error | E2E-04R |
| SDK-9 | Removed issue rerun has one migration target / Legacy surface is absent | hidden `issue rerun`; public inventory | `quality`; `tests/contract/test_bound_public_surface.py` + `test_bound_public_docs.py`; assert old symbol/case/docs absent and successor present | none |
| SDK-10 | Squad handoff mode follows reviewed closed policy / Known modes round-trip | `squad create/get/list/update`; `squad` / `page_squad` | `quality`; existing squad operation/model case tables; assert `leader|direct`, exact update presence and unchanged fields | E2E-02H |
| SDK-11 | Squad handoff mode follows reviewed closed policy / Omitted and unknown modes follow reviewed policy | squad decoder; `squad` | `compatibility`; squad model fixtures; omitted defaults `leader`, unknown raises `OutputShapeError` | none |
| SDK-12 | Task-run document attribution remains typed and access-safe / Accessible attribution decodes | `agent tasks`, `issue runs`, `issue run-messages`; `page_task_runs` / `page_run_messages` | `quality`; `tests/contract/test_issue_models.py` and task/run wire fixtures; assert optional IDs, `kind=doc_comment`, pagination | E2E-03A |
| SDK-13 | Task-run document attribution remains typed and access-safe / Inaccessible document does not leak | `issue runs/run-messages/cancel-task`; task/message/action schemas | `quality` authorization/not-found fixtures assert typed failure/omission and no title/content/URL; real access requires second identity | E2E-03D |
| SDK-14 | Retained responses remain backward and forward decodable / Presence matrix is complete | all changed approved response IDs | `quality`; existing contract/component response tables; assert omitted/null/empty/populated/false/zero/open values or typed failure | none |
| CLI-1 | Reviewed target commands govern public parity / Changed command mappings are exact | approved changed CLI nodes; operation schemas | `quality`; `tests/unit/resources/test_operations.py` and `tests/component/resources/cases.py`; exact argv/mode/stdin/timeout/decoder | none |
| CLI-2 | Reviewed target commands govern public parity / Deferred commands stay non-public | deferred nodes including `squad briefs`; inventory | `quality`; `tests/contract/test_bound_public_surface.py`; assert no client/resource/export/canonical operation | none |
| CLI-3 | Reviewed target commands govern public parity / Retained commands do not drift | retained node registry | `contract-check` + `quality`; contract registry and operation fingerprints remain exact | none |
| CLI-4 | Update-style presence is explicit / Omission and explicit values produce distinct plans | changed create/update nodes; input mappings | `quality`; operation case tables assert omitted vs empty/false/zero/null argv and owned-boundary failures | none |
| CLI-5 | Public operation inventory is closed / Inventory mismatch fails offline | approved/public/canonical inventories | `quality`; `tests/contract/test_bound_public_surface.py` and operation completeness assertion; zero/multiple/missing vector fails | none |
| VR-1 | Upgrade verification is layered and traceable / Lower-level matrices are table-driven | test architecture; N/A runtime schema | `quality`; repository test-structure guards and case tables; assert rows/shared fixtures rather than parallel hierarchy | none |
| VR-2 | Upgrade verification is layered and traceable / Offline gate remains backend-free | repository gates; N/A runtime schema | `quality`, `compatibility`, `contract-check`, `.github/workflows/package-test.yml` `build-and-validate`; assert all gates pass and offline collection excludes `tests/live/*` | none |
| VR-3 | Interaction-only behavior has isolated live evidence / Readiness gate protects the attempt | wrapper `version`, daemon status and exact checkout; manifest schema | local harness preflight + `.github/workflows/live-smoke.yml` `multica-live`; extend `tests/unit/test_e2e_verification.py`; assert every material input before mutation | all live cases |
| VR-4 | Interaction-only behavior has isolated live evidence / Independent walkthrough is not a test rerun | public SDK/CLI reads; case schemas | Tester performs listed manual action from fresh checkout after harness; final comment distinguishes script and manual observations | all live cases |
| VR-5 | Interaction-only behavior has isolated live evidence / Evidence is genuine and sanitized | harness artifact manifest and actual text captures | `quality`; `tests/unit/test_e2e_verification.py`; sanitizer/allowlist/hash assertions; Tester attaches genuine text/PNG | E2E-01P, E2E-02H, E2E-03A/D |
| VR-6 | Interaction-only behavior has isolated live evidence / Cleanup preserves proof | harness cleanup registry/schema | `quality`; existing cleanup-failure tests extended per resource; assert nonzero on cleanup failure while branch/MR/attachments persist | all live cases |
| VR-7 | Evidence publication is exact-revision and attachment based / Tester publishes complete result | Multica comment/attachment contract; N/A repo schema | Tester read-back asserts product/test SHA, commands/exits, links, images, cleanup and findings; not a CI action | all live cases |
| VR-8 | Evidence publication is exact-revision and attachment based / Planning artifacts do not claim execution | Git tree and planning docs; N/A runtime schema | `contract-check` + review; assert no PASS claim or tracked raw evidence | none |
| VR-9 | Automatic local runs obey workspace limit / Long suite moves to CI | GitHub workflows above; N/A runtime schema | operator records ten-minute stop and exact-SHA CI link; suites are not split | none |

### Selected live cases, setup, reset and cleanup

All selected cases extend `scripts/e2e/verify_multica_test.py` through repeatable `--case`; the existing `--output` directory, exact SDK SHA/CLI version preflight, sanitizer, manifest/hash writer, resource registry, nonzero failure result, and `finally` cleanup remain authoritative. `tests/unit/test_e2e_verification.py` and `tests/unit/resources/e2e_cases.py` gain case/config/cleanup rows. No second runner or output schema is created.

| Case | Initial state and public action | Independent Tester observation | Reset / failure cleanup | Evidence and images |
|---|---|---|---|---|
| E2E-01V | Primary identity creates a unique project plus blocker, blocked, and dependent issues; calls SDK create/update/get/list with `--blocked-by` semantics | Independently inspect visible `manual|stage`, closed state, ordering, count and dependent `blocking`; remove one manual blocker through public SDK | Record every issue/project ID before linking; remove test links, cancel/delete test issues as supported, delete project; read-back absence/state. On failure retain sanitized IDs and return nonzero | manifest events, actual text, `blockers-visible-before.png` / `blockers-visible-after.png` |
| E2E-01P | Under exclusive lease, primary creates a private-project blocker visible only to primary and a public blocked issue visible to both; restricted wrapper reads public issue | Compare primary/restricted reads; restricted sees greater `blocked_count` than visible `blocked_by` without hidden ID/title in stdout/stderr/manifest | Primary removes blocker, deletes both test projects/issues; restricted performs final public read; cleanup failure blocks completion | two sanitized role-labelled texts, `blockers-primary.png`, `blockers-restricted.png`, no raw identity/URL |
| E2E-01G | Primary creates isolated issues and attempts self, cycle and cross-workspace/hidden references using only operator-provided test workspaces/resources | Inspect typed/redacted failures and unchanged blocker state; max-100 remains lower-level to avoid mass live data | Delete every created issue/project; if operator-provided foreign/hidden fixture was not created by this run, never mutate it | manifest error codes and post-failure state; no image because error text is not a changed read surface |
| E2E-02H | Primary creates unique squad with default mode, reads it, updates to `direct`, then back to `leader`, and lists after each write | Inspect default `leader`, both round-trips and unrelated fields | Delete test squad; verify not found. Workflow-side-effect setup is excluded from this case and remains fixture-based | actual normalized text and `handoff-leader.png` / `handoff-direct.png` |
| E2E-03A | Stand operator supplies a disposable accessible doc-discussion run fixture or approved public action to create one; primary calls SDK `agents.tasks`, `issues.runs`, and `issues.run_messages` | Inspect `doc_id`, `doc_thread_id`, `doc_comment_id`, `kind=doc_comment`, squad attribution and pagination without reading document content | Delete only run-owned issue/document when API supports it; otherwise operator fixture is read-only and its fixture ID is omitted from Git/evidence | sanitized attribution text, `task-doc-accessible.png`, manifest hashes |
| E2E-03D | Same run is queried through restricted wrapper whose identity is preconfigured without owning-agent/document access | Confirm documented omission or typed not-found/authorization and absence of title/content/URL | No mutation by restricted identity; primary performs E2E-03A cleanup; failure retains only sanitized recovery labels | role-labelled error/outcome text and `task-doc-restricted.png`; no private URL/content |
| E2E-04R | Primary creates one uniquely named retryable test task using an approved fixture, previews SDK command, executes `issue rerun-task` once | Inspect returned task row and exactly one new run relationship; separately inspect local absence of legacy method | Cancel only still-running test task if required, then remove test issue/project; do not rerun on ambiguous result | command/result event, revisions and cleanup; image only if target read output differs visibly |

### Harness and capture contract

- Implementer owns the extension of `scripts/e2e/verify_multica_test.py`, `tests/unit/test_e2e_verification.py`, and shared case fixtures. The harness accepts case selection and two wrapper executable parameters, records tested product revision separately from test-code revision, uses only unique test-owned resources, and preserves its existing output-outside-Git, sanitization, artifact hashes, and failure-safe cleanup contracts.
- The harness does not provision the stand/identity/profile/daemon/database/ports, embed credentials/hostnames, invoke the primary Multica profile/daemon, manufacture evidence, or commit logs/JSON/images. Wrapper parameters identify operator-owned launchers; they do not expose tokens or profile paths in artifacts.
- Baseline/candidate capture uses official CLI `0.7.1` and `0.13.0` binaries pinned by the approved contract against equivalent safe fixtures only where the operation exists in both versions. New-only fields use pre-mutation/post-mutation candidate captures and are labelled accordingly; a nonexistent baseline behavior is never invented.
- Capture fixes locale, terminal width, output mode, role label and fixture lifecycle. A render of actual captured text is labelled as a render. ANSI, TTY, and progress limitations are stated rather than inferred. Missing mandatory captures prevents complete verification.
- Tester performs the listed manual actions from the fresh checkout after the harness; rerunning the harness is not the independent walkthrough.

### Evidence publication and cleanup

- Git/GitHub retains only normal development results: implementation/tests/scripts/fixtures/docs and real commits. Tests and separately generated functional results use distinct commits only when both exist naturally.
- Multica final evidence comment contains product/test revisions, commands and exit codes, assertions, hashes, provenance, MR/commit/file links, PNG attachments, diagnostic attachments, and cleanup status; attachment read-back is mandatory.
- Raw logs, diagnostic JSON, hashes, screenshots, generated reports, private URLs, and personal data are not committed. JSON is committed only if JSON generation itself is the tested product behavior.
- Cleanup removes only test-owned stand resources and local transient captures. Evidence branch/MR/commits remain; closing, merging, or deleting them requires separate authorization.
- Automatic local suites stop at ten minutes and move to existing GitHub Actions on the published exact SHA. Manual Tester walkthroughs may exceed ten minutes.

## Work packages

### WP-1 — Approved contract and deterministic foundation

- stage: `1`
- tasks: `1.1`, `1.2`, `1.3`, `1.4`
- depends_on: none
- deliverable: closed `0.13.0` approved contract, schema support, validated deterministic generated projection, and no pending command/response dispositions.
- responsibility scope: contract/schema/generator/generated projection and directly related contract tests/fixtures; critical shared files are `contracts/sdk-contract.json` and `src/multica_py/_generated/approved_sdk.py`.
- contract surface: exact provenance, compatibility interval, operation/response registry, mapping/presence/constraint metadata, generator outputs.
- DoD/evidence: contract validate/render/check, deterministic rerender, source-link audit, focused schema/generator tests, clean diff excluding evidence.
- parallel safety: foundation is isolated as the sole predecessor and sole owner of shared contract/generated files.

### WP-2 — Issue blockers and rerun replacement

- stage: `2`
- tasks: `2.1`, `2.2`, `2.3`, `2.4`
- depends_on: `WP-1`
- deliverable: privacy-safe blocker read/mutation behavior and complete legacy-rerun migration.
- responsibility scope: issue entities/models/private wires/resources/exports and directly related issue tests/fixtures/type samples/docs snippets; excludes shared contract/generated files and squad/task wires.
- contract surface: blocker identity/kind/count/presence, eager/command pairs, validation/error/invalidation, rerun-task signature/result.
- DoD/evidence: focused unit/contract/component/type tests cover positive, negative, omission, privacy, lifecycle, max-100, exact argv, and removed-symbol inventory.
- parallel safety: writes only issue-owned runtime/tests while sibling WP-3 owns squad/task paths and WP-4 owns remaining mappings/cases.

### WP-3 — Squad handoff and task document attribution

- stage: `2`
- tasks: `3.1`, `3.2`, `3.3`, `3.4`
- depends_on: `WP-1`
- deliverable: reviewed closed handoff mode and access-safe task document attribution through existing surfaces.
- responsibility scope: squad entities/resources, agent-task/run models and private wires, and directly related tests/fixtures/type samples; excludes issue blocker paths and shared contract/generated files.
- contract surface: `handoff_mode` presence, `leader|direct` values, legacy default and typed rejection; document identity/kind/actor attribution, access omission/errors, retained delete action result.
- DoD/evidence: focused unit/contract/component/type checks prove known/unknown/omitted values, access-safe shapes, malformed failures, exact argv, and no new document resource.
- parallel safety: squad/task files and test rows are disjoint from WP-2 issue files; shared operation-table edits belong to WP-4.

### WP-4 — Remaining command/response reconciliation

- stage: `2`
- tasks: `4.1`, `4.2`, `4.3`
- depends_on: `WP-1`
- deliverable: every remaining reviewed `adapt|retain|support|remove|defer` decision reflected in runtime and closed canonical inventories.
- responsibility scope: non-issue/non-squad/task resource/model adapters, canonical operation/response tables, fingerprints, completeness guards, and related fixtures; excludes WP-2/WP-3 owned feature files and WP-1 contract/generated files.
- contract surface: exact command plans, update presence, pagination, open values, response/error shapes, public/deferred set equality.
- DoD/evidence: targeted table suites and inventory guards pass; no deferred public method appears; no duplicate canonical vector exists.
- parallel safety: owns central mapping/case tables so siblings add feature-specific tests in their owned modules and coordinate through the WP-1 contract.

### WP-5 — Verification script and CI coverage

- stage: `3`
- tasks: `5.1`, `5.2`, `5.3`
- depends_on: `WP-2`, `WP-3`, `WP-4`
- deliverable: repeatable focused stand script, CI/lower-level coverage, and recorded exact-revision repository gates.
- responsibility scope: the existing `scripts/e2e/verify_multica_test.py`, `tests/unit/test_e2e_verification.py`, shared E2E case fixtures, CI workflow/test extensions, and directly related tooling docs; excludes product runtime, a parallel runner, and release prose.
- contract surface: E2E case inputs/assertions/cleanup, CI commands, source-link/determinism/privacy/package gates, test-time limit behavior.
- DoD/evidence: script self-checks/focused dry-safe tests, CI configuration validation, repository gates with commands/exit codes; no live run during implementation planning.
- parallel safety: starts after product siblings converge and writes verification paths disjoint from WP-6 documentation.

### WP-6 — Documentation and migration

- stage: `3`
- tasks: `6.1`, `6.2`
- depends_on: `WP-2`, `WP-3`, `WP-4`
- deliverable: one coherent direct-upgrade, API, privacy, compatibility, migration, and release narrative.
- responsibility scope: README, docs, changelog, examples/typed documentation fixtures, and release/package prose; excludes CI/scripts and production runtime.
- contract surface: rerun migration, blocker privacy, handoff/task attribution, open/deferred policy, compatibility bounds, direct `0.7.1→0.13.0` release notes.
- DoD/evidence: documentation contract/type checks and package-content checks pass; no unsupported command or private stand detail is documented.
- parallel safety: docs-only write zone is independent of WP-5 verification paths after product contracts settle.

### WP-7 — Independent exact-revision verification

- stage: `4`
- tasks: `7.1`, `7.2`, `7.3`
- depends_on: `WP-5`, `WP-6`
- deliverable: published exact revision with independent automated/manual stand evidence and attachment read-back.
- responsibility scope: verification execution and Multica evidence publication only; Tester does not edit product/CI tests and reports findings for Implementer repair.
- contract surface: readiness, tested revisions, assertions, captures, attachments, cleanup, unresolved findings.
- DoD/evidence: remote SHA equality, focused script result, independent walkthrough, required genuine PNG/text, commands/exit codes, links/hashes, attachment read-back, cleanup report.
- parallel safety: final evidence consumes the consolidated candidate and has no sibling writes.

## Topology and coverage audit

- `WP-1 -> {WP-2, WP-3, WP-4} -> {WP-5, WP-6} -> WP-7`.
- stage mapping: `WP-1 -> 1`; `WP-2 -> 2`; `WP-3 -> 2`; `WP-4 -> 2`; `WP-5 -> 3`; `WP-6 -> 3`; `WP-7 -> 4`.
- Stages are consecutive and every predecessor has a lower stage than its dependent.
- Parallel frontier exists at stage 2 (`WP-2`, `WP-3`, `WP-4`) and stage 3 (`WP-5`, `WP-6`); sibling write zones do not conflict.
- Task coverage is exact and one-time: WP-1 owns all `1.x`; WP-2 all `2.x`; WP-3 all `3.x`; WP-4 all `4.x`; WP-5 all `5.x`; WP-6 all `6.x`; WP-7 all `7.x`. No task is uncovered or duplicated.
