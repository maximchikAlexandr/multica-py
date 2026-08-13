## Context

The immutable behavior baseline is `e719de13442841c64ed96855c5227bbe5e173f10`, after the entity/process-result refactor merged. The current planning commit is `2ff0fd954851b9125ea3adba39696c00a57e8eab`; `git rev-parse 2ff0fd9^` and the merge-base of the planning commit with the pinned baseline both resolve to the baseline. The OpenSpec planning commit is part of the starting tree: implementation starts at that commit or a plan-only descendant, and no baseline precondition requires the implementation checkout's `HEAD` to equal `e719de1`.

Public behavior is already governed by `contracts/sdk-contract.json`, generated descriptors in `_generated/approved_sdk.py`, canonical `OperationCase` rows, OpenSpec main specs, and offline test layers. This change does not redesign that public surface; it removes internal parallel sources of truth while keeping those independent guards. Baseline measurements and comparisons use an explicit checkout/reference of the pinned baseline; phase gates run at the current phase tip and compare their evidence to that baseline.

The confirmed duplication sits at five seams:

- `MulticaClient.with_options` and `BaseResource._effective_config` independently enumerate the same five `OperationOptions` fields.
- Each entity repeats msgspec declarations in `_PUBLIC_FIELDS`, while `_base.py` repeats relation/runtime names globally and some classes repeat constructor seeds in `_RUNTIME_INIT_FIELDS`.
- `LazyCollection` and `LazyMapping` each own the same generation/waiter/failure protocol.
- `models/relations.py` reads `Command._plan`, copies `_Step` fields, and reconstructs aliases/references/continuations to build cached and paginated commands.
- Eighteen generated bindings are imported as marker values while resource methods separately write validation and argv; test catalogs then repeat the expected call.

The work is intentionally phased. A complete verification gate after every phase is more important than maximizing line deletion. No later phase starts while an earlier phase has a failing gate.

## Goals / Non-Goals

**Goals:**

- Give each overlay, field-classification, lazy-generation, and command-composition policy one private owner.
- Remove migration-only and uncalled code while retaining independent regression evidence and active runtime errors/version enforcement.
- Prove contract-generated realization on one homogeneous family and expand only when measured evidence supports it.
- Preserve public API, exact CLI contracts, immutable snapshots, relation lifecycle, diagnostics, and process behavior.
- Leave an atomic, phase-ordered implementation plan with explicit verification and rollback points.

**Non-Goals:**

- A whole-repository rewrite, public API change, dynamic public method generation, runtime contract interpreter, or second command namespace.
- A general merge framework, entity metaclass/DSL, public field-policy extension system, generic cache library, event framework, workflow/DAG engine, or pluggable backend.
- Generated implementations for imperative, composite, temporary-file, spawn, pagination, or runtime-specific operations.
- A repository-wide bound-relation lifecycle rewrite or implementation of a lifecycle pilot in this change.
- New dependencies, packaging changes, unrelated documentation cleanup, or replacement of independent expected values with expectations derived from production inputs.

## Decisions

### 1. Establish the immutable baseline and remove confirmed bloat first

Before production edits, record the required style, type, offline, collection, contract, and diff gates from an explicit checkout of the pinned baseline, while leaving the planning commit in the implementation worktree. Phase 0 then performs four independent deletions:

1. Convert `tests/cases/legacy_payloads.py` once into a literal mapping from current active `OperationCase.id` to its existing SHA-256 value. The six removed legacy operations do not become current keys. Delete `LEGACY_ARGV_MIGRATION`, the contract JSON `legacy_argv_migration` object, `ContractCatalog.legacy_argv_migration`, loader closed-key logic, and migration-only tests. The test hashes the final current-case payload tuple and compares it with the literal mapping. Manual cases receive an explicit stable provenance reference at their declaration/family construction point; no reverse lookup or replacement ID map is introduced.
2. Delete `CliCompatMatrix`, `default_policy`, and `supported_range_text` plus their test-only assertions/imports. Keep `_load_supported_bounds`, generated `MIN_CLI_VERSION`/`MAX_CLI_VERSION`, `check_version`, and `check_version_from_config` on the runtime path.
3. Delete `_internal/executable.py`. `CliTransport` continues to build argv from `ClientConfig.executable` and translate execution/spawn `FileNotFoundError` and `PermissionError` into the existing SDK exceptions.
4. Delete `.github/workflows/.gitkeep`; tracked workflow YAML already preserves the directory.

