## Delivery contract

- Change: `update-multica-0-11-0`
- Planning issue: `MYL-668`
- Planning base: `b268e3bec0436fe51727fda50583344f57663284`
- Planning base tree: `6fb22297ab62a86b591dc058fdc7a03b107c97fd`
- Upstream baseline: Multica `0.7.1` at `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`
- Upstream target: Multica `0.11.0` release `449794198` at `cb190810a659c1a61c4a86d9f6ecfc9df4b086d8`
- Development and test-code repository: `https://github.com/maximchikAlexandr/multica-py`
- Estimate source of truth: root planning issue properties `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours`; this file intentionally contains no numeric estimate totals.
- Planning authority: proposal, design, delta specs, tasks, and this delivery contract. Operational status and assignees remain in Multica.

## E2E decision

`e2e_required=true`.

The remaining material integration gaps depend on a real CLI process plus server
persistence: literal inline text, file text, escaped metadata keys, and mutation
refusal after project archival. Existing/planned unit, contract, and fake-CLI
tests prove argv, validation, decoding, and error classification, but cannot
prove persisted bytes or archived remote state.

The sole local runner remains `scripts/e2e/verify_multica_test.py`, with tests
under `tests/unit/test_e2e_verification.py` and the existing trusted
`.github/workflows/live-smoke.yml`. Implementation extends these seams for
observed CLI `0.11.0`; no second runner, framework, profile override, daemon
control, private endpoint, credential, or public hostname is added.

Private non-member behavior lacks an authorized second stand identity. No-body
`499` lacks a deterministic safe cancellation trigger. Runtime deletion would
target a stand-owned runtime, and skill-limit payloads do not justify live
oversize writes. These remain mandatory lower-level cases, not live claims.
Rerun-task and webhook/squad/runtime-profile validation are also deterministic
command/lifecycle checks.

No before/after PNG is required because the approved change does not alter
terminal tables, logs, progress, summaries, browser UI, or Mac-rendered output.
No renderer belongs in readiness. A visible-output implementation change blocks
verification until the image contract is revised with a confirmed renderer,
equivalent fixtures, actual before/after text, and PNG capture.

## Verification matrix

