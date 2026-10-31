## Context

The exact SDK planning base is `b268e3bec0436fe51727fda50583344f57663284`. It approves Multica `0.7.1` at source commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`, renders one generated runtime projection from `contracts/sdk-contract.json`, supports a `0.6.2` minimum, and rejects `0.7.2` because it is the current exclusive ceiling.

Multica `0.7.2` release `428864784` is pinned at commit `f05a525ac8e82f5e9169ad078e44f166fad6d5c8`. Its verified inventory remains 209 public command nodes, but `issue rerun` becomes hidden/deprecated, `issue rerun-task` becomes public, `issue comment add` gains steering flags, and `daemon stop` gains `--force`. Eight of 196 reviewed response entrypoints change behavior or error semantics. Evidence, collector output, audits, binaries, and transient renders are review-only; only the approved contract can generate production artifacts.

The current code already has a rich `TaskRun`, comment supplement decoding, shell-free command plans, process-lifecycle handling, property resources, centralized typed errors, and frozen table cases. The design extends those paths and keeps human implementation approval as a separate gate.

## Goals / Non-Goals

**Goals:**

- Define a direct `0.7.1` to `0.7.2` upgrade with exact release, tag, source, archive, executable, command, response, and compatibility provenance.
- Approve stable Python names, types, defaults, migration behavior, validation, and error boundaries for run rerun, comment steering, daemon force, property capacity, and task/chat privacy.
- Preserve deterministic generation, open future values, table-driven tests, exact-SHA evidence, and rollback to the `0.7.1` projection.
- Add only the focused live verification needed to prove server-side authority/privacy and isolated daemon lifecycle behavior.

**Non-Goals:**

- Removing the deprecated issue-level rerun in this non-breaking SDK release or promising it beyond the documented compatibility interval.
- Adding generic task-control, steering-manager, daemon-supervisor, permission-policy, property-catalog, or E2E framework abstractions.
- Adding SDK operations for hidden `probe-runtimes`, UI, desktop, WeCom/Lark, provider/runtime internals, or other release-note items without a reviewed public CLI contract.
- Generating from extractor output, audits, release archives, live output, or evidence files; running implementation during planning.

## Decisions

### 1. Advance one approved contract and preserve the existing compatibility floor

The approved contract will use exact baseline `0.7.1` and target `0.7.2` identities, preserve `min_cli_version=0.6.2`, set `max_tested_cli_version=0.7.2`, and use `0.7.3` as the exclusive ceiling. Every changed inventory/response row will carry exact old and target source URLs, reviewed input/output/error actions, fixture actions, and documentation actions. Validate, source-checkout validation, render, check, source-link audit, and repeated-render diff will consume only `contracts/sdk-contract.json`.

Alternative considered: raise the minimum to `0.7.1`. Rejected because the target does not require dropping already-supported callers; operation-level minimums and the existing preflight can express additive `0.7.2` surfaces.

### 2. Add run-targeted rerun and retain one explicitly temporary legacy shim

`IssueResource.rerun_task(run_id, *, issue_id=None, fresh=False)` and its command form will emit `issue rerun-task <run-id>`, optional `--issue <issue-ref>`, presence-only `--fresh`, and `--output json`, then decode and bind the existing `TaskRun`. Full and short run IDs are accepted; `issue_id` is optional narrowing context, not a replacement run identity. `fresh` must be an exact boolean. The returned task uses the response's issue context when present and the supplied `issue_id` only as relation context when the response omits it.

Existing `rerun(issue_id)` remains source-compatible for this release, calls only the target hidden/deprecated legacy command, and emits one `DeprecationWarning` directing callers to `rerun_task`. It remains excluded from the target public command-node count and is documented for removal in the next breaking SDK release. It continues returning `ActionResult[None]`; the new task result is never coerced into that old type.

Alternative considered: remove `rerun` immediately. Rejected because the target still provides a compatibility command and a patch-level SDK update can offer a safe migration interval. Alternative considered: silently redirect issue IDs to the new operation. Rejected because issue identity and run identity are not interchangeable.

### 3. Extend the existing comment content path with typed steering inputs and open receipts

Comment `add` and `reply` eager/command forms will accept `steer_run_ids: tuple[str, ...] = ()` and `steer_active: bool = False`. Ordered run IDs emit repeatable `--steer`; `steer_active=True` emits `--steer-active`. Each ID must be nonblank, the collection must be a tuple of strings, and `steer_active` must be an exact boolean. Steering remains text-only: any attachment combined with either steering input fails before transport; the existing exactly-one content-channel rule remains unchanged.

The existing `Comment` projection will expose `trigger_outcomes` and keep `supplements`. A `CommentTriggerOutcome` carries optional target agent/task IDs plus open nonblank `status` and optional open `reason_code`; unknown valid strings remain decodable. Existing `CommentSupplement` fields remain unchanged. Permission denial, self-steer, per-run/global caps, race fallback, coalesced/deferred/blocked outcomes, and multiple receipts are server-owned outcomes, not local policy duplication.

Alternative considered: a separate steering resource or closed status/reason enums. Rejected because steering is one mode of comment creation and the server can add outcomes without an SDK release.

### 4. Expose daemon force through the existing lifecycle operation

`DaemonResource.stop(*, force=False)` and its command form will append `--force` only when true and will continue returning no fabricated JSON payload. The SDK will rely on the target CLI's graceful wait, profile/PID identity check, exact child termination, and cleanup confirmation. Existing centralized process/error handling will surface graceful timeout, profile/PID mismatch, forced termination failure, and unconfirmed cleanup without retrying, killing by executable name, or directly managing daemon state.

Alternative considered: a second `force_stop` method or SDK-side signal logic. Rejected because it duplicates one target flag and could bypass target identity safeguards.

### 5. Keep property capacity and privacy changes at existing boundaries

Property create/update will locally accept at most 200 ordered options only for `select` and `multi_select`, preserve existing actor/list-type exclusions and nonblank validation, and reject 201 before transport with the established validation category. Tests cover 50, 51, 200, and 201 on both operations.

`agents.tasks` and `issues.runs` retain optional/open `can_supplement`; fixtures distinguish member, authorized agent, self, permission-denied, omitted, and false. Foreign chat-task content is absent/redacted rather than synthesized. `issues.run_messages` retains `RunMessage`/task-message payload types and maps the target foreign-chat 404 through the existing `NotFoundError` boundary.

Alternative considered: permission enums or client-side authorization prediction. Rejected because authority depends on caller/server state and must not be cached or inferred locally.

### 6. Ponytail full gate

No new subsystem is necessary. The approved contract/generator, `TaskRun`, comment wire/entity models, property resource, subprocess plan, typed error classifier, shared table-case dataclasses, current live-test fixtures, and CI workflow are sufficient. A rerun service, steering manager, daemon supervisor, permission registry, property validator framework, second generator, and second E2E runner are removed from the design. The only new public structures are the smallest stable method inputs and one outcome record required to expose reviewed target behavior.

### 7. Focus live verification on irreducibly server-owned behavior

`e2e_required=true`. Lower-level tests prove argv, decoding, validation, deterministic generation, and error classification. A focused isolated live walkthrough is still required for (a) steering authorization/caps/race fallback and foreign-chat privacy across real member/agent identities, and (b) forced daemon shutdown's PID/profile identity and cleanup confirmation. These outcomes depend on server authority, scheduling, and real process state and cannot be proven by fake CLI output alone.

The Implementer will extend the existing `tests/live` harness rather than add a runner. Tester will use the project test repository `https://github.com/maximchikAlexandr/multica-py`, the isolated `multica-test` stand, a dedicated `myl-623-tester-N` profile/daemon, disposable issues/comments/runs/properties, and owned ports/data only. The primary Multica profile, daemon, containers, and reference checkout are forbidden. Visible CLI output is not intentionally changed, so no before/after PNG is required; actual text and images become mandatory only if implementation changes visible output.

