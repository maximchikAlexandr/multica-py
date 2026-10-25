## 1. Approved target and deterministic contract

- [ ] 1.1 Replace target/release/asset/binary provenance with verified Multica `0.7.0`, retain `0.6.1` as the effective baseline, and generate the reviewed compatibility interval.
- [ ] 1.2 Reconcile exactly 209 target CLI nodes and their positional/local/persistent flags with explicit support decisions; retain `daemon autostart*` as `defer` and workflow-management/internals as `not_sdk_surface`.
- [ ] 1.3 Reconcile exactly 196 supported response items with 60 changed and 136 unchanged unique verdicts, paired old/target source URLs, fixture action, test reference, and documentation action.
- [ ] 1.4 Trace every changed input to path/query/JSON/header/multipart/stdin/file/local-control destinations and approve five-state presence, enums, and normalized constraints with positive/negative vectors.
- [ ] 1.5 Update contract schema/loader/generator only where the target data requires it; render the committed approved runtime projection and prove repeated rendering is byte-identical.
- [ ] 1.6 Add fail-closed mutation/reconciliation tests for provenance, counts, duplicate/missing verdicts, unreviewed candidates, mappings, presence, constraints, compatibility, and deterministic generation.

## 2. Property types and comparison filters

- [ ] 2.1 Extend property definition/value types and exports for `multi_text` and `multi_url` using the existing typed JSON boundary.
- [ ] 2.2 Extend issue property write encoding/decoding for ordered arrays, duplicates, explicit empty arrays, omission, null, invalid elements, and URL validation.
- [ ] 2.3 Extend the existing issue-list property predicate model and argv/query adapter with reviewed comparison operators and deterministic order.
- [ ] 2.4 Add frozen unit/contract/component rows for positive and negative array, presence, ordering, duplicate, null, comparison, operator/type, and legacy equality cases.

## 3. Project and daemon response adaptations

- [ ] 3.1 Add nullable `workflow_id` to project wire/public models, decoders, compatibility fixtures, and exports without adding workflow-management methods.
- [ ] 3.2 Adapt project create/update mappings for reviewed workflow presence and validation semantics; cover omitted, null, empty, present, invalid, and legacy responses.
- [ ] 3.3 Add optional `cli_commit` to daemon status decoding and public typing with target, empty, omitted, malformed, and legacy fixture cases.

## 4. Wakeup condition and diagnostics

- [ ] 4.1 Extend the existing wakeup condition enum/request mapping for the reviewed PR-conflict condition in eager and command APIs.
- [ ] 4.2 Preserve exactly-one condition validation and add positive/negative argv parity cases for create and update.
- [ ] 4.3 Decode reviewed wakeup diagnostics and stale `last_error` clearing with explicit omitted/null/empty distinctions and self-hosted compatibility fixtures.

## 5. Runtime sharing, privacy, and authorization

- [ ] 5.1 Add reviewed `shared_with` wire/public typing, decoder behavior, exports, and legacy omission handling to runtime list/rename/update results.
- [ ] 5.2 Adapt runtime update/delete for explicit sharing, atomic privacy revocation, busy blockers, and structured 409 context without partial local mutation or retry.
- [ ] 5.3 Adapt agent create/update authorization errors for explicitly granted runtimes and cover allowed, denied, revoked, malformed, and legacy paths.
- [ ] 5.4 Add frozen resource, decoder, bound-entity, conflict, and redaction cases for sharing order, identity shape, revoke atomicity, blocker context, and authorization.

## 6. Upload, network, server, and workspace errors

- [ ] 6.1 Extend centralized transport error decoding for the reviewed stable server and network shapes while retaining generic fallback behavior.
- [ ] 6.2 Adapt attachment/skill upload paths and workspace create/update allowlist failures to expose only approved typed safe context.
- [ ] 6.3 Add component and unit fixtures for status/code/message/context mapping, malformed payloads, redaction of URLs/hosts/paths/credentials/personal data, and no unintended retry.

## 7. Documentation and compatibility migration

- [ ] 7.1 Update compatibility, CLI coverage, API, and migration docs for the direct `0.6.1` to `0.7.0` interval and each supported adaptation.
- [ ] 7.2 Document retained/deferred/non-surface decisions, array/comparison syntax, presence semantics, workflow field, daemon commit, wakeup conflicts, runtime grants/revocation, and sanitized errors with checked examples.
- [ ] 7.3 Update changelog and release documentation with provenance, generation commands, package checks, rollback, and the human approval gate.

## 8. Offline, CI, package, and live verification

- [ ] 8.1 Run source-link audit, strict approved-contract validation, deterministic render, generated freshness check, and contract schema/inventory reconciliation.
- [ ] 8.2 Run focused tests after each owned resource change, then offline unit/contract/component/packaging suites, collection audit, mypy for source/tests, Ruff check/format, and build wheel/sdist import checks.
- [ ] 8.3 Extend existing GitHub CI jobs and fixtures only as required for the new offline contract; do not introduce a second test framework or private service dependency.
- [ ] 8.4 Extend the existing five-input live-smoke harness for the exact CLI `0.7.0` candidate, disposable project lifecycle and read-only daemon commit case with failure-safe cleanup; keep property, wakeup, runtime/privacy, authorization, and structured-error scenarios on the explicit lower-level checks in `delivery-plan.md` because the declared stand provides none of their required fixtures or provisioning controls.
- [ ] 8.5 Have an independent Tester perform the delivery-plan walkthrough, publish exact revision/command/assertion/cleanup evidence and required before/after text plus PNG attachments in Multica, and leave the evidence branch/PR open unless separately instructed.
- [ ] 8.6 Verify the final Git diff contains no collector output, raw logs, diagnostic JSON, screenshots, generated evidence, private URLs/hosts/personal data, or hand-edited generated files before release approval.
