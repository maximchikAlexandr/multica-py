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

Most requirements are deterministically provable through the existing approved-contract validator/generator, table-driven unit/contract rows, fake-CLI components, controlled filesystem/process fixtures, packaging tests, and CI. Six remaining results depend on a real `0.9.0` CLI/backend interaction and cannot be established by those layers alone: run-targeted rerun lifecycle, server cancellation status/body, private-project authorization filtering, project-inherited subscriber provenance, runtime-update process exit, and exact runtime-usage window behavior.

The live scope is therefore focused and reuses `tests/live/test_smoke.py`, `scripts/e2e/verify_multica_test.py`, `.github/workflows/live-smoke.yml`, and the isolated project stand described by the Multica project. No second runner, browser framework, profile-discovery layer, or private URL is added to Git. Stand URL, profile, daemon, credentials, database, ports, and identity are runtime parameters supplied through the protected environment. Planning does not execute tests.

## Verification matrix

| Case ID | OpenSpec requirement / tasks | Verification gap and local E2E decision | Public boundary / schema | Local script | Independent agent steps | CI disposition | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| V090-01 | Exact provenance, 236 command nodes, 196 response verdicts, deterministic projection; 1.1–1.5 | Lower-level contract checks are sufficient | Approved contract schema and generated projection | Existing contract validate/render/check and source-link commands | Fresh-checkout comparison of identities, inventory counts, verdict uniqueness, canonical vectors, and repeated render | Extend `contract-check` for exact `0.9.0` source | Exact identities; 236/236; 28/1/18 deltas; 196 unique rows; no pending; byte-stable render | Commands, exits, exact SHA, contract/file links in Multica; no image |
| V090-02 | Issue requester/list creator and project visibility/creator; 2.1–2.2 | Frozen wire and fake-CLI cases sufficiently prove field presence; private authorization result is covered by V090-09 live | Existing issue/project list/get models and standard errors | Focused unit/contract/component nodes | Inspect present/omitted/null/malformed/open-value rows and run focused nodes | Existing non-live jobs | Typed values; old omission compatibility; malformed failure; no hidden identity synthesis | Test paths, assertions, exits; no image |
| V090-03 | Task credits/redaction, attachment dimensions, comment resolution; 2.3–2.5 | Lower-level decoding and exact operation tables are sufficient | Existing issue-run, agent-task, attachment, and comment envelopes | Focused table-driven unit/contract/component nodes | Compare both task paths and retained operation vectors; inspect malformed fixtures | Existing non-live jobs | Present/omitted/null/malformed parity; open future values; exact argv/destination/eager-preview | Test/file links and assertions; no image |
| V090-04 | Run-targeted rerun migration; 3.1–3.2, 3.5 | `e2e`: real lifecycle state and resume/fresh result remain after lower-level argv/result checks | Public SDK issue run operations and CLI `issue rerun-task` | Extend `tests/live/test_smoke.py`; invoke through existing verifier | Create disposable task/run, record run id, invoke resume then fresh through public SDK, inspect new run/result linkage, and remove run-owned issue data | Protected exact-SHA `live-smoke` | Old issue-targeted API absent; exact argv; resume/fresh distinguished; typed result and linkage; invalid id/error remain standard | Sanitized lifecycle IDs, command/exits/assertions in Multica; no image unless visible output changes |
| V090-05 | Relationship fail-closed and atomic file binding; 3.3–3.4, 5.3 | Controlled fake CLI/filesystem fixtures are sufficient; no live mutation is needed | Existing issue create/update, comment, attachment, file/stdin paths | Focused unit/component/process nodes | Inspect no-transport assertions, literal argv/stdin, caller-file preservation, and cleanup | Existing non-live jobs | Invalid combinations perform zero I/O; special content literal; failures report no partial success; cleanup is scoped | Test/file links and exits; no image |
| V090-06 | Runtime capacity/usage and update exit; 4.1–4.2 | `e2e`: server-owned day window and real process exit cannot be proved from fixture shape alone | Public runtime usage/update resources | Extend live smoke and existing verifier | On isolated runtime, compare requested days with returned boundary dates; execute controlled successful update check and a safe known nonzero update path without altering the shared daemon | Protected exact-SHA `live-smoke` | Exact window; open provider/model; zero exit typed success; nonzero raises despite text; no main daemon touched | Sanitized dates, exit/assertion summary, CI link; no image unless output changes |
| V090-07 | User profile and workspace pin; 4.3 | Lower-level response fixtures and list-order rows are sufficient | Existing user profile and workspace list models | Focused unit/contract/component nodes | Inspect nullable/omitted/malformed fixtures and pinned-first ordering | Existing non-live jobs | Nullable profile value; optional RFC3339 pin; stable pinned-first ordering; malformed failure | Test paths and assertions; no image |
| V090-08 | Project-inherited subscribers and safe relations; 4.4–4.5 | `e2e`: real inheritance and authorization-owned omission remain after decoder/loader tests | Public issue subscriber list and bound relations | Extend live smoke and existing verifier | Create disposable project/issue, add project subscriber through test CLI, list issue subscribers through SDK, inspect reason and relation; repeat with inaccessible fixture where available; clean created data | Protected exact-SHA `live-smoke` | `reason=project`; identity/order/cursor preserved; direct rows compatible; omitted/redacted identifiers create no loader | Sanitized IDs and assertions in Multica; no image |
| V090-09 | 499/no-body and private-project semantics; 5.1–5.2, 5.4 | `e2e`: actual status/body and server filtering require real CLI/backend | Shared transport, standard errors, issue/project public reads | Extend live smoke and verifier | Trigger a cancellable disposable run, cancel through supported public action, inspect status/body classification; use isolated permitted/denied identities for direct/list private-project reads | Protected exact-SHA `live-smoke` | Cancellation is standard cancellation, not shape error; no body required; private direct read is not-found; list omits; no identity leak | Sanitized stderr/status/assertions and CI link; no raw private response or image |
| V090-10 | Documentation, CI, full repository gates; 6.1–6.5 | Repository/CI checks are sufficient | Docs, Makefile, workflows, package artifacts | Existing Make targets and strict OpenSpec validation | Verify migration example compiles, deferred list matches contract, and exact-SHA CI covers required gates | Existing CI; unsplit suite moves to CI when local ten-minute policy applies | OpenSpec, contract, sources, operations, tests, mypy, Ruff, docs, package, live collection, clean Git | Commands/exits, CI/PR/commit/file links; no raw logs committed |
| V090-11 | Independent delivery evidence; 7.1–7.6 | Manual independent evidence contract; not another automated suite | Exact Git revision, Multica comment/attachments, PR/CI links | Existing scripts only | Fresh checkout, case mapping, readiness gate, run only unresolved live cases, impact-assess new SHA, post and read back evidence, clean run-owned data | CI evidence consumed, not duplicated | Local SHA equals remote; every case PASS/FAIL is revision-bound; attachments accessible; branch/PR preserved | Multica attachments and links; conditional PNG contract below |

