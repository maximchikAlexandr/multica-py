## Delivery contract

- Change: `update-multica-0-12-1`
- Planning issue: `MYL-672`
- Planning base: `b268e3bec0436fe51727fda50583344f57663284` (tree `6fb22297ab62a86b591dc058fdc7a03b107c97fd`)
- Upstream baseline: Multica `0.7.1` at `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`
- Upstream target: Multica `0.12.1`, release `455946845`, at `fc8028d761707b506cec498385f31fcebbbff598`
- Test repository: the same `multica-py` GitHub repository named by the project resource; private stand endpoints are supplied only through Tester environment parameters.
- Estimate source of truth: root planning issue properties `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours`; this file intentionally contains no numeric estimate total.
- Planning authority: proposal, design, delta specs, and tasks in this change. Live status, assignees, approvals, attempts, and evidence results remain in Multica.

## E2E decision

`e2e_required=true`.

Most acceptance is fully provable through the repository's existing frozen tables, contract validation, fake-CLI component fixtures, typing, packaging, and CI. Four material gaps remain because their expected result depends on the real `0.12.1` CLI/server/database authorization path: issue description optimistic concurrency, comment idempotent replay, skill base-revision conflict, and caller-dependent guest visibility combined with project progress. A fixture can prove SDK decoding but cannot prove that the target server preserves state, deduplicates the write, or redacts the field for the actual caller.

The plan therefore adds one gated module to the existing `tests/live` layer and does not create a second runner or configuration namespace. It reuses the five required `MULTICA_LIVE_*` inputs from `tests/live/conftest.py`, adds only guest-fixture inputs needed by the authorization case, and updates the existing harness from its hard-coded prepared target `0.7.0` to `0.12.1`. Local execution binds `MULTICA_LIVE_CLI=multica-test` to the isolated profile, daemon, and prepared workspace. No private hostname, credential, personal identity, profile content, or diagnostic output is committed. The primary Multica profile/daemon and reference checkout are forbidden.

## Verification matrix

