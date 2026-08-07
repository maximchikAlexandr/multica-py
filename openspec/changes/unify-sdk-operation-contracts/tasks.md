## 1. Approved operation convention contract

- [x] 1.1 Extend `contracts/schema/upstream-contract-v2.schema.json` and the typed loader in `tools/upstream_contract/contract.py` so every public entry point requires `category`, `response_id`, `typed_input_id`, `input_mode`, `presence_policy_ids`, and `command_symbol`; reject unknown category/input-mode values and incomplete records.
- [x] 1.2 Add response catalog entries for `Page[T]` and compatible page subtypes for canonical CLI/direct-resource collection results, record the relation `.all()` tuple exception, and add `ActionResult[None]`, `ActionResult[str]`, `ActionResult[RepositoryMutationResult]`, and `ActionResult[RuntimeUpdateResult]`, keeping public types closed and free of `Any`.
- [x] 1.3 Promote the currently manual canonical methods into approved operation entries with source/test references, then populate one public-convention record for each of the 124 methods currently returned by `discover_public_methods()`; assert a bijection rather than preserving 124 as a permanent magic number.
- [x] 1.4 Trace every approved `ProjectUpdateRequest`, `AgentUpdateRequest`, `SkillUpdateRequest`, and `IssueUpdateRequest` field through the pinned v0.4.20 upstream `RunE`/helper path and record the exact omitted/null/empty/zero/false mapping plus source lines; include composite unassign/clear steps where a single update flag is not the approved representation.
- [x] 1.5 Trace every approved autopilot, trigger, label, project-resource, runtime, and user-profile update field through the pinned upstream path; approve the documented issue-parent, autopilot-project, and profile clear mechanisms only after source confirmation, and fail contract validation for any nullable field without a distinct clear representation.
- [x] 1.6 Add/normalize presence policies for `omit`, `nullable_clear`, `required_nonnull`, `empty_present`, `empty_collection_clear`, `false_present`, and `zero_present`; ensure ordered binding mappings reference these policies field-for-field.
- [x] 1.7 Update contract rendering/check commands and generated operation-case materialization to consume the new convention fields without allowing evidence or heuristics to change public behavior.
- [x] 1.8 Add schema/loader mutation cases proving missing conventions, duplicate categories, unknown types, response/category mismatches, incomplete presence vectors, missing clear evidence, and a non-bijective canonical surface fail closed.
- [x] 1.9 Run the focused contract/schema tests and `uv run python scripts/upstream_contract.py validate --approved contracts/sdk-contract.json --source-checkout <pinned-v0.4.20-source>`; record a green validation before runtime surface edits.

## 2. Common page and action result models

- [x] 2.1 Replace the duplicate common and issue-activity page cores with one frozen generic `multica_py.models.common.Page[T]` carrying `items`, `limit`, `offset`, `total`, `has_more`, and the existing closed cursor union.
- [x] 2.2 Implement typed `__iter__`, `__len__`, and integer/slice `__getitem__` on `Page[T]`, with no hidden I/O and no mutable collection exposure.
- [x] 2.3 Convert `IssueListPage`, `AutopilotListPage[T]`, `AutopilotRunListPage[T]`, `MetadataPage`, and `IssueChildrenResult` into compatible page shapes; retain warning-free read-only `issues`, `autopilots`, `runs`, and `children` aliases that return the identical `items` tuple.
- [x] 2.4 Generalize the existing frozen `ActionResult` to `ActionResult[T]` with typed `value`, `success`, and optional non-secret `message`, while keeping CLI/validation/decode failures exceptional.
- [x] 2.5 Export `Page`, `ActionResult`, all retained page names, and the new update request models through `multica_py.models` and `multica_py.__init__`; update `__all__` and public-surface contract tables without exporting internal helpers.
- [x] 2.6 Add focused unit and contract tests for canonical/direct-resource page immutability, tuple identity, iteration, length, integer/slice indexing, neutral unpaged metadata, offset/cursor metadata, compatibility aliases, relation `.all()` tuple snapshots, generic action values, encoding/decoding where supported, and no public `Any`.
- [x] 2.7 Run the focused model/public-surface tests plus `uv run mypy src` and `uv run mypy tests`; resolve any `msgspec.Struct` inheritance limitation with concrete compatible frozen structs as allowed by the design, not by weakening the public contract.

## 3. Typed-input and overload completion

