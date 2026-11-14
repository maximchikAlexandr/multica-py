## Delivery contract

- Change: `update-multica-0-9-0`
- Planning issue: `MYL-662`
- Planning base: `b268e3bec0436fe51727fda50583344f57663284`
- Source test repository: `https://github.com/maximchikAlexandr/multica-py`
- Upstream baseline: Multica `0.7.1` at `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`
- Upstream target: Multica `0.9.0` release `444052572` at `8cd8a2db978d532d8627c78cd29f05deab6c6f17`
- Estimate source of truth: the root planning issue properties `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours`; this file intentionally contains no numeric O/M/P/E total.
- Planning authority: proposal, design, delta specs, tasks, and this delivery contract. Live status and assignees remain in Multica.

## E2E decision

`e2e_required=true`.

Most requirements are deterministically provable through the existing approved-contract validator/generator, table-driven unit/contract rows, fake-CLI components, controlled filesystem/process fixtures, packaging tests, and CI. Five remaining results depend on a real `0.9.0` CLI/backend interaction and cannot be established by those layers alone: run-targeted rerun lifecycle, private-project authorization filtering, project-inherited subscriber provenance, safe runtime-update failure, and exact runtime-usage window behavior. A deterministic public action that makes the real backend return HTTP 499 with no body does not exist in the reviewed `0.9.0` surface, so that classification is proved at the fake-CLI/process boundary and SHALL NOT be reported as live evidence.

The live scope is therefore focused and reuses `tests/live/test_smoke.py`, `scripts/e2e/verify_multica_test.py`, `.github/workflows/live-smoke.yml`, and the isolated project stand described by the Multica project. No second runner, browser framework, profile-discovery layer, or private URL is added to Git. Stand URL, profile, daemon, credentials, database, ports, and identity are runtime parameters supplied through the protected environment. Planning does not execute tests.

## Verification matrix

