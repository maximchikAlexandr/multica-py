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

The existing `scripts/e2e/verify_multica_test.py` is the sole local runner. It already provides wrapper-owned `multica-test` isolation, a CLI version gate, an output-outside-checkout rule, sanitized `multica-py-e2e-v2` artifacts, resource registration, and failure-safe cleanup. Implementation extends that seam for observed CLI `0.10.0`, literal inline/file persistence, escaped metadata-key persistence, and archived-project mutation refusal. No second script, runner framework, profile override, daemon control, private endpoint, or credential is added.

Private non-member behavior lacks an authorized second stand identity; no-body `499` lacks a deterministic safe cancellation setup; and runtime-delete conflict would target the stand-owned runtime. These are mandatory lower-level cases, not live claims. Rerun-task and webhook validation also remain deterministic command/lifecycle tests. This selection is minimal: real process/server persistence and archived state use the stand; deterministic shape, classification, and pre-I/O behavior use existing tables/fake CLI.

No before/after PNG is required because public terminal tables, logs, progress, summaries, browser UI, and Mac-rendered output are unchanged. No renderer belongs in readiness. If implementation changes visible output, verification is blocked pending a revised image contract.

## Verification matrix

| Case ID | Requirement / scenario | Gap and decision | Public action / initial state | Existing verifier or independent Tester steps | CI disposition | Assertions | Evidence / images |
|---|---|---|---|---|---|---|---|
| V100-01 | Exact provenance; `209→246`; `196/196`; deterministic generation | Lower-level sufficient | Approved contract and generated projection from exact pinned source | Tester compares identities/counts/source links and two render digests from a fresh checkout | Extend contract checks | Exact values; zero pending; repeat render identical; check mode clean | Commands, exits, links, digests in Multica; no image |
| V100-02 | Additive fields: present/omitted/null/malformed/open values | Lower-level sufficient | Decode frozen response fixtures through existing wire/public models | Tester inspects scenario rows and runs focused model/decode tests | Extend ordinary test job | Legacy omission works; null preserved; malformed fails typed; valid unknown token survives | Focused output and file/commit links; no image |
| V100-03 | Private project membership-only get/list | Live excluded: no authorized second stand principal | Pinned member success and privileged non-member `404`/omission fixtures | Tester runs model/resource/fake-CLI cases and confirms no live-auth claim | Ordinary CI | No redacted/synthetic private project; malformed private fields fail | Fixture/test links and limitation; no image |
| V100-04 | Rerun-task resume/fresh and removed issue rerun | Lower-level lifecycle/argv sufficient | `issues.rerun_task[_command](task_id, mode=...)` against fake CLI results | Tester runs exact argv, result, missing/conflict, malformed cases | Ordinary CI | Explicit task identity; one mode; typed result; no issue inference/legacy alias | Test/commit links; no image |
| V100-05 | Literal inline text persistence | Live selected | Existing verifier creates disposable project/issue via SDK with literal backslashes, then separate SDK get | Tester repeats with fresh resource and inspects stored text | Exact-head live workflow may run same verifier | Stored value byte-equivalent to input; cleanup passes | Sanitized scenario event/hash/exit and links; no image |
| V100-06 | File text persistence and one trailing LF | Live selected, separate lifecycle/assertion | Existing verifier writes run-owned UTF-8 file, updates disposable issue through public file channel, then SDK get | Tester repeats with a new file/resource and removes run-owned file | Exact-head live workflow may run same verifier | Multiline content exact except one trailing LF; unrelated text unchanged; cleanup passes | Sanitized before/action/after hashes and cleanup; no image |
| V100-07 | Metadata key escaping | Live selected, separate lifecycle/assertion | SDK set/get/delete on disposable issue using one slash/percent/space/Unicode key | Tester performs fresh set/get/list/delete and inspects one entry | Exact-head live workflow may run same verifier | Exact key/value; no extra path segment/entry; cleanup passes | Sanitized key digest, outcomes, links; no image |
| V100-08 | Archived-project `409` | Live selected, separate archive/restore cleanup | SDK create project → `multica-test project archive <id> --output json` → SDK `projects.update` → CLI restore → SDK delete | Tester repeats on fresh disposable project and separately reads archived state | Exact-head live workflow may run same verifier | Typed ConflictError; archived project unchanged; restore before delete; no retry | Sanitized state/error/cleanup events, exits, links; no image |
| V100-09 | No-body `499` cancellation | Live excluded: no deterministic safe cancellation trigger | Fake CLI emits target cancellation exit with empty stdout/body | Tester runs focused transport/component case | Ordinary CI | Typed cancellation; no JSON-shape error; no retry | Test output/link and limitation; no image |
| V100-10 | Runtime-delete bounded conflict | Live excluded: stand runtime must not be deletion target | Existing structured/optional/plain/malformed `409` fake-CLI fixtures through `runtimes.delete(cascade=False)` | Tester runs transport/component cases and confirms no cascade/follow-up | Ordinary CI | Typed bounded details; redaction; no cascade; no second delete | Test output/link and safety rationale; no image |
| V100-11 | Webhook constraints and deferred surfaces | Lower-level pre-I/O/audit sufficient | Valid repeated filter argv; invalid requires/conflicts; public export inventory | Tester confirms invalid case creates no process and deferred symbols absent | Ordinary CI | Exact argv; no invalid invocation; no deferred public API | Test/export/package links; no image |
| V100-12 | Docs, package, exact-SHA delivery | Repository/CI sufficient | Full required gates on published candidate | Tester checks remote equality, CI, package contents, and documentation | Required/package jobs | OpenSpec/contract/source/tests/types/lint/docs/package/content gates pass | Commands/exits and CI/MR/commit/file links; no image |

