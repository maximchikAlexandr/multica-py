## Context

The repository currently approves Multica `0.7.0` at source commit `dbdbb299164347586e2650bb67684a490726a798` and renders one generated runtime projection from `contracts/sdk-contract.json`. The exact SDK planning base is `f3c41027b89550731e52335e6bea42eeb7b4e905`. Multica `0.7.1` is the next stable release, release id `425269384`, at source commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`.

The reviewed delta keeps all 209 CLI nodes but changes help for `agent create`, `agent update`, `issue wakeup create`, and `issue wakeup update`. It also changes retained behavior for wakeup issue-state conditions, provider-reserved agent arguments, create-issue autopilot settlement, issue search and workflow assignment, concurrent project-resource updates, portable/atomic skill bundles, and process-cleanup task outcomes. The upstream dossier closes all 196 supported response entrypoints. Collector files, audit JSON, binaries, and review supplements remain evidence only; the approved contract is the only production generator input.

## Goals / Non-Goals

**Goals:**

- Define a direct `0.7.0` to `0.7.1` upgrade with exact source, release, archive, executable, command, and response provenance.
- Preserve the current public resource architecture and compatibility floor while moving maximum tested to `0.7.1` and the exclusive ceiling to `0.7.2`.
- Specify complete typed/open behavior, table-driven regressions, deterministic generation, documentation, packaging, and independent verification evidence.
- Keep server-only corrections observable through existing SDK operations without inventing new public methods.

**Non-Goals:**

- Adding SDK operations for Devin ACP, AppConfig daemon setup, claim-only fields, workflow prompts, Lark media, UI, i18n, or analytics internals.
- Generating public behavior directly from extractor output, release notes, source diffs, or live evidence.
- Adding another generator, compatibility registry, validation framework, E2E framework, or runtime dependency.
- Running implementation or verification during this planning change.

## Decisions

### 1. Advance one approved contract and preserve one compatibility lineage

Update the existing contract target to `0.7.1`, append exact target release/binary identity, preserve `min_cli_version=0.6.2`, set `max_tested_cli_version=0.7.1`, and reject versions at or above `0.7.2`. The implementation SHALL retain the exact `0.7.0` and `0.7.1` source URLs for every changed row and SHALL render through the existing validate/render/check commands.

Alternative considered: raise the minimum CLI to `0.7.0`. Rejected because no reviewed removal requires dropping already-supported `0.6.2` callers; the policy-valid equivalent is the existing floor plus the new exclusive ceiling.

### 2. Treat `blocked` as an open issue-state value on the existing wakeup path

Extend the existing issue-state condition validation and generated command mapping with `blocked`. The same value SHALL round-trip through create, update, get, list, and events. Existing validation SHALL continue to reject an unknown state, a missing `--until-issue` dependency, and condition combinations that are mutually exclusive.

Alternative considered: introduce a wakeup-specific closed enum or a second condition model. Rejected because upstream owns the state vocabulary and the current open-string condition path already preserves future values.

### 3. Keep agent reserved-argument policy at the current request/error boundary

Retain `custom_args` as an ordered tuple carried by the current create/update methods and agent model. Contract fixtures SHALL cover allowed values, provider-reserved rejection with the standard error payload, omission, an explicit empty tuple, and a runtime change that retains existing arguments.

Alternative considered: pre-encode provider-specific reserved names as an SDK enum or validator. Rejected because the provider owns and can extend this policy; duplicating it would drift and could reject valid future arguments before the authoritative CLI responds.

### 4. Model corrected autopilot settlement without closing nullable or open fields

Keep `AutopilotRun.task_id` nullable for legacy and non-task data. The existing run decoder and relation helpers SHALL represent create-issue settlement through task success, an issue reaching `blocked` without a false run failure, and failure/retry chains. `failure_reason`, task `result`, and process-cleanup values SHALL remain open strings/mappings rather than closed enums.

Alternative considered: synthesize a task id or add a closed settlement enum. Rejected because either loses legacy nullability or turns upstream lifecycle expansion into a decoding break.

### 5. Prove server correctness changes through existing public operations

Issue search SHALL accept an out-of-range int4-looking query as text. Workflow-resolved issue updates SHALL preserve the returned assignee. Concurrent project-resource partial updates SHALL prove that unrelated fields are not lost. Skill import/refresh SHALL use existing skill methods and model boundaries while fixtures cover portable path rejection, binary skipping, complete bundle success, remote 400/413/502/503/504 failures, and preservation of the prior bundle on refresh failure.

Alternative considered: add SDK transaction, bundle, or workflow abstractions. Rejected because the public command tree and successful response models are unchanged; focused behavioral fixtures and component checks close the reviewed gap.

### 6. Ponytail full gate

No new subsystem is necessary: the need is fully covered by the existing approved contract, deterministic generator, resource adapters, frozen/open models, shared standard-error decoder, table-case types, and repository verification commands. Parallel validators, version-specific resource wrappers, provider policy registries, task-result enums, bundle managers, and another E2E runner are omitted.

### 7. Independent evidence uses one focused isolated walkthrough

Implementation SHALL add one repository-native verification script using the project-described isolated `multica-test` target. It SHALL assert representative real-boundary behavior for wakeup `blocked`, provider-reserved arguments, autopilot settlement, issue boundary/assignee behavior, concurrent project-resource updates, atomic skill refresh, and process-cleanup decoding, while reusing lower-level tests for exhaustive case matrices. The script SHALL record the exact product and test revisions, use disposable data, sanitize outputs, and clean up failure-safely. The Tester SHALL independently perform the public actions and inspect resulting objects/state; replaying the script alone is not the manual check.

No before/after PNG is required because this change does not alter human-facing terminal tables, logs, progress, summaries, or browser UI. Actual JSON/text outputs, commands, exit codes, hashes, assertions, and provenance SHALL be attached only to Multica, not committed.

## Risks / Trade-offs

- **Wide source diff can hide SDK-relevant behavior** → Close all 209 command nodes and 196 supported response entrypoints with old/target source URLs and explicit actions.
- **Open upstream values reduce static exhaustiveness** → Keep open strings/mappings and test known `0.7.1` values without rejecting unknown future values.
- **Server-correctness changes can look wire-compatible** → Require component fixtures plus focused real-boundary assertions for concurrency, settlement, and atomic refresh.
- **Live evidence can accidentally target the primary profile or wrong revision** → Use only the isolated project stand and `multica-test`, prove exact revisions before mutation, and publish sanitized evidence with read-back.
- **Skill failure testing can overwrite the prior bundle** → Use disposable skills and assert the old bundle before and after each failure class, with failure-safe cleanup.
- **Full offline verification may exceed the local ten-minute limit** → Stop only the owned test process at ten minutes and finish the exact published revision in GitHub Actions without splitting the suite.

## Migration Plan

1. Update the approved contract provenance, ceiling, command inventory, four changed help mappings, response registry, and source/test references.
2. Validate the contract, render the existing generated projection, and prove check-mode freshness from the approved contract alone.
3. Extend the existing resource/model adapters only where required and add table rows or focused regressions for every specified behavior.
4. Update compatibility, API, migration, coverage, changelog, packaging, and release documentation for direct `0.7.0` to `0.7.1` adoption.
5. Run focused gates locally; run any automated suite expected to exceed ten minutes in GitHub Actions on the published exact revision.
6. Have an independent Tester execute the isolated walkthrough, attach sanitized evidence in Multica with read-back, and remove only disposable stand data.
7. Roll back by reverting the implementation commit set and restoring the prior generated projection and `0.7.0` target; no persistent data migration is introduced.

## Open Questions

None. The approved scope keeps public enums open where upstream owns future values, preserves the existing compatibility floor, and excludes upstream-only internals.
