## Delivery contract

- Change: `update-multica-0-7-2`
- Planning base: `b268e3bec0436fe51727fda50583344f57663284`
- Upstream baseline: Multica `0.7.1` at `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`
- Upstream target: Multica `0.7.2` release `428864784` at `f05a525ac8e82f5e9169ad078e44f166fad6d5c8`
- Test repository: `https://github.com/maximchikAlexandr/multica-py`
- Estimate source of truth: root planning issue properties `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours`; this file intentionally contains no numeric estimate total.
- Planning authority: proposal, design, delta specs, and tasks in this change. Operational status and assignee state remain in Multica.

## E2E decision

`e2e_required=true`.

Most behavior is sufficiently proved by existing frozen operation/response tables, programmable `FakeMultica` component tests, process fixtures, contract checks, and CI. One irreducible gap requires real interaction: server-computed steering authority and foreign-chat privacy across independently authenticated member, self-agent, authorized-agent, and denied-agent callers. Fake responses can prove decoding but cannot prove actual-caller authorization.

The live scope is therefore limited to V072-06. It is currently `blocked_by_environment`: `tests/live/conftest.py` exposes one preauthenticated profile, and neither the repository nor the assigned E2E skill provides a supported way to authenticate as the three additional callers. Agent listing is not authentication. The test owner SHALL supply four isolated authenticated profile references and document their supported provisioning channel before implementation completion or parent-level Tester execution; credentials SHALL NOT be generated, copied, or inferred by the SDK work. Readiness SHALL fail before mutation when any profile, identity proof, or provisioning provenance is absent.

Per-run/global cap outcomes and race fallback remain deterministic contract/component cases. The SDK does not own server scheduling, and the pinned target exposes no barrier hook that can force the race without timing guesses. Daemon graceful timeout, selected profile/PID mismatch, forced-termination failure, and unconfirmed cleanup also remain lower-level cases: the SDK delegates those decisions to the pinned CLI, and `FakeMultica` plus the existing process-contract harness can assert exact argv, typed error propagation, no retry, and no SDK-side signal or executable-name kill. No live daemon failure is conditionally promised.

No before/after image is planned because the change does not intentionally alter visible CLI tables, logs, progress, summaries, or browser UI. If implementation changes visible output, verification SHALL stop for a planning revision that selects an actually available capture method and specifies equivalent baseline/candidate fixtures; no unavailable renderer is a prerequisite.

## Verification matrix

