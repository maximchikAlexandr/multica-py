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

The plan therefore adds one gated live module to the existing `tests/live` layer and no second runner. It uses the isolated project stand through parameters such as `MULTICA_E2E_PROFILE`, `MULTICA_E2E_API_URL`, and a run namespace; no private hostname, credential, personal identity, profile content, or diagnostic output is committed. The primary Multica profile/daemon and reference checkout are forbidden.

## Verification matrix

| Case ID | OpenSpec requirement / scenario | Verification gap and decision | Public boundary | Local test script | Independent agent steps | CI disposition | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| V121-01 | Exact provenance, `209→276` command reconciliation, 196 response verdicts, deterministic generation | Contract checks are sufficient; no live gap | Approved contract and generated projection | Existing contract/unit checks; no live script | Compare exact identities/totals/links, repeat render/check, inspect clean diff | Existing `contract-check`, updated target pin | Exact pins; 276/68/1/34; 196/118; no pending; byte-stable render | Commands, exits, SHA, source/file/CI links in Multica; no image |
| V121-02 | Rerun removal/replacement and all changed request mappings | Exact argv/body/failure tables are sufficient; triggering arbitrary agent work live adds cost without a distinct SDK assertion | `IssueResource`, bound issue, command builder, shared errors | Existing unit/component tables; no live script | Inspect canonical operation/discovery rows and run focused argv/error cases | Existing non-live jobs | Old operation absent; replacement exact; omission/constraints/errors exact | Commands, exits, test/file links; no image |
| V121-03 | Issue `description_revision` and stale-write conflict | Real state preservation after server conflict remains unproved below live | Issue get/edit/update and typed 409 error | `tests/live/test_v0121_upgrade.py::test_issue_description_revision_conflict` | Create isolated issue, read revision, perform current write, submit stale write, reread state, clean up | Gated local live only; CI lower-level coverage remains mandatory | Revision advances; stale write is typed 409; winning content remains | Sanitized actual text/assertion summary and IDs redacted in Multica; no image |
| V121-04 | Comment idempotent replay | Real server deduplication remains unproved below live | Comment add/list and typed replay result | `tests/live/test_v0121_upgrade.py::test_comment_idempotent_replay` | Add same logical comment twice with one idempotency identity, list thread, inspect identity/count, clean up parent issue | Gated local live only | Same logical result; one stored comment; content/revision typed | Sanitized assertion summary in Multica; no image |
| V121-05 | Skill revision/base-revision conflict | Real atomic state preservation after stale mutation remains unproved below live | Skill get/update/files and typed 409 error | `tests/live/test_v0121_upgrade.py::test_skill_base_revision_conflict` | Create isolated skill, read revision, apply current update, submit stale update, reread metadata/files, delete test skill | Gated local live only | Revision advances; stale mutation is typed conflict; prior complete state remains | Sanitized text/assertions and file links in Multica; no image |
| V121-06 | Guest redaction and project progress | Authorization-dependent projection and computed progress require real actors/server state | Workspace members, project get/list, issue create/status | `tests/live/test_v0121_upgrade.py::test_guest_redaction_and_project_progress` | Create isolated project/issues, transition states, use configured non-guest/guest fixtures, compare projections, clean up run-owned data | Gated local live only; no private CI credentials | Progress matches states; authorized scope visible; guest projection omits redacted IDs | Sanitized projections/assertions in Multica; no image |
| V121-07 | Remaining 118 changed responses, open values, pagination, malformed output, 400/409/413/499 | Frozen decoder and fake-CLI fixtures are sufficient and safer than manufacturing every server failure | Existing domain models/resources/shared transport | Existing unit/contract/component tables; no live script | Trace each registry row to a concrete test and run focused domain selections | Existing non-live jobs | Every row mapped; presence/nullability/open values exact; malformed fails closed; typed errors retained | Test paths, commands, exits, registry/file links; no image |
| V121-08 | Compatibility, docs, package, exact-SHA release | Repository and CI gates are sufficient | Makefile, workflows, package and docs | Existing commands; no live script | Fresh checkout at candidate SHA; run focused gates; verify remote SHA and linked CI/package evidence | Existing lint/types/test/compat/contract/package jobs | Claims agree; live tests excluded from offline collection; package imports; local=remote SHA | Commit/MR/file/CI links and command exits in Multica; no image |

## Live script and environment contract