| Case ID | OpenSpec requirement / tasks | Verification gap and local E2E decision | Public boundary / schema | Local script | Independent agent steps | CI disposition | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| V090-01 | Exact provenance, 236 command nodes, 196 response verdicts, deterministic projection; 1.1–1.5 | Lower-level contract checks are sufficient | Approved contract schema and generated projection | Existing contract validate/render/check and source-link commands | Fresh-checkout comparison of identities, inventory counts, verdict uniqueness, canonical vectors, and repeated render | Extend `contract-check` for exact `0.9.0` source | Exact identities; 236/236; 28/1/18 deltas; 196 unique rows; no pending; byte-stable render | Commands, exits, exact SHA, contract/file links in Multica; no image |
| V090-02 | Issue requester/list creator and project visibility/creator; 2.1–2.2 | Frozen wire and fake-CLI cases sufficiently prove field presence; private authorization result is covered by V090-09 live | Existing issue/project list/get models and standard errors | Focused unit/contract/component nodes | Inspect present/omitted/null/malformed/open-value rows and run focused nodes | Existing non-live jobs | Typed values; old omission compatibility; malformed failure; no hidden identity synthesis | Test paths, assertions, exits; no image |
| V090-03 | Task credits/redaction, attachment dimensions, comment resolution; 2.3–2.6 | Lower-level decoding and exact operation tables are sufficient | Existing issue-run, agent-task, attachment, and comment envelopes | Focused table-driven unit/contract/component nodes | Compare both task paths and retained operation vectors; inspect malformed fixtures | Existing non-live jobs | Present/omitted/null/malformed parity; open future values; exact argv/destination/eager-preview | Test/file links and assertions; no image |
| V090-04 | Run-targeted rerun migration; 3.1–3.2, 3.5 | `e2e`: real lifecycle state and resume/fresh result remain after lower-level argv/result checks | Public SDK `projects.create`, `issues.create`, `issues.runs`, `issues.rerun_task`, and `issues.cancel_task` | Extend `tests/live/test_smoke.py` and its existing fixtures | With the protected rerun agent, create a unique project and assigned issue, wait boundedly for its source run to become terminal, invoke resume and fresh reruns, assert distinct linked runs, cancel any active reruns, then delete and verify removal of the project | Protected exact-SHA `live-smoke` | Old issue-targeted API absent; exact argv; resume/fresh produce distinct typed runs linked to the source issue/agent; invalid id remains standard; cleanup is verified | Sanitized lifecycle IDs, command/exits/assertions in Multica; no image unless visible output changes |
| V090-05 | Relationship fail-closed and atomic file binding; 3.3–3.4, 5.3 | Controlled fake CLI/filesystem fixtures are sufficient; no live mutation is needed | Existing issue create/update, comment, attachment, file/stdin paths | Focused unit/component/process nodes | Inspect no-transport assertions, literal argv/stdin, caller-file preservation, and cleanup | Existing non-live jobs | Invalid combinations perform zero I/O; special content literal; failures report no partial success; cleanup is scoped | Test/file links and exits; no image |
| V090-06 | Runtime capacity/usage and update exit; 4.1–4.2 | `e2e` for the server-owned usage window and a safe nonexistent-runtime update failure; fake-process rows cover successful update and failure-after-progress text | Public `runtimes.usage` and `runtimes.update`; fake CLI/process update rows | Extend live smoke usage/failure assertions and focused process fixtures | On the protected isolated runtime, call usage for 1 and 7 days and compare ordered UTC bounds/subset behavior; call update on the reserved absent UUID and prove standard nonzero failure plus unchanged runtime inventory; prove zero result and failure-after-text with exact fake-process rows | Protected exact-SHA `live-smoke` for usage/nonexistent update; existing non-live jobs for remaining update paths | Exact window and nonempty prepared sample; open provider/model; nonexistent update raises standard not-found/command error; runtime inventory unchanged; zero exit typed success; text cannot mask nonzero | Sanitized dates/error/assertion summary and CI link; no image unless output changes |
| V090-07 | User profile and workspace pin; 4.3 | Lower-level response fixtures and list-order rows are sufficient | Existing user profile and workspace list models | Focused unit/contract/component nodes | Inspect nullable/omitted/malformed fixtures and pinned-first ordering | Existing non-live jobs | Nullable profile value; optional RFC3339 pin; stable pinned-first ordering; malformed failure | Test paths and assertions; no image |
| V090-08 | Project-inherited subscribers and safe relations; 4.4–4.5 | `e2e`: real inherited provenance remains after decoder/loader tests and requires an administrator-seeded subscription because `0.9.0` has no public CLI/SDK project-subscription mutation | Public `issues.subscribers.list` and bound relations | Extend live smoke and its existing fixtures | Read the protected seeded project/issue, assert their relationship, list issue subscribers, and match the expected user with `reason=project`; do not mutate the persistent fixture | Protected exact-SHA `live-smoke` | `reason=project`; identity/order/cursor preserved; no duplicate direct row; omitted/redacted identifiers create no loader | Sanitized IDs and assertions in Multica; no image |
| V090-09 | 499/no-body and private-project semantics; 5.1–5.2, 5.4 | Split proof: 499/no-body at deterministic fake CLI/process boundary; private authorization against live server | Shared transport/standard errors; public project/issue reads under two profiles | Focused process fixture plus live-smoke | Feed an exact 499/no-stdout process result and assert standard cancellation; with verified distinct primary/denied profiles, create a unique private project and issue, prove denied get/list omission, then delete and verify removal | Existing non-live jobs for 499; protected exact-SHA `live-smoke` for privacy | Cancellation is not shape error and needs no body; private direct reads are not-found; lists omit IDs; profiles are distinct; no identity leak | Sanitized assertions and CI link; no raw private response or image |
| V090-10 | Documentation, CI, full repository gates; 6.1–6.5 | Repository/CI checks are sufficient | Docs, Makefile, workflows, package artifacts | Existing Make targets and strict OpenSpec validation | Verify migration example compiles, deferred list matches contract, and exact-SHA CI covers required gates | Existing CI; unsplit suite moves to CI when local ten-minute policy applies | OpenSpec, contract, sources, operations, tests, mypy, Ruff, docs, package, live collection, clean Git | Commands/exits, CI/PR/commit/file links; no raw logs committed |
| V090-11 | Independent delivery evidence; 7.1–7.6 | Manual independent evidence contract; not another automated suite | Exact Git revision, Multica comment/attachments, PR/CI links | Existing scripts only | Fresh checkout, case mapping, readiness gate, run only unresolved live cases, impact-assess new SHA, post and read back evidence, clean run-owned data | CI evidence consumed, not duplicated | Local SHA equals remote; every case PASS/FAIL is revision-bound; attachments accessible; branch/PR preserved | Multica attachments and links; conditional PNG contract below |

