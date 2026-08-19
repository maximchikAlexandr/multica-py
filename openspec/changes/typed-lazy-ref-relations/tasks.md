## 1. Lazy reference foundation

- [ ] 1.1 Add `UnloadedReferenceError` and `UnsupportedReferenceTargetError` to the public exception hierarchy with source/reference/discriminator fields and stable pre-I/O messages; extend public-symbol tests for both.
- [ ] 1.2 Change `_GenerationState` initialization to use an explicit sentinel so `None` can be a loaded value, while preserving collection/mapping cache, waiter, retry, refresh-restoration, and invalidation behavior.
- [ ] 1.3 Implement `LazyRef[T]` in `models/relations.py` with `loaded`, raising `value`, `get`, `get_command`, `refresh`, `refresh_command`, and `invalidate`; build cached and live commands only through existing `_internal.commands` transformations.
- [ ] 1.4 Add focused generation-state/LazyRef tests for initial value and initial `None`, cached get, unload error, failed-first-load retry, concurrent success/failure coalescing, atomic successful/failed target refresh, and invalidation racing a generation.
- [ ] 1.5 Verify `refresh()` and `refresh_command().run()` on an explicitly-null loaded absence both return cached `None`, remain loaded, produce a no-step command, and perform zero transport I/O.
- [ ] 1.6 Add typed usage cases proving `LazyRef[T]` and `LazyRef[T | None]` narrow without `Any`, and keep `LazyRef` importable only from the dedicated relations module.

## 2. Presence-preserving source decoding

- [ ] 2.1 Make optional reference-bearing Issue wire fields (`parent_issue_id`, `project_id`, and `assignee`) presence-aware with `msgspec.UNSET`, while preserving current public `Issue.parent_id`, `project_id`, and `assignee` values.
- [ ] 2.2 Make optional reference-bearing Autopilot, AutopilotRun, and TaskRun inputs presence-aware for `project_id`, `issue_id`, and `agent_id`; preserve existing public values and inherited TaskRun issue context.
- [ ] 2.3 Store only immutable wire-presence seeds in private schema/provenance state; make `detach()` copy them while clearing client and freshening mutable relation state, and verify repr, equality, hashing, `to_dict()`, and `to_json()` neither expose them nor perform I/O.
- [ ] 2.4 Add table-driven decoder/entity tests for each optional source shape: omitted produces missing context, explicit null produces loaded absence, and a non-null ID produces an unloaded loadable handle; repeat the classification after detach and assert a loadable detached handle raises `DetachedEntityError`.
- [ ] 2.5 Add serialization/construction tests proving `from_dict(to_dict(entity))` and direct/manual public `None` construction have missing context (never inferred explicit absence), while a manually constructed non-null ID is loadable once bound.

## 3. Exact bound-entity reference inventory

- [ ] 3.1 Add passive `Issue.parent`, `Issue.project`, and `Issue.assignee_ref` handles; preserve `Issue.assignee` as `IssueAssignee | None`, dispatch only `agent`/`squad` through their typed `get_command()` services, and fail member/unknown kinds before I/O.
- [ ] 3.2 Add passive `Autopilot.project` and discriminated `Autopilot.assignee` handles using typed project/agent/squad services and the source wrapper's exact client view.
- [ ] 3.3 Add passive `AutopilotRun.autopilot`, `AutopilotRun.issue`, `TaskRun.issue`, and `TaskRun.agent` handles using only typed autopilot/issue/agent services and inherited source context.
- [ ] 3.4 Ensure every handle is cached in its source wrapper's private runtime state, creates no I/O on property access, returns targets bound to the originating profile/workspace/server/executor/semaphore view, and raises detached/missing/unsupported errors in the specified order.
- [ ] 3.5 Add one table-driven governed-dispatch suite covering all nine members, required/optional annotations, exact command argv, returned target type/binding, scalar/snapshot compatibility, and zero-I/O property access.
- [ ] 3.6 Add negative public-surface tests proving creator/member, trigger, task, squad-leader, comment-author, and workspace-user lazy-reference members are absent and no raw argv, list scan, or invented lookup backs a reference.
- [ ] 3.7 Add table-driven mutation tests for `update(parent_id=...)`, `update(project_id=...)`, `update(assignee_id=...)`, `assign(...)`, and `unassign()`: every success derives a coherent new wrapper and presence/handle state from the returned wire snapshot while every original scalar/snapshot and handle cache remains unchanged; every failure publishes no replacement and changes no original state.

