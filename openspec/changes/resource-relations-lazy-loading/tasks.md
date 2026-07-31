## 1. Phase 0 — pinned contract correctness

- [ ] 1.1 Revalidate only closed drift IDs D01–D19 from `design.md` against current `main`, pinned Multica CLI `0.4.9` source commit `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`, verified binary help, and real response fixtures; any newly discovered drift requires a spec amendment or follow-up change.
- [ ] 1.2 Trace and govern issue list, children, pull-requests, metadata, runs, run-messages, rerun, and cancel-task inputs through upstream `RunE`/helpers; approve exact argv, addressing, envelopes, pagination, presence, and response adapters.
- [ ] 1.3 Trace and govern `agent skills` list/set, agent tasks/avatar, `skill files` operations, squad members, workspace members, and project resources; correct singular/plural groups and avatar flags with positive/negative vectors.
- [ ] 1.4 Trace and govern autopilot get/list/runs/manual trigger and trigger add/update/delete; model get aggregate envelope and remove/replace unsupported get-run and legacy nested trigger surfaces.
- [ ] 1.5 Trace attachment, user, repository, and runtime operations; replace incorrect upload/download/repository semantics and remove unsupported attachment-list, arbitrary user list/get, repository get, and runtime get surfaces with migration decisions.
- [ ] 1.6 Use wire-only `msgspec.UNSET` for the closed seed catalog: `autopilots.get.triggers` and `autopilots.get.autopilot.subscribers`; no other embedded field seeds a relation in this change.
- [ ] 1.7 Ensure every operation behind all 33 relations has source refs, mappings/destinations, five-state presence, exact response shape, strategy, public type, decoder, compatibility classification, validators, and canonical vectors in `contracts/sdk-contract.json`.
- [ ] 1.8 Render `src/multica_py/_generated/approved_sdk.py` only through `scripts/upstream_contract.py render`; run validate/check twice and prove deterministic bytes with no transient evidence in tracked paths.
- [ ] 1.9 Update table-driven canonical/manual/legacy operation cases for all additions, removals, and intentional changes; recompute exact method/case/fingerprint counters and preserve the no-allowlist completeness assertion.
- [ ] 1.10 Before relation implementation, annotate every normative inventory row R01–R33 with its approved contract source and stable behavior case ID `relation:RNN`; each later relation task follows Red (failing public case) → Green (minimal loader/wrapper) → Refactor → focused gates before the next row.

## 2. Phase 1 — shared semaphore and bound foundation

- [ ] 2.1 Add private `ProcessSemaphore` injection to `MulticaClient`; keep config, transport, services, and close behavior independent per view with no runtime/identity registry.
- [ ] 2.2 Refactor every `with_*()` derivation to pass the existing semaphore while preserving exact server/profile/workspace/cwd/environment/timeout settings.
- [ ] 2.3 Preserve existing independent close, timeout, cancellation, descendant cleanup, shell-free invocation, and redaction; add no family lifecycle or `ClientClosedError`.
- [ ] 2.4 Add the closed `*Data` catalog, externally read-only `ResourceEntity[TData]`, `to_data()`, `from_data()`, and `DetachedEntityError`; every response creates a new wrapper.
- [ ] 2.5 Add `BaseResource` adapt/bind-one/bind-many/bind-page helpers; bind the originating client view and keep raw argv/transport outside relation loaders.
- [ ] 2.6 Add regression cases proving list/get return distinct immutable wrappers, no cross-wrapper lazy state exists, and `to_data()` provides structural equality/serialization.
- [ ] 2.7 Implement public `LazyCollection`, `OffsetLazyCollection`, `CursorLazyCollection`, and `LazyMapping` plus private typed loader closures and `_collect_offsets`/`_collect_cursors`; add no descriptor/strategy registry.
- [ ] 2.8 Memoize lazy objects per bound entity/query with one lock/state/value, retryable failures, blocking atomic refresh, detached/context errors, and offset/cursor no-progress guards.
- [ ] 2.9 Implement `Project.resources` and `Project.issues` as the first unpaged/paged vertical slice, including precise project-resource mutation invalidation and exact call-count tests.