| Case ID | OpenSpec requirement / scenario | Verification gap and decision | Public boundary | Local test script | Independent agent steps | CI disposition | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| V121-01 | Exact provenance, `209→276` command reconciliation, 196 response verdicts, deterministic generation | Contract checks are sufficient; no live gap | Approved contract and generated projection | Existing contract/unit checks; no live script | Compare exact identities/totals/links, repeat render/check, inspect clean diff | Existing `contract-check`, updated target pin | Exact pins; 276/68/1/34; 196/118; no pending; byte-stable render | Commands, exits, SHA, source/file/CI links in Multica; no image |
| V121-02 | Rerun removal/replacement and all changed request mappings | Exact argv/body/failure tables are sufficient; triggering arbitrary agent work live adds cost without a distinct SDK assertion | `IssueResource`, bound issue, command builder, shared errors | Existing unit/component tables; no live script | Inspect canonical operation/discovery rows and run focused argv/error cases | Existing non-live jobs | Old operation absent; replacement exact; omission/constraints/errors exact | Commands, exits, test/file links; no image |
| V121-03 | Issue `description_revision` and stale-write conflict | Real state preservation after server conflict remains unproved below live | Issue get/edit/update and typed 409 error | `tests/live/test_v0121_upgrade.py::test_issue_description_revision_conflict` | Through the existing prepared client, create a UUID-named issue, read revision, perform current write, submit stale write, reread state, clean up | Repository-native isolated local live is required; existing protected `live-smoke.yml` may additionally run when provisioned | Revision advances; stale write is typed 409; winning content remains | Sanitized actual text/assertion summary and IDs redacted in Multica; no image |
| V121-04 | Comment idempotent replay | Real server deduplication remains unproved below live | Comment add/list and typed replay result | `tests/live/test_v0121_upgrade.py::test_comment_idempotent_replay` | Through the existing prepared client, add the same logical comment twice with one idempotency identity, inspect identity/count, clean up parent issue | Repository-native isolated local live is required; existing protected `live-smoke.yml` may additionally run when provisioned | Same logical result; one stored comment; content/revision typed | Sanitized assertion summary in Multica; no image |
| V121-05 | Skill revision/base-revision conflict | Real atomic state preservation after stale mutation remains unproved below live | Skill get/update/files and typed 409 error | `tests/live/test_v0121_upgrade.py::test_skill_base_revision_conflict` | Through the existing prepared client, create a UUID-named skill, apply current and stale updates, reread metadata/files, delete test skill | Repository-native isolated local live is required; existing protected `live-smoke.yml` may additionally run when provisioned | Revision advances; stale mutation is typed conflict; prior complete state remains | Sanitized text/assertions and file links in Multica; no image |
| V121-06 | Guest redaction and project progress | Authorization-dependent projection and computed progress require real actors/server state | Workspace members, project get/list, issue create/status/delete | `tests/live/test_v0121_upgrade.py::test_guest_redaction_and_project_progress` | Require a dedicated empty prepared guest-visible project; owner creates two UUID issues, leaves one `todo`, moves one to `done`, then owner and guest read the same project/workspace state; owner deletes both and rereads the empty baseline | Repository-native isolated local live is required; existing protected `live-smoke.yml` may additionally run when provisioned | Both actors see the reviewed progress fields for one done of two total (and 50% where supplied); non-guest sees approved guest `project_ids`; guest membership projection omits them; project returns empty | Sanitized projections/assertions and cleanup read-back in Multica; no image |
| V121-07 | Remaining 118 changed responses, open values, pagination, malformed output, 400/409/413/499 | Frozen decoder and fake-CLI fixtures are sufficient and safer than manufacturing every server failure | Existing domain models/resources/shared transport | Existing unit/contract/component tables; no live script | Trace each registry row to a concrete test and run focused domain selections | Existing non-live jobs | Every row mapped; presence/nullability/open values exact; malformed fails closed; typed errors retained | Test paths, commands, exits, registry/file links; no image |
| V121-08 | Compatibility, docs, package, exact-SHA release | Repository and CI gates are sufficient | Makefile, workflows, package and docs | Existing commands; no live script | Fresh checkout at candidate SHA; run focused gates; verify remote SHA and linked CI/package evidence | Existing lint/types/test/compat/contract/package jobs | Claims agree; live tests excluded from offline collection; package imports; local=remote SHA | Commit/MR/file/CI links and command exits in Multica; no image |

## Live script and environment contract

- Implementer owns `tests/live/test_v0121_upgrade.py`, `tests/live/conftest.py`, `tests/live/README.md`, `.github/workflows/live-smoke.yml`, and directly related live-only fixtures. It SHALL extend the existing `prepared_client`, markers, and public SDK calls; it SHALL NOT add browser automation, a second framework, a parallel runner/config namespace, shelling to the primary CLI profile, or hardcoded stand endpoints.
- Entry command: `MULTICA_LIVE_CLI=multica-test MULTICA_LIVE_EXPECTED_VERSION=0.12.1 MULTICA_LIVE_SERVER_URL=<private-api-url> MULTICA_LIVE_WORKSPACE_ID=<prepared-workspace-id> MULTICA_LIVE_PROFILE=<isolated-owner-profile> MULTICA_LIVE_GUEST_PROFILE=<isolated-read-only-guest-profile> MULTICA_LIVE_GUEST_PROJECT_ID=<dedicated-empty-resettable-project-id> uv run pytest -o addopts="" -q -rP -m live_smoke tests/live/test_v0121_upgrade.py`.
- `tests/live/conftest.py` SHALL retain the five existing required inputs and change its exact prepared-version assertion to `0.12.1`; guest profile/project inputs are the only additions. `tests/live/README.md` SHALL document this same command and isolation contract. `.github/workflows/live-smoke.yml` SHALL retain its protected manual harness, update all version/evidence expectations to `0.12.1`, and remain optional when its protected environment is unavailable; required evidence comes from the isolated local harness.
- Product revision and test revision SHALL both equal the published candidate SHA unless evidence explicitly identifies a separate test-only commit and its relationship. `multica-test version --output json` SHALL report `0.12.1` before an attempt, and the wrapper SHALL resolve to the isolated test profile/daemon rather than the primary Multica state.
- Initial state uses the existing UUID-derived naming pattern, with no matching issue, comment, or skill. `MULTICA_LIVE_GUEST_PROJECT_ID` identifies a dedicated prepared project in the configured workspace: the owner profile can create/update/delete issues in it, the guest profile can read it, its membership already grants the reviewed guest scope, and readiness requires it to contain no issues. No test mutates or deletes the project or membership.
- For V121-06, cleanup is registered before setup. The owner creates two UUID-named issues in that prepared project, leaves one `todo`, transitions one to `done`, and both owner and guest read that same project plus workspace-member projection. Assertions require both project projections to report the reviewed fields for one done of two total (and 50% where the target supplies a percentage), require the owner-visible guest row to preserve exactly the prepared project ID, and require the guest-visible row to omit `project_ids`. In `finally`, the owner deletes both issues in reverse creation order and rereads the project until the baseline is empty; a deletion or baseline assertion failure is reported as cleanup failure. There is no hidden assignment step or manual per-run preparation.
- Non-guest and guest actors are supplied by the existing live fixture configuration. The plan never records credentials, email addresses, tokens, profile paths, private URLs, or personal data.
- Actual commands, outputs, exit codes, diagnostic JSON, IDs, hashes, and logs are Multica-only evidence. Git contains only reusable tests/fixtures and normal generated product artifacts.