## 4. Duplicate-aware bounded prefetch

- [ ] 4.1 Add the smallest private lazy-load protocol needed by `MulticaClient.prefetch()` so existing collection/mapping behavior is unchanged and `LazyRef` can provide a scope/type/ID key plus controlled result publication.
- [ ] 4.2 Add a private `_BoundEntity` clone-and-rebind path that copies immutable public target data plus immutable private wire-presence/operation provenance, installs the identical originating client view, and allocates fresh relation maps, `_GenerationState` objects, loaders, locks, and cached outcomes.
- [ ] 4.3 Define the private singular scope key from effective normalized CLI executable/server URL, profile, workspace ID, executor identity, and process-semaphore identity; validate every selected entity has one identical complete scope before scheduling any I/O.
- [ ] 4.4 Update `MulticaClient.prefetch()` scheduling to skip loaded references, deduplicate identical handles, coalesce equal singular keys within one call, fan out independent bound target wrappers, retain earliest-input/fail-fast behavior, and use the existing thread pool and shared process semaphore for distinct keys.
- [ ] 4.5 Add focused prefetch tests proving identical complete scopes coalesce, different workspace/profile/server-executable/executor/semaphore scopes fail before I/O, equal IDs across target types do not collide, loaded `None` schedules no job, missing/unsupported references preserve fail-fast behavior, worker/semaphore bounds and retry remain intact, and collection/mapping behavior is unchanged.
- [ ] 4.6 Add nested-reference fan-out tests proving primary and secondary target wrappers preserve identical omitted/null/non-null provenance and origin behavior while their nested loads, invalidations, generation states, and caches remain independent.

## 5. Documentation and example

- [ ] 5.1 Update API and service-usage docs with the dedicated `LazyRef` import, exact inventory, passive properties, explicit load points, optional absence, typed errors, refresh semantics, and bounded duplicate-aware prefetch.
- [ ] 5.2 Update migration documentation to preserve scalar IDs and `Issue.assignee`, introduce `Issue.assignee_ref`, list unsupported singular edges, and explain immutable mutation replacement.
- [ ] 5.3 Add `examples/singular_references.py` demonstrating optional issue parent/project handling, `value` after load/prefetch, refresh, and bounded prefetch with no implicit I/O.
- [ ] 5.4 Extend docs/example contract tests so every documented reference resolves, unsupported names remain absent, and examples use only approved public imports and typed services.

## 6. Verification

- [ ] 6.1 Run focused unit, component, contract, and typecheck tests for relation state, presence decoding, inventory dispatch, immutable mutation, serialization passivity, and prefetch; verify test discovery before execution.
- [ ] 6.2 Run `uv run pytest -m "not live"` and collect-only, confirming no live nodes enter the offline suite.
- [ ] 6.3 Run `uv run mypy src`, `uv run mypy tests`, `uv run ruff check`, and `uv run ruff format --check` with no new dependency, public `Any`, duplicate helper, or unrelated serial marker.
- [ ] 6.4 Run approved-contract check/render determinism, package/release validation, public-symbol/signature and canonical-operation integrity checks, then `openspec validate typed-lazy-ref-relations --strict`.
- [ ] 6.5 Review the final implementation diff against all nine inventory rows and the exclusion list, recording any infrastructure-limited live verification without weakening offline acceptance.