## 3. Phase 2 — workspace graph

- [ ] 3.1 Bind `Workspace` and implement unpaged `members`, `agents`, `skills`, `projects`, `labels`, `repositories`, `runtimes`, and `squads` through `with_workspace()` views sharing only the original semaphore.
- [ ] 3.2 Implement offset-paged `Workspace.issues`, preserving all client configuration and pagination metadata/progress guards.
- [ ] 3.3 Implement `Workspace.autopilots` over the governed aggregate/list page and retain total metadata.
- [ ] 3.4 Prove every workspace relation binds children to its derived client view and repeated calls return distinct wrappers.
- [ ] 3.5 Add table-driven exact-argv, zero-I/O property, lazy-state, blocking-refresh, empty/multiple result, derived-view, and shared-semaphore coverage for all ten workspace relations.

## 4. Phase 3 — agent skill squad and member graph

- [ ] 4.1 Migrate embedded `Agent.skills` snapshot data to the documented seed field and implement bound unpaged `Agent.skills` through governed plural commands with set-mutation invalidation.
- [ ] 4.2 Implement unpaged `Agent.tasks` and offset-paged `Agent.issues` using `--assignee-id <agent-id>`.
- [ ] 4.3 Implement bound `Skill.files` through governed plural commands and invalidate its cache after successful file mutations.
- [ ] 4.4 Implement bound `Squad.members` and invalidate after successful add/remove; implement offset-paged `Squad.issues` by assignee.
- [ ] 4.5 Bind `WorkspaceMember` and implement offset-paged `WorkspaceMember.issues` by assignee.
- [ ] 4.6 Add table-driven exact-argv/shape/call-count/cache/refresh/invalidation/pagination/error cases for all seven relations and reject legacy singular agent-skill/skill-file argv.

## 5. Phase 4 — issue comment and run graph

- [ ] 5.1 Migrate eager issue fields: `labels` to `label_names` snapshot plus bound relation, children stage data to `child_stages` plus full-child relation, and metadata snapshot to `LazyMapping` public semantics.
- [ ] 5.2 Implement default flat `Issue.comments` and parameterized `recent_comment_threads` query view with full cursor-pair behavior and precise successful comment mutation invalidation.
- [ ] 5.3 Bind `CommentThread` with inherited issue context and implement cursor-paged `CommentThread.comments`, including cursor no-progress detection.
- [ ] 5.4 Implement unpaged `Issue.labels` and `Issue.subscribers` with precise add/remove mutation invalidation and presence-aware complete-cache seeding.
- [ ] 5.5 Implement mapping `Issue.metadata` from the governed JSON object with set/delete invalidation and typed key/value behavior.
- [ ] 5.6 Implement aggregate `Issue.pull_requests` wrapper adaptation and `Issue.children` flattening while retaining totals, stages, done counts, and unstaged grouping.
- [ ] 5.7 Implement unpaged `Issue.runs`, bind `TaskRun` with issue context, and implement `TaskRun.messages` using task-run ID plus inherited issue ID where required.
- [ ] 5.8 Add adversarial presence fixtures across list/get/children/runs, proving missing versus explicit empty, complete-only seeding, and immutable replacement.
- [ ] 5.9 Add table-driven exact-argv/shape/call-count/cache/refresh/invalidation/cursor/mapping/aggregate/error coverage for all ten issue/comment/run relations and reject legacy decoder/addressing forms.

## 6. Phase 5 — autopilot graph and ergonomics