| Case ID | OpenSpec requirement / scenario | Verification gap and local E2E decision | Public boundary / schema | Local script | Independent Tester actions | CI disposition / test | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| V072-01 | Exact provenance, 209/209 commands, 196 responses, deterministic projection | Lower-level contract/source checks are sufficient | Approved contract and generated projection | None | Inspect exact identities, unique verdicts, source links, ignored paths, and repeated render from fresh checkout | Extend existing contract/upstream job | Exact release/tag/commits/digests; eight changed; no pending nodes; byte-stable render | Commands, exits, SHA, source/CI links in Multica; no image |
| V072-02 | Run-targeted rerun and deprecated legacy rerun | Unit/contract/fake-CLI rows fully prove mapping and result types | `IssueResource.rerun_task`, `TaskRun`, legacy action result | None | Inspect signatures/vectors and run full/short/narrow/fresh/error/warning cases | Existing non-live unit/contract/component jobs | Exact argv; typed task; issue context; no ID inference; one warning; distinct legacy type | Test/commit/file links and assertions; no image |
| V072-03 | Comment steering inputs, cap/race outcomes, and decoding | Lower-level rows prove validation, open decoding, caps and deterministic race-fallback mapping; only actual-caller authority/privacy remains V072-06 | Comment add/reply, `CommentTriggerOutcome`, supplements | None | Run content-channel, ordered flags, active, self/cap/race, attachment conflict, malformed/open outcome, and multi-receipt cases | Existing non-live unit/contract/component jobs | Exact argv; zero I/O on conflict; open values; documented cap responses; deterministic race fallback; independent ordered receipts | Test paths, command, exit, assertions; no image |
| V072-04 | Daemon force transport and error classification | Lower-level check sufficient: SDK delegates lifecycle policy and target has no safe failure-injection hook | `DaemonResource.stop`, action/process error boundary | None | Run ordinary/force argv through operation tables and `FakeMultica`; inject graceful-timeout, PID/profile mismatch, unresolved PID, force-failure, confirmed-termination, and unconfirmed-cleanup responses; inspect no SDK retry/signal fallback | Existing process/component jobs using `tests/fixtures/fake_multica` and `tests/component/test_process_contract.py` | No JSON fabrication; force presence only when true; exact typed failures; no retry, direct signal, state deletion, or executable-name kill | Test/fixture links and assertions; no live process mutation or image |
| V072-05 | Property 50/51/200/201 and task/chat privacy decoding | Table/fake-CLI rows sufficiently prove input and wire/error boundaries | Property create/update; agent tasks; issue runs/messages | None | Run all boundaries, type restrictions, actor authority fixtures, omission/false, redaction, and 404 classification | Existing non-live unit/contract/component jobs | Ordered 200 accepted; 201 zero-I/O failure; optional/open permission; no foreign transcript | Test paths, command, exit, assertions; no image |
| V072-06 | Real steering authority and foreign-chat privacy | `e2e_required`, currently blocked: actual-caller authorization/privacy cannot be proved with the one available authenticated profile | Public SDK over `multica-test` against isolated backend | Existing `tests/live` harness; optional focused `tests/live/test_v072.py` may be prepared but SHALL refuse mutation until all profile inputs pass readiness | After full WP fan-in and prerequisite resolution, validate four distinct caller identities; member creates uniquely labelled owner issue and two chat tasks, self-agent starts/owns the active run, authorized agent submits permitted steering, denied agent submits the denied request, member reads receipts/task visibility, and denied/foreign agent requests the other chat transcript expecting redacted not-found; reset uses fresh labelled fixtures, and member cleanup removes only run-owned comments/issues/chat fixtures while leaving profiles/credentials untouched | No CI credential provisioning. Run only in an existing protected live job after the test owner supplies all four profile references through a supported channel; otherwise report BLOCKED, not skipped/PASS | Caller IDs are distinct; self/authorized/denied outcomes match actual caller; receipt order is preserved; foreign content is absent and transcript returns redacted not-found; cleanup inventory contains no run-owned mutable fixture | Sanitized IDs, commands, exits, assertion summary, provisioning-channel label, revision and file links in Multica; no credentials, raw transcript, environment dump, or image |
| V072-07 | Daemon graceful/force identity and cleanup | Explicit lower-level exclusion from live E2E; target CLI owns OS lifecycle and offers no reproducible failure injector | `DaemonResource.stop`, approved target contract, `FakeMultica`, process harness | None | Independently inspect pinned target source mapping and execute V072-04 focused fixtures only; do not start, stop, signal, or corrupt any live daemon/profile | Existing process/component jobs | Every target outcome maps without fabricated success; SDK never performs fallback termination or state cleanup | Source/test links, command, exit, assertions in Multica; no daemon PID/profile evidence required |
| V072-08 | Documentation, repository gates, exact-SHA publication | Repository/CI checks are sufficient | Docs, Makefile, CI, package artifacts | None | Check scenario mapping, strict validation, focused results, published SHA, CI and tracked-tree hygiene | Existing CI with required extensions | OpenSpec/contract/source/tests/types/lint/docs/package clean; local SHA equals remote; evidence accessible | CI/MR/commit/file links and sanitized attachments in Multica; no diagnostic files committed |

## Script and environment contract