## Existing verifier extension contract

- Path remains `scripts/e2e/verify_multica_test.py`; existing tests remain under `tests/unit/test_e2e_verification.py` and related case tables.
- Entry command remains `uv run python scripts/e2e/verify_multica_test.py --output <new-or-empty-run-owned-directory-outside-checkout>`.
- Readiness SHALL prove: clean exact candidate checkout; remote SHA equality; product and test-code SHA; `multica-test` executable resolution; wrapper-owned config with no explicit profile/server/workspace override; daemon-reported CLI `0.10.0`; focused lower-level readiness; empty output; and cleanup authority. It SHALL NOT require a renderer.
- The existing manifest schema remains `multica-py-e2e-v2`. Add scenario outcomes and allowlisted commands without environment dumps, tokens, cookies, private hostnames, personal data, binaries, or unrelated logs.
- Register each disposable resource immediately. Cleanup order is metadata/file state, issue lifecycle, project restore when archived, project deletion, and existing property archival. Cleanup runs on success, assertion failure, interruption, and partial setup.
- A selected case is PASS only when its assertions and cleanup pass at the recorded product revision. A new revision requires impact assessment and reruns only affected live cases.

## CI and independent evidence

- Implementer owns existing unit/contract/component/package tables, the verifier extension, and the exact-PR-head live workflow update to observed CLI `0.10.0`. Tester verifies coverage and does not edit these files.
- CI resolves an open same-repository PR head, checks out its full SHA, revalidates before/after, restricts credentials to the protected environment, and uploads only a sanitized allowlist.
- Automated local suites expected to exceed or reaching ten minutes stop only their owned process and run unsplit in GitHub Actions at the exact revision. Manual walkthroughs are not subject to the automated-suite limit.
- Tester publishes one final Multica comment with candidate/test-code SHA, observed CLI version, each V100 outcome, exact commands/exits, assertion summary, lower-level limitations, CI/MR/commit/file links, cleanup, and no-image rationale. Attachments and comment are read back. Real outputs/logs/diagnostic JSON/hashes remain outside Git.
- Cleanup removes disposable stand resources and run-owned output while preserving evidence branch/MR/commits. Merge, closure, and branch deletion require separate authorization.

## Delivery topology

`delivery_mode=dag` because the authoritative `Estimate, hours` property is above the topology threshold and stage 4 contains a genuine non-conflicting parallel frontier. Exact estimate totals exist only in root issue properties.

Estimate basis: remaining work for one experienced developer familiar with the Python/SDK stack, without AI acceleration. Confidence is medium and calibration is uncalibrated. Evidence includes the complete revised OpenSpec, current approved contract/generator, existing model/resource/transport seams, frozen test tables, the existing isolated verifier, and live workflow. No tests were run for estimation.

Stage mapping: `WP-1 -> 1`, `WP-2 -> 2`, `WP-3 -> 3`, `WP-4 -> 4`, `WP-5 -> 4`, `WP-6 -> 5`, `WP-7 -> 6`. Manager SHALL copy each integer to the corresponding WP child issue.

### WP-1 — Approved contract foundation

- Tasks: `1.1–1.5`; stage `1`; depends on none.
- Deliverable: reviewed direct-range contract and byte-stable projection.
- Owned responsibility: `contracts/sdk-contract.json`, generated projection, contract generator validation/render/source-link fixtures and contract-specific tests. These critical shared files freeze after acceptance.
- Contract surface: provenance/compatibility, command registry, response registry, dispositions, generated identifiers.
- DoD/evidence: validate/render/check, repeat-render equality, exact counts/digests/links, focused contract tests.
- Parallel safety: exclusive foundation consumed by every successor.

### WP-2 — Response and rerun result models