## Readiness, attempts, and cleanup

- Before consuming a live attempt, Tester SHALL verify exact local/remote candidate SHA, `multica-test` target identity `0.12.1`, isolated profile and daemon, all five existing required `MULTICA_LIVE_*` values, API reachability, prepared workspace, disposable UUID namespace, focused lower-level PASS, live collection, and cleanup hooks. For V121-06 it SHALL additionally prove the prepared project is in that workspace and empty, the owner can create/update/delete a disposable readiness issue, the guest can read the same project but cannot mutate it, and the non-guest membership projection contains that project in the guest scope; the readiness issue is deleted before the attempt.
- A failed readiness gate consumes no product assertion and is reported as not run. Live runs are not used to debug setup or tests; cheaper deterministic checks repair those first.
- Each PASS records case ID, candidate SHA, material fixture revision, public actions, assertions, cleanup result, and evidence links. A candidate change requires impact assessment and rerun only for affected cases; uncertain impact leaves the case unverified.
- Cleanup removes run-owned issues/comments/skills/projects when supported and records any residue. V121-06 removes only its run-owned issues and verifies the dedicated prepared project is empty; it never changes membership or deletes that project. Cleanup removes local diagnostic output but preserves branch, commits, CI/MR links, and Multica evidence. It SHALL NOT merge, close, or delete the branch.

## Independent Tester contract

- Tester SHALL use a fresh checkout at the published candidate SHA and SHALL not edit implementation, CI tests, fixtures, generated product artifacts, or the live script.
- Tester SHALL independently inspect V121-01 through V121-08 mappings, run focused lower-level commands, execute the four live cases after readiness, and verify linked CI/package results.
- Automatic test outcomes, independent manual observations, and CI outcomes are reported separately. A second invocation of the same pytest node is not a manual check; the manual check is a fresh public-action walkthrough and independent inspection of resulting server state.
- The final Multica comment SHALL include candidate SHA, commands/exits, assertion summaries, cleanup result, normal commit/MR/file links, CI links, and sanitized text artifacts. Tester SHALL read the comment and attachments back and confirm accessibility.

## Image contract

No before/after image is planned because the SDK consumes structured JSON and the approved scope does not alter a terminal table, log renderer, progress display, final summary, or browser UI. This is an evidence decision, not a claim that upstream help text is unchanged.

If candidate implementation changes visible output, Tester SHALL stop and request a planning revision. That revision must identify equivalent `0.7.1` baseline and `0.12.1` candidate fixtures, locale, terminal width, output mode, actual captured text, supported color/TTY/progress limitations, confirmed Mac renderer readiness, PNG filenames, and Multica attachment/read-back requirements. Rendered text must be labelled as a render rather than a terminal screenshot.

## Verification ownership

- Implementer owns tasks 1.1–6.2, including approved contract, generated projection, production code, lower-level tests/fixtures, live test module, CI, docs, and exact-SHA publication.
- Independent Tester owns execution/evidence for tasks 6.3–6.6 and reports findings without modifying implementation or test artifacts.
- Planning verification and human implementation approval remain separate gates; this package does not authorize implementation.

