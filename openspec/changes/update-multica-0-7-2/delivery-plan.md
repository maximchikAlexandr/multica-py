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

Most behavior is sufficiently proved by existing frozen operation/response tables, fake-CLI component tests, process fixtures, contract checks, and CI. Two gaps require real interaction: server-computed steering authority/privacy/race outcomes across member and agent identities, and daemon force behavior across graceful timeout, selected profile/PID identity, termination, and cleanup. Fake responses can prove decoding but cannot prove those server and operating-system decisions.

The live scope is therefore limited to cases V072-06 and V072-07 below. It reuses `tests/live`, the `multica-test` test profile/stand, and a dedicated `myl-623-tester-N` daemon profile. It adds no runner or broad product walkthrough. The main Multica profile, daemon, containers, reference checkout, and non-owned processes are forbidden.

No before/after image is planned because the change does not intentionally alter visible CLI tables, logs, progress, summaries, or browser UI. If implementation changes visible output, verification stops for a planning revision requiring actual baseline/candidate text and Mac PNG renders through the bundled `scripts/render_terminal.swift` from `openspec-e2e-testing`; redirected output must disclose ANSI/TTY/progress limits.

## Verification matrix

| Case ID | OpenSpec requirement / scenario | Verification gap and local E2E decision | Public boundary / schema | Local script | Independent Tester actions | CI disposition / test | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| V072-01 | Exact provenance, 209/209 commands, 196 responses, deterministic projection | Lower-level contract/source checks are sufficient | Approved contract and generated projection | None | Inspect exact identities, unique verdicts, source links, ignored paths, and repeated render from fresh checkout | Extend existing contract/upstream job | Exact release/tag/commits/digests; eight changed; no pending nodes; byte-stable render | Commands, exits, SHA, source/CI links in Multica; no image |
| V072-02 | Run-targeted rerun and deprecated legacy rerun | Unit/contract/fake-CLI rows fully prove mapping and result types | `IssueResource.rerun_task`, `TaskRun`, legacy action result | None | Inspect signatures/vectors and run full/short/narrow/fresh/error/warning cases | Existing non-live unit/contract/component jobs | Exact argv; typed task; issue context; no ID inference; one warning; distinct legacy type | Test/commit/file links and assertions; no image |
| V072-03 | Comment steering inputs and outcome decoding | Lower-level rows prove validation/decoding; live authority/race gap is V072-06 | Comment add/reply, `CommentTriggerOutcome`, supplements | None | Run content-channel, ordered flags, active, attachment conflict, malformed/open outcome, and multi-receipt cases | Existing non-live unit/contract/component jobs | Exact argv; zero I/O on conflict; open values; independent ordered receipts | Test paths, command, exit, assertions; no image |
| V072-04 | Daemon force transport and error classification | Process fixtures prove SDK behavior; actual identity/cleanup gap is V072-07 | `DaemonResource.stop`, action/process error boundary | None | Run ordinary/force argv and simulated timeout/mismatch/termination/cleanup cases; inspect no SDK kill fallback | Existing process/component jobs | No JSON fabrication; force presence; typed failures; no retry or executable-name kill | Test/fixture links and assertions; no image |
| V072-05 | Property 50/51/200/201 and task/chat privacy decoding | Table/fake-CLI rows sufficiently prove input and wire/error boundaries | Property create/update; agent tasks; issue runs/messages | None | Run all boundaries, type restrictions, actor authority fixtures, omission/false, redaction, and 404 classification | Existing non-live unit/contract/component jobs | Ordered 200 accepted; 201 zero-I/O failure; optional/open permission; no foreign transcript | Test paths, command, exit, assertions; no image |
| V072-06 | Real steering authority, caps, race fallback, receipts, and foreign-chat privacy | `e2e_required`: server authorization, scheduling race, and privacy cannot be proved by fake output | Public SDK over `multica-test` against isolated backend | Extend `tests/live/test_smoke.py` or add one focused `tests/live/test_v072.py` using existing fixtures | From fresh candidate checkout create disposable issue/runs/comments with permitted and denied member/agent actors; exercise explicit and active steering, self/caps/race fallback, multi-receipt, task pages, and foreign chat messages; inspect returned models and server state | Gated live job only where safe identities/credentials already exist; otherwise local-only with Multica evidence | Status/reason/receipt ordering matches server; ordinary trigger fallback remains; actual caller authority governs; foreign content absent and messages return redacted 404 | Sanitized IDs, commands, exits, assertion summary, revision and CI/file links in Multica; no raw transcript or image |
| V072-07 | Real daemon graceful/force identity and cleanup | `e2e_required`: OS process identity and cleanup confirmation require a real dedicated daemon | Public SDK/CLI using dedicated `myl-623-tester-N` profile | Same focused live module and existing daemon/process helpers | Record primary daemon PID without modifying it; start owned dedicated daemon/profile; verify normal stop, controlled graceful-timeout force path when fixture supports it, PID/profile mismatch refusal, and confirmed cleanup; compare exact child PID before any termination | Local isolated process case; CI only if existing runner supports safe dedicated daemon profiles | Primary PID untouched; only owned exact PID can terminate; mismatch/unconfirmed cleanup fails; status/profile files cleaned only on confirmed success | Commands/exits, sanitized profile label, PID hashes/observations and cleanup result in Multica; no raw environment dump or image |
| V072-08 | Documentation, repository gates, exact-SHA publication | Repository/CI checks are sufficient | Docs, Makefile, CI, package artifacts | None | Check scenario mapping, strict validation, focused results, published SHA, CI and tracked-tree hygiene | Existing CI with required extensions | OpenSpec/contract/source/tests/types/lint/docs/package clean; local SHA equals remote; evidence accessible | CI/MR/commit/file links and sanitized attachments in Multica; no diagnostic files committed |