- Tasks: `2.1–2.5`; stage `2`; depends on `WP-1`.
- Deliverable: all target public/wire/entity field adaptations, including the complete rerun-task result model/decoder/export contract.
- Owned responsibility: `src/multica_py/models/**`, `entities/**`, relevant `_internal/*_wires.py`/decoders, `models/__init__.py`, root exports, and direct model/decode/presence tests. It does not edit command builders or transport.
- Contract surface: field types/presence, page/private/subscriber semantics, rerun result shape and exports.
- DoD/evidence: all present/omitted/null/malformed/legacy cases pass; rerun result imports are stable; mypy/Ruff pass.
- Parallel safety: serialized before WP-3 because command code consumes its decoder and shared exports have one owner.

### WP-3 — Command migration and transport safety

- Tasks: `3.1–3.5`; stage `3`; depends on `WP-2`.
- Deliverable: rerun-task command methods plus text, metadata, webhook, cancellation, archive, and runtime-delete safety.
- Owned responsibility: `src/multica_py/resources/**`, `_internal/transport.py`, `exceptions.py`, and direct argv/transport tests. It consumes but does not edit WP-2 model/wire/export files.
- Contract surface: rerun signature/modes; argv/stdin/file channels; path escaping; webhook constraints; typed errors/no retry.
- DoD/evidence: exact positive/negative rows, invalid no-process assertions, redaction/no-follow-up assertions, mypy/Ruff.
- Parallel safety: explicit predecessor edge removes the prior wire/export race.

### WP-4 — Consolidated tests, CI, and existing verifier

- Tasks: `4.1–4.4`; stage `4`; depends on `WP-3`.
- Deliverable: consolidated tables/fake CLI, exact-head live workflow, and extended existing verifier.
- Owned responsibility: shared `tests/cases/**`, component/cross-surface unit fixtures, `scripts/e2e/verify_multica_test.py`, its unit tests, and live workflow. Direct predecessor tests are changed only for shared consolidation.
- Contract surface: operation completeness, live authorization/SHA gate, `multica-py-e2e-v2` outcomes/readiness/cleanup.
- DoD/evidence: every scenario maps once; verifier self-tests cover version mismatch, sanitization, partial cleanup, archive restore, and output policy; no second runner.
- Parallel safety: runs beside WP-5; tests/scripts/CI and prose docs have disjoint primary write zones.

### WP-5 — Compatibility and migration documentation

- Tasks: `5.1`; stage `4`; depends on `WP-3`.
- Deliverable: consistent compatibility/API/migration/coverage/changelog/contribution/package/release docs.
- Owned responsibility: `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/**`, and doc checks; no code/tests/workflows/planning edits.
- Contract surface: target envelope, rerun migration, retained/deferred surface, selected live and lower-level evidence.
- DoD/evidence: docs/source-link checks pass; examples use approved APIs; no private values.
- Parallel safety: disjoint from WP-4 tests/scripts/CI.

### WP-6 — Integrated repository verification

- Tasks: `5.2–5.4`; stage `5`; depends on `WP-4`, `WP-5`.
- Deliverable: one consolidated checked and published candidate revision.
- Owned responsibility: integration fixes exposed by required gates, verification records, and normal publication; no scope/topology expansion.
- Contract surface: strict OpenSpec/contract/source/operation/test/type/lint/docs/package/content gates and exact remote SHA.
- DoD/evidence: focused gates pass; full non-live passes locally within limit or unsplit in CI; forbidden artifacts absent; SHA equality recorded.
- Parallel safety: serialized after both stage-4 siblings.

### WP-7 — Independent verification and evidence

- Tasks: `6.1–6.4`; stage `6`; depends on `WP-6`.
- Deliverable: exact-revision selected-live and lower-level verdict with read-back-verified Multica evidence.
- Owned responsibility: wrapper-owned isolated verifier run, fresh manual selected scenarios, lower-level evidence inspection, outside-Git staging, cleanup, and publication. Tester edits no product/tests/fixtures.
- Contract surface: V100 matrix, exact identities, scenario outcomes, limitations, cleanup, no-image rationale.
- DoD/evidence: readiness passes; every row has outcome; cleanup passes; branch/MR/commits remain; comment/attachments read back; no unsupported PASS.
- Parallel safety: final verification is serialized on the consolidated SHA.

## Coverage and frontier audit

Task ownership is exact and non-overlapping: `1.1–1.5` → WP-1; `2.1–2.5` → WP-2; `3.1–3.5` → WP-3; `4.1–4.4` → WP-4; `5.1` → WP-5; `5.2–5.4` → WP-6; `6.1–6.4` → WP-7. Dependencies list direct edges only.

Frontiers are stage 1 `{WP-1}`; stage 2 `{WP-2}`; stage 3 `{WP-3}`; stage 4 `{WP-4, WP-5}`; stage 5 `{WP-6}`; stage 6 `{WP-7}`. Stage 4 proves real parallel execution with disjoint primary write zones, so DAG delivery remains valid.