## Ponytail gate

`ponytail full` was applied before design and after the E2E plan. Every material addition has a named requirement or unique risk and reuses an existing seam:

| Addition | Requirement / unique risk | Existing seam | Why the seam alone is insufficient |
|---|---|---|---|
| Contract inventory/response expansion | Exact 276-node and 196-row closed review | `contracts/sdk-contract.json`, `scripts/upstream_contract.py` | Current data is pinned to 0.7.1 and cannot represent the target decisions without approved rows |
| `rerun_task` replacement | Target removes public rerun and adds replacement | `IssueResource`, bound issue, generated bindings, frozen operation cases | Existing operation invokes a removed public command |
| Revision/replay/redaction fields | 118 changed response rows and stale/replay/privacy semantics | Existing frozen models, decoders, resource adapters, table cases | Current types and fixtures omit target fields and conflict/replay projections |
| Four live cases | Server state preservation, deduplication, computed progress, caller redaction | Existing `tests/live/conftest.py`, `tests/live/README.md`, `prepared_client`, and protected `live-smoke.yml` harness | The harness is fixed to `0.7.0` and lacks guest profile plus dedicated resettable project fixtures; deterministic fixtures still cannot prove real target server/authorization behavior |
| CI source pin/docs | Exact target source and package claims | Existing `contract-check`, Make targets, docs | Current workflow and claims fetch/name 0.7.1 |

Skipped as duplicate or risk-free scope: new resource families for the other 67 added help nodes, `doc`/`environment`, a second generator, a second live runner, decorative images, and intermediate-release deliveries. Directly related tests, fixtures, snapshots, docs, and service files remain in the owning work package even when not exhaustively named.

## Estimate basis

The authoritative totals are stored only in the root planning issue properties. The estimate covers remaining work for one experienced developer familiar with the Python/CLI stack, without AI acceleration, from the exact planning base through implementation, required tests, narrow live-script creation, documentation, publication, likely review repairs, and independent-verification preparation. It excludes unattended CI time, approval queues, meetings, and external blocking.

Confidence is medium and calibration is unavailable: the acceptance package and current seams are inspectable and prior upstream upgrades are close analogues, but the large reviewed contract rewrite, 118 changed response adaptations, permission-dependent stand cases, and repair cycles couple the upper range. No tests or application code were run for estimation.

## Delivery topology

`delivery_mode=dag` because the authoritative `Estimate, hours` property exceeds the single-package threshold and the graph contains a real three-way parallel frontier after one shared contract foundation. Task coverage is complete and non-overlapping; dependencies are direct only. Stages are consecutive topological levels, and Manager SHALL materialize the exact `wp_id -> stage` mapping: `WP-1 -> 1`, `WP-2 -> 2`, `WP-3 -> 2`, `WP-4 -> 2`, `WP-5 -> 3`, `WP-6 -> 4`.

### WP-1 — Approved contract and shared foundation

- `stage`: 1
- `depends_on`: none
- OpenSpec task coverage: 1.1–1.8 and 2.3–2.5
- Deliverable: one closed, validated `0.7.1→0.12.1` approved contract, byte-stable generated projection, and immutable shared command/wire/transport foundation.
- Owned responsibility scope: `contracts/sdk-contract.json`, `scripts/upstream_contract.py`, `src/multica_py/_generated/approved_sdk.py`, `src/multica_py/_internal/wire_models.py`, `src/multica_py/_internal/decoders.py`, `src/multica_py/_internal/transport.py`, `src/multica_py/_internal/commands.py`, `src/multica_py/_internal/content.py`, `src/multica_py/_internal/argv.py`, source-link/contract validators, and their focused tests. It owns reusable presence/constraint primitives, literal-content behavior, shared typed-error decoding, inventory/response decisions, and wire decoding; later packages consume rather than rewrite them.
- Contract surface: exact provenance; 276/68/1/34 command totals; 196/118 response totals; compatibility floor/maximum/ceiling; dispositions; source/test traceability; reusable presence/constraint and literal-content semantics; sanitized 400/409/413/499 decoding.
- DoD/evidence: validate/render/check twice; exact totals and links pass; repeated render clean; focused shared command/wire/transport primitive tests pass; review-only artifacts absent from Git.
- Parallel-safety rationale: this predecessor establishes the complete shared contract/command/wire/transport foundation before domain siblings begin.