Alternative considered: retain legacy maps as historical documentation. Rejected because frozen hashes already hold the independent behavioral baseline and the maps duplicate mutable current IDs in two places.

### 2. Put option application next to the option and config types

Add one private function in `config.py`, conceptually `_apply_operation_options(config, options) -> ClientConfig`. It returns a msgspec replacement snapshot, iterating msgspec-declared `OperationOptions` fields rather than maintaining another five-name tuple. `None` is a real value, an empty normalized environment tuple is a real value, and only `Unset` means inherit. `options=None` returns a distinct immutable config snapshot so existing command snapshot identity/immutability behavior remains intact.

`MulticaClient.with_options` constructs and normalizes `OperationOptions`, calls the helper, then builds a distinct client with the existing shared semaphore. `BaseResource._effective_config` calls the same helper for command snapshots. No transport or public configuration abstraction is added.

Alternative considered: a generic overlay protocol or reusable merge utility. Rejected because only `OperationOptions -> ClientConfig` is required and a generalized mechanism would obscure presence semantics.

### 3. Derive bound-entity policy lazily from msgspec metadata

`entities/_base.py` owns a small cached private policy derivation per concrete entity type. It reads `msgspec.structs.fields(cls)` and records ordered public Python names, private runtime names, constructor-seed names, and Python-to-encoded-name conversion:

- `_client` and fields whose Python name starts with `_` are runtime/private.
- A public Python field encoded under an underscore-prefixed wire name is a constructor seed: it remains accepted for construction/relation context but is excluded from public snapshots.
- Remaining fields are public in msgspec declaration order, regardless of a non-private alias such as `skill_refs -> skills`.
- `AutopilotRun.trigger_payload` and `result` are the only explicit public runtime overlays. Their current immutable JSON normalization remains local and is included in public value operations.

All equality, hash, repr, serialization, unknown-field validation, and `_set_runtime` validation use this derived policy. `_PUBLIC_FIELDS`, `_RUNTIME_FIELDS`, and `_RUNTIME_INIT_FIELDS` are deleted. The cache is an implementation detail keyed by class; it is not a registry users or subclasses populate.

Alternative considered: metaclasses, descriptors, or per-entity policy declarations. Rejected because msgspec already exposes the required schema metadata and the exception set is proven and tiny.

### 4. Share a generic snapshot-generation engine, not container behavior

Introduce one private `_GenerationState[R]` in `models/relations.py`. It owns the condition, state enum, generation number, waiter counts/outcomes, previous successful snapshot, load/refresh transition, failure restoration, and invalidation. Its operation accepts a callable that returns one already normalized snapshot of `R`.

`LazyCollection` stores `_RelationLoad[T]` as its state snapshot so tuple items and `RelationMetadata` replace/restore atomically. It continues to normalize iterable loaders and expose collection behavior. `LazyMapping` stores an immutable mapping snapshot and retains mapping lookup/iteration semantics. Command loaders pass through the same state engine using container-owned normalization. This avoids trying to encode collection metadata into a generic cache abstraction.

Alternative considered: a common relation base class. Rejected because collection and mapping protocols, normalization, and metadata are distinct; only their transition protocol is shared.

### 5. Expose narrow private Command transformations to relation code

`_internal.commands` remains the sole owner of `_CommandPlan`, `_Step`, `_StepRef`, rendering, reference resolution, and execution. Add only private transformations needed by current relations:

- replace a command with a no-step cached-result command while retaining its config/transport snapshot for inspection;
- wrap execution with the relation's coalescing callback;
- alias the result of the existing single step;
- produce a result-field argument reference for an existing or inserted flag;
- build a sequential continuation from the aliased first step and a pre-renderable template, with relation-supplied gate, continuation predicate, and finalizer callbacks.

The command helper validates that the source command has the supported single-step shape and raises a private construction error for any unsupported shape. Offset/cursor knowledge remains in relations: flag names and result field paths, cursor-pair completeness, repeated/no-progress checks, limits, aggregation, and metadata. After migration, an AST/import boundary test rejects `_plan`, `_CommandPlan`, `_Step`, and `_StepRef` use from `models/relations.py`.

Alternative considered: expose `_CommandPlan` as a public plan API or build a workflow engine. Rejected because callers need only `Command[T]` inspection/execution and current relations need only sequential pagination composition.

### 6. Generate ordinary private builders for one family

