## 1. Approved Upstream Contract

- [ ] 1.1 Update `contracts/sdk-contract.json` with exact `0.7.0` baseline, `0.7.1` target/release/archive/executable provenance, preserved `0.6.2` minimum, maximum-tested `0.7.1`, and exclusive `0.7.2` ceiling.
- [ ] 1.2 Reconcile all 209 CLI nodes and every positional/local/inherited flag, including source-traced mappings, presence semantics, open/closed value policy, and positive/negative cases for the four changed help nodes.
- [ ] 1.3 Reconcile exactly 196 supported response entrypoints with one old/target source pair, disposition, public-model action, fixture action, documentation action, and error behavior each.
- [ ] 1.4 Record the approved retained/adapted/not-SDK-surface decisions and prove that review evidence and `.devlocal` artifacts cannot drive generation.
- [ ] 1.5 Run contract validate and render from the approved contract, commit the refreshed generated projection, and prove check-mode byte stability.

## 2. Wakeup and Agent Behavior

- [ ] 2.1 Extend existing wakeup condition mappings with open state `blocked` across create and update without adding a second enum or resource.
- [ ] 2.2 Extend shared wakeup decoding and table rows for `blocked` through create, update, get, list, and events.
- [ ] 2.3 Add wakeup negative rows for invalid state, missing issue dependency, and every applicable mutually-exclusive condition combination.
- [ ] 2.4 Add agent create/update cases for allowed custom arguments, provider-reserved standard error, omitted arguments, explicit empty array, and runtime change retaining arguments.

## 3. Autopilot and Task Outcomes

- [ ] 3.1 Adapt existing autopilot fixtures and relations for create-issue `task_id`, successful completion, blocked issue settlement without false run failure, failure/retry ordering, and nullable legacy data.
- [ ] 3.2 Add malformed non-null `task_id` output-shape coverage while retaining `AutopilotRun.task_id` nullability.
- [ ] 3.3 Add known process-cleanup result/failure fixtures on issue-run and agent-task paths and prove unknown valid future values remain open.
- [ ] 3.4 Add invalid wire-shape coverage for open task `failure_reason` and `result` boundaries without introducing closed enums.

## 4. Issue, Project Resource, and Skill Corrections

- [ ] 4.1 Add issue-search coverage proving an out-of-range int4-looking query remains text and returns the existing typed page.
- [ ] 4.2 Add workflow-resolution update coverage proving the returned issue preserves its assignee.
- [ ] 4.3 Add a component regression for concurrent project-resource partial updates, omitted-versus-null behavior, and preservation of unrelated fields.
- [ ] 4.4 Extend skill bundle fixtures for portable-path rejection, traversal/absolute/platform escape cases, binary skipping, and complete portable bundle success.
- [ ] 4.5 Add standard-error cases for remote 400, 413, 502, 503, and 504 skill acquisition failures and prove refresh preserves the prior complete bundle after every failure class.

## 5. Documentation and Repository Verification

- [ ] 5.1 Update compatibility, API, service-usage, migration, CLI-coverage, changelog, contributing, packaging, and release documentation for direct `0.7.0` to `0.7.1` migration and the preserved compatibility floor.
- [ ] 5.2 Run focused table-driven unit, contract, and component tests for every changed behavior and record exact commands and exit codes.
- [ ] 5.3 Run strict OpenSpec validation, source-link audit, contract validate/render/check, public-operation completeness, live-test collection isolation, mypy for source/tests, Ruff check/format, documentation, and packaging gates.
- [ ] 5.4 Run the full non-live suite locally only if it can complete within ten minutes; otherwise run the unsplit suite in GitHub Actions against the published exact revision and preserve the CI link.

## 6. Independent Verification Evidence and Delivery

- [ ] 6.1 Map every changed scenario to an existing or extended unit, contract, fake-CLI component, lifecycle, concurrency, documentation, or packaging check; add no task-specific live script or infrastructure.
- [ ] 6.2 Have an independent Tester use a fresh exact-revision checkout to inspect the mapping, run the focused lower-level checks, and verify that their assertions cover wakeup, agent, autopilot, issue, project-resource, skill, and process-cleanup behavior without claiming live-server proof.
- [ ] 6.3 Publish normal development and test commits according to their natural results, push normally, and prove the remote branch SHA equals the reviewed local SHA.
- [ ] 6.4 Attach commands, exit codes, assertions, CI/MR/commit/file links, and the no-image rationale in Multica, read the comment and attachments back, and keep diagnostic outputs untracked.