| Case ID | OpenSpec requirement / scenario | Gap and local E2E decision | Affected public boundary | Local script | Independent Tester steps | CI disposition | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| V110-01 | Exact target authority; complete commands/responses; deterministic generation | Lower-level sufficient | Approved contract, renderer, source-link audit | None | From a fresh checkout, compare target identities, counts, dispositions, source links, and two render digests | Extend contract checks in ordinary CI | Exact pins; all command/response rows covered; zero pending; repeat render identical | Commands, exits, links, digests in Multica; no image |
| V110-02 | Presence, nullability, malformed values, open enums | Lower-level sufficient | Frozen wire/public model decoding | None | Inspect scenario rows and run focused decoder/model tests | Extend ordinary CI | Legacy omission works; null policy holds; malformed fails typed; valid unknown token survives | Focused output and file/commit links; no image |
| V110-03 | Squad assignees, payload conditions, runtime machine binding | Lower-level sufficient | Resource command builders and pre-I/O validation | None | Run exact positive argv and invalid zero-process cases | Extend ordinary CI | Exact destinations and presence; conflicts/requires/exactly-one reject before process | Test output and links; no image |
| V110-04 | Task-identity rerun and legacy removal | Lower-level lifecycle/argv sufficient | `issues.rerun_task[_command]`, typed result, exports | None | Run exact argv/result/missing/conflict/malformed cases and inspect public inventory | Extend ordinary CI | Explicit task identity; one mode; typed result; no issue inference or legacy alias | Test/commit links; no image |
| V110-05 | Private project membership-only behavior | Live excluded: no authorized second principal | Project resource/model with pinned success/not-found/omission fixtures | None | Run model/resource/fake-CLI cases and confirm no live-auth claim | Ordinary CI | No redacted/synthetic private project; malformed fields fail | Fixture/test links and limitation; no image |
| V110-06 | Literal inline text persistence | Live selected: real persistence gap | Public SDK update followed by separate SDK get | `uv run python scripts/e2e/verify_multica_test.py --output <new-empty-run-owned-directory-outside-checkout>` | Repeat on a fresh disposable issue and inspect stored text | Exact-head live workflow may run the same verifier | Stored value is byte-equivalent to input; cleanup passes | Sanitized scenario event/hash/exit and links; no image |
| V110-07 | File text persistence | Live selected: distinct lifecycle/assertion | Run-owned UTF-8 file, public file channel, separate SDK get | Same existing verifier | Repeat with a fresh file/resource; remove only run-owned file | Exact-head live workflow may run the same verifier | Multiline value exact except approved single trailing LF; unrelated text unchanged; cleanup passes | Sanitized before/action/after hashes and cleanup; no image |
| V110-08 | Metadata key escaping | Live selected: real path/server round-trip | SDK set/get/list/delete on a disposable issue | Same existing verifier | Repeat with slash/percent/space/Unicode key and inspect one exact entry | Exact-head live workflow may run the same verifier | Exact key/value; no extra segment or entry; cleanup passes | Sanitized key digest, outcomes, links; no image |
| V110-09 | Archived-project conflict | Live selected: real state/error gap | SDK create/update plus isolated CLI archive/restore | Same existing verifier | Repeat on a fresh project; separately read archived state | Exact-head live workflow may run the same verifier | Typed conflict; project unchanged; restore precedes delete; no retry | Sanitized state/error/cleanup events, exits, links; no image |
| V110-10 | No-body `499`, bounded runtime `409`, skill `413` | Live excluded for determinism and safety | Existing transport and fake-CLI error fixtures | None | Run focused transport/component cases and inspect no retry/follow-up | Ordinary CI | Correct typed errors; redaction; no retry/cascade/second mutation | Test output/link and safety rationale; no image |
| V110-11 | Deferred surfaces and exact operation completeness | Lower-level audit sufficient | Public exports, generated registry, docs, package | None | Compare dispositions with discovered symbols and package contents | Ordinary CI | Canonical supported set is closed; deferred symbols absent | Test/export/package links; no image |
| V110-12 | Exact-SHA repository delivery | Repository/CI sufficient | Required gates on one published candidate | None | Check remote equality, CI, package, docs, and forbidden-content results | Required/package jobs | OpenSpec/contract/source/tests/types/lint/docs/package/content gates pass | Commands/exits and CI/MR/commit/file links; no image |

## Existing verifier extension contract

- The path remains `scripts/e2e/verify_multica_test.py`; unit coverage remains
  in the existing verifier tests and frozen case tables.
- The entry command remains
  `uv run python scripts/e2e/verify_multica_test.py --output <new-empty-run-owned-directory-outside-checkout>`.
- Readiness SHALL prove a clean exact candidate checkout, remote SHA equality,
  product and test-code SHA, `multica-test` executable resolution,
  wrapper-owned configuration with no explicit profile/server/workspace
  override, daemon-reported CLI `0.11.0`, focused lower-level readiness, empty
  output, and cleanup authority. It SHALL NOT require a renderer.
- The existing sanitized manifest is extended only with allowlisted scenario
  outcomes and commands. Environment dumps, tokens, cookies, private hostnames,
  personal data, binaries, and unrelated logs SHALL NOT be recorded.
- Every disposable resource is registered immediately. Cleanup order is
  metadata/file state, issue lifecycle, project restore when archived, project
  deletion, and any existing property archival. Cleanup runs on success,
  assertion failure, interruption, and partial setup.
- A selected case is PASS only when its assertions and cleanup pass at the
  recorded product revision. A new revision requires impact assessment and
  reruns only affected live cases; unresolved impact remains unverified.

## CI and independent evidence

- Implementer owns the existing unit/contract/component/package tables, verifier
  extension, fixtures, and exact-head live workflow. Tester verifies coverage
  and SHALL NOT edit product code, tests, fixtures, workflows, or generated
  output.
