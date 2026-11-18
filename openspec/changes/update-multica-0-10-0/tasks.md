## 1. Approved Upstream Contract

- [ ] 1.1 Update `contracts/sdk-contract.json` with exact `0.7.1` baseline and `0.10.0` target release/source/archive/executable/version-output provenance, the direct comparison range, preserved supported minimum, maximum-tested `0.10.0`, and policy-derived exclusive ceiling.
- [ ] 1.2 Reconcile all `209` baseline and `246` target CLI nodes (`38` added, `1` removed, `26` changed), including every positional/local/inherited flag, default, alias/deprecation, imperative/declarative constraint, presence rule, RunE/helper destination, source-only name, disposition, full-SHA source link, and positive/negative test reference.
- [ ] 1.3 Reconcile exactly `196` supported response entrypoints (`94` changed, `102` unchanged, zero pending) with baseline/target source, model/error/fixture/doc action, omission/null/presence behavior, and malformed-payload behavior.
- [ ] 1.4 Record explicit retained/adapted/removed/deferred/not-SDK-surface decisions and enforce that collector output, audits, release notes, binaries, and `.devlocal` evidence cannot drive generation.
- [ ] 1.5 Run approved-contract validate and render, commit only the refreshed existing generated projection, and prove repeat-render byte equality plus check-mode freshness.

## 2. Retained Models and Resource Behavior

- [ ] 2.1 Extend existing wire/public models and entity binders for proven additive task, attachment, comment-resolution, project activity/archive/list pagination, runtime, user-profile, workspace, issue-requester, and subscriber coverage/delivery fields.
- [ ] 2.2 Add table-driven present/omitted/null/malformed and older-server fixtures for every target-added field while preserving open upstream-owned values and source-significant absence.
- [ ] 2.3 Adapt private-project get/list behavior to preserve membership-only not-found/omission/redaction semantics without broadening access or synthesizing projects.
- [ ] 2.4 Adapt project list/activity/archive and subscriber projections to preserve `has_more`, ordering, `project_covered`, delivery, timestamps, numeric precision, and malformed-value rejection.
- [ ] 2.5 Define the rerun-task public result model, wire decoder, model/root exports, present/malformed fixtures, and typed compatibility contract consumed by the issue resource; do not add command construction in this task.

## 3. Rerun, Text, Metadata, Webhook, and Error Safety

- [ ] 3.1 Remove the target-invalid issue-targeted rerun mapping and add explicit run/task-targeted `rerun_task[_command]` resume/fresh methods that consume the task 2.5 result decoder, plus operation-table rows and migration coverage without an identity-inference alias.
- [ ] 3.2 Adapt existing command builders so inline text stays literal, file/stdin content loses at most one trailing LF, explicit empty differs from omission, and explicitly false stdin selection preserves stored text.
- [ ] 3.3 Encode metadata keys as one escaped segment and add Unicode, slash, percent, space, empty/invalid, and round-trip command cases.
- [ ] 3.4 Normalize target webhook filter required/conflict/presence rules at the existing pre-I/O boundary and add valid repeated-value plus invalid no-process-invocation cases.
- [ ] 3.5 Map no-body `499` cancellation, private not-found, archived-project `409`, and bounded runtime-delete/confirmation conflicts through existing typed errors with redaction and no retry or destructive follow-up.

## 4. Table-Driven Tests and CI

- [ ] 4.1 Extend existing `ArgvCase`, `CommandCase`, decode, operation-completeness, legacy, and malformed tables for every changed contract row; add focused tests only where lifecycle, privacy, concurrency, or destructive safety cannot be represented as a row.
- [ ] 4.2 Add or update fake-CLI component fixtures for literal channels, rerun-task result/error modes, private omission, project pagination/activity/archive, inherited subscriber delivery, cancellation, metadata escaping, webhook validation, and bounded destructive conflicts.
- [ ] 4.3 Update the exact-PR-head live workflow and its safe fixtures to require observed CLI `0.10.0`, immutable candidate SHA, protected credentials, sanitized allowlisted evidence, and post-suite SHA revalidation.
- [ ] 4.4 Extend `scripts/e2e/verify_multica_test.py` and its existing unit fixtures for observed CLI `0.10.0`, literal inline/file read-back, escaped metadata-key read-back, archived-project SDK conflict, sanitized scenario outcomes, restore/delete cleanup, and exact-revision readiness; add no second runner or embedded private value.

## 5. Documentation and Repository Verification

- [ ] 5.1 Update compatibility, API, service-usage, migration, CLI-coverage, changelog, contributing, packaging, and release documentation for direct `0.7.1` to `0.10.0` adoption, rerun-task migration, mandatory adaptations, and explicitly deferred families.
- [ ] 5.2 Run focused unit, contract, fake-CLI component, and packaging checks for every changed behavior and record exact commands, exit codes, and assertions.
- [ ] 5.3 Run strict OpenSpec validation, approved-contract validate/render/check, second-render equality, source-link audit, public-operation completeness, non-live collect-only isolation, mypy for source/tests, Ruff check/format, documentation, package build/import, and forbidden-content gates.
- [ ] 5.4 Run the full non-live suite locally only if it can complete within ten minutes; otherwise stop only the owned test process and run the unsplit suite in GitHub Actions against the published exact revision.

## 6. Independent E2E Evidence and Delivery

- [ ] 6.1 Have an independent Tester pass the existing verifier readiness gate with wrapper-owned `multica-test` isolation and disposable stand data, then execute `scripts/e2e/verify_multica_test.py` once for the consolidated exact revision.
- [ ] 6.2 Have Tester independently walk through literal inline/file persistence, metadata-key round-trip, and archived-project mutation refusal on fresh disposable resources; inspect SDK/CLI output and remote state rather than rerunning the verifier, and inspect lower-level evidence for private membership, rerun-task, `499`, webhook, and runtime-delete scenarios.
- [ ] 6.3 Preserve ordinary development/test scripts, fixtures, generated product outputs, and real commits in Git, but publish real outputs, logs, hashes, diagnostic JSON, private endpoints, and any images only as sanitized Multica evidence; clean stand data while preserving the evidence branch/MR/commits.
- [ ] 6.4 Publish normal commits, push without force, prove remote SHA equals the reviewed local SHA, attach commands/exit codes/assertions/provenance/CI/MR/commit/file links and the no-image rationale in Multica, and verify comment and attachment read-back.