## Script and environment contract

- Implementer SHALL reuse the existing pytest/live infrastructure and shared fixtures. The only permitted new test module is one focused `tests/live/test_v072.py` when adding rows to `tests/live/test_smoke.py` would obscure unrelated smoke coverage. No second runner, validator, orchestration layer, or test dependency is allowed.
- The live entry command SHALL select only V072-06/V072-07 nodes and SHALL record the candidate SDK SHA plus `multica version --output json` target identity before consuming an attempt. Automatic local runs remain subject to the ten-minute limit; manual Tester actions are not.
- Runtime parameters SHALL be supplied through existing test configuration: test CLI executable/profile, stand endpoint, permitted member/agent identities, dedicated profile name, owned data root, and owned port if needed. Private values, hostnames, Basic Auth, tokens, and personal data SHALL not be committed or echoed.
- V072-06 setup creates disposable issues, runs, comments, and chat fixtures with unique `myl-623` labels. V072-07 setup creates one dedicated daemon profile/data root and records the primary daemon PID solely to prove it is not targeted.
- Readiness SHALL confirm exact product revision, target CLI version/commit, stand health, actor permissions, unique fixtures, dedicated profile/data/port availability, and that the dedicated PID differs from the primary daemon. A readiness failure consumes no live attempt.
- Each live case has one initial attempt and at most one repair rerun after deterministic diagnosis on a new candidate revision or corrected fixture. Repeating a PASS on unchanged revision/inputs is forbidden. Unresolved impact leaves the case unverified.
- Failure-safe cleanup stops only the exact owned daemon PID after re-reading dedicated and primary daemon status, removes run-owned mutable fixtures/profile/data, and preserves the branch, MR, commits, CI links, and Multica evidence. It SHALL NOT merge, close, or delete the branch/MR.

## Independent Tester and evidence contract

- Tester SHALL use a fresh checkout at the published candidate SHA, SHALL not edit implementation/CI tests/fixtures, and SHALL independently map V072-01 through V072-08 to concrete assertions before execution.
- Automatic results, manual Tester observations, and CI outcomes remain distinct. A second invocation of pytest is not an independent walkthrough.
- PASS is case-specific and records candidate SHA, CLI version/commit, material fixture IDs, commands, exit codes, assertions, attempt number, and cleanup. A new candidate SHA requires impact assessment and reruns only affected cases.
- Normal development results, test scripts/fixtures, generated product artifacts, and real product commits belong in Git according to their natural commit boundaries. Actual logs, diagnostic JSON, hashes, command outputs, provenance evidence, images, and assertion narratives belong only in Multica.
- The final Tester comment SHALL include MR/commit/file and CI links, attach sanitized text evidence and any required images, and read back the comment and attachments. Private hostnames, credentials, profiles, tokens, raw chat content, personal data, and environment dumps are forbidden.