## Protected fixture ownership and exact live procedures

The administrator of the protected GitHub environment `multica-live` owns the stand prerequisites. Before dispatch, that administrator SHALL provision and protect these inputs beside the existing CLI/server/workspace/profile values: `MULTICA_LIVE_PRIMARY_USER_ID`, `MULTICA_LIVE_DENIED_PROFILE`, `MULTICA_LIVE_DENIED_USER_ID`, `MULTICA_LIVE_RERUN_AGENT_ID`, `MULTICA_LIVE_RUNTIME_ID`, `MULTICA_LIVE_SUBSCRIPTION_PROJECT_ID`, `MULTICA_LIVE_SUBSCRIPTION_ISSUE_ID`, and `MULTICA_LIVE_SUBSCRIBER_USER_ID`. The two profiles SHALL be pre-authenticated human workspace members with distinct `users.profile_get().id` values. The denied user SHALL not be a member of a private project created by the test. The runtime SHALL belong only to the isolated stand and contain at least one usage row in the last UTC day so both requested windows are observable.

The same administrator SHALL seed the persistent subscriber fixture by using the server's supported `PUT /api/projects/{project_id}/subscription` endpoint under the primary test identity, because the reviewed `0.9.0` CLI/SDK exposes no project-subscription mutation. The configured issue SHALL belong to that project and its issue subscriber list SHALL expose exactly the configured user with `reason=project` and no duplicate direct row. The candidate and Tester treat this fixture as read-only. The administrator also SHALL supply an executable test agent that may receive a disposable issue. Missing, mismatched, unobservable, or unauthorized prerequisites block live-smoke dispatch; the workflow reports the missing variable/assertion and SHALL NOT invent an identity, subscription, runtime mutation, or second attempt.

The existing `tests/live/conftest.py` readiness fixture SHALL construct primary and denied clients from their protected profiles; call `auth.status()` and `users.profile_get()` for both; compare IDs to the protected expected values; assert the IDs differ; verify the workspace, rerun agent, runtime, seeded project, and seeded issue are readable from the primary profile; verify the seeded issue belongs to the seeded project; and verify the expected inherited subscriber row. These checks run before any disposable mutation.

The live cases SHALL use these reproducible actions:

1. Rerun: the primary client creates a UUID-suffixed disposable project and an issue assigned to `MULTICA_LIVE_RERUN_AGENT_ID`; bounded polling of `issues.runs(issue.id)` waits for the initial run to reach a terminal state. It calls `issues.rerun_task(source_run.id, issue_id=issue.id, fresh=False)` and then the same public method with `fresh=True`, asserting distinct new run IDs, source issue/agent linkage, and the requested resume/fresh semantics. In `finally`, it calls `issues.cancel_task(run.id, issue_id=issue.id)` for every queued/running rerun, polls boundedly for terminal state, deletes the disposable project, and verifies `projects.get(project.id)` returns standard not-found. Any failed cancellation or deletion is a cleanup failure in the evidence.
2. Runtime usage and safe failure: the primary client records the IDs from `runtimes.list()`, calls `runtimes.usage(MULTICA_LIVE_RUNTIME_ID, days=1)` and `days=7`, and asserts nonempty prepared samples, unique ascending UTC dates, no date older than each inclusive server window, and that the one-day rows are a subset of the seven-day rows. It then calls `runtimes.update("00000000-0000-0000-0000-000000000000", target_version="0.9.0", wait=True)` and asserts the standard not-found/command error and nonzero process outcome. A second `runtimes.list()` SHALL have the same IDs, proving no stand runtime was altered. Successful update and failure-after-progress-text remain exact fake-process tests because mutating the shared prepared runtime is not safe.
3. Privacy: the primary client creates a UUID-suffixed project with `visibility="private"` and no denied-profile member, then creates one issue in it. The denied client asserts standard not-found from `projects.get` and `issues.get`, and asserts both IDs are absent from corresponding list traversal. In `finally`, the primary client deletes the project and verifies not-found. The distinct-profile readiness assertion is part of this case's evidence.
4. Inherited subscriber: the primary client reads the configured seeded project and issue, confirms the project binding, and calls `issues.subscribers.list(issue.id)`. It asserts one configured user row with `reason=project`, retained ordering/cursor behavior, and no direct duplicate. This case performs no mutation and has no candidate-owned cleanup; the protected-environment administrator owns fixture lifecycle.