- Implementer SHALL reuse the existing pytest/live infrastructure and shared fixtures. The only permitted new test module is one focused `tests/live/test_v072.py` when adding readiness and V072-06 rows to `tests/live/test_smoke.py` would obscure unrelated smoke coverage. No second runner, validator, orchestration layer, credential provisioner, or test dependency is allowed.
- The live entry command SHALL select only V072-06 and SHALL record the candidate SDK SHA plus `multica version --output json` target identity before consuming an attempt. Automatic local runs remain subject to the ten-minute limit; manual Tester actions are not.
- Required external inputs are four distinct profile references: `member_profile`, `self_agent_profile`, `authorized_agent_profile`, and `denied_agent_profile`, plus a non-secret `provisioning_channel` label supplied by the test owner. The current repository provides only one profile and no provisioning channel, so these inputs are unavailable at the planning base. Private values, hostnames, Basic Auth, tokens, and personal data SHALL not be committed or echoed.
- Readiness SHALL use a benign authenticated identity/read call through each profile, prove four distinct caller IDs and expected project/task relationships, confirm exact product revision, target CLI version/commit and stand health, and then create no data if any assertion fails. Agent listing SHALL NOT satisfy caller authentication. A readiness failure consumes no live attempt and produces BLOCKED evidence.
- V072-06 setup SHALL have the member profile create a uniquely labelled disposable owner issue and two chat tasks; the self-agent profile SHALL own/start the active run; the authorized and denied profiles SHALL be bound only to their intended permission relations. Each attempt SHALL use fresh issue/run/chat fixtures. Cleanup SHALL switch back to the member profile, enumerate the unique label, delete only run-owned comments/issues/chat fixtures in dependency order, verify the label inventory is empty, and leave all supplied profiles/credentials untouched. Failed cleanup remains a failure and records sanitized fixture IDs for owner recovery.
- Cap limits and race fallback SHALL be exercised with deterministic lower-level input/output fixtures, including values immediately below/at/above each reviewed cap and a pinned race-fallback response. No sleep, timing loop, or live synchronization hook is permitted unless a future planning revision identifies a supported target barrier.
- V072-07 SHALL use only `tests/fixtures/fake_multica`, operation tables, and `tests/component/test_process_contract.py`. The fixture SHALL return each pinned CLI error shape while recording argv/exit/stderr; assertions SHALL prove the SDK does not retry, signal a PID, delete profile/state data, or kill by executable name. No real daemon/profile/data root/port is allocated.
- Each live case has one initial attempt and at most one repair rerun after deterministic diagnosis on a new candidate revision or corrected fixture. Repeating a PASS on unchanged revision/inputs is forbidden. Unresolved impact leaves the case unverified.
- Failure-safe cleanup removes only V072-06 run-owned mutable fixtures through the member profile and preserves supplied profiles, the branch, MR, commits, CI links, and Multica evidence. It SHALL NOT touch the primary daemon/containers, merge, close, or delete the branch/MR.

## Independent Tester and evidence contract

- The Independent Tester gate SHALL start on the implementation parent only after every WP child has completed and fanned in. Tester SHALL use a fresh checkout at the published candidate SHA, SHALL not edit implementation/CI tests/fixtures, and SHALL independently map V072-01 through V072-08 to concrete assertions before execution. No WP child completion depends on Tester execution or evidence.
- Automatic results, manual Tester observations, and CI outcomes remain distinct. A second invocation of pytest is not an independent walkthrough.
- PASS is case-specific and records candidate SHA, CLI version/commit, material fixture IDs, commands, exit codes, assertions, attempt number, and cleanup. A new candidate SHA requires impact assessment and reruns only affected cases.
- Normal development results, test scripts/fixtures, generated product artifacts, and real product commits belong in Git according to their natural commit boundaries. Actual logs, diagnostic JSON, hashes, command outputs, provenance evidence, images, and assertion narratives belong only in Multica.
- The final Tester comment SHALL include MR/commit/file and CI links, attach sanitized text evidence and any required images, and read back the comment and attachments. Private hostnames, credentials, profiles, tokens, raw chat content, personal data, and environment dumps are forbidden.

## Verification ownership and parent-level gate

- Implementer owns every OpenSpec task 1.1–6.4, including approved contract, generated projection, product code, lower-level tests, blocked-live readiness/preparation, CI, documentation, exact-SHA publication, and the parent-level verification manifest/handoff bundle.
- After full WP fan-in, Independent Tester owns the operational parent-level gate: independent inspection, focused lower-level execution, V072-06 execution only when its external prerequisite is satisfied, Multica-only evidence publication, attachment read-back, and findings. This gate has no OpenSpec task ID and belongs to no WP child.
- If the four authenticated profiles and supported provisioning provenance remain unavailable, the parent-level gate SHALL report BLOCKED and overall implementation delivery SHALL not be declared complete; it SHALL NOT simulate actors, treat agent listing as authentication, or downgrade the required live case.
- Planning verification and human implementation approval remain separate gates. This package does not authorize implementation.

