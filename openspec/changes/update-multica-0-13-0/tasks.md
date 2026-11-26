## 1. Approved contract foundation

- [ ] 1.1 Update `contracts/sdk-contract.json` with exact `0.13.0` release/archive/executable/version provenance, the retained compatibility floor, maximum-tested `0.13.0`, exclusive `0.13.1` ceiling, and exact old/target source links.
- [ ] 1.2 Close dispositions for all `277` target command nodes and removed `issue rerun`, including args, flags, defaults, aliases, presence semantics, constraints, and approved/deferred public mappings.
- [ ] 1.3 Close all `196` response work items with shape, nullability, omission, pagination, privacy, error, SDK, test, and documentation decisions.
- [ ] 1.4 Extend existing contract schema/validation/generation only where the approved new fields require it, then regenerate tracked runtime projection solely from the approved contract.

## 2. Issue blockers and rerun replacement

- [ ] 2.1 Add presence-aware blocker wire/public models for `blocked_by`, `blocking`, `blocked_count`, and open reference kind, preserving old-payload omission and hidden-count privacy.
- [ ] 2.2 Add exact eager/command blocker mutation APIs and bound-issue relations through existing issue seams, with local self/type/blank/max-100 validation, authoritative typed errors, and scoped invalidation.
- [ ] 2.3 Remove legacy public `issue rerun` and implement/align `issue rerun-task` exact signatures, presence behavior, result decoding, exports, and migration boundary.
- [ ] 2.4 Extend existing frozen unit/contract/component/type case tables for positive, negative, omission/null/empty, manual/stage/closed, hidden-count, self/cycle/cross-workspace/max-100, rerun, privacy, and typed-error behavior.

## 3. Squad handoff and task document attribution

- [ ] 3.1 Add squad `handoff_mode` to approved models and create/update/get/list adapters with reviewed `leader|direct` values, legacy omission defaulting to `leader`, and typed rejection of unreviewed values.
- [ ] 3.2 Add task-run document identity, kind, and actor/source attribution through existing private wires and public task/run models without adding a document resource or leaking inaccessible metadata.
- [ ] 3.3 Preserve delete `ActionResult[None]` and shared redaction/error behavior for the reviewed cleanup/access deltas.
- [ ] 3.4 Extend existing frozen unit/contract/component/type tables for `leader|direct`, unknown/omitted handoff modes, task document nullability/omission/access, delete side effect, and malformed payloads.

## 4. Retained command and response adaptation

- [ ] 4.1 Apply every remaining approved `adapt`, `retain`, `support`, `remove`, and `defer` decision to existing resources/models/wires without adding deferred public commands.
- [ ] 4.2 Update canonical operation cases, response fixtures, fingerprints, completeness assertions, and source refs so public contract, runtime, tests, and docs inventories have exact set equality.
- [ ] 4.3 Add table rows for all changed presence/constraint/response/error semantics, including retained pagination and unknown open values, without parallel case hierarchies.

## 5. Verification implementation

- [ ] 5.1 Extend `scripts/e2e/verify_multica_test.py` and its existing unit fixtures with case selection, parameterized stand bindings, wrapper-owned second-identity support, and read-only named document-fixture inputs for blocker privacy/lifecycle, handoff round-trip, task document attribution/access, and rerun-task; retain its SHA/version gate, sanitization, manifest, resource registry, and failure-safe cleanup instead of adding another runner.
- [ ] 5.2 Add/extend existing CI tests and fixtures for approved command/response mappings, deterministic generation, source-link completeness, privacy, compatibility, packaging, and collection-only live exclusion; do not add a CI framework.
- [ ] 5.3 Run focused offline checks and complete repository gates within the local automatic-test limit, moving longer suites to existing GitHub Actions on the published exact revision and recording commands/exit codes.

## 6. Documentation and migration

- [ ] 6.1 Update README, API, compatibility, CLI coverage, service usage, migration, changelog, and release docs for direct `0.7.1→0.13.0`, blocker privacy, handoff mode, task document attribution, rerun-task migration, deferred commands, and open-value policy.
- [ ] 6.2 Update typed documentation examples/fixtures and release/package metadata without introducing unsupported commands, private stand coordinates, or generated evidence.

## 7. Independent exact-revision evidence

- [ ] 7.1 Publish the candidate revision normally, verify remote SHA equality, and record readiness for the isolated project stand, dedicated `multica-test` profile/data namespace, and capture renderer.
- [ ] 7.2 Have the independent Tester run the focused script and a separate manual public-SDK walkthrough, capture actual normalized text plus genuine baseline/candidate PNGs for changed read output, and retain failed diagnostics without claiming PASS.
- [ ] 7.3 Attach sanitized commands, exit codes, assertions, hashes/revisions, MR/commit/file links, images, and cleanup result to Multica with read-back; preserve evidence branch/MR/commits and do not merge, close, or delete them without authorization.