- Implementer owns `tests/live/test_v0121_upgrade.py` and directly related reusable fixtures. It SHALL use the repository's pytest markers and public SDK calls; it SHALL NOT add browser automation, a second framework, shelling to the primary CLI profile, or hardcoded stand endpoints.
- Entry command: `MULTICA_E2E_PROFILE=<isolated-profile> MULTICA_E2E_API_URL=<private-api-url> MULTICA_E2E_RUN_ID=<unique-run-id> uv run pytest -o addopts="" -q -m live_smoke tests/live/test_v0121_upgrade.py`.
- Product revision and test revision SHALL both equal the published candidate SHA unless evidence explicitly identifies a separate test-only commit and its relationship. The installed CLI SHALL report target `0.12.1` and target commit prefix before an attempt.
- Initial state is a unique run namespace with no matching issue, comment, skill, project, or membership fixture. Setup creates only run-owned resources. Cleanup is registered before the first mutation and runs on pass or failure.
- Non-guest and guest actors are supplied by the stand fixture configuration. The plan never records credentials, email addresses, tokens, profile paths, private URLs, or personal data.
- Actual commands, outputs, exit codes, diagnostic JSON, IDs, hashes, and logs are Multica-only evidence. Git contains only reusable tests/fixtures and normal generated product artifacts.

## Readiness, attempts, and cleanup

- Before consuming a live attempt, Tester SHALL verify exact local/remote candidate SHA, target CLI identity, isolated profile and daemon, API reachability, disposable namespace, both actor permissions, focused lower-level PASS, live collection, and cleanup hooks.
- A failed readiness gate consumes no product assertion and is reported as not run. Live runs are not used to debug setup or tests; cheaper deterministic checks repair those first.
- Each PASS records case ID, candidate SHA, material fixture revision, public actions, assertions, cleanup result, and evidence links. A candidate change requires impact assessment and rerun only for affected cases; uncertain impact leaves the case unverified.
- Cleanup removes run-owned issues/comments/skills/projects/memberships when supported and records any residue. It removes local diagnostic output but preserves branch, commits, CI/MR links, and Multica evidence. It SHALL NOT merge, close, or delete the branch.

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
| Four live cases | Server state preservation, deduplication, computed progress, caller redaction | Existing gated `tests/live` pytest layer and isolated project stand | Deterministic fixtures cannot prove real target server/authorization behavior |
| CI source pin/docs | Exact target source and package claims | Existing `contract-check`, Make targets, docs | Current workflow and claims fetch/name 0.7.1 |

Skipped as duplicate or risk-free scope: new resource families for the other 67 added help nodes, `doc`/`environment`, a second generator, a second live runner, decorative images, and intermediate-release deliveries. Directly related tests, fixtures, snapshots, docs, and service files remain in the owning work package even when not exhaustively named.

## Estimate basis

The authoritative totals are stored only in the root planning issue properties. The estimate covers remaining work for one experienced developer familiar with the Python/CLI stack, without AI acceleration, from the exact planning base through implementation, required tests, narrow live-script creation, documentation, publication, likely review repairs, and independent-verification preparation. It excludes unattended CI time, approval queues, meetings, and external blocking.

Confidence is medium and calibration is unavailable: the acceptance package and current seams are inspectable and prior upstream upgrades are close analogues, but the large reviewed contract rewrite, 118 changed response adaptations, permission-dependent stand cases, and repair cycles couple the upper range. No tests or application code were run for estimation.

## Delivery topology

`delivery_mode=dag` because the authoritative `Estimate, hours` property exceeds the single-package threshold and the graph contains a real three-way parallel frontier after one shared contract foundation. Task coverage is complete and non-overlapping; dependencies are direct only. Stages are consecutive topological levels, and Manager SHALL materialize the exact `wp_id -> stage` mapping: `WP-1 -> 1`, `WP-2 -> 2`, `WP-3 -> 2`, `WP-4 -> 2`, `WP-5 -> 3`, `WP-6 -> 4`.

### WP-1 — Approved contract and deterministic projection

- `stage`: 1
- `depends_on`: none
- OpenSpec task coverage: 1.1–1.7
- Deliverable: one closed, validated `0.7.1→0.12.1` approved contract and byte-stable generated projection.
- Owned responsibility scope: `contracts/sdk-contract.json`, `scripts/upstream_contract.py`, generated approved SDK projection, source-link/contract validators, and their focused tests. It owns all shared inventory/response decisions; later packages consume rather than rewrite them.
- Contract surface: exact provenance; 276/68/1/34 command totals; 196/118 response totals; compatibility floor/maximum/ceiling; dispositions; source/test traceability.
- DoD/evidence: validate/render/check twice; exact totals and links pass; repeated render clean; review-only artifacts absent from Git.
- Parallel-safety rationale: this predecessor establishes shared contracts once before domain siblings begin.