## Script and environment contract

- Implementer SHALL extend only existing scripts/tests/fixtures required by the matrix: `tests/live/test_smoke.py`, `scripts/e2e/verify_multica_test.py`, existing table-driven cases, and `.github/workflows/live-smoke.yml`. A new script is allowed only if those seams cannot express a listed case, and that insufficiency must be documented before adding it.
- Automated entry commands remain the repository's focused pytest nodes, `make contract`, `make lint`, `make types`, `make package`, `make test`, and the trusted live-smoke workflow. The full automated local suite obeys the ten-minute rule and is never split to evade it.
- Protected runtime inputs include candidate SHA/PR, test CLI path and exact version, server URL, workspace/profile, isolated daemon, backend/database/ports, disposable actor and project identifiers, and credentials. Names and values remain outside public Git.
- Readiness requires a clean exact candidate checkout, successful focused lower-level checks, verified CLI `0.9.0` identity, isolated bindings distinct from the main Multica profile/daemon, disposable fixtures, sufficient permissions for both permitted and denied identities, and cleanup callbacks.
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
- Owned responsibility scope: `contracts/sdk-contract.json`, its schema and validate/render/check/source-link tooling where required, `src/multica_py/_generated/approved_sdk.py`, central generated operation/vector metadata, and directly related contract tests/fixtures. These are critical shared files and no sibling may rewrite them.
- Contract surface: exact release/source/archive/executable identities; tested interval; 236 command dispositions and mappings; 196 response verdicts; deterministic generated bindings, validators, sources, and vectors.
- Definition of done/evidence: validate/render/check and source-link audit pass; inventory and response counts are exact; two renders are byte-identical; no evidence, `.devlocal`, binary, archive, diagnostic, or transient render is tracked.
- Parallel-safety rationale: this predecessor owns every shared contract/generated write before domain siblings start, preventing concurrent edits to the largest conflict surface.

### WP-2 — Issue-family models, rerun migration, and mutation safety

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 5.4
- Deliverable: typed issue/project/task/attachment/comment additions, explicit run-targeted rerun migration, authorization-safe private-project behavior, and fail-closed/atomic issue relationship mutations.
- Owned responsibility scope: issue/project/task wire projections, `src/multica_py/resources/issues.py`, issue/project/task/attachment/comment domain models and relations, domain-specific exports, operation rows, fake-CLI fixtures, type-check examples, and directly related tests/docs. It consumes but does not rewrite WP-1 outputs. Shared cross-domain docs/CI remain WP-5 responsibility.
- Contract surface: requester/list creator, project visibility/creator, task credits/redaction, attachment dimensions, comment resolution, rerun-task resume/fresh, prevalidation, atomic attachment binding, private 404/omission/redaction.
- Definition of done/evidence: present/omitted/null/malformed/open-value tables pass; exact argv and eager/preview equivalence pass; obsolete issue rerun is absent with compiling migration; invalid relationships perform zero transport/mutation; private identities are not synthesized or leaked.
- Parallel-safety rationale: production writes stay in issue-family resources/models/tests and do not touch WP-3 transport internals or WP-4 runtime/user/workspace/subscriber modules. Any unavoidable root export or shared-doc collision is deferred to WP-5.

