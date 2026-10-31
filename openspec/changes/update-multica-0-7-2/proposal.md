## Why

Multica `0.7.2` replaces public issue-level reruns with run-targeted reruns, adds comment steering and forced daemon shutdown, widens property option limits, and tightens task/chat privacy. The SDK needs one direct, evidence-backed `0.7.1` to `0.7.2` contract refresh so these changes are typed, safe, deterministic, and explicitly governed instead of inferred from extractor output.

## What Changes

- Advance the approved upstream target to exact Multica `0.7.2` release `428864784` at commit `f05a525ac8e82f5e9169ad078e44f166fad6d5c8`, retain exact `0.7.1` baseline commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`, preserve the existing `0.6.2` minimum, and move the exclusive compatibility ceiling to `0.7.3` with `0.7.2` as maximum tested.
- Reconcile both 209-node public command trees, every positional/local/inherited flag and constraint, the removed/hidden/deprecated `issue rerun`, new `issue rerun-task`, changed comment-add and daemon-stop inputs, and all 196 supported response entrypoints with exactly eight changed verdicts.
- Add `issues.rerun_task(run_id, *, issue_id=None, fresh=False) -> TaskRun`; retain `issues.rerun(issue_id)` only as an explicitly deprecated compatibility shim over the target's hidden legacy command for this compatibility interval, with removal documented for a future breaking SDK release.
- Add repeatable comment steering by run ID and active-run selection to the existing add/reply path, preserving text-only input, attachment conflicts, ordinary-trigger fallback, open outcome strings, and existing comment/supplement fields.
- Add `force=False` to daemon stop while preserving no-JSON success and requiring guarded graceful-timeout, profile/PID identity, forced-termination, and confirmed-cleanup behavior.
- Expand select and multi-select property create/update validation to 200 options, preserve existing typed validation errors above the limit, and cover 50/51/200/201 boundaries.
- Preserve optional/open `can_supplement`, task-message payloads, and existing task/comment models while adding member/agent/self/permission-denied and foreign-chat privacy fixtures.
- Regenerate only from `contracts/sdk-contract.json`, extend existing table-driven fixtures/tests and documentation, and keep collector output, audits, release binaries, and transient renderings untracked.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: Pin direct `0.7.1` to `0.7.2` provenance, complete command/response reconciliation, compatibility policy, reviewed mappings, and deterministic projection.
- `sdk-surface`: Govern run-targeted rerun, deprecated legacy rerun, comment steering, task privacy, and open typed response behavior on existing resources and models.
- `property-resource`: Raise reviewed select/multi-select option limits to 200 for create and update while preserving property-type restrictions and typed failures.
- `subprocess-transport`: Add forced daemon-stop lifecycle behavior without inventing JSON output or weakening process identity and cleanup safety.
- `verification-and-release`: Require table-driven boundary/privacy/lifecycle coverage, deterministic generation, documentation, packaging, source-link, exact-SHA, and independent verification gates.

## Impact

- Approved contract and generated projection: `contracts/sdk-contract.json`, `src/multica_py/_generated/approved_sdk.py`, validation/render/check tooling, and exact source/test references.
- Existing issue, comment, task-run, daemon, and property resources; shared wire/entity models; operation tables; compatibility checks; and public documentation. No new top-level resource, runner, framework, or runtime dependency is introduced.
- Existing unit, contract, component, process, packaging, and CI fixtures. Verification uses lower-level deterministic checks plus a focused isolated live CLI walkthrough for server-authority/privacy behavior. That live gate is blocked until the test owner supplies independently authenticated caller profiles through a documented supported channel; the single profile in the current harness is insufficient. Evidence remains Multica-only.
- The legacy issue-level rerun remains callable only as a documented deprecated shim and is not represented as a target public CLI node.
