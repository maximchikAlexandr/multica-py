## Context

The repository at `origin/main@b268e3bec0436fe51727fda50583344f57663284` approves Multica `0.7.1` at upstream commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`, with 193 SDK operations and 196 response entrypoints. No open SDK PR provides a later published migration base. The active `0.7.2` planning work is below this change's target and is not a stacked predecessor.

The reviewed target is stable Multica `0.8.1`, release `436353568`, published `2026-11-06T10:15:19Z`, at commit `b1ea927def6490c43bedff537b6f4ed9a47fa828`. The official darwin/arm64 archive digest is `d7737360df06c05a547072755e3f3fe0e4d51a1bf4e4a4890d6b105ffc38a976`; its extracted executable digest is `355ca19f1573d2b4cf5cfe614ca9b760f6b33628f70d4ceaa1c6a86f1726a565`. Version output confirms `0.8.1`, commit `b1ea927de`, `darwin/arm64`, build time `2026-11-06T10:12:35Z`.

Baseline evidence uses official `0.7.1` archive digest `a1f78965984fa0eacff331d67360da2cfc8298e9e97d5f136000b3e8682b1c9b` and executable digest `f167df5161555d8696a996be8fedfde8ab1cbad27c419c9a7905b23492ad9350`. Collector runs against both official binaries and pinned source close the target inventory at 225 CLI nodes and the supported response review at 196/196 with `response_review_complete=true`. Evidence remains ignored under `.devlocal/upstream-contract/v0.7.1..v0.8.1/`; it is not a production input.

### Release lineage

| Release | Release id | Pinned commit | darwin/arm64 archive SHA-256 | Reviewed significance |
|---|---:|---|---|---|
| `0.7.2` | `428864784` | `f05a525ac8e82f5e9169ad078e44f166fad6d5c8` | `d1a7286f44423e2e469ff10c8cbffeb952a41507990824bfb6d1b777b45f23e9` | Run-targeted retry groundwork, `--fresh`, property selection cap, project-resource delete fix |
| `0.8.0` | `432551995` | `9b1ab4f9eed9153a94719596eb8a728d2770f065` | `cb649675ba1cb1e92f1d31c1595ecac4b05135871098ae26f1aad5f2ea08aaad` | Workflow/view CLI, workflow-aware statuses, roots-only resolution data, runtime concurrency, attachment path fix |
| `0.8.1` | `436353568` | `b1ea927def6490c43bedff537b6f4ed9a47fa828` | `d7737360df06c05a547072755e3f3fe0e4d51a1bf4e4a4890d6b105ffc38a976` | Skill history, updated-time filters, image dimensions, workspace pinning, project creator fields |

### Closed CLI manifest

The complete target accounting is `193 retained + 15 changed + 17 added = 225`; the one removed baseline row is tracked separately. The 193 retained rows are the baseline command paths whose usage, arguments, flags, visibility, and SDK disposition are byte-for-byte unchanged in the reconciled manifest. The non-retained rows below are the complete delta; no other command has a pending verdict.

| Path | Delta | SDK disposition |
|---|---|---|
| `issue rerun-task` | added | Adapt as the proposed replacement for approved `issues.rerun` only after human approval |
| `project workflow`, `project workflow get`, `project workflow set` | added | Deferred; new public command group outside the approved SDK contract |
| `runtime concurrency` | added | Deferred as a management operation; retained runtime model/update fields still adapt |
| `view`, `view get`, `view issues`, `view list` | added | Deferred; new public command group |
| `workflow`, `workflow create`, `workflow delete`, `workflow get`, `workflow handoff`, `workflow handoff set`, `workflow list`, `workflow update` | added | Deferred; new public command group |
| `issue rerun` | removed from public help, hidden/deprecated in target | Remove false public SDK mapping only as part of the approved breaking migration |
| root `multica` | changed children | Record `view` and `workflow`; no SDK root operation |
| `daemon start`, `daemon restart` | changed flags | Watchdog options are process-control and deferred |
| `daemon stop` | changed flags | `--force` is process-control and deferred |
| `issue` | changed children | Record retry replacement; no SDK group operation |
| `issue comment add` | changed flags | Literal attachments retained; steering deferred |
| `issue create` | changed flags | Literal attachments retained; interactive assignee-picker is non-surface |
| `issue list` | changed flags | Adapt paired updated-time range |
| `issue update` | changed flags | Adapt literal repeatable attachments |
| `login` | changed callback-host help/validation | Existing auth behavior retained; no new SDK argument |
| `project` | changed children | Project-workflow deferred |
| `runtime` | changed children | Concurrency command deferred; response/update fields adapt |
| `setup`, `setup cloud`, `setup self-host` | changed callback-host help/validation | Local setup/process behavior remains outside resource API |

The added grouping above contains exactly 17 command nodes: 3 project-workflow nodes, 1 runtime-concurrency node, 4 view nodes, 8 workflow nodes, and 1 rerun-task node. Changed grouping contains exactly 15 nodes. `issue wakeup checkin` remains public although literal extraction misses its loop-created Cobra node; reconciled evidence adds only this confirmed row. Hidden `probe-runtimes`, hidden/deprecated `issue rerun`, and the root constructor are not public additions.

### Closed supported-response manifest

The 173 unchanged entrypoints retain their existing contract rows and source-reviewed conclusions. The following table is the complete set of 23 changed entrypoints; no other supported response changes.

| Entrypoints | Count | Reviewed change | Action |
|---|---:|---|---|
| `agents.tasks` | 1 | Optional integer `credits_micros`; foreign private-chat content redaction | Adapt retained task-run model and fixtures |
| `attachments.upload`, `attachments.upload_bytes` | 2 | Optional integer image `width`/`height` | Adapt retained attachment result |
| `issues.comments.add` | 1 | Base comment unchanged; steering adds dispatch outcomes and conflicts with attachments | Retain non-steering path; defer steering and guard against accidental exposure |
| `issues.comments.list` direct/flat/thread/recent | 4 | Roots-only rows add optional resolution projection; other projections omit it | Adapt projection-aware decoding and fixtures |
| `issues.rerun` | 1 | Hidden issue-targeted action replaced by run-targeted task-returning command | Breaking adapt/remove decision at human gate |
| `issues.runs` | 1 | Optional integer `credits_micros`; private-chat redaction | Adapt retained task-run model and fixtures |
| `projects.create/get/list/refresh/set_status/update/update_bound` | 7 | Nullable `creator_type` and `creator_id` | Adapt retained project model and fixtures |
| `runtimes.list/rename/update` | 3 | Nullable `max_concurrent_tasks`; absent/int/null update semantics | Adapt retained runtime models, input, and validation |
| `users.profile_get/profile_update` | 2 | Always-present nullable target `whats_new_seen_version`, older omission tolerated | Adapt retained profile model and fixtures |
| `workspaces.list` | 1 | Optional RFC3339 `pinned_at`, pinned memberships first | Adapt list-only projection and order fixtures |

## Goals / Non-Goals

**Goals:**

- Define one exact `0.7.1` to `0.8.1` contract refresh with closed command and response accounting.
- Adapt only already-supported public operations and models, plus the explicitly proposed run-targeted retry replacement.
- Preserve omission/null/open-enum semantics, endpoint-specific projections, deterministic generation, existing architecture, and lower compatibility lineage.
- Supply complete positive/negative verification, migration documentation, exact-revision publication, and independent evidence contracts.

**Non-Goals:**

- Implementing or testing this change during planning.
- Automatically exposing workflow, project-workflow, view, runtime-concurrency management, comment steering, skill-history, daemon process-control, interactive, hidden, UI, infrastructure, or server-only behavior.
- Adding a second contract, generator, version-specific facade, compatibility registry, test runner, dependency, or evidence repository.
- Committing binaries, upstream source, collector output, audit files, diagnostic JSON, screenshots, or local stand details.

## Decisions

### 1. Advance one approved contract through the complete stable lineage

Implementation updates the existing approved contract to target `0.8.1`, records all intermediate stable releases, retains the reviewed minimum, and sets `0.8.2` as the exclusive ceiling. Existing validate/render/check tooling remains the only generation path.

Alternative considered: implement `0.7.2` first or stack on unpublished work. Rejected because the effective published base is exact `origin/main`; splitting would duplicate reconciliation and make the migration baseline depend on an unmerged artifact.

### 2. Propose one truthful breaking retry migration

The package proposes replacing `issues.rerun(issue) -> None` with `issues.rerun_task(run_id, *, issue=None, fresh=False) -> TaskRun`. The old hidden target command is not a supported compatibility mechanism and SHALL NOT be called or emulated. Human approval of this exact break is a prerequisite for implementation.

Alternative considered: keep the old method name and reinterpret its argument as a run id. Rejected because it would silently change identity semantics and return type. A compatibility wrapper is also rejected because an issue id cannot truthfully select the target run.

### 3. Adapt retained fields at their existing model boundaries

Task credits, image dimensions, project creator identity, runtime concurrency, user-profile version state, workspace pinning, and comment resolution fields extend existing frozen models and wire decoders. Optional/nullable fields tolerate baseline omission; list-only and roots-only fields remain projection-specific.

Alternative considered: create target-version response classes. Rejected because the wire changes are additive and the current open/optional model pattern already preserves old servers and future values.

### 4. Preserve distinct input presence and validation semantics

Updated-time bounds are validated as one half-open RFC3339 interval. Runtime concurrency uses the existing unset sentinel so omission, integer, and explicit null remain distinct. Attachment sequences emit one flag per literal path, including commas. Table-driven cases cover transport-not-called negatives.

Alternative considered: pass through CLI validation or normalize comma-separated strings. Rejected because SDK validation is already part of the public contract and comma splitting would corrupt valid paths.

### 5. Fail closed on newly discovered public groups

New workflow, view, project-workflow, runtime-concurrency management, and comment-steering APIs remain deferred. They are recorded in provenance and coverage decisions but do not create contract operations, exports, models, or generated rows.

Alternative considered: mirror every new CLI node for parity. Rejected because discovery is evidence, not approval, and the new response families are outside the reviewed 196-entrypoint SDK contract.

### 6. Ponytail full gate

No new subsystem is necessary. Each need is covered by the existing approved contract, generator, resource methods, unset sentinel, frozen/open models, shared decoders, table-case types, and repository gates. Another generator, compatibility layer, response hierarchy, workflow/view resource tree, steering result abstraction, E2E runner, dependency, or test framework is removed from the design.

### 7. Verification stays at the lowest sufficient boundary

`e2e_required=false`. The change affects SDK argv, validation, deterministic contract projection, and JSON decoding; existing unit, contract, fake-CLI component, packaging, and CI checks can prove every scenario without a live backend. The independent Tester verifies exact-revision behavior from a fresh checkout and publishes evidence in Multica.

Alternative considered: use the isolated `multica-py` stand for every response. Rejected because live mutable state would add cost and weaker determinism without closing a gap left by the planned contract and component fixtures. If implementation unexpectedly changes visible output or reveals a real cross-component gap, planning must be revised before live execution.

## Risks / Trade-offs

- **Breaking retry approval may be rejected** -> Implementation remains blocked; a revised OpenSpec must choose and specify a different truthful public contract before any code change.
- **Wide upstream range can hide a retained behavior change** -> The closed 225-node and 196-entrypoint audits, source links, and `response_review_complete=true` are mandatory gates.
- **Projection-specific fields can leak into broader models** -> Roots-only resolution and workspace-list pinning get endpoint-specific old/new/omitted fixtures.
- **Null and omission can collapse** -> Runtime updates use the existing unset sentinel and complete absent/null/int negative tables.
- **Deferred commands can enter through generation** -> Contract diff and public-surface completeness tests reject any operation not explicitly approved.
- **Local automated suites can exceed ten minutes** -> Run the full suite unsplit in GitHub Actions on the published exact SHA; preserve focused local evidence.

## Migration Plan

1. After human approval, update exact release/source/binary provenance, compatibility interval, all command dispositions, response verdicts, and source/test references in `contracts/sdk-contract.json`.
2. Replace the approved retry operation with the run-targeted signature and task response; update migration/API documentation before removing the legacy public method.
3. Render through existing tooling and prove deterministic bytes and contract/source-link consistency.
4. Adapt existing inputs, models, decoders, and relations only where specified; extend table-driven unit/contract/component fixtures for all positive and negative scenarios.
5. Update compatibility, migration, API, coverage, changelog, packaging, and release documentation.
6. Run focused gates locally and long automated suites unsplit in GitHub Actions on the exact published revision; obtain independent Tester evidence in Multica.
7. Roll back by reverting the implementation commit set and restoring the prior `0.7.1` approved contract and generated projection. No database or persistent-data migration is introduced.

## Open Questions

The human gate must approve or reject the specified breaking `issues.rerun` replacement. There are no implementation alternatives or TODOs delegated to the Implementer: approval authorizes the exact run-targeted contract above; rejection requires a new planning revision and continues to block implementation.