- [ ] 6.1 Correct autopilot get adaptation, bind `Autopilot`, and seed complete trigger/subscriber aggregate relations without a second read subprocess.
- [ ] 6.2 Implement offset-paged `Autopilot.runs` over governed `autopilot runs <id>` with total metadata and progress guards.
- [ ] 6.3 Implement `Autopilot.triggers` read plus trigger-add/update/delete invalidation; expose `Autopilot.subscribers` as a read-only seeded relation.
- [ ] 6.4 Bind `AutopilotRun` and implement `messages` through the governed task-run message operation only when `task_id` exists; raise typed context error otherwise.
- [ ] 6.5 Remove/replace legacy `run`, `get_run`, and nested trigger methods according to approved migration decisions and update canonical discovery.
- [ ] 6.6 Implement `MulticaClient.prefetch(entities, selector, *, max_parallel=4) -> None` with ThreadPoolExecutor, selected-lazy-object deduplication, loaded-skip, `max_parallel` validation, deterministic first-exception propagation, pending-future cancellation, and common semaphore.
- [ ] 6.7 Add table-driven aggregate-seeding, offset-page, mutation-invalidation, absent-task, cache/refresh, exact-call-count, and bounded-prefetch coverage for all four autopilot relations.

## 7. Unsupported relations and public migration

- [ ] 7.1 Assert that no hidden collection exists for project/agent/squad autopilots, label issues, skill agents, runtime agents, repository projects, issue attachments, or workspace users because pinned CLI lacks a safe server-side list/filter.
- [ ] 7.2 Keep issue/autopilot/run singular parent/project/assignee/creator references outside `ManyRelation` and document them as a later `LazyRef` capability.
- [ ] 7.3 Export only bound entities, immutable snapshots, lazy/page/cursor/query types, and typed relation errors without public `Any` or CLI import-time requirements; keep client references, semaphore injection, operation IDs, loaders, and paging helpers private.
- [ ] 7.4 Publish a complete alpha migration table for bound entities, `to_data()`, conflicting eager names, plural command corrections, issue addressing/decoders, and every removed/replaced unsupported legacy method.
- [ ] 7.5 Update public examples for all graph phases, explicit load points, page/all/blocking-refresh, immutable replacement/presence behavior, local invalidation, prefetch, and independent client views.

## 8. Complete verification and acceptance

- [ ] 8.1 Verify that the R01–R33 contract references and `relation:RNN` behavior cases established in task 1.10 remain one-to-one with public discovery; do not create a duplicate trace matrix.
- [ ] 8.2 Run focused unit/component/contract tests for every relation and all 19 drift dispositions; assert complete argv, exact transport method/stdin/timeout, response shape, and exact subprocess count.
- [ ] 8.3 Run concurrency/lazy-state/replacement/presence/pagination/prefetch adversarial tests, including serialized first load, failed retry, blocking failed refresh, distinct wrappers, missing/empty fields, and offset/cursor no-progress.
- [ ] 8.4 Run `uv run pytest -m "not live"` and collect-only; keep offline green and confirm no `tests/live/*` nodes are collected.
- [ ] 8.5 Run `uv run mypy src`, `uv run mypy tests`, `uv run ruff check`, and `uv run ruff format --check`; add no dependency, `Any` leak, duplicate helper, or unrelated serial marker.
- [ ] 8.6 Run approved-contract validate/render/check, deterministic second render, package validation, release validation, canonical-method completeness, and legacy-payload bijection with recomputed exact counters.
- [ ] 8.7 Run gated prepared-target live smoke covering representative unpaged, offset, cursor/query, aggregate, mapping, local mutation-invalidation, immutable replacement, and bounded-prefetch flows across workspace/project, agent/skill/squad, issue/comment/run, and autopilot phases.
- [ ] 8.8 Clean only uniquely named test-created live records, record proof IDs separately, and report infrastructure-limited or unsupported flows honestly.
- [ ] 8.9 Run `openspec validate resource-relations-lazy-loading --strict`, inspect the final diff against the full issue #14 matrix, and obtain implementation review before merge.
