## 1. Approved Upstream Contract Foundation

- [ ] 1.1 Update `contracts/sdk-contract.json` with exact SDK base, `0.7.1` baseline, `0.12.1` release/source/archive/executable/version provenance, preserved `0.6.2` floor, maximum-tested `0.12.1`, and exclusive `0.12.2` ceiling.
- [ ] 1.2 Reconcile all `209` baseline and `276` target command nodes, including `68` additions, `1` removal, `34` changed nodes, every positional/local/inherited flag, default, alias, presence rule, imperative constraint, destination, and the eight source-only names.
- [ ] 1.3 Record exactly one reviewed support/adapt/retain/remove/defer/not-SDK-surface disposition for every command item and prove deferred and hidden families cannot enter public discovery.
- [ ] 1.4 Reconcile all `196` supported response work items, including exactly `118` changed rows, with old/target source URLs and complete model/adapter/fixture/doc/error/presence actions.
- [ ] 1.5 Extend contract validation for inventory/response totals, provenance mixing, duplicate/pending rows, compatibility bounds, exact source links, and sole-generator-input enforcement.
- [ ] 1.6 Render the committed `src/multica_py/_generated/approved_sdk.py` only from the approved contract and prove repeated validate/render/check runs are byte-stable.
- [ ] 1.7 Update contract and generated-projection tests for all exact identities, totals, dispositions, compatibility metadata, and evidence-exclusion invariants.
- [ ] 1.8 Implement all approved shared target wire structs and decode helpers in `src/multica_py/_internal/wire_models.py` and `src/multica_py/_internal/decoders.py`, with focused shared-wire tests, so later domain packages consume one immutable foundation.

## 2. Command Surface and Transport

- [ ] 2.1 Replace `issues.rerun` and resource/bound `rerun` methods with reviewed `issues.rerun_task`, `rerun_task`, and `rerun_task_command` mappings, results, issue relations, issue exports, and issue-local tests.
- [ ] 2.2 Adapt only `IssueResource` and bound Issue command builders for approved changed issue inputs while retaining stable public names outside the explicit rerun replacement; comment, skill, project, workspace, and operational builders remain in tasks 3.x/4.x.
- [ ] 2.3 Encode every reviewed omitted/null/empty/zero/false presence rule and requires/conflicts/exactly-one/at-least-one/required-together/custom constraint at the existing validation boundary.
- [ ] 2.4 Preserve target inline/file/stdin literal text and trailing-LF behavior in the shared transport and issue paths; domain token mappings remain in their owning 3.x/4.x tasks.
- [ ] 2.5 Preserve shared sanitized decoding for reviewed 400, 409, 413, and 499 responses and add no domain-specific error bypass.
- [ ] 2.6 Extend issue-local and shared-transport exact-argv/body/error tests with positive, negative, omission, explicit-value, and malformed-input rows; do not edit central `tests/cases/operations.py` or `tests/unit/resources/test_operations.py`.
- [ ] 2.7 Remove obsolete rerun runtime/export and issue-test references; central operation discovery and documentation reconciliation remain in tasks 5.1–5.2.

## 3. Collaboration Response Adaptation

- [ ] 3.1 Extend issue domain models/adapters for `description_revision`, requester/subscriber/status and other approved issue-row changes by consuming the task 1.8 wire foundation, with exact omission/nullability/open-value behavior.
- [ ] 3.2 Implement revision-aware issue description writes and table/component cases for current revision, stale typed 409 conflict, omission, explicit empty content, and preserved server state.
- [ ] 3.3 Extend comment models/adapters, domain command builders, and domain-local cases for target revisions and idempotency identity, proving successful replay resolves to one logical comment and malformed/conflict responses fail closed.
- [ ] 3.4 Extend skill models/adapters, domain command builders, and domain-local cases for target revision/base-revision semantics, current/stale/omitted inputs, conflict preservation, and existing portable atomic bundle behavior.
- [ ] 3.5 Extend project models/adapters, domain command builders, and domain-local cases for approved progress, activity, archive, membership, and pagination response fields without exposing deferred project command families.
- [ ] 3.6 Extend all approved workspace response models, domain command builders, and domain-local cases, including member/invitation guest role and conditional `project_ids`, authorized visibility, guest redaction, older-payload compatibility, and malformed rows.
- [ ] 3.7 Add table-driven domain-owned unit/contract/component fixtures for positive, negative, omitted, null, empty, zero/false, unknown-open-value, pagination, redaction, replay, and typed-error cases across tasks 3.3–3.6 without editing shared test registries or conftest files.
- [ ] 3.8 Keep all collaboration model changes frozen/typed, update only domain-owned exports, and prove existing supported `0.6.2`/`0.7.1` fixtures still decode.