- [x] 3.1 Extend `_resolve_request` in `resources/_base.py` with an explicit `allow_empty` mode: required calls retain the exact mixed/neither error contract, while optional filters and all-optional updates construct their default typed model.
- [x] 3.2 Change the existing all-optional update models `ProjectUpdateRequest`, `AgentUpdateRequest`, `SkillUpdateRequest`, `IssueUpdateRequest`, and `UserProfileUpdate` to the exact `Unset`/nullable field matrix in `design.md`; preserve/verify the existing all-optional `AutopilotTriggerUpdate`, and treat the new `AutopilotUpdateRequest` and `LabelUpdateRequest` from 3.3 as the remaining members of the same complete all-optional set. Add validation that rejects `None` for non-nullable fields before I/O, and do not apply this no-op model contract to required-value updates.
- [x] 3.3 Add frozen `AutopilotUpdateRequest` and `LabelUpdateRequest` models with the specified `Unset` defaults, nullable fields, subscriber-empty clear behavior, and existing field validation; do not add unapproved upstream fields.
- [x] 3.4 Add dual typed-object/direct-keyword overloads to `issues.list_command/list`, using `allow_empty=True` so no-input and `IssueListFilter()` calls build identical unfiltered plans.
- [x] 3.5 Add dual overloads to `issues.comments.list_flat`, `list_thread`, and `list_recent` and their command siblings; keep every direct request field keyword-only and preserve cursor/since/limit validation and argv.
- [x] 3.6 Add dual overloads to `issues.metadata.query` and `set_typed` and their command siblings; preserve predicate order, JSON scalar typing, cursor rules, and the existing direct `set(issue_id, key, value)` sibling.
- [x] 3.7 Add dual overloads to top-level and bound autopilot `trigger_add`/`trigger_update` eager and command methods, routing both forms through the same request validation and bound cache invalidation.
- [x] 3.8 Convert `autopilots.update` and `labels.update` plus command siblings to dual-input methods over `AutopilotUpdateRequest` and `LabelUpdateRequest`; retain stable target identifiers as positional arguments and make request fields keyword-only.
- [x] 3.9 Add one frozen typed-input case table that discovers every governed request/filter annotation across resource and bound methods and asserts exact request-field names, types, defaults, eager/command overload parity, and no unlisted object-only exception.
- [x] 3.10 Add table rows for object/direct command parity, mixed input, missing required input, optional empty input, unknown keyword, and request `__post_init__` failures; assert exact preview/argv/mode/stdin/timeout/result equality and zero transport calls on every invalid case.
- [x] 3.11 Run `uv run pytest -m "not live" tests/unit/resources -k 'request or direct or operation'`, `uv run mypy src`, and `uv run mypy tests` before presence-aware command changes.

## 4. Presence-aware update command plans

- [x] 4.1 Update `ProjectResource.update_command`, `AgentResource.update_command`, and `SkillResource.update_command` to branch on `Unset` rather than `None`, emit approved nullable-clear mappings, preserve explicit accepted empty values, and delegate all-`Unset` calls to the matching `get_command`.
- [x] 4.2 Update `IssueResource.update_command` to apply the approved per-field clear mappings for description, assignee, project, and parent; build an ordered composite plan when clearing requires a separate upstream action, finish with the authoritative issue entity, and delegate all-`Unset` calls to `get_command`.
- [x] 4.3 Update `AutopilotResource.update_command` to consume `AutopilotUpdateRequest`, distinguish omitted subscribers from `subscribers=()`, remove the canonical need for the resource-specific `clear_subscribers` input, preserve any documented compatibility overload only if it maps unambiguously, and delegate all-`Unset` calls to `get_command`.
- [x] 4.4 Update `LabelResource.update_command` and `UserResource.profile_update_command` to use the approved presence mappings and no-op reads; `description=None` on the user profile must use the approved clear behavior rather than omission.
- [x] 4.5 Update top-level and bound autopilot trigger-update no-op behavior to inspect `autopilot get` and return the matching typed trigger without mutation; raise the existing typed not-found/output error if the requested trigger is absent.
- [x] 4.6 Confirm `ProjectResourceCollection.update_local_directory` (`ProjectResourceUpdateLocalDirectoryRequest.local_path`) and `RuntimeResource.update` (`RuntimeUpdate.target_version`; `wait` remains an optional control field) preserve required-value semantics: omission or `None` is rejected before I/O, no all-omitted no-op is constructed, and required-value failures are covered separately from all-optional updates.
- [x] 4.7 Add one frozen all-optional update-field presence table covering every applicable omitted, `None`, `""`, `()`, `False`, and `0` vector, plus a required-value boundary table for project-resource/runtime missing/null cases; assert exact preview and transport argv, result type, validation error, and multi-step ordering from approved contract data.
- [x] 4.8 Add focused no-op tests only for the all-optional `ProjectUpdateRequest`, `AgentUpdateRequest`, `SkillUpdateRequest`, `IssueUpdateRequest`, `AutopilotUpdateRequest`, `LabelUpdateRequest`, `AutopilotTriggerUpdate`, and `UserProfileUpdate` surfaces, asserting the read command preview, one read execution, zero mutation execution, and current-entity return; explicitly exclude project-resource and runtime updates, whose omission/null failures are covered by 4.6.
- [x] 4.9 Run the focused update/resource/command-preview tests plus `uv run mypy src` and `uv run mypy tests`; do not proceed while any nullable clear lacks approved source evidence.

