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

After the E2E plan, the live scope remains only the interactions lower-level checks cannot prove: hidden blocker counts/privacy, authoritative graph failures, handoff round-trip, task document attribution/access, and rerun-task replacement. All other cases stay in existing lower-level tables and CI. Each production, test/evidence, and WP addition has a unique requirement/risk and an existing seam identified in `design.md`.

## E2E decision

`e2e_required=true` because real backend authorization and lifecycle state determine whether hidden blocker counts leak identities, whether cycle/cross-workspace constraints hold, whether stage/manual handoff round-trips, and whether task document attribution is omitted or rejected for an unauthorized caller. Fake CLI and contract fixtures can prove SDK mapping but cannot prove these integrated access/lifecycle outcomes. No broader command sweep is permitted.

Test repository URL source: active project description resource `https://github.com/maximchikAlexandr/multica-py`. Tester uses the isolated project stand described by the project, `multica-test`, a dedicated test profile/daemon, a fresh checkout, and unique test-owned resource names. Private stand URLs and credentials remain outside Git and published artifacts.

### Verification matrix

| Case | OpenSpec requirement/scenario | Gap and local decision | Public boundary | Script | Independent Tester steps | CI disposition | Assertions | Artifacts/images |
|---|---|---|---|---|---|---|---|---|
| E2E-01 | Issue blockers: visible/hidden privacy | Real visibility filtering and hidden count cannot be proved by fake output; focused live required | public SDK issue get/blocker mutation and `multica-test issue get` | `scripts/e2e/verify_multica_013.py --case blockers` | Create visible and access-restricted blockers with two identities; inspect as privileged/restricted callers; remove only created links | Lower-level table cases plus existing `ci` job; live remains local-only because CI has no private stand fixture | visible order/kind; count may exceed visible rows; no hidden id in repr/error/log; self/cycle/cross-workspace/max-100 failures match local/server boundary | sanitized JSON/assert log; actual baseline/candidate text; `blockers-before.png`, `blockers-after.png` |
| E2E-02 | Squad handoff mode | Server default and stage/manual round-trip require real persistence | public SDK squad create/update/get/list | same script `--case handoff` | Create test squad, inspect default, set `manual`, set `stage`, fetch/list after each mutation, delete created squad | Exact argv/model cases in existing unit/component/contract jobs | values round-trip; omission fixture remains lower-level; unknown-value fixture remains lower-level; no unrelated field loss | sanitized state log; actual text; `handoff-before.png`, `handoff-after.png` |
| E2E-03 | Task-run document attribution/access | Authorization-dependent omission/error and actor attribution require backend | public SDK task/run reads plus `multica-test issue runs`/messages as available | same script `--case task-doc` | Trigger uniquely named task with accessible document, inspect attribution as allowed and restricted identities, avoid reading document content, clean test issue/document if owned | Wire/null/unknown/error fixtures in existing CI; live local-only | exact identity/kind/actor where accessible; inaccessible metadata omitted or typed error; no title/content/URL inference | sanitized attribution log; diagnostic JSON attached only on failure; `task-doc-before.png`, `task-doc-after.png` |
| E2E-04 | Removed rerun / rerun-task replacement | Real target command/result and task transition require CLI/backend | public SDK `rerun_task` preview/execution and `multica-test issue rerun-task` | same script `--case rerun-task` | Create a retryable test task, preview command, execute once, inspect new run/task relationship, confirm legacy method absent locally | Signature/argv/error/type fixtures and public-inventory gate in CI | exact command; successful typed result; one expected new run; legacy public symbol absent | command/result log and revision; no image beyond changed read captures already required unless output differs visibly |

### Script and fixture contract

- Implementer owns `scripts/e2e/verify_multica_013.py` and any safe reusable fixtures. The script accepts case selection, records tested product revision separately from test-code revision, uses only unique test-owned resources, returns nonzero on assertion/cleanup failure, and performs failure-safe cleanup.
- The script does not provision the stand, embed credentials/hostnames, invoke the primary Multica profile/daemon, manufacture evidence, or commit logs/JSON/images.
- Readiness gate: exact candidate SHA is published; focused lower-level checks are green; the isolated frontend/API and `multica-test` profile/daemon are healthy; unique namespace is recorded; baseline CLI `0.7.1` and candidate CLI `0.13.0` binaries/checksums are available for equivalent output capture; macOS terminal capture or an explicitly identified actual-text renderer is confirmed before mutation.
- Capture uses equivalent fixtures, locale, terminal width, and output mode. A render of captured text is labelled as a render. ANSI, TTY, and progress limitations are stated rather than inferred. Missing mandatory captures prevents complete verification.
- Tester performs the listed manual actions from a fresh checkout after the script; rerunning the script is not the independent walkthrough.

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
- deliverable: open handoff mode and access-safe task document attribution through existing surfaces.
- responsibility scope: squad entities/resources, agent-task/run models and private wires, and directly related tests/fixtures/type samples; excludes issue blocker paths and shared contract/generated files.
- contract surface: `handoff_mode` presence/open values, document identity/kind/actor attribution, access omission/errors, retained delete action result.
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
- responsibility scope: `scripts/e2e`, CI workflow/test extensions, verification fixtures, and directly related tooling docs; excludes product runtime and release prose.
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