### WP-2 — Issue command and response adaptation

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 2.1–2.2, 2.6–2.7, and 3.1–3.2
- Deliverable: exact issue-domain adaptation and complete `rerun` to `rerun_task` public replacement on the predecessor command/wire/transport foundation.
- Owned responsibility scope: `src/multica_py/resources/issues.py`, `src/multica_py/models/issues.py`, `src/multica_py/entities/issues.py`, issue-bound relations, and issue-local tests/fixtures. It consumes WP-1 shared command/transport primitives and SHALL not edit central operation registries/conftest, WP-1 shared files, or any WP-3/WP-4 domain resource.
- Contract surface: exact issue argv/body/channels, issue-local presence and imperative constraints, issue text mappings, typed issue errors, and canonical `rerun_task` behavior; central public-discovery reconciliation belongs to WP-5.
- DoD/evidence: every assigned issue command/response row has positive, negative, omission, explicit-value, and malformed cases as applicable; old issue rerun is absent; replacement is canonical; no non-issue builder or domain fixture is changed.
- Parallel-safety rationale: writes are issue-local and disjoint from WP-3 collaboration models and WP-4 operational models; all shared command/wire/transport files belong exclusively to WP-1.

### WP-3 — Collaboration models, conflicts, replay, progress, and guests

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 3.3–3.8
- Deliverable: typed comment/skill/project/workspace target response semantics with deterministic conflict, replay, pagination, and redaction coverage.
- Owned responsibility scope: `src/multica_py/resources/issue_comments.py`, `skills.py`, `skill_files.py`, `projects.py`, `project_resources.py`, and `workspaces.py`; corresponding comment/project/skill/workspace model/entity files; and domain-local tests/fixtures. It consumes WP-1 shared command/wire/transport foundation without editing it, issue-domain files, central registries/conftest, or operational resources.
- Contract surface: revisions/base revisions, idempotency, project progress/activity, guest/project scope, omission/nullability/open values, older-payload compatibility.
- DoD/evidence: every assigned changed registry row maps to a concrete frozen case or focused deterministic test; stale/replay/redaction behavior is asserted; supported older fixtures remain green.
- Parallel-safety rationale: collaboration files and fixtures are separate from WP-2 issue and WP-4 operational write zones; every sibling independently consumes the immutable WP-1 foundation, and shared integration waits for WP-5.

### WP-4 — Operational response models and retained behavior

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 4.1–4.7
- Deliverable: all remaining approved operational response adaptations and regression coverage across configuration, daemon, runtime/profile/usage, agent/autopilot/task/attachment, and retained rows.
- Owned responsibility scope: `src/multica_py/resources/configuration.py`, `daemon.py`, `runtimes.py`, `runtime_profiles.py`, `agents.py`, `autopilots.py`, and `attachments.py`; corresponding operational model/entity files; and domain-local tests/fixtures. It consumes WP-1 shared command/wire/transport foundation without editing it, `resources/workspaces.py`, central registries/conftest, or WP-2/WP-3 domain files.
- Contract surface: configuration limits, daemon controls, machine-bound profile fields, usage windows, outcomes/credits/dimensions, pagination, open values, malformed outputs, retained errors.
- DoD/evidence: all assigned registry actions are implemented and traceable; changed and unchanged rows pass focused coverage; no version wrapper or deferred family appears.
- Parallel-safety rationale: operational domains have no sibling production write zone; cross-domain docs/helpers are deferred to WP-5.

### WP-5 — Integration, docs, CI, and candidate publication

