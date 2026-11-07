## 1. Approved contract and provenance

- [ ] 1.1 Recheck that the implementation base is `b268e3bec0436fe51727fda50583344f57663284` with no published same-or-higher migration predecessor, then record the exact `0.7.1`, `0.7.2`, `0.8.0`, and `0.8.1` release, commit, archive, executable, and version-output provenance in `contracts/sdk-contract.json`.
- [ ] 1.2 Reconcile the approved contract to the closed `209 -> 225` CLI inventory: 193 retained target rows, 15 changed rows, 17 added rows, one removed baseline row, the public dynamic `issue wakeup checkin` exception, hidden/source-only rows, and explicit support/defer/non-surface dispositions.
- [ ] 1.3 Reconcile all 196 supported response entrypoints, add pinned source/model/fixture decisions for the 23 changed rows, retain the other 173 without expansion, and make `response_review_complete=true` reproducible.
- [ ] 1.4 Update compatibility metadata to maximum-tested `0.8.1` and exclusive ceiling `0.8.2` while preserving the reviewed minimum and exact rollback projection.
- [ ] 1.5 Run approved-contract schema validation, pinned-source validation, contract-diff classification, and source-link audit; prove no binary, source checkout, collector output, audit JSON, response review, or `.devlocal` evidence is tracked.

## 2. Issue inputs, comments, and retry migration

- [ ] 2.1 Extend the existing issue-list input and binding with paired `updated_since`/`updated_until` RFC3339 validation, strict increasing range, stable pagination flags, exact argv cases, and transport-not-called negative cases.
- [ ] 2.2 Preserve literal repeatable attachment paths across issue create, issue update, and comment add, adding exact argv/body cases for multiple paths, commas, ordering, omission, and existing external-file validation.
- [ ] 2.3 Extend roots-only comment response projection with optional resolution identity/content/truncation fields while preserving omission in default, flat, recent, and thread projections, open enums, and tombstones; add summary/since old/new/invalid fixtures.
- [ ] 2.4 After explicit human approval, replace the approved `issues.rerun(issue) -> None` operation with `issues.rerun_task(run_id, *, issue=None, fresh=False) -> TaskRun`, exact `rerun-task` argv/binding/response metadata, public resource method, bound behavior where applicable, and migration/removal tests that prohibit silent issue-targeted emulation.
- [ ] 2.5 Add a public-surface guard proving comment steering, assignee-picker, hidden retry/probe commands, and other deferred issue behavior create no SDK signatures, operations, models, exports, or generated rows; cover the steering/attachment conflict in reviewed evidence without exposing steering.

## 3. Retained response models

- [ ] 3.1 Add optional integer `credits_micros` to the shared task-run usage projection used by agent task and issue run pages, preserving tokens, costs, timestamps, result/error nullability, pagination, private-content behavior, and old/new/invalid fixtures.
- [ ] 3.2 Add optional integer image `width` and `height` to upload and upload-bytes attachment results, covering image values, non-image omission, older omission, null compatibility where the existing wire permits it, and invalid wire types.
- [ ] 3.3 Add nullable `creator_type` and `creator_id` to the shared project model and all seven project-returning paths, preserving bound relations and adding old/new/null/unknown-open-value fixtures.
- [ ] 3.4 Add nullable `max_concurrent_tasks` to runtime definitions and distinct update presence semantics for unset, integer `1..50`, and explicit null; cover list, rename, update result, invalid booleans/ranges/types, and retained visibility/sharing fields.
- [ ] 3.5 Add nullable or older-server-omitted `whats_new_seen_version` to user profile get/update decoding, preserving timestamps and prior fields with old/new/null/invalid fixtures.
- [ ] 3.6 Add list-only optional RFC3339 `pinned_at` to workspace rows and pinned-first ordering cases, proving create/get/update omission and invalid timestamp handling.

## 4. Deterministic projection and focused verification

- [ ] 4.1 Render `src/multica_py/_generated/approved_sdk.py` only from the reviewed contract, render a second time from unchanged input, compare bytes, and pass generated-source check mode and operation completeness.
- [ ] 4.2 Extend existing `ArgvCase`, `DecodeCase`, `CommandCase`, contract mutation, component, and packaging tables rather than adding duplicate helpers or a new framework; map every delta-spec scenario and each of the 23 changed entrypoints to concrete assertions.
- [ ] 4.3 Run focused issue/comment/retry, task-run, attachment, project, runtime, user, workspace, contract, generator, and public-invariant tests; resolve every failure without broad refactoring.
- [ ] 4.4 Run Ruff, mypy for `src` and `tests`, offline test collection/execution, live collection exclusion, docs, packaging, contract/source-link, and repository verification gates. Move any automated suite predicted to exceed or reaching ten minutes unsplit to GitHub Actions on the exact published revision.

## 5. Documentation and release

- [ ] 5.1 Update API, compatibility, migration, coverage, changelog, and release documentation for the complete `0.7.1 -> 0.8.1` lineage, paired time filtering, literal attachments, projection-specific fields, new optional model fields, and the approved run-targeted retry break.
- [ ] 5.2 Document deferred workflow/view/project-workflow/runtime-concurrency-management/comment-steering/process-control surfaces and the rule that evidence does not approve SDK coverage.
- [ ] 5.3 Build and inspect package artifacts, verify generated/runtime/docs consistency, and confirm no private URL, hostname, credential, local evidence, binary, source clone, diagnostic JSON, or image is committed.

## 6. Publication and independent evidence

- [ ] 6.1 Publish the implementation branch normally, record exact local and remote SHAs, and prove `git rev-parse HEAD` equals `git ls-remote origin refs/heads/<branch>` without force push.
- [ ] 6.2 Link the exact published revision to required GitHub Actions jobs and preserve normal development test/result commit separation only when each has a distinct durable product result.
- [ ] 6.3 Have an independent Tester use a fresh checkout to map every verification case to concrete tests/assertions, run focused lower-level checks, inspect deterministic fixtures, and verify exact-SHA CI without editing implementation, tests, or fixtures.
- [ ] 6.4 Publish the Tester's commands, exit codes, assertions, commit/MR/file/CI links, and applicable attachments in Multica with read-back; keep raw logs, diagnostic JSON, hashes, provenance dumps, private data, and images out of Git, and preserve branch/MR/commits during cleanup.