## Estimate basis

The authoritative totals are stored only in the root planning issue properties. The estimate covers remaining work for one experienced developer familiar with the Python/CLI stack, without AI acceleration, from the exact planning base through implementation, tests, documentation, exact-revision verification, and likely review repairs. It excludes unattended CI time, approval queues, meetings, and external blocking.

Confidence is medium-low and calibration is unavailable. Acceptance is explicit, the current source/tests and the archived `0.7.1` upgrade are inspectable analogues, and the repository already contains the required lower-level extension points. Material uncertainty remains in the large approved-contract edit, exact target outcome fields, the unresolved external multi-profile prerequisite, and likely repair cycles across full typing/package gates. External waiting and test-owner credential provisioning are excluded from developer-hours. Tests were not run for estimation. A public-contract decision change, newly available target failure-injection hook, supplied live identities with materially different setup, or a target response shape that differs from the pinned review invalidates the estimate. Exact totals and range remain exclusively in the root issue properties.

## Delivery topology

`delivery_mode=dag` because the authoritative `Estimate, hours` property is above the single-package threshold and the graph has a genuine two-way parallel frontier after one shared contract foundation. Task coverage is complete and non-overlapping; dependencies are direct only. Stages are consecutive topological layers, and Manager SHALL copy the exact `wp_id -> stage` mapping to child issue `stage` fields.

Stage mapping: `WP-1 -> 1`, `WP-2 -> 2`, `WP-3 -> 2`, `WP-4 -> 3`, `WP-5 -> 4`.

### WP-1 — Approved 0.7.2 contract and generated foundation

- `stage`: 1
- `depends_on`: none
- OpenSpec task coverage: 1.1, 1.2, 1.3, 1.4, 1.5
- Deliverable: one validated `0.7.2` approved contract, closed command/response reconciliation, compatibility interval, and byte-stable generated projection that all domain packages consume.
- Owned responsibility scope: `contracts/sdk-contract.json`, contract schema/validation/render/source-link tooling as required, `src/multica_py/_generated/approved_sdk.py`, central generated operation/vector metadata, and directly related contract tests/fixtures. This package owns critical shared generated files for the graph.
- Contract surface: exact release/tag/source/binary identities; 209/209 node dispositions; 196 unique response verdicts; eight changed rows; public/hidden rerun classification; new input/output bindings; deterministic compatibility and source links.
- Definition of done/evidence: validate, source-checkout validation, render, check, source-link audit, inventory/response integrity, and repeated-render diff are clean; review/transient artifacts are absent from Git.
- Parallel-safety rationale: the predecessor centralizes all shared contract/generated writes before resource siblings begin.

### WP-2 — Issue rerun, comment steering, and task/chat privacy

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 2.1, 2.2, 2.3, 2.4, 2.5, 3.5, 3.6
- Deliverable: run-targeted rerun, deprecated legacy migration, safe comment steering/outcomes, caller-specific supplement permission, and foreign-chat privacy implemented through existing issue/comment/task paths.
- Owned responsibility scope: issue and comment resources, `TaskRun`/agent-task/comment wire/entity models, related exports and bound relations, centralized privacy-safe error fixtures, and focused unit/contract/component tests. It consumes and does not rewrite WP-1 contract/generated outputs after foundation handoff.
- Contract surface: full/short run ID and `--issue`/`--fresh`; distinct legacy action result and warning; ordered steering flags and attachment conflict; open outcome/supplement projections; actual-caller `can_supplement`; redacted foreign-chat 404.
- Definition of done/evidence: all mapping, validation, open/malformed decoding, warning, authority fixture, race fallback, multi-receipt, redaction, and typed-error cases pass with exact argv and zero-I/O negatives.
- Parallel-safety rationale: all shared issue/comment/task wire files belong here; sibling WP-3 owns daemon/property files and cannot edit this package's domain.