- `stage`: 3
- `depends_on`: WP-2, WP-3, WP-4
- OpenSpec task coverage: 5.1–5.6
- Deliverable: integrated candidate with coherent docs/CI/package claims, complete scenario map, required repository gates, and normal-push exact-SHA proof.
- Owned responsibility scope: `tests/cases/operations.py`, `tests/unit/resources/test_operations.py`, shared `tests/conftest.py` and `tests/component/conftest.py`, `src/multica_py/client.py`, root/public export registries, cross-domain integration helpers, public docs, changelog, package metadata/checks, non-live CI workflows, and integration repairs after all siblings finish. It SHALL not edit live harness files owned by WP-6.
- Contract surface: migration/rollback, source pin, full gate set, ten-minute policy, exact candidate SHA, evidence-clean tree.
- DoD/evidence: focused gates pass; long suite is preserved unsplit in CI when required; local HEAD equals remote; all claims match the approved contract.
- Parallel-safety rationale: starts only after all stage-2 siblings, so shared docs, CI, and integration fixes cannot race active domain writes.

### WP-6 — Live script and independent evidence

- `stage`: 4
- `depends_on`: WP-5
- OpenSpec task coverage: 6.1–6.6
- Deliverable: reusable gated live coverage plus independent exact-revision lower-level/live/CI evidence with cleanup and Multica read-back.
- Owned responsibility scope: `tests/live/test_v0121_upgrade.py`, `tests/live/conftest.py`, `tests/live/README.md`, `.github/workflows/live-smoke.yml`, directly related live-only fixtures, readiness/cleanup documentation including the resettable prepared guest project contract, execution evidence, and final Multica publication. Implementer owns changes through task 6.2; Tester never edits implementation artifacts.
- Contract surface: issue and skill revision conflicts, comment replay, guest redaction/project progress, exact-SHA evidence, attachments/read-back, cleanup.
- DoD/evidence: readiness passes before mutation; all four live cases and independent deterministic review are case-recorded; evidence is readable in Multica; no private or transient artifact is tracked; branch remains preserved and unmerged.
- Parallel-safety rationale: live and independent verification require the consolidated published candidate and therefore follow WP-5.

## Frontier validation

- Stage 1 frontier: WP-1 establishes shared contract authority.
- Stage 2 frontier: WP-2, WP-3, and WP-4 are independent siblings with disjoint responsibility/write zones and may execute concurrently.
- Stage 3 frontier: WP-5 integrates all sibling results and publishes the candidate.
- Stage 4 frontier: WP-6 verifies the immutable candidate and publishes evidence.

The graph has a real three-way parallel frontier. WIP policy is operational and is not encoded as extra dependencies or stages.

## Critical shared-file ownership

Each mutable shared path has exactly one owner. Directly related domain tests, fixtures, snapshots, and service files follow that owner unless this table assigns them to the later integrator.

| Critical path / surface | Sole owner | Consumer rule |
|---|---|---|
| `contracts/sdk-contract.json`, `scripts/upstream_contract.py`, `src/multica_py/_generated/approved_sdk.py` | WP-1 | WP-2/3/4 consume the frozen projection |
| `src/multica_py/_internal/wire_models.py`, `src/multica_py/_internal/decoders.py`, `src/multica_py/_internal/transport.py`, `src/multica_py/_internal/commands.py`, `src/multica_py/_internal/content.py`, `src/multica_py/_internal/argv.py` | WP-1 | Stage-2 siblings consume this immutable command/wire/transport foundation and SHALL NOT edit it |
| `resources/issues.py`, `models/issues.py`, `entities/issues.py` | WP-2 | WP-3/4 consume WP-1 directly and do not edit issue files |
| `resources/issue_comments.py`, `skills.py`, `skill_files.py`, `projects.py`, `project_resources.py`, `workspaces.py` and corresponding domain models/entities | WP-3 | WP-2/4 do not edit collaboration/workspace paths |
| `resources/configuration.py`, `daemon.py`, `runtimes.py`, `runtime_profiles.py`, `agents.py`, `autopilots.py`, `attachments.py` and corresponding operational models/entities | WP-4 | WP-2/3 do not edit operational paths |
| `tests/cases/operations.py`, `tests/unit/resources/test_operations.py`, shared test conftest/fixtures, `src/multica_py/client.py`, public export registries | WP-5 | Stage-2 packages use domain-local cases; reconciliation waits for all siblings |
| `tests/live/test_v0121_upgrade.py`, `tests/live/conftest.py`, `tests/live/README.md`, `.github/workflows/live-smoke.yml` | WP-6 | No earlier WP edits the live runner/configuration surface |