### WP-3 — Shared process, cancellation, and literal input boundaries

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 5.1, 5.2, 5.3
- Deliverable: one shared 499/no-body cancellation classification and preserved literal comment/attachment file/stdin behavior with scoped cleanup.
- Owned responsibility scope: `src/multica_py/_internal/transport.py`, process/error helpers, comment/attachment file/stdin resource paths outside issue-family mutation ownership, and their focused process/component/unit tests and fixtures. It consumes but does not rewrite WP-1 outputs or WP-2 issue mutation logic.
- Contract surface: cancellation status/body, neighboring nonzero errors, sanitized stderr/command context, literal argv/stdin, caller-file preservation, run-owned temporary cleanup, passive preview.
- Definition of done/evidence: cancellation cannot degrade into an output-shape error; other nonzero exits retain standard classification; shell-like content remains literal; cleanup tests prove no caller data loss or leaked run-owned temporary input.
- Parallel-safety rationale: transport/process files and focused tests are disjoint from the issue-domain and system-domain sibling zones; integration of shared exports/documentation waits for WP-5.

### WP-4 — Runtime, user, workspace, and subscriber adaptations

- `stage`: 2
- `depends_on`: WP-1
- OpenSpec task coverage: 4.1, 4.2, 4.3, 4.4, 4.5
- Deliverable: typed runtime capacity/usage/update behavior, nullable user-profile value, workspace pin projection/order, project-inherited subscribers, and authorization-safe bounded relations.
- Owned responsibility scope: runtime/user/workspace/subscriber resources and models, `src/multica_py/models/system.py`, subscriber relation models/loaders, their domain operation tables, fixtures, and tests. It consumes but does not rewrite WP-1 outputs, WP-2 issue mutation paths, or WP-3 transport classification.
- Contract surface: exact usage window, runtime update exit/result, open provider/model values, `whats_new_seen_version`, `pinned_at`, subscriber `reason=project`, cursor/order, omitted/redacted loader behavior.
- Definition of done/evidence: complete presence and malformed fixtures pass; runtime nonzero cannot report success; pinned ordering and exact window are asserted; inherited/direct subscriber rows remain distinguishable; hidden relation identifiers produce no loader/permalink.
- Parallel-safety rationale: system and subscriber modules/tests are separate from issue mutation and transport internals. Shared root exports, CI, and docs are reserved for WP-5.

### WP-5 — Integration, documentation, live verification, and exact-SHA delivery

- `stage`: 3
- `depends_on`: WP-2, WP-3, WP-4
- OpenSpec task coverage: 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
- Deliverable: coherent public exports/docs/CI, all repository gates, focused protected live evidence for unresolved real-boundary gaps, normal exact-SHA publication, and independent Tester evidence/read-back.
- Owned responsibility scope: root exports, cross-domain integration helpers/tests, compatibility/API/migration/coverage/changelog/contributing/release docs, CI/live-smoke workflow and verifier integration, publication proof, and evidence coordination. After predecessors complete, this package may make necessary integration repairs across their areas and records them explicitly.
- Contract surface: documented compatibility and rerun migration; scenario-to-test mapping; strict offline/package/release gates; protected exact-SHA live cases; conditional visible-output captures; local/remote SHA equality; Multica attachment/read-back and cleanup contracts.
- Definition of done/evidence: focused and required full gates pass under the ten-minute/CI policy; every scenario maps to a sufficient assertion or focused live result; local/remote SHA match; independent evidence is attached and read back without private data; branch/PR/commits remain unmerged and preserved.
- Parallel-safety rationale: this integrator starts only after all domain siblings close, so root exports, shared helpers, docs, CI, live fixtures, and cross-domain repairs cannot race active sibling writes.

## Frontier validation

- Stage 1 frontier: WP-1 only, because approved contract/generated authority must be established once.
- Stage 2 frontier: WP-2, WP-3, and WP-4 are mutually independent with disjoint critical production/test write-zones and may run concurrently.
- Stage 3 frontier: WP-5 integrates completed siblings and performs documentation, repository gates, live evidence, and publication.

The graph has a real three-way parallel frontier. WIP limits are operational Manager policy and are not encoded as extra dependencies or stages.