- CI resolves an open same-repository PR head, checks out its full SHA,
  revalidates before and after the suite, restricts credentials to the protected
  environment, and uploads only the sanitized allowlist.
- Automated local suites expected to exceed or reaching ten minutes stop only
  their owned process and run unsplit in GitHub Actions at the exact revision.
  Manual Tester walkthroughs are not subject to the automated-suite limit.
- Tester publishes one final Multica comment with candidate/test-code SHA,
  observed CLI version, every V110 outcome, exact commands/exits, assertion
  summary, lower-level limitations, CI/MR/commit/file links, cleanup, and the
  no-image rationale. Any attachment and the comment are read back.
- Real outputs, logs, diagnostic JSON, hashes, and private addresses remain
  outside Git. Cleanup removes disposable stand resources and run-owned output
  while preserving the evidence branch, MR, and commits. Merge, closure, and
  branch deletion require separate authorization.

## Delivery topology

`delivery_mode=dag` because the authoritative `Estimate, hours` property is
above the topology threshold and stage 4 contains a genuine non-conflicting
parallel frontier. Exact estimate totals exist only in the root issue properties.

Estimate basis: remaining work for one experienced developer familiar with the
Python SDK stack, without AI acceleration. Confidence is medium and calibration
is uncalibrated. Evidence includes the complete OpenSpec package, current
approved contract/generator, existing model/resource/transport seams, frozen
case tables, isolated verifier, and trusted live workflow. Uncertainty is driven
by the breadth of direct-range response reconciliation, cross-release presence
semantics, and likely integration repairs. No tests were run for estimation.

Stage mapping: `WP-1 -> 1`, `WP-2 -> 2`, `WP-3 -> 3`,
`WP-4 -> 4`, `WP-5 -> 4`, `WP-6 -> 5`, `WP-7 -> 6`.
Manager SHALL copy each integer to the corresponding WP child issue.

### WP-1 — Approved contract foundation

- Tasks: `1.1–1.5`; stage `1`; depends on none.
- Deliverable: reviewed direct-range contract and byte-stable generated
  projection for exact Multica `0.11.0`.
- Owned responsibility: `contracts/sdk-contract.json`, generated projection,
  contract validation/render/source-link fixtures, and contract-specific tests.
  These critical shared files freeze after acceptance.
- Contract surface: provenance, compatibility, command registry, response
  registry, dispositions, mappings, constraints, generated identifiers.
- DoD/evidence: exact target/count/source assertions, validate/render/check,
  second-render equality, and focused contract tests.
- Parallel safety: exclusive foundation consumed by every successor.

### WP-2 — Response and rerun models

- Tasks: `2.1–2.5`; stage `2`; depends on `WP-1`.
- Deliverable: all approved target wire/public/entity adaptations, including the
  complete task-rerun result decoder and export contract.
- Owned responsibility: `src/multica_py/models/**`,
  `src/multica_py/entities/**`, relevant
  `src/multica_py/_internal/*_wires.py` and decoders, exports, and direct
  model/decode/presence tests. It does not edit command builders or transport.
- Contract surface: field types and presence, privacy/page/subscriber semantics,
  target optional fields, rerun result shape, and public exports.
- DoD/evidence: present/omitted/null/malformed/unknown/legacy rows pass; rerun
  result imports are stable; focused mypy and Ruff pass.
- Parallel safety: serialized before WP-3 because commands consume its decoder
  and shared exports have one owner.

### WP-3 — Command migration and transport safety

- Tasks: `3.1–3.5`; stage `3`; depends on `WP-2`.
- Deliverable: task-rerun methods plus literal text, metadata, squad, webhook,
  runtime-profile, pagination, cancellation, conflict, and size-limit behavior.
- Owned responsibility: `src/multica_py/resources/**`, command/input models,
  `src/multica_py/_internal/transport.py`, `exceptions.py`, and direct
  argv/validation/transport tests. It consumes but does not edit WP-2-owned
  wire/entity/export files.
- Contract surface: rerun signature/modes; argv/stdin/file channels; path
  escaping; target constraints; typed errors, redaction, and no retry.
