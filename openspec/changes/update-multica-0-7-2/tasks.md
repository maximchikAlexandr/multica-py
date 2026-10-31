## 1. Approved Upstream Contract

- [ ] 1.1 Reproduce the pinned `0.7.1` and `0.7.2` release, tag, source, archive, executable, version, OS/architecture, and ancestry evidence outside the tracked tree.
- [ ] 1.2 Update `contracts/sdk-contract.json` with exact baseline/target provenance, preserved `0.6.2` minimum, maximum-tested `0.7.2`, and exclusive `0.7.3` ceiling.
- [ ] 1.3 Reconcile all 209 baseline and 209 target public command nodes, Cobra/source-only nodes, every effective argument/flag/constraint/destination/secret channel, and the `rerun`/`rerun-task`, steering, daemon-force, hidden-node, and wakeup-checkin decisions.
- [ ] 1.4 Reconcile exactly 196 unique response work items with eight changed and 188 unchanged verdicts, exact old/target URLs, public-model, fixture, documentation, and typed-error actions, and `response_review_complete=true`.
- [ ] 1.5 Validate and source-check the approved contract, render the existing generated projection from it alone, and prove check-mode and repeated-render byte stability while keeping review/transient artifacts untracked.

## 2. Run Rerun and Comment Steering

- [ ] 2.1 Add generated/manual operation metadata and eager/command `issues.rerun_task` bindings for full/short run IDs, optional issue narrowing, exact boolean fresh presence, and existing bound `TaskRun` decoding.
- [ ] 2.2 Retain `issues.rerun(issue_id)` as a distinct `ActionResult[None]` compatibility shim that emits one `DeprecationWarning`, is excluded from the target public command count, and is documented for future breaking removal.
- [ ] 2.3 Extend comment add/reply eager and command signatures with ordered `steer_run_ids` and `steer_active`, preserving content-channel validation and rejecting steering plus attachments before transport.
- [ ] 2.4 Add immutable open `CommentTriggerOutcome` decoding on `Comment.trigger_outcomes` while preserving independent legacy fields and `CommentSupplement` collections.
- [ ] 2.5 Add table-driven unit/contract/component cases for rerun full/short/ambiguous/not-found/unauthorized/fresh/legacy behavior and steering explicit/active/permission/self/caps/race/attachment/multi-receipt/malformed behavior.

## 3. Daemon, Property, and Privacy Adaptation

- [ ] 3.1 Add exact boolean `force=False` to daemon stop eager/command forms, append `--force` only when true, and preserve the existing no-JSON `ActionResult[None]` transport contract.
- [ ] 3.2 Add process cases for ordinary success, graceful timeout, confirmed forced termination, PID/profile mismatch, unresolved PID, force failure, and unconfirmed cleanup without SDK-side fallback termination.
- [ ] 3.3 Enforce the 200-option maximum for select/multi-select property create/update while preserving type restrictions, omission, order, nonblank validation, and the existing typed failure category.
- [ ] 3.4 Add table rows for property create/update at 50, 51, 200, and 201 options plus non-select rejection and zero-transport failure assertions.
- [ ] 3.5 Extend agent-task and issue-run fixtures for member/authorized-agent/self/permission-denied/omitted `can_supplement` and foreign-chat redaction while keeping the field open and optional.
- [ ] 3.6 Add run-message foreign-chat 404 coverage that preserves the existing message payload and redacted `NotFoundError` boundary.

## 4. Focused Live and CI Verification Assets

- [ ] 4.1 Extend the existing `tests/live` harness with exact-revision fixtures for the `multica-test` stand, dedicated `myl-623-tester-N` profile/daemon, disposable identities/issues/runs/comments/properties, readiness checks, attempt recording, and failure-safe cleanup.
- [ ] 4.2 Add focused live cases for steering authority, self/cap/race fallback, multiple receipts, task visibility, and foreign-chat transcript privacy using real member/agent identities without leaking private content.
- [ ] 4.3 Add focused live daemon cases that compare the dedicated PID/profile against the primary daemon, prove ordinary and confirmed forced cleanup, and fail closed on identity or cleanup uncertainty.
- [ ] 4.4 Keep visible-output captures disabled because output is unchanged; if implementation changes terminal tables/logs/progress/summaries, stop for a planning revision requiring actual baseline/candidate text and Mac PNG rendering via bundled `scripts/render_terminal.swift`.
- [ ] 4.5 Extend existing GitHub CI jobs/fixtures for all applicable offline and isolated live checks without adding a runner, private hostname, credential, or personal profile to the repository.

## 5. Documentation and Repository Gates

- [ ] 5.1 Update compatibility, API, service-usage, migration, CLI-coverage, changelog, contributing, packaging, and release documentation for direct `0.7.1` to `0.7.2`, compatibility bounds, rerun migration, steering, force, property capacity, privacy, and rollback.
- [ ] 5.2 Run focused unit, contract, component, process, live-collection-isolation, and packaging checks for every changed scenario and record exact commands and exit codes.
- [ ] 5.3 Run strict OpenSpec validation, contract validate/source-check/render/check, source-link audit, deterministic regeneration diff, public-operation completeness, mypy for source/tests, Ruff check/format, docs, and package/release gates.
- [ ] 5.4 Run the full non-live suite locally only if it is expected to finish within ten minutes; otherwise run it unsplit in GitHub Actions on the published exact revision and preserve the CI link.

## 6. Independent Verification and Delivery

- [ ] 6.1 Map every OpenSpec scenario to a lower-level check, focused live case, existing sufficient coverage, or explicit exclusion and keep automated, manual Tester, and CI results distinct.
- [ ] 6.2 Have an independent Tester use a fresh exact-SHA checkout to inspect the mapping, run focused lower-level checks, execute only the authorized isolated live cases, and record case-level product/CLI revisions, fixtures, assertions, attempts, and cleanup.
- [ ] 6.3 Publish normal development/test commits according to their natural durable results, push without force, and prove local candidate HEAD equals the remote branch SHA.
- [ ] 6.4 Attach sanitized commands, exit codes, assertions, CI/MR/commit/file links, and any required artifacts to the final Multica comment, read back comment and attachments, and keep logs, diagnostics, hashes, provenance output, and images out of Git.