The 499/no-body case SHALL use the existing fake-CLI/process harness: an exact fixture exits through the reviewed cancellation status path, writes no stdout body, and supplies only sanitized stderr context. The assertion is the SDK's standard cancellation exception rather than an output-shape exception. No live evidence may claim that the real backend emitted 499 unless a future public reproducible action is separately approved through planning.

## Script and environment contract

- Implementer SHALL extend only existing scripts/tests/fixtures required by the matrix: `tests/live/test_smoke.py`, `scripts/e2e/verify_multica_test.py`, existing table-driven cases, and `.github/workflows/live-smoke.yml`. A new script is allowed only if those seams cannot express a listed case, and that insufficiency must be documented before adding it.
- Automated entry commands remain the repository's focused pytest nodes, `make contract`, `make lint`, `make types`, `make package`, `make test`, and the trusted live-smoke workflow. The full automated local suite obeys the ten-minute rule and is never split to evade it.
- Protected runtime inputs include candidate SHA/PR, test CLI path and exact version, server URL, workspace, the two named profiles and expected user IDs, isolated daemon/backend/database/ports, rerun agent, prepared runtime, seeded subscriber fixture IDs, and credentials. Values remain outside public Git; variable names above are the executable workflow contract.
- Readiness requires a clean exact candidate checkout, successful focused lower-level checks, verified CLI `0.9.0` identity, isolated bindings distinct from the main Multica profile/daemon, all protected preflight assertions above, and registered `finally` cleanup for every disposable project/run. Failure blocks dispatch rather than weakening a case.
- The issue supplies no separate numeric live-attempt budget. Tester SHALL consume one consolidated attempt only after readiness; failures are diagnosed with captured evidence and lower-level checks before any authorized rerun. A new SHA reruns only impacted cases after explicit impact assessment.
- Cleanup removes only data, processes, temporary files, and local diagnostics created by the verification run. It preserves the evidence branch, PR, commits, CI links, and Multica attachments and SHALL NOT merge, close, or delete them.

## Independent Tester contract

- Tester SHALL use a fresh checkout at the published candidate SHA, verify remote equality, and SHALL not edit product code, CI tests, fixtures, or planning artifacts.
- Each case records the product SHA, test/evidence revision where different, material fixture identity, command, exit status, observable assertions, and PASS/FAIL. A second invocation of an automated test is not an independent manual check.
- Manual steps use public SDK/CLI actions and inspect returned typed objects, process outcomes, and server state. Browser UI is not required because no OpenSpec requirement changes browser behavior.
- Any finding that changes product scope, public naming, compatibility, destructive policy, or contract dependency returns to planning revision; an implementation defect returns to the Implementer without rewriting evidence.

## Image and publication contract

- The planned change does not require a visible CLI table, log, progress, summary, or browser UI change. Cases therefore require no decorative image when actual output remains unchanged.
- If implementation changes visible output, Tester SHALL preserve equivalent baseline `0.7.1` and candidate `0.9.0` text with locale, terminal width, TTY/color mode, fixture, and revision. On macOS, readiness SHALL confirm an actual terminal capture path using the system screenshot facility before the attempt; the resulting PNGs preserve the tested output language. A text-to-image render, if used, is labeled as a render rather than a terminal screenshot.
- Required filenames are `V090-<case>-baseline.txt`, `V090-<case>-candidate.txt`, `V090-<case>-baseline.png`, and `V090-<case>-candidate.png`. Missing mandatory text or PNG prevents PASS for that visible-output case.
- The final Tester comment SHALL attach required images and sanitized compact evidence, include PR/commit/file/CI links, and be read back to confirm attachment accessibility. Commands, outputs, diagnostic JSON, hashes, provenance, and images remain Multica-only unless the generated file itself is the product behavior under test.

## Estimate basis

The authoritative totals are stored only in the root planning issue properties. The estimate covers remaining work for one experienced developer familiar with Python and CLI SDKs, without AI acceleration, from base `b268e3bec0436fe51727fda50583344f57663284` through implementation, required tests and documentation, likely review repairs, exact-revision publication, and implementation-side verification support. It excludes unattended CI time, approval queues, meetings, and external blocking.