## 5. Page-return migration

- [ ] 5.1 Update canonical issue-list, autopilot-list/history, comment flat/thread/recent, metadata-query, and issue-children decoders/finalizers to populate the common page fields and compatibility aliases without losing upstream offset, cursor, total, count, or stage metadata.
- [ ] 5.2 Convert the top-level unpaged direct-resource list commands in agents, labels, projects, repositories, runtimes, skills, squads, and workspaces from `tuple[T, ...]` to neutral `Page[T]`; preserve order and bound-entity wrapping, and do not convert relation `.all()` snapshots.
- [ ] 5.3 Convert nested unpaged direct-resource list commands for agent skills/tasks, issue comments/labels/subscribers/pull requests/runs/run messages/search, project resources, runtime usage/activity, skill files, squad members, workspace members, and daemon disk usage to `Page[T]` with exact element types; relation snapshots remain tuple results.
- [ ] 5.4 Convert issue-label add/remove refreshed collection results to the compatible label page contract, keeping the mutation command and cache invalidation behavior unchanged.
- [ ] 5.5 Update every bound relation loader/finalizer that consumes a migrated direct-resource result to read `.items`, while keeping `LazyCollection.all()`, `OffsetLazyCollection.all()`, `CursorLazyCollection.all()`, and their public cached relation snapshots unchanged as tuples and excluded from the page gate.
- [ ] 5.6 Update eager and `*_command()` annotations together for every migrated canonical CLI/direct-resource collection operation; verify `Command[Page[T]]` matches the eager `Page[T]` or exact compatible subtype, while relation `.all()` annotations remain tuple snapshots.
- [ ] 5.7 Expand `OperationCase` result assertions for canonical/direct-resource unpaged, offset, cursor, aggregate, empty, legacy-envelope, and bound-page results; include iteration, length, indexing, metadata, and compatibility-alias identity checks, plus explicit relation `.all()` tuple assertions.
- [ ] 5.8 Update component fake-CLI and live-smoke assertions for canonical/direct-resource collection results to use `.items`/iteration and preserve exact subprocess routing; assert relation `.all()` tuple snapshots separately, and keep all live modules triple-marked and offline-excluded.
- [ ] 5.9 Run all unit/contract/component tests touching collection methods and relations, followed by `uv run pytest -m "not live" --collect-only` to confirm no live node is collected.

## 6. Action-result migration

- [ ] 6.1 Add private base-resource plan adapters for successful void and payload actions that wrap exactly once in `ActionResult[T]`, preserve redacted public messages only, and leave transport/decode exceptions unchanged.
- [ ] 6.2 Convert the 26 canonical void actions listed in `design.md` to `ActionResult[None]` in both eager and command annotations/finalizers; update bound and nested delegators to reuse the same wrapper rather than nesting it.
- [ ] 6.3 Convert `issues.deprioritize` and token-based `auth.login` to `ActionResult[str]`; retain `auth.login(token=None) -> ManagedProcess` with precise eager/command overloads and spawn execution.
- [ ] 6.4 Convert `repositories.add/remove` to `ActionResult[RepositoryMutationResult]` and `runtimes.update` to `ActionResult[RuntimeUpdateResult]`, preserving every decoded payload field under `.value`.
- [ ] 6.5 Keep entity, state-snapshot, comment, metadata-entry, attachment, page, scalar read, mapping, and process operations on their natural categories; add negative assertions preventing opportunistic `ActionResult` use outside the approved matrix.
- [ ] 6.6 Update cache invalidation maps on bound actions so invalidation runs only after a successful wrapped action and the original `ActionResult` is returned unchanged.
- [ ] 6.7 Add table-driven cases for each action payload family, representative void actions from every resource, token/interactive login overloads, transport failures, decode failures, and bound invalidation; assert no CLI-executing public method retains a bare `None` return annotation.
- [ ] 6.8 Run focused action/auth/repository/runtime/bound-resource tests plus `uv run mypy src` and `uv run mypy tests`.

