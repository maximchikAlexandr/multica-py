## 1. Baseline and Gate Setup

- [x] 1.1 Verify the pinned baseline is `e719de13442841c64ed96855c5227bbe5e173f10` by checking that it is the parent and merge-base of planning commit `2ff0fd954851b9125ea3adba39696c00a57e8eab`; verify the implementation worktree starts at that planning commit or a plan-only descendant, rather than requiring `HEAD` to equal the baseline. Resolve the exact pinned upstream source checkout from `contracts/sdk-contract.json` provenance, and record baseline/planning commit IDs plus both absolute paths/revisions in `pilot-evidence.md`.
- [x] 1.2 From an explicit checkout/reference of the pinned baseline, record baseline tracked LOC for production, tests, generator/contract, and the files touched by each planned phase; also record counts of `_PUBLIC_FIELDS`, `_RUNTIME_FIELDS`, `_RUNTIME_INIT_FIELDS`, `_set_runtime`, relation `_plan`/`_Step` accesses, marker-only binding casts, and private invalidation callbacks.
- [x] 1.3 Run and record the baseline gate from the pinned baseline checkout/reference: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`, `uv run mypy tests`, `uv run pytest -m "not live"`, `uv run pytest -m "not live" --collect-only`, approved-contract `validate` with the exact pinned source checkout, approved-contract `check`, and `git diff --check`; verify collection contains no `tests/live/*` node.
- [x] 1.4 Use the pinned baseline from task 1.1 as the comparison reference for every later inventory, fingerprint, LOC, and phase-gate result. Run each phase gate at its current phase tip (a descendant of the planning commit), and never require the current `HEAD` to equal the pinned baseline.

## 2. Phase 0 — Current-ID Regression Guard

- [x] 2.1 Convert the existing active legacy fingerprint/migration pairs once into a literal `dict[current OperationCase.id, sha256]` fixture, exclude the six removed-operation entries, and delete the one-time conversion mechanism so the committed fixture is independent test data.
- [x] 2.2 Replace `test_legacy_payload_bijection` with a current-ID fingerprint test that asserts exact key equality, unique case resolution, and literal hashes over resource, method, args, sorted kwargs, transport method, exact argv, stdin, timeout, and stdout.
- [x] 2.3 Remove `LEGACY_ARGV_MIGRATION` and its reverse lookup from `tests/cases/operations.py`; give every manual case a non-null explicit/family provenance reference without introducing another ID map.
- [x] 2.4 Remove `legacy_argv_migration` from `contracts/sdk-contract.json`, `ContractCatalog`, contract loading/closed-key validation, fixtures, exports, and migration-only contract tests while leaving operation/vector/source/test reference closure intact.
- [x] 2.5 Add a mutation-focused test proving a changed guarded payload field fails against the literal current-ID fingerprint without regenerating the expected value.

## 3. Phase 0 — Confirmed Dead Code

- [x] 3.1 Delete `CliCompatMatrix`, `default_policy`, and `supported_range_text` plus only their test-only imports/assertions; retain generated version bounds and runtime `check_version_from_config` coverage.
- [x] 3.2 Delete `_internal/executable.py` and its writable-directory warning tests/imports; retain focused transport tests for `FileNotFoundError` and `PermissionError` classification on execution and spawn paths.
- [x] 3.3 Delete `.github/workflows/.gitkeep` and verify the workflow directory still contains tracked YAML files.
- [x] 3.4 Run focused operation-fingerprint, upstream-contract, compatibility, and transport tests and fix only Phase 0 regressions.
- [x] 3.5 Run and record the complete Phase 0 gate using the command set from task 1.3 at the Phase 0 tip, compare its evidence with the pinned baseline, stop before Phase 1 on any failure, and commit the gated Phase 0 changes as one recoverable checkpoint.

## 4. Phase 1 — Operation Option Ownership

- [x] 4.1 Add focused table-driven tests for all five option fields covering `Unset` inheritance, scalar/path `None` clears, empty environment clears, normalization errors, source immutability, snapshot identity, and shared semaphore behavior.
- [x] 4.2 Implement one private config-level `OperationOptions -> ClientConfig` overlay function that derives the option field list from msgspec metadata and treats only `Unset` as omitted.
- [x] 4.3 Replace the field-enumeration logic in `MulticaClient.with_options` and `BaseResource._effective_config` with the shared function while keeping distinct client transports/resources and the existing shared semaphore.
- [x] 4.4 Run focused client-isolation, command-options, raw-command, transport-snapshot, and composite-command tests; confirm preview/execution use the same immutable effective config.
- [x] 4.5 Run and record the complete Phase 1 gate using the command set from task 1.3 at the Phase 1 tip, compare its evidence with the pinned baseline, stop on failure, and commit the gated Phase 1 changes as one recoverable checkpoint.

## 5. Phase 2 — Schema-Derived Entity Field Policy

- [x] 5.1 Add a closed characterization table for every concrete bound entity listing baseline public fields, private runtime fields, constructor seeds, encoded aliases, and the two public runtime overlays.
- [x] 5.2 Implement a cached private per-class policy derivation in `entities/_base.py` using `msgspec.structs.fields()` Python names and encoded names; keep `_client` private and declaration order stable.
- [x] 5.3 Route equality, hash, repr, dictionary/JSON serialization, unknown-input checks, encoded-name conversion, attribute overlay reads, and `_set_runtime` validation through the derived policy.
- [x] 5.4 Preserve `AutopilotRun.trigger_payload` and `result` as the only explicit normalized public runtime overlays and add nested mutable-input round-trip/hash/repr tests.
- [x] 5.5 Migrate `_issue_id`, autopilot `triggers`, and autopilot `subscribers` to schema-derived constructor-seed handling and test detached/rebound/presence-aware relation behavior.
- [x] 5.6 Delete all `_PUBLIC_FIELDS`, `_RUNTIME_FIELDS`, and `_RUNTIME_INIT_FIELDS` declarations and add a source-boundary test preventing their reintroduction or a replacement registry/metaclass.
- [x] 5.7 Run focused bound-entity, entity-relocation, decoder, serialization, relation-seeding, and continuation-action tests.
- [x] 5.8 Run and record the complete Phase 2 gate using the command set from task 1.3 at the Phase 2 tip, compare its evidence with the pinned baseline, stop on failure, and commit the gated Phase 2 changes as one recoverable checkpoint.

## 6. Phase 3 — Shared Relation Generation State

- [x] 6.1 Extend synchronized table-driven tests so both `LazyCollection` and `LazyMapping` cover cached hits, concurrent first-load success, concurrent first-load failure, retry, successful refresh, failed-refresh restoration, invalidation races, and exact loader counts.
- [x] 6.2 Implement private generic `_GenerationState[R]` with one condition, three states, generation-specific waiter outcomes, previous-snapshot restoration, and blocking invalidation.
- [x] 6.3 Migrate `LazyCollection` to store an atomic `_RelationLoad` snapshot in `_GenerationState` while retaining tuple normalization and `RelationMetadata` ownership in the collection.
- [x] 6.4 Migrate `LazyMapping` to store its immutable mapping snapshot in `_GenerationState` while retaining mapping normalization and mapping protocol behavior.
- [x] 6.5 Delete the duplicated collection/mapping transition, waiter, outcome, retry, refresh, and invalidation implementations and verify no public cache/base-class/backend abstraction was introduced.
- [x] 6.6 Run focused relation concurrency, cache, refresh, invalidation, mapping, pagination, prefetch, and mutation-invalidation tests.
- [x] 6.7 Run and record the complete Phase 3 gate using the command set from task 1.3 at the Phase 3 tip, compare its evidence with the pinned baseline, stop on failure, and commit the gated Phase 3 changes as one recoverable checkpoint.

## 7. Phase 4 — Command-Owned Composition

- [x] 7.1 Add focused command-module tests for no-step cached values, coalesced run overrides, single-step aliasing, existing/inserted result-field flag references, sequential templates, config/semaphore retention, cleanup, redaction, and rejection of unsupported source plan shapes.
- [x] 7.2 Add the narrow private transformations in `_internal.commands` without exposing `_CommandPlan`, `_Step`, `_StepRef`, retry orchestration, parallel steps, rollback, or a public plan API.
- [x] 7.3 Migrate `LazyCollection` and `LazyMapping` cached/coalesced command construction to those transformations and preserve zero-I/O cached execution.
- [x] 7.4 Migrate offset pagination to command-owned alias/reference/continuation transformations while keeping offset calculation, page/item limits, progress guards, aggregation, and metadata in `models/relations.py`.
- [x] 7.5 Migrate cursor pagination to the same transformations while preserving insertion/replacement of the complete `before`/`before_id` pair and repeated-cursor guards.
- [x] 7.6 Remove all `command._plan`, `_CommandPlan`, `_Step`, `_StepRef`, and `_replace_plan` access/import from `models/relations.py`; add an AST/import boundary test enforcing this ownership.
- [x] 7.7 Run focused command-options, command-preview, redaction, offset/cursor pagination, cached mapping/collection, no-progress, and subprocess-count tests.
- [x] 7.8 Run and record the complete Phase 4 gate using the command set from task 1.3 at the Phase 4 tip, compare its evidence with the pinned baseline, stop on failure, and commit the gated Phase 4 changes as one recoverable checkpoint.

## 8. Post-Phase-4 Lifecycle Measurement

- [x] 8.1 Recount private entity-to-resource calls, `_set_runtime` uses, invalidation callbacks, relation ownership concepts, and files required to change one representative complex relation; append baseline/final comparison and raw commands to `pilot-evidence.md`.
- [x] 8.2 Record a clear lifecycle decision in `pilot-evidence.md`: either no material duplication remains, or a separate future OpenSpec proposal may pilot exactly one complex relation with named deletion criteria; do not implement a lifecycle pilot in this change.

## 9. Phase 5 — Squad-Member Generated Builder Pilot

- [x] 9.1 Add generator tests for exactly `squads.members.list`, `squads.members.add`, and `squads.members.remove`, including deterministic output and fail-closed rejection of unsupported mappings or validators.
- [x] 9.2 Generate typed private argv-builder functions for the three pilot operations from approved command, positional mappings, and `nonblank:*` validators; add no generic runtime interpreter or `python_path` reflection.
- [x] 9.3 Update `SquadMemberResource` command methods to call the generated builders, remove their marker-only binding casts/imports and duplicated validation/argv assembly, and retain the explicit eager methods and existing result adapters.
- [x] 9.4 Add/retain table-driven tests proving unchanged public signatures, eager-to-command delegation, pre-I/O validation, exact list/add/remove argv, options snapshots, results, exceptions, and literal current-ID fingerprints.
- [x] 9.5 Run deterministic approved-contract render/check and verify regeneration produces no diff beyond the expected generated builder output.
- [x] 9.6 Record pilot baseline/final production-plus-test LOC, concepts removed/added, all parity results, and every stop/go criterion in `pilot-evidence.md`.
- [x] 9.7 Apply the stop/go rule: revert the pilot if it adds concepts or lacks measurable net deletion; otherwise retain only the squad-member pilot and record any eligible next family for planning review without implementing expansion.
- [x] 9.8 Run and record the complete Phase 5 gate using the command set from task 1.3 at the Phase 5 tip, compare its evidence with the pinned baseline, stop on failure, and commit the gated pilot decision as one recoverable checkpoint.

## 10. Final Integrated Verification and Handoff

- [x] 10.1 Run `openspec validate simplify-sdk-architecture --strict --json` and resolve every proposal/spec/design/task inconsistency without changing implementation scope. Evidence: command returned `valid: true`, `issues: []`, summary `1 passed / 0 failed`, exit 0; no artifact inconsistencies remained and implementation scope was unchanged.
- [x] 10.2 Run final public discovery and compare eager/command inventories, normalized signatures, return annotations, canonical operation rows, generated entrypoints, and root exports with the recorded baseline. Evidence: focused inventory tests passed `9 passed` on both baseline and current tip; all discovery/normalized-signature/return/canonical-row/entrypoint/root-export counts and SHA-256 digests matched exactly; no implementation or public API files changed.
- [x] 10.3 Run final focused public-behavior matrices for entity field policy, relation concurrency/cache/pagination, command previews/redaction, options snapshots, transport errors, temporary cleanup, process lifecycle, and the retained/reverted generator pilot decision. Evidence: entity/public-boundary matrix `223 passed`; relation concurrency/cache/pagination matrix `279 passed`; command-options/preview/redaction/transport matrix `144 passed`; temporary cleanup matrix `9 passed, 44 deselected`; process lifecycle matrix `33 passed`; contract/fingerprint/retained-pilot matrix `10 passed, 413 deselected`; first-failure stop condition was not reached.
- [x] 10.4 Run and record the final complete gate using the command set from task 1.3 at the final implementation tip, compare it with the pinned baseline, include zero collected live nodes and contract validation against the exact pinned source checkout, and do not reset `HEAD` to the baseline. Evidence: all final gates passed at tip `9ea828a37c6330f55a50e5879358de9c3781d41b`; offline `1892 passed, 6 deselected`, collection `1892/1898` with zero `tests/live/*` nodes, pinned-source validation/check and diff check exit 0; no reset was performed.
- [x] 10.5 Update `pilot-evidence.md` with final gate outputs, diff/LOC totals, phase commit IDs, deferred decisions, and an explicit statement that no new dependency or public API change was introduced.