## 4. Operational Response Adaptation

- [ ] 4.1 Extend configuration projections, domain command builders, and domain-local cases for approved target limits and fields with target and older-payload presence cases.
- [ ] 4.2 Extend daemon start/stop/log projections, domain command builders, and domain-local cases for approved log controls and response changes without changing human-visible renderer output.
- [ ] 4.3 Extend runtime/profile/usage projections, domain command builders, and domain-local cases for every approved changed registry row, including machine-bound profiles, usage windows, omission/nullability, and open values; consume workspace projections owned by task 3.6 without editing workspace resource/model/entity files.
- [ ] 4.4 Extend agent/autopilot/task/attachment projections, domain command builders, and domain-local cases for approved run outcome, task-credit, dimensions, and related target fields while preserving existing relation and pagination behavior.
- [ ] 4.5 Apply every remaining operational response-registry action in its domain-owned model/resource seam by consuming the task 1.8 wire foundation, and record each row's concrete test and documentation reference.
- [ ] 4.6 Add domain-owned frozen unit/contract/component rows for positive, malformed, omitted, null, empty, numeric-boundary, pagination, unknown-open-value, and retained typed-error behavior across tasks 4.1–4.5 without editing shared test registries or conftest files.
- [ ] 4.7 Prove all unchanged response rows remain source-equal and regression-covered and that no deferred resource family or version-specific wrapper was introduced.

## 5. Integration, Documentation, and Publication

- [ ] 5.1 Reconcile central shared surfaces after all domain packages: `tests/cases/operations.py`, `tests/unit/resources/test_operations.py`, shared component fixtures/conftest files, public client/export registries, and the complete scenario-to-test map; then run public-operation completeness, live-test collection isolation, contract validate/render/check, deterministic diff, and source-link audit.
- [ ] 5.2 Update compatibility, API, service-usage, migration, CLI-coverage, changelog, contributing, packaging, and release documentation for the direct upgrade, rerun replacement, revision/replay/redaction semantics, deferred scope, and rollback.
- [ ] 5.3 Update the existing non-live GitHub contract job to fetch exact target source and keep all review-only artifacts under ignored paths; add no new CI framework or private stand dependency and leave `.github/workflows/live-smoke.yml` exclusively to task 6.2.
- [ ] 5.4 Run focused unit/contract/component checks, mypy for source/tests/scripts, Ruff check/format, documentation and package checks, recording exact commands and exits.
- [ ] 5.5 Run the full non-live suite locally only when expected to complete within ten minutes; otherwise publish the exact revision and run the unsplit suite in GitHub Actions.
- [ ] 5.6 Separate natural implementation/test results into ordinary commits where each has a distinct durable result, push normally, and prove local HEAD equals the remote candidate SHA.

## 6. Isolated Live and Independent Evidence

- [ ] 6.1 Add the gated `tests/live/test_v0121_upgrade.py` module by reusing the existing `prepared_client`, live markers, five required `MULTICA_LIVE_*` values, UUID naming, and cleanup pattern; add only the minimal `MULTICA_LIVE_GUEST_PROFILE` and `MULTICA_LIVE_GUEST_PROJECT_ID` fixture inputs needed for the read-only guest assertion.
- [ ] 6.2 Update `tests/live/conftest.py` and `tests/live/README.md` from exact prepared target `0.7.0` to `0.12.1`, document `MULTICA_LIVE_CLI=multica-test` with the isolated daemon/profile/workspace and guest fixtures, update `.github/workflows/live-smoke.yml` to target `0.12.1` without adding a runner/config namespace, and enforce exact revisions, stand readiness, UUID namespace, permissions, collection, and failure-safe cleanup.
- [ ] 6.3 Have an independent Tester use a fresh exact-revision checkout and isolated data to run the issue-description, comment-idempotency, skill-revision, and guest/project-progress cases without editing implementation or test artifacts.
- [ ] 6.4 Have Tester inspect lower-level mappings and run focused deterministic checks for command inventory, rerun replacement, all changed response domains, errors, compatibility, docs, and packaging.
- [ ] 6.5 Publish case-level commands, exit codes, assertions, tested SHA, fixtures, commit/MR/file/CI links, cleanup result, and no-image rationale in Multica; attach any actual outputs only there and verify comment/attachment read-back.
- [ ] 6.6 Remove run-owned stand entities and local diagnostics while preserving branch, commits, CI/MR links, and Multica evidence; do not merge, close, or delete the branch without separate authorization.