### WP-2 — Command surface and transport replacement

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 2.1–2.7
- Deliverable: exact adapted command builders and the complete `rerun` to `rerun_task` public replacement with typed transport behavior.
- Owned responsibility scope: issue resource/bound relation and shared command/validation/transport paths, generated-binding consumers, command option tests, operation cases, and directly related docs/tests. It SHALL not edit WP-1 contract/generator outputs or WP-3/WP-4 domain models.
- Contract surface: exact argv/body/channels, presence semantics, imperative constraints, literal text behavior, 400/409/413/499 decoding, public discovery.
- DoD/evidence: all adapted command rows have positive/negative/omission cases; old rerun is absent; replacement is canonical; deferred families remain absent.
- Parallel-safety rationale: writes are command/transport-oriented and disjoint from WP-3 collaboration models and WP-4 operational models; shared contract files belong exclusively to WP-1.

### WP-3 — Collaboration models, conflicts, replay, progress, and guests

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 3.1–3.8
- Deliverable: typed issue/comment/skill/project/workspace target response semantics with deterministic conflict, replay, pagination, and redaction coverage.
- Owned responsibility scope: collaboration domain models/resources/decoders and their unit/contract/component fixtures, including issue descriptions, comments, skills, projects, and workspace membership. It does not own shared transport internals or operational domains.
- Contract surface: revisions/base revisions, idempotency, project progress/activity, guest/project scope, omission/nullability/open values, older-payload compatibility.
- DoD/evidence: every assigned changed registry row maps to a concrete frozen case or focused deterministic test; stale/replay/redaction behavior is asserted; supported older fixtures remain green.
- Parallel-safety rationale: collaboration files and fixtures are separate from WP-2 command/transport and WP-4 operational write zones; any shared integration helper waits for WP-5.

### WP-4 — Operational response models and retained behavior

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 4.1–4.7
- Deliverable: all remaining approved operational response adaptations and regression coverage across configuration, daemon, runtime/profile/workspace/usage, agent/autopilot/task/attachment, and retained rows.
- Owned responsibility scope: operational domain models/resources/decoders and their unit/contract/component fixtures. It consumes shared errors and contract outputs without editing WP-2 transport or WP-3 collaboration domains.
- Contract surface: configuration limits, daemon controls, machine-bound profile fields, usage windows, outcomes/credits/dimensions, pagination, open values, malformed outputs, retained errors.
- DoD/evidence: all assigned registry actions are implemented and traceable; changed and unchanged rows pass focused coverage; no version wrapper or deferred family appears.
- Parallel-safety rationale: operational domains have no sibling production write zone; cross-domain docs/helpers are deferred to WP-5.

### WP-5 — Integration, docs, CI, and candidate publication

- `stage`: 3
- `depends_on`: WP-2, WP-3, WP-4
- OpenSpec task coverage: 5.1–5.6
- Deliverable: integrated candidate with coherent docs/CI/package claims, complete scenario map, required repository gates, and normal-push exact-SHA proof.
- Owned responsibility scope: cross-domain integration tests/helpers, public docs, changelog, package metadata/checks, CI workflows, final generated-consumer reconciliation, and integration repairs after all siblings finish.
- Contract surface: migration/rollback, source pin, full gate set, ten-minute policy, exact candidate SHA, evidence-clean tree.
- DoD/evidence: focused gates pass; long suite is preserved unsplit in CI when required; local HEAD equals remote; all claims match the approved contract.
- Parallel-safety rationale: starts only after all stage-2 siblings, so shared docs, CI, and integration fixes cannot race active domain writes.

### WP-6 — Live script and independent evidence

- `stage`: 4
- `depends_on`: WP-5
- OpenSpec task coverage: 6.1–6.6
- Deliverable: reusable gated live coverage plus independent exact-revision lower-level/live/CI evidence with cleanup and Multica read-back.
- Owned responsibility scope: `tests/live/test_v0121_upgrade.py`, stand-specific reusable fixtures using parameterized configuration, readiness/cleanup documentation, execution evidence, and final Multica publication. Tester never edits implementation artifacts.
- Contract surface: issue and skill revision conflicts, comment replay, guest redaction/project progress, exact-SHA evidence, attachments/read-back, cleanup.
- DoD/evidence: readiness passes before mutation; all four live cases and independent deterministic review are case-recorded; evidence is readable in Multica; no private or transient artifact is tracked; branch remains preserved and unmerged.
- Parallel-safety rationale: live and independent verification require the consolidated published candidate and therefore follow WP-5.

## Frontier validation

- Stage 1 frontier: WP-1 establishes shared contract authority.
- Stage 2 frontier: WP-2, WP-3, and WP-4 are independent siblings with disjoint responsibility/write zones and may execute concurrently.
- Stage 3 frontier: WP-5 integrates all sibling results and publishes the candidate.
- Stage 4 frontier: WP-6 verifies the immutable candidate and publishes evidence.

The graph has a real three-way parallel frontier. WIP policy is operational and is not encoded as extra dependencies or stages.