## 7. Canonical surface and routing gates

- [ ] 7.1 Extend `OperationCase` with expected category and public response ID, populate them from the approved contract for every canonical row, and retain unique case IDs and one canonical row per discovered method.
- [ ] 7.2 Strengthen `test_discovered_public_methods` to assert discovered-method/convention-record bijection, eager/command parameter parity, `Command[T]` result parity, typed-input mode, presence policy completeness, and category/response annotation compatibility.
- [ ] 7.3 Add a closed rule that every canonical CLI/direct-resource collection tuple response has migrated to a page, while relation `.all()` tuple snapshots remain explicitly exempt; every former void action has migrated to `ActionResult[None]`, and scalar/mapping/process exceptions exactly match the approved matrix.
- [ ] 7.4 Update generated and manual canonical result assertions, legacy payload migration fingerprints where public results intentionally changed, and component routing cases without duplicating argv expectations.
- [ ] 7.5 Update public-export, bound-surface, baseline-spec, SDK-contract, packaging, and generated-runtime tests for the new generic models and annotations; preserve clean import without a CLI.
- [ ] 7.6 Re-run command-preview focused cases for no-I/O construction, redaction, snapshot configuration, multi-step clears, no-op reads, runtime references, composite failure stop, and all transport modes to prove the existing plan remains the single execution path.

## 8. Documentation and migration

- [ ] 8.1 Add one SDK-wide operation conventions section to `docs/api.md` covering direct keywords vs typed objects, mixed-input rejection, optional filters, all-optional versus required-value update semantics, `Unset`/`None`/falsey behavior, result categories, `.items` pages for canonical/direct-resource collections, tuple relation snapshots, and eager/command equivalence.
- [ ] 8.2 Update resource examples in `docs/api.md`, `docs/service-usage.md`, README, and examples to show direct keywords first, a reusable typed-object alternative, page iteration/`.items`, and `ActionResult.value`; remove the old request-object-only exception list.
- [ ] 8.3 Add a precise breaking-change matrix to `docs/migration.md` mapping every former canonical/direct-resource tuple/page alias and every former `None`/payload action return to its new access pattern; state that relation `.all()` tuple snapshots remain unchanged, and that resource-named page aliases remain warning-free for at least one minor and removable only in a future major change.
- [ ] 8.4 Add the breaking page/action and explicit-`None` semantics to `CHANGELOG.md`, including before/after snippets for projects update, issues list, projects list, delete actions, repository mutations, and command execution.
- [ ] 8.5 Extend documentation contract tests so public examples and named symbols are pinned to actual signatures, and fail if docs reintroduce resource-specific request, page, action, or command conventions.

## 9. Final verification and release readiness

- [ ] 9.1 Run `uv run pytest -m "not live"` end to end and confirm all offline layers pass with no network/backend dependency.
- [ ] 9.2 Run `uv run pytest -m "not live" --collect-only` and confirm no `tests/live/*` node is collected and all expected unit/contract/component/packaging nodes are present.
- [ ] 9.3 Run `uv run mypy src`, `uv run mypy tests`, `uv run ruff check`, and `uv run ruff format --check`; fix every error without `Any` leaks or broad ignores.
- [ ] 9.4 Run `uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json`, contract schema validation, generated-runtime freshness checks, and source-link audit; confirm only approved contract data drives public behavior.
- [ ] 9.5 Run `openspec validate unify-sdk-operation-contracts` and `openspec validate --specs`; reconcile any overlap with the already-merged `cli-command-preview` requirements without weakening either contract.
- [ ] 9.6 Build wheel and sdist, run packaging tests against both artifacts, and verify `Page`, `ActionResult`, retained page types, request models, and `py.typed` are present and importable before a CLI invocation.
- [ ] 9.7 Run the separately gated live smoke suite only with configured Multica credentials/runtime, record its result without weakening offline gates, and complete the release/migration checklist for this breaking public-contract change.