- DoD/evidence: exact positive/negative cases, invalid zero-process assertions,
  no-follow-up assertions, focused mypy and Ruff.
- Parallel safety: exclusive command/transport integration predecessor.

### WP-4 — Consolidated tests, CI, and existing verifier

- Tasks: `4.1–4.4`; stage `4`; depends on `WP-3`.
- Deliverable: consolidated case tables/fake CLI, exact-head live workflow, and
  extended existing verifier.
- Owned responsibility: shared `tests/cases/**`, component and cross-surface
  fixtures, `scripts/e2e/verify_multica_test.py`, its unit tests, and
  `.github/workflows/live-smoke.yml`. Predecessor tests are changed only where
  shared consolidation requires it.
- Contract surface: canonical operation completeness, target live authorization
  and SHA gate, sanitized outcomes, readiness, archive restore, and cleanup.
- DoD/evidence: each scenario maps once; verifier self-tests cover version/SHA
  mismatch, sanitization, partial cleanup, and output policy; no second runner.
- Parallel safety: runs beside WP-5; tests/scripts/workflow and prose docs have
  disjoint primary write zones.

### WP-5 — Compatibility and migration documentation

- Tasks: `5.1`; stage `4`; depends on `WP-3`.
- Deliverable: consistent direct-migration, compatibility, API, coverage,
  changelog, contribution, package, and release documentation.
- Owned responsibility: `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`,
  `docs/**`, and documentation checks; no code, test, workflow, generated
  contract, or planning edits.
- Contract surface: target envelope, rerun replacement, retained/adapted/deferred
  coverage, and selected live versus lower-level evidence.
- DoD/evidence: docs/source-link checks pass; examples use approved APIs; no
  private values or unsupported-family claims.
- Parallel safety: disjoint from WP-4 test, script, fixture, and CI ownership.

### WP-6 — Integrated repository verification

- Tasks: `5.2–5.4`; stage `5`; depends on `WP-4`, `WP-5`.
- Deliverable: one consolidated checked and normally published candidate
  revision.
- Owned responsibility: integration fixes exposed by required gates,
  verification records, and exact-SHA publication; no product-scope or topology
  expansion.
- Contract surface: strict OpenSpec/contract/source/operation/test/type/lint/
  docs/package/content gates and remote SHA equality.
- DoD/evidence: focused gates pass; full non-live suite passes locally within
  the limit or unsplit in CI; forbidden artifacts are absent; SHA equality is
  recorded.
- Parallel safety: serialized after both stage-4 siblings own and reconcile
  their disjoint outputs.

### WP-7 — Independent verification and evidence

- Tasks: `6.1–6.4`; stage `6`; depends on `WP-6`.
- Deliverable: exact-revision V110 live/lower-level verdict with
  read-back-verified Multica evidence.
- Owned responsibility: wrapper-owned isolated verifier run, fresh manual
  selected scenarios, lower-level evidence inspection, outside-Git staging,
  cleanup, and publication. Tester edits no product, test, fixture, workflow, or
  generated file.
- Contract surface: V110 matrix, exact identities, outcomes, limitations,
  cleanup, links, and no-image rationale.
- DoD/evidence: readiness passes; every row has a revision-bound outcome;
  cleanup passes; branch/MR/commits remain; comments/attachments read back; no
  unsupported PASS.
- Parallel safety: final verification is serialized on the consolidated SHA.

## Coverage and frontier audit

Task ownership is exact and non-overlapping: `1.1–1.5` → WP-1;
`2.1–2.5` → WP-2; `3.1–3.5` → WP-3; `4.1–4.4` → WP-4;
`5.1` → WP-5; `5.2–5.4` → WP-6; `6.1–6.4` → WP-7.
Dependencies list direct edges only.

Frontiers are stage 1 `{WP-1}`; stage 2 `{WP-2}`; stage 3 `{WP-3}`;
stage 4 `{WP-4, WP-5}`; stage 5 `{WP-6}`; stage 6 `{WP-7}`.
Stage 4 proves real parallel execution with disjoint primary write zones, so DAG
delivery remains valid.