## Risks / Trade-offs

- **The hidden legacy rerun disappears in a later CLI** → Mark it deprecated, bind it only inside the declared interval, document migration, and remove it only through a future breaking change.
- **Short run IDs resolve ambiguously** → Preserve target `--issue` narrowing, test ambiguity/not-found errors, and never resolve IDs locally.
- **Steering outcomes evolve** → Keep status/reason strings open while strictly validating required shape and IDs.
- **Force stop could affect the wrong daemon** → Require a dedicated profile, compare target PID with primary daemon status, reject identity mismatch, and terminate only the owned child.
- **Live authority/race cases are timing-sensitive** → Gate attempts on exact revision/readiness, capture task/run IDs and outcomes, diagnose with deterministic checks before retry, and preserve a case-level attempt ledger.
- **Wide contract edits can hide omissions** → Require 209/209 command closure, 196 unique response work items, exactly eight changed verdicts, source-link audit, and byte-stable regeneration.
- **Full automated verification can exceed ten minutes** → Stop only the owned local suite at the limit and run the unsplit suite in GitHub Actions on the published exact revision.

## Migration Plan

1. Reproduce exact release/source/binary evidence outside the tracked tree and update only the reviewed approved contract.
2. Render the existing generated projection, add the new operation/input/output bindings, and preserve the legacy rerun shim as deprecated manual compatibility surface.
3. Extend issue/comment/task, daemon, and property adapters plus table-driven unit/contract/component/process/live fixtures.
4. Update compatibility, API, migration, coverage, changelog, contributing, packaging, and release documentation for direct `0.7.1` to `0.7.2` adoption and rerun migration.
5. Run focused local gates, publish normally, and run any suite expected to exceed or reaching ten minutes unsplit in GitHub Actions at the same SHA.
6. Have an independent Tester verify lower-level mappings and the isolated live cases, attach sanitized evidence in Multica, and read back the comment/attachments.
7. Roll back by reverting implementation commits and restoring the `0.7.1` approved/generated projection; no persistent product-data migration is introduced. Do not close, merge, or delete the evidence branch without separate authorization.

## Open Questions

None. Public naming, result types, open-value policy, legacy deprecation, steering exposure, daemon force exposure, compatibility bounds, and verification boundaries are fixed by this package.
