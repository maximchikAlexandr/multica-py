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

## 4. Verification Preparation and CI Assets

- [ ] 4.1 Extend the existing `tests/live` readiness layer to require four independently authenticated profile inputs (member, self-agent, authorized agent, denied agent), validate caller identity without exposing credentials, and refuse mutation when any profile or documented provisioning provenance is absent.
- [ ] 4.2 Prepare focused authority/privacy live cases inside one uniquely named disposable project per attempt; add member-owned setup, bounded cancel/terminal refresh for captured runs, public project-delete cascade read-back for issues/runs/chat threads, fresh-project reset, and sanitized fail-closed recovery for any residual state; keep the case blocked until the test owner supplies the four profiles through a supported authentication channel.
- [ ] 4.3 Add deterministic `FakeMultica` and existing process-contract cases for ordinary/forced daemon argv, graceful timeout, PID/profile mismatch, unresolved PID, force failure, confirmed termination, and unconfirmed cleanup; do not add a live daemon failure injector.
- [ ] 4.4 Keep visible-output captures disabled because output is unchanged; if implementation changes terminal tables/logs/progress/summaries, stop for a planning revision that selects an available capture method and requires actual baseline/candidate text and images.
- [ ] 4.5 Extend existing GitHub CI jobs/fixtures for applicable offline checks and live readiness collection without adding a runner, private hostname, credential, personal profile, or credential provisioning to the repository.

## 5. Documentation and Repository Gates

- [ ] 5.1 Update compatibility, API, service-usage, migration, CLI-coverage, changelog, contributing, packaging, and release documentation for direct `0.7.1` to `0.7.2`, compatibility bounds, rerun migration, steering, force, property capacity, privacy, and rollback.
- [ ] 5.2 Run focused unit, contract, component, process, live-collection-isolation, and packaging checks for every changed scenario and record exact commands and exit codes.
- [ ] 5.3 Run strict OpenSpec validation, contract validate/source-check/render/check, source-link audit, deterministic regeneration diff, public-operation completeness, mypy for source/tests, Ruff check/format, docs, and package/release gates.
- [ ] 5.4 Run the full non-live suite locally only if it is expected to finish within ten minutes; otherwise run it unsplit in GitHub Actions on the published exact revision and preserve the CI link.

## 6. Independent Verification and Delivery

- [ ] 6.1 Map every OpenSpec scenario to a lower-level check, focused live case, existing sufficient coverage, or explicit exclusion and keep automated, manual Tester, and CI results distinct.
- [ ] 6.2 Prepare and publish a parent-level verification manifest for a fresh exact-SHA checkout, including mapped lower-level commands, the blocked four-profile live prerequisite, permitted live actions, fixture/reset/cleanup steps, and required revision/assertion/attempt fields.
- [ ] 6.3 Publish normal development/test commits according to their natural durable results, push without force, and prove local candidate HEAD equals the remote branch SHA.
- [ ] 6.4 Publish the implementation handoff bundle with sanitized command inventory, exit-code summary, CI/MR/commit/file links, expected attachment slots, and read-back procedure; keep actual Tester logs, diagnostics, hashes, provenance output, assertions, and images out of Git for the parent-level post-fan-in gate.