### WP-3 — Daemon force lifecycle and property capacity

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 3.1, 3.2, 3.3, 3.4
- Deliverable: truthful daemon force-stop transport/safety and reviewed 200-option property boundaries with deterministic process and resource coverage.
- Owned responsibility scope: daemon and property resources/models, process-lifecycle fixtures needed for stop, property case tables, and their focused unit/contract/component tests. Shared issue/comment/task wires belong to WP-2; generated bindings belong to WP-1.
- Contract surface: exact boolean `force`, no-JSON action result, timeout/PID/profile/termination/cleanup errors; select/multi-select 50/51/200/201 behavior and non-select restrictions.
- Definition of done/evidence: complete argv and process/error cases prove no SDK-side fallback kill or false success; property rows prove ordered capacity and zero-I/O rejection.
- Parallel-safety rationale: daemon/property production and test write zones are disjoint from WP-2's issue/comment/task ownership.

### WP-4 — Verification preparation and CI integration

- `stage`: 3
- `depends_on`: WP-2, WP-3
- OpenSpec task coverage: 4.1, 4.2, 4.3, 4.4, 4.5
- Deliverable: deterministic daemon/cap/race verification assets, a fail-closed four-profile authority/privacy readiness contract, run-owned fixture/reset/cleanup preparation, and safe CI integration with no new runner or credential provisioner.
- Owned responsibility scope: existing `tests/live` readiness/module, V072-06 setup/reset/cleanup preparation, `FakeMultica`/process-contract additions for task 4.3, applicable CI workflow changes, and directly related documentation. Domain unit/component files remain with predecessors unless an integration repair is required after both complete.
- Contract surface: exact candidate/CLI identity; four distinct authenticated profile inputs and provisioning provenance; permitted/denied/self relations; foreign-chat non-disclosure; deterministic cap/race and daemon outcome fixtures; blocked readiness; cleanup and attempt ledger; visible-output revision gate.
- Definition of done/evidence: lower-level nodes are deterministic; live readiness refuses mutation without all external inputs; setup/reset/cleanup procedures are executable once profiles are supplied; no live daemon is touched; secrets/private data are absent; and applicable CI uses the same exact revision. Actual Tester execution is not part of this WP.
- Parallel-safety rationale: this package starts after both product siblings and owns the shared live/CI integration surface without racing their domain edits.

### WP-5 — Documentation, full gates, publication, and verification handoff

- `stage`: 4
- `depends_on`: WP-4
- OpenSpec task coverage: 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4
- Deliverable: coherent migration/release documentation, complete scenario mapping, all Implementer repository gates, exact-SHA normal publication, and a complete parent-level independent-verification manifest/handoff bundle.
- Owned responsibility scope: compatibility/API/service/migration/coverage/changelog/contributing/packaging/release docs, cross-domain verification commands and integration repairs after predecessors close, publication proof, and preparation of the Tester manifest/evidence slots/read-back procedure.
- Contract surface: direct migration and deprecation guidance; OpenSpec/contract/source/tests/types/lint/docs/package gates; ten-minute automated-suite policy; exact local/remote SHA; MR/commit/file/CI links; blocked-live prerequisite; Multica-only result/attachment contract.
- Definition of done/evidence: every scenario maps to sufficient lower-level evidence or the explicit V072-06 blocker; required Implementer gates pass or the unsplit long suite is linked from CI; remote SHA equals candidate HEAD; the parent-level manifest and handoff bundle are published; no private/transient evidence is committed; branch/MR remain unmerged and preserved. Independent Tester execution/evidence is explicitly excluded from this WP and starts only after all children fan in.
- Parallel-safety rationale: the final integrator begins only after live/CI assets and all product packages close, so shared docs/gates/repairs cannot race active work.

## Frontier validation

- Stage 1 frontier: WP-1 only, because approved contract/generated authority is shared foundation.
- Stage 2 frontier: WP-2 and WP-3 are independent with disjoint production/test ownership and can run concurrently.
- Stage 3 frontier: WP-4 integrates both domains into deterministic verification preparation and CI readiness.
- Stage 4 frontier: WP-5 performs final documentation, Implementer gates, publication, and parent-level verification handoff preparation.

The graph therefore contains a real parallel frontier. WIP limits are operational Manager policy and are not encoded as dependencies or stages.