Confidence is medium and calibration is unavailable. Acceptance is explicit, all affected paths and close upstream-upgrade analogues are inspectable, and the verified upstream dossier closes the command and response inventories. Material bounded uncertainty remains in translating the large reviewed dossier into the approved contract, cross-version presence fixtures, safe live authorization/lifecycle setup, and likely repair cycles across the full offline/package gates. Tests were not run for estimation. Numeric O/M/P/E totals are intentionally not duplicated here.

The estimate covers contract/provenance work; typed model, resource, relation, and transport adaptations; tests/fixtures; migration and compatibility documentation; CI/live-smoke extension; exact-revision publication; and likely review fixes. It excludes deferred command families, destructive issue deletion, implementation of UI/process-control candidates, unattended CI time, human approval queues, and external outages. A scope change that promotes a deferred family, changes destructive policy, removes the isolated live environment, or changes the approved base invalidates the estimate.

## Delivery topology

`delivery_mode=dag` because the authoritative `Estimate, hours` property exceeds the single-package threshold and the graph has a genuine three-way parallel frontier after one shared contract foundation. Task coverage is complete and non-overlapping. Dependencies below are direct only; stages are consecutive topological layers.

Stage mapping: `WP-1 -> 1`, `WP-2 -> 2`, `WP-3 -> 2`, `WP-4 -> 2`, `WP-5 -> 3`.

### WP-1 — Approved contract and generated foundation

- `stage`: 1
- `depends_on`: none
- OpenSpec task coverage: 1.1, 1.2, 1.3, 1.4, 1.5
- Deliverable: one validated `0.9.0` approved contract, complete command/response reconciliation, compatibility metadata, generated projection, and central canonical operation/decoder vectors consumed by all domain work.
- Owned responsibility scope: `contracts/sdk-contract.json`, its schema and validate/render/check/source-link tooling where required, `src/multica_py/_generated/approved_sdk.py`, `tests/cases/operations.py`, central decoder/vector metadata, and directly related contract tests/fixtures. These are critical shared files and no Stage-2 sibling may edit or regenerate them.
- Contract surface: exact release/source/archive/executable identities; tested interval; 236 command dispositions and mappings; 196 response verdicts; deterministic generated bindings, validators, sources, and vectors.
- Definition of done/evidence: validate/render/check and source-link audit pass; inventory and response counts are exact; two renders are byte-identical; no evidence, `.devlocal`, binary, archive, diagnostic, or transient render is tracked.
- Parallel-safety rationale: this predecessor owns every shared contract/generated write before domain siblings start, preventing concurrent edits to the largest conflict surface.

### WP-2 — Issue, project, task, subscriber, and relation domain

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 2.1, 2.2, 2.3, 2.5, 3.1, 3.2, 3.3, 4.4, 4.5, 5.4
- Deliverable: typed issue/project/task additions, explicit run-targeted rerun migration, project-inherited subscribers, authorization-safe relations/private-project behavior, and fail-closed issue relationship mutations.
- Owned responsibility scope: issue/project/task/subscriber models and resources, `src/multica_py/resources/issues.py`, their bound relation loaders, and only their focused test modules such as `tests/unit/resources/test_issues.py` and existing issue/project/subscriber relation tests. It consumes but SHALL NOT edit `tests/cases/operations.py`, attachment/comment test modules, shared transport/process files, WP-4 system tests, root exports, or shared docs/CI.
- Contract surface: requester/list creator, project visibility/creator, task credits/redaction, rerun-task resume/fresh, mutation prevalidation, private 404/omission/redaction, subscriber `reason=project`, cursor/order, and omitted/redacted loader behavior.
- Definition of done/evidence: present/omitted/null/malformed/open-value focused rows pass without modifying the central operation table; obsolete issue rerun is absent with compiling migration; invalid relationships perform zero transport/mutation; inherited/direct subscribers remain distinguishable; hidden identifiers produce no loader/permalink; private identities are not synthesized or leaked.
- Parallel-safety rationale: this package owns the complete issue/project/task/subscriber relation test zone. It has no write authority over WP-3 attachment/comment tests, WP-4 runtime/user/workspace tests, or WP-1's central operation/vector tables; root integration waits for WP-5.