The generator gets a compile-time allowlist containing only the three pilot operation IDs: `squads.members.list`, `squads.members.add`, and `squads.members.remove`. For each, generation reads the approved binding's command, positional mappings, and `nonblank:*` validators, fails closed on an unsupported mapping/validator, and emits a typed private function such as `_build_squad_members_add_argv(squad_id, member_id) -> tuple[str, ...]`. There is no generic runtime builder and no runtime reading of `python_path`.

`SquadMemberResource` keeps its explicit typed methods and existing `_decoded_page_command`/`_action_command` result paths. The command methods call generated builders; eager methods still call their sibling's `.run()`. The unused binding marker casts/imports disappear for that family.

The pilot comparison is committed in `pilot-evidence.md`. It records baseline/final production and test line counts, concepts removed/added, deterministic render/check output, signature inventory, validator timing, exact argv/result parity, and independent fingerprint status. Expansion is out of the default implementation path: even if all criteria pass, the implementer records which other homogeneous marker-only family is eligible and stops for review. The planning-review decision may amend the change before expansion. If the pilot adds concepts or lacks net deletion, it is reverted; descriptor-only generation remains.

Alternative considered: generate all eighteen marker-only families immediately. Rejected because the families include composite and runtime-specific behavior and the issue explicitly requires a measured pilot gate.

### 7. Defer lifecycle abstraction after a measurement-only checkpoint

After Phases 2–4, capture counts for private entity-to-resource calls, `_set_runtime` uses, invalidation callbacks, and files/concepts needed to change a representative relation. Record the conclusion in `pilot-evidence.md`. This change does not implement an `Issue.comments` or other lifecycle pilot. If duplication remains material, a separate OpenSpec proposal may define exactly one pilot and its rollback criteria.

## Risks / Trade-offs

- [Field classification misidentifies an alias or constructor seed] → Add a closed table over every concrete bound entity comparing derived public/private/seed sets to the baseline before deleting declarations; retain focused round-trip, detach, rebind, hash, repr, and AutopilotRun JSON tests.
- [Shared generation state changes waiter behavior under races] → Move existing collection and mapping concurrency cases unchanged first, add synchronized success/failure/refresh/invalidate cases for both containers, and keep the old implementation available for per-phase rollback until the gate passes.
- [Command helper becomes a hidden workflow framework] → Limit accepted input to a single existing step plus sequential continuation, keep pagination semantics in relations, and reject parallelism/rollback/retry orchestration or public exposure.
- [Generator and tests share one unchecked source] → Keep literal current-case fingerprints and table expectations independent; generator output continues to come only from the approved contract and deterministic render/check.
- [Line-count optimization harms readability] → Public resource methods remain explicit and typed; net deletion is necessary but not sufficient for pilot expansion, and named concept counts are reviewed alongside LOC.
- [Full gates are expensive per phase] → Run focused tests while editing, but do not waive the required phase gate; use phase commits as recoverable rollback points.
- [Pinned upstream checkout is unavailable locally] → Treat contract source validation as a delivery blocker, resolve the exact checkout from approved provenance, and never substitute a newer checkout or skip the validation silently.

## Migration Plan

1. Record baseline commands/results from `e719de13442841c64ed96855c5227bbe5e173f10`, verify the implementation worktree starts from `2ff0fd954851b9125ea3adba39696c00a57e8eab` or a plan-only descendant, and create a Phase 0 commit containing only confirmed deletions and converted current-ID fingerprints.
2. Implement and gate the shared config overlay; commit Phase 1.
3. Add derived entity policy with characterization tests, delete parallel declarations, gate, and commit Phase 2.
4. Introduce `_GenerationState`, migrate collection and mapping, gate, and commit Phase 3.
5. Add narrow command transformations, migrate relations off plan internals, gate, and commit Phase 4.
6. Implement only the squad-member generator pilot, write `pilot-evidence.md`, apply the stop/go rule, gate, and commit Phase 5.
7. Record the relation-lifecycle remeasurement and final integrated verification proof. Do not implement the deferred pilot.

Each phase is independently revertible through its commit. If a phase cannot preserve its focused and full gates, revert that phase and leave later phases unstarted. The public package requires no consumer migration because signatures and behavior are unchanged.

## Open Questions

There are no unresolved requirements before implementation. Whether another marker-only family should be generated is deliberately a post-pilot review decision, not an assumption for this plan. Whether a relation-lifecycle pilot is justified is deliberately deferred to a separate OpenSpec change after measurement.