## Verification ownership

- Implementer owns OpenSpec tasks 1.1–6.3, including approved contract, generated projection, product code, lower-level/live tests and fixtures, CI, documentation, and exact-SHA publication.
- Independent Tester owns execution and evidence for task 6.4 and reports findings without modifying implementation artifacts.
- Planning verification and human implementation approval remain separate gates. This package does not authorize implementation.

## Estimate basis

The authoritative totals are stored only in the root planning issue properties. The estimate covers remaining work for one experienced developer familiar with the Python/CLI stack, without AI acceleration, from the exact planning base through implementation, tests, documentation, exact-revision verification, and likely review repairs. It excludes unattended CI time, approval queues, meetings, and external blocking.

Confidence is medium and calibration is unavailable. Acceptance is explicit, the current source/tests and the archived `0.7.1` upgrade are inspectable analogues, and the repository already contains the required extension points. Material uncertainty remains in the large approved-contract edit, exact target outcome fields, race-safe live fixtures, dedicated daemon cleanup cases, and likely repair cycles across full typing/package gates. Tests were not run for estimation. A public-contract decision change, unavailable test identities, or a target response shape that differs from the pinned review invalidates the estimate. Exact totals and range remain exclusively in the root issue properties.

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

### WP-4 — Isolated live verification assets and CI integration

- `stage`: 3
- `depends_on`: WP-2, WP-3
- OpenSpec task coverage: 4.1, 4.2, 4.3, 4.4, 4.5
- Deliverable: focused reusable live fixtures/cases for real steering/privacy and daemon identity/cleanup plus safe CI integration, with no new runner.
- Owned responsibility scope: existing `tests/live` harness/module, live fixtures, applicable CI workflow changes, run-owned setup/readiness/cleanup logic, and directly related documentation. Domain unit/component files remain with predecessors unless an integration repair is required after both complete.
- Contract surface: exact candidate/CLI identity; permitted/denied actors; steering caps/race/receipts; foreign-chat non-disclosure; dedicated profile/PID separation; cleanup and attempt ledger; conditional visible-output capture gate.
- Definition of done/evidence: selected live nodes are repeatable on the isolated stand, readiness consumes no attempt, primary daemon is untouched, cleanup is failure-safe, secrets/private data are absent, and applicable CI uses the same exact revision.
- Parallel-safety rationale: this package starts after both product siblings and owns the shared live/CI integration surface without racing their domain edits.

### WP-5 — Documentation, full gates, publication, and independent evidence

- `stage`: 4
- `depends_on`: WP-4
- OpenSpec task coverage: 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4
- Deliverable: coherent migration/release documentation, complete scenario mapping, all repository gates, exact-SHA normal publication, and independent Tester evidence with read-back.
- Owned responsibility scope: compatibility/API/service/migration/coverage/changelog/contributing/packaging/release docs, cross-domain verification commands and integration repairs after predecessors close, publication proof, and Tester evidence coordination.
- Contract surface: direct migration and deprecation guidance; OpenSpec/contract/source/tests/types/lint/docs/package gates; ten-minute automated-suite policy; exact local/remote SHA; MR/commit/file/CI links; Multica-only results and attachments.
- Definition of done/evidence: every scenario maps to sufficient evidence; required gates pass or the unsplit long suite is linked from CI; remote SHA equals candidate HEAD; Tester evidence is attached and read back; no private/transient evidence is committed; branch/MR remain unmerged and preserved.
- Parallel-safety rationale: the final integrator begins only after live/CI assets and all product packages close, so shared docs/gates/repairs cannot race active work.

## Frontier validation

- Stage 1 frontier: WP-1 only, because approved contract/generated authority is shared foundation.
- Stage 2 frontier: WP-2 and WP-3 are independent with disjoint production/test ownership and can run concurrently.
- Stage 3 frontier: WP-4 integrates both domains into isolated live/CI verification.
- Stage 4 frontier: WP-5 performs final documentation, gates, publication, and independent evidence.

The graph therefore contains a real parallel frontier. WIP limits are operational Manager policy and are not encoded as dependencies or stages.