### WP-3 — Attachment, comment, transport, and literal input boundaries

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 2.4, 2.6, 3.4, 5.1, 5.2, 5.3
- Deliverable: typed attachment dimensions and comment resolution, one shared 499/no-body cancellation classification, atomic attachment binding, and preserved literal comment/attachment file/stdin behavior with scoped cleanup.
- Owned responsibility scope: attachment/comment models and resources, `src/multica_py/_internal/transport.py`, process/error helpers, `tests/unit/resources/test_attachments.py`, `tests/unit/resources/test_issue_comments.py`, and focused transport/process fixtures. It consumes but SHALL NOT edit `tests/cases/operations.py`, WP-2 issue/project/task/subscriber test modules, WP-4 system tests, root exports, or shared docs/CI.
- Contract surface: attachment dimensions, comment resolution, cancellation status/body, neighboring nonzero errors, atomic binding, sanitized stderr/command context, literal argv/stdin, caller-file preservation, run-owned temporary cleanup, and passive preview.
- Definition of done/evidence: attachment/comment present/omitted/null/malformed rows pass in their exclusively owned modules; cancellation cannot degrade into an output-shape error; other nonzero exits retain standard classification; shell-like content remains literal; failed binding reports no partial success; cleanup proves no caller data loss or leaked run-owned temporary input.
- Parallel-safety rationale: this package exclusively owns both attachment/comment test modules and shared transport/process tests. It does not touch WP-2 relation tests, WP-4 system tests, or WP-1's central tables; root integration waits for WP-5.

### WP-4 — Runtime, user, and workspace adaptations

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 4.1, 4.2, 4.3
- Deliverable: typed runtime capacity/usage/update behavior, nullable user-profile value, and workspace pin projection/order.
- Owned responsibility scope: runtime/user/workspace resources and models, `src/multica_py/models/system.py`, `tests/unit/resources/test_runtimes.py`, and existing user/workspace/system focused fixtures and tests. It consumes but SHALL NOT edit `tests/cases/operations.py`, subscriber/issue relation tests, attachment/comment tests, shared transport/process files, root exports, or shared docs/CI.
- Contract surface: exact usage window, runtime update exit/result, open provider/model values, `whats_new_seen_version`, `pinned_at`, and stable pinned-first ordering.
- Definition of done/evidence: complete presence and malformed focused fixtures pass without modifying the central operation table; runtime nonzero cannot report success; pinned ordering and exact usage windows are asserted.
- Parallel-safety rationale: this package exclusively owns the runtime/user/workspace system test zone and has no subscriber or shared table responsibility. Shared root exports, CI, and docs are reserved for WP-5.

### WP-5 — Integration, documentation, live verification, and exact-SHA delivery

- `stage`: 3
- `depends_on`: WP-2, WP-3, WP-4
- OpenSpec task coverage: 3.5, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
- Deliverable: coherent public exports/docs/CI, all repository gates, focused protected live evidence for unresolved real-boundary gaps, normal exact-SHA publication, and independent Tester evidence/read-back.
- Owned responsibility scope: root exports, cross-domain integration helpers/tests, compatibility/API/migration/coverage/changelog/contributing/release docs, CI/live-smoke workflow and verifier integration, publication proof, and evidence coordination. After predecessors complete, this package alone may reconcile cross-domain operation-table/vector fallout in `tests/cases/operations.py` and make necessary integration repairs across predecessor areas, recording them explicitly.
- Contract surface: documented compatibility and rerun migration; scenario-to-test mapping; strict offline/package/release gates; protected exact-SHA live cases; conditional visible-output captures; local/remote SHA equality; Multica attachment/read-back and cleanup contracts.
- Definition of done/evidence: focused and required full gates pass under the ten-minute/CI policy; every scenario maps to a sufficient assertion or focused live result; local/remote SHA match; independent evidence is attached and read back without private data; branch/PR/commits remain unmerged and preserved.
- Parallel-safety rationale: this integrator starts only after all domain siblings close, so root exports, shared helpers, docs, CI, live fixtures, and cross-domain repairs cannot race active sibling writes.

## Frontier validation

- Stage 1 frontier: WP-1 only, because approved contract/generated authority must be established once.
- Stage 2 frontier: WP-2 owns issue/project/task/subscriber relation modules and focused tests; WP-3 owns attachment/comment plus transport/process modules and tests; WP-4 owns runtime/user/workspace modules and system tests. All three consume WP-1's `tests/cases/operations.py` and decoder/vector metadata read-only, so their critical write-zones are concrete and disjoint.
- Stage 3 frontier: WP-5 integrates completed siblings and performs documentation, repository gates, live evidence, and publication.

The graph has a real three-way parallel frontier. WIP limits are operational Manager policy and are not encoded as extra dependencies or stages.
