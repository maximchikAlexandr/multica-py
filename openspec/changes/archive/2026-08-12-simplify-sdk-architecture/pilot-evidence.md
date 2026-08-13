# Simplify SDK architecture: baseline evidence

Pinned baseline evidence plus the completed Phase 0–Phase 4 checkpoints and
the measurement-only 8.1–8.2 block. Phase 5 and final verification are
complete through task 10.5; no additional implementation or public-surface
work is pending in this change. A separate final integrated verification
outside task 10.4 remains deferred by the accepted scope.

## Revisions and absolute checkouts

| Item | Absolute path | Revision | Verification |
| --- | --- | --- | --- |
| Immutable SDK baseline worktree | `/Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/baseline-sdk-architecture` | `e719de13442841c64ed96855c5227bbe5e173f10` | `git -C <path> rev-parse HEAD` |
| Implementation worktree before Phase 0 checkpoint | `/Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/workdir/multica-py` | `52634ea98e09c11eb1685a98e35611960ce32eb7` plus the scoped Phase 0 working tree | phase gate ran on this planning descendant |
| OpenSpec planning commit | `/Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/workdir/multica-py` | `2ff0fd954851b9125ea3adba39696c00a57e8eab` | `git rev-parse 2ff0fd9^` and merge-base both resolve to baseline |
| Pinned upstream source checkout | `/Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/upstream-multica-v0.4.20` | `93342d04a7a9f788fec921e5aa736f86c7f22d8f` | detached checkout; exact `sdk-contract.json` target commit |

The approved contract records upstream tag `v0.4.20`, version `0.4.20`,
release ID `366120041`, and release provenance reference
`.devlocal/upstream-contract/v0.4.9..v0.4.20/release/release-verification.json`.
The source checkout above was cloned from `git@github.com:multica-ai/multica.git`
and detached at the approved target commit. Contract validation was run
against that absolute checkout, not against a newer source tree.

The implementation ancestry checks were:

```text
git rev-parse 2ff0fd954851b9125ea3adba39696c00a57e8eab^
e719de13442841c64ed96855c5227bbe5e173f10
git merge-base 2ff0fd954851b9125ea3adba39696c00a57e8eab e719de13442841c64ed96855c5227bbe5e173f10
e719de13442841c64ed96855c5227bbe5e173f10
git merge-base --is-ancestor 2ff0fd954851b9125ea3adba39696c00a57e8eab HEAD
0
```

Thus the implementation tip is a descendant of the planning commit, and the
planning commit's parent and merge-base with the pinned baseline are the
pinned baseline. No comparison requires implementation `HEAD` to equal the
baseline.

## Baseline tracked LOC

Counts below are newline counts from `git ls-files` in the explicit baseline
worktree. Phase manifests are the planned scope anchors from `tasks.md` and
`design.md`; overlapping files are counted once within each phase manifest.

| Scope | Tracked files | LOC |
| --- | ---: | ---: |
| Production (`src`) | 73 | 13,288 |
| Tests (`tests`) | 84 | 24,027 |
| Generator/contract (`tools`, `contracts`, `scripts`) | 16 | 20,568 |
| Phase 0 cleanup/fingerprint anchors | 13 | 24,732 |
| Phase 1 options anchors | 4 | 1,076 |
| Phase 2 entity-policy anchors | 14 | 3,478 |
| Phase 3 relation-state anchors | 7 | 5,935 |
| Phase 4 command-encapsulation anchors | 5 | 2,776 |
| Phase 5 generator-pilot anchors | 8 | 20,776 |

Phase anchor manifests:

- Phase 0: `tests/cases/legacy_payloads.py`,
  `tests/cases/operations.py`, `tests/unit/resources/test_operations.py`,
  `contracts/sdk-contract.json`, `tools/upstream_contract/contract.py`,
  `tests/contract/test_sdk_contract.py`, `tests/unit/test_upstream_contract.py`,
  `src/multica_py/_internal/compat.py`,
  `src/multica_py/_internal/compatibility_models.py`,
  `src/multica_py/_internal/executable.py`,
  `tests/unit/test_compat_policy.py`, `tests/unit/test_compatibility.py`,
  `.github/workflows/.gitkeep`.
- Phase 1: `src/multica_py/config.py`, `src/multica_py/client.py`,
  `src/multica_py/resources/_base.py`, `tests/unit/test_command_options.py`.
- Phase 2: `src/multica_py/entities/*.py`,
  `tests/unit/resources/test_bound_entity.py`,
  `tests/contract/test_bound_public_surface.py`,
  `tests/contract/test_entity_relocation.py`.
- Phase 3 (exactly 7 tracked files, 5,935 LOC): `src/multica_py/models/relations.py`
  (732), `tests/unit/resources/test_agent_skill_squad_relations.py` (1,202),
  `tests/unit/resources/test_autopilot_relations.py` (908),
  `tests/unit/resources/test_issue_relations.py` (1,004),
  `tests/unit/resources/test_project_relations.py` (872),
  `tests/unit/resources/test_relations.py` (62), and
  `tests/unit/resources/test_workspace_relations_extra.py` (1,155).
  `tests/unit/resources/test_workspace_relations.py` (395) is explicitly
  excluded; it is not a Phase 3 relation-state anchor.
- Phase 4: `src/multica_py/_internal/commands.py`,
  `src/multica_py/models/relations.py`,
  `tests/contract/test_entity_relocation.py`,
  `tests/unit/test_command_options.py`,
  `tests/unit/resources/test_workspace_relations_extra.py`.
- Phase 5 (exactly 8 tracked files, 20,776 LOC):
  `tools/upstream_contract/generation.py` (380),
  `scripts/upstream_contract.py` (13), `contracts/sdk-contract.json`
  (16,266), `src/multica_py/_generated/approved_sdk.py` (1,817),
  `src/multica_py/resources/squad_members.py` (59),
  `tests/unit/resources/test_agent_skill_squad_relations.py` (1,202),
  `tests/unit/resources/test_operations.py` (972), and
  `tests/contract/test_sdk_contract.py` (67). The remaining operation and
  contract test files, including `tests/cases/operations.py`, are excluded
  from this pilot anchor.

The two manifests above are pinned to baseline revision
`e719de13442841c64ed96855c5227bbe5e173f10`; the parenthetical values are
newline counts from that revision. To reproduce the tracked-file set and LOC
denominator, run this exact check from the repository root (the `test` rejects
missing or extra paths before counting):

```sh
baseline=e719de13442841c64ed96855c5227bbe5e173f10
check_manifest() {
  expected=$(printf '%s\n' "$@" | sort)
  actual=$(git ls-tree -r --name-only "$baseline" -- "$@" | sort)
  test "$actual" = "$expected" || return 1
  printf '%s\n' "$actual" | while IFS= read -r file_path; do
    git show "$baseline:$file_path" | wc -l
  done | awk '{ total += $1 } END { print total }'
}

check_manifest \
  src/multica_py/models/relations.py \
  tests/unit/resources/test_agent_skill_squad_relations.py \
  tests/unit/resources/test_autopilot_relations.py \
  tests/unit/resources/test_issue_relations.py \
  tests/unit/resources/test_project_relations.py \
  tests/unit/resources/test_relations.py \
  tests/unit/resources/test_workspace_relations_extra.py  # 5,935

check_manifest \
  tools/upstream_contract/generation.py \
  scripts/upstream_contract.py \
  contracts/sdk-contract.json \
  src/multica_py/_generated/approved_sdk.py \
  src/multica_py/resources/squad_members.py \
  tests/unit/resources/test_agent_skill_squad_relations.py \
  tests/unit/resources/test_operations.py \
  tests/contract/test_sdk_contract.py  # 20,776
```

## Baseline duplication and deletion inventory

All counts are from the pinned baseline worktree. Declaration counts are
reported separately from use counts where that distinction matters.

| Inventory | Count |
| --- | ---: |
| `_PUBLIC_FIELDS` declaration/use lines in `src/multica_py/entities` | 19 |
| `_RUNTIME_FIELDS` declaration/use lines in `src/multica_py/entities` | 3 |
| `_RUNTIME_INIT_FIELDS` declaration lines in `src/multica_py/entities` | 3 |
| `_set_runtime` references in production | 40 |
| `_set_runtime` references in tests | 12 |
| Relation lines accessing `_plan`, `_Step`, or `_StepRef` | 22 unique lines |
| Relation `_plan` matches | 13 |
| Relation `_Step` matches | 10 |
| Relation `_StepRef` matches | 4 |
| Marker-only binding casts | 18 entries in 6 resource files |
| Private invalidation callback definitions (`def _invalidate...`) | 8 |
| `LEGACY_ARGV_MIGRATION` references | 10 |
| `legacy_argv_migration` contract/code references | 9 |
| `.github/workflows/.gitkeep` tracked files | 1 |
| `_internal/executable.py` tracked files | 1 |

The 18 marker-only binding casts are in `attachments.py` (2),
`autopilots.py` (3), `issue_labels.py` (3), `project_resources.py` (4),
`skill_files.py` (3), and `squad_members.py` (3). The eight private
invalidation callbacks are in `entities/agents.py` (1), `entities/issues.py`
(4), `entities/projects.py` (1), `entities/skills.py` (1), and
`entities/squads.py` (1).

## Baseline gates

Preparation used `uv sync --all-groups --frozen` in the baseline worktree.
The required gates below then ran from the pinned baseline checkout. Raw logs
are retained at the following absolute path for this workspace:
`/Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/baseline-gate-logs/`.

| Gate | Command/result |
| --- | --- |
| Ruff lint | `uv run ruff check .` — exit 0 |
| Ruff format | `uv run ruff format --check .` — exit 0 |
| Source typing | `uv run mypy src` — exit 0; 72 source files |
| Test typing | `uv run mypy tests` — exit 0; 79 source files |
| Offline tests | `uv run pytest -m "not live"` — exit 0; 1,856 passed, 6 deselected, 71.60s |
| Offline collection | `uv run pytest -m "not live" --collect-only` — exit 0; 1,862 collected, 1,856 selected, 6 deselected |
| Live exclusion | Collection output contains no `tests/live/` node |
| Approved contract validation | `uv run python scripts/upstream_contract.py validate --approved contracts/sdk-contract.json --source-checkout /Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/upstream-multica-v0.4.20` — exit 0 |
| Approved contract check | `uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json` — exit 0 |
| Diff whitespace | `git diff --check` — exit 0 |
| Public discovery guard | `uv run pytest tests/unit/resources/test_operations.py::test_discovered_public_methods` — exit 0; 1 passed |

The planning-tree artifact validation also passed before this evidence was
written:
`uv run openspec validate simplify-sdk-architecture --strict --json` — valid,
0 issues (exit 0).

## Phase 0 gate and baseline comparison

The Phase 0 gate ran on a descendant of planning commit `2ff0fd954851b9125ea3adba39696c00a57e8eab`, with the current-ID guard checkpoint
`52634ea98e09c11eb1685a98e35611960ce32eb7` as its parent. The one recoverable
checkpoint containing this evidence is the Phase 0 implementation tip.

| Gate | Pinned baseline | Phase 0 result |
| --- | --- | --- |
| Ruff lint | exit 0 | `uv run ruff check .` — exit 0 |
| Ruff format | exit 0 | `uv run ruff format --check .` — exit 0; 162 files formatted |
| Source typing | 72 source files, exit 0 | `uv run mypy src` — exit 0; 70 source files after deleting two dead modules |
| Test typing | 79 source files, exit 0 | `uv run mypy tests` — exit 0; 79 source files |
| Offline tests | 1,856 passed, 6 deselected | `uv run pytest -m "not live"` — 1,858 passed, 6 deselected |
| Offline collection | 1,862 collected; 1,856 selected; no live nodes | `uv run pytest -m "not live" --collect-only -q` — 1,864 collected; 1,858 selected; 6 deselected; `live_nodes=0` |
| Approved contract validation | exit 0 against pinned checkout | `uv run python scripts/upstream_contract.py validate --approved contracts/sdk-contract.json --source-checkout /Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/upstream-multica-v0.4.20` — exit 0 |
| Approved contract check | exit 0 | `uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json` — exit 0 |
| Diff whitespace | exit 0 | `git diff --check` — exit 0 |
| Public discovery | 1 passed | `uv run pytest tests/unit/resources/test_operations.py::test_discovered_public_methods` — 1 passed |

The focused Phase 0 verification ran 98 tests covering current-ID
fingerprints/mutation, upstream contract closure, compatibility behavior,
execution/spawn transport mappings, and public discovery: all 98 passed.

The cleanup is limited to the approved dead surfaces: `CliCompatMatrix`,
`default_policy`, `supported_range_text`, their unused compatibility-model
module, `_internal/executable.py`, and `.github/workflows/.gitkeep`. Generated
`MIN_CLI_VERSION`/`MAX_CLI_VERSION`, `_load_supported_bounds`, and
`check_version_from_config` remain. The transport still maps
`FileNotFoundError`/`PermissionError` to `ExecutableNotFoundError` /
`ExecutableNotRunnableError` on both execution and spawn paths, with focused
tests for all four cases. The workflow directory retains five tracked YAML
files.

## Phase 1 gate and baseline comparison

Phase 1 tasks 4.1–4.5 ran on the descendant of planning commit
`2ff0fd954851b9125ea3adba39696c00a57e8eab` whose immediate Phase 0 parent was
`c0110e6`. The single private `_apply_operation_options` overlay in
`src/multica_py/config.py` is metadata-driven from `OperationOptions`; both
`MulticaClient.with_options` and `BaseResource._effective_config` use it.
Every effective config is an immutable replacement snapshot, while client and
resource transports remain distinct and retain the shared semaphore. Preview
and execution snapshot tests cover the same effective config identity.

The table-driven option tests cover all five fields (`profile`, `workspace_id`,
`timeout`, `cwd`, and `environment`) and assert inheritance via `Unset`,
explicit `None`, empty environment, invalid values, frozen snapshots, and
preservation of unrelated fields. The focused Phase 1 verification selected
330 tests across client isolation, client options, command options, raw CLI
commands, composite snapshots, and transport snapshots: all 330 passed and 77
were deselected by the focused expression.

| Gate | Pinned baseline | Phase 1 result |
| --- | --- | --- |
| OpenSpec validation | valid, 0 issues | `uv run openspec validate simplify-sdk-architecture --strict --json` — exit 0; valid, 0 issues |
| Ruff lint | exit 0 | `uv run ruff check .` — exit 0 |
| Ruff format | exit 0 | `uv run ruff format --check .` — exit 0; 162 files formatted |
| Source typing | 72 source files, exit 0 | `uv run mypy src` — exit 0; 70 source files |
| Test typing | 79 source files, exit 0 | `uv run mypy tests` — exit 0; 79 source files |
| Offline tests | 1,856 passed, 6 deselected | `uv run pytest -m "not live"` — 1,870 passed, 6 deselected, 64.30s |
| Offline collection | 1,862 collected; 1,856 selected; no `tests/live/*` nodes | `uv run pytest -m "not live" --collect-only -q` — 1,876 collected; 1,870 selected; 6 live-marked nodes deselected; no `tests/live/*` nodes |
| Approved contract validation | exit 0 against pinned checkout | `uv run python scripts/upstream_contract.py validate --approved contracts/sdk-contract.json --source-checkout /Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/upstream-multica-v0.4.20` — exit 0 |
| Approved contract check | exit 0 | `uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json` — exit 0 |
| Diff whitespace | exit 0 | `git diff --check` — exit 0 |
| Public discovery | 1 passed | `uv run pytest tests/unit/resources/test_operations.py::test_discovered_public_methods` — 1 passed |

The Phase 1 checkpoint commit contains this evidence and is a recoverable
descendant of `c0110e6`; it is pushed to `feat/simplify-sdk-architecture`.

## Phase 2 gate and baseline comparison

Phase 2 tasks 5.5–5.8 ran from the Phase 1 checkpoint `559900f36008a052edac32b927a50212bb1f501f`, a descendant of planning commit
`2ff0fd954851b9125ea3adba39696c00a57e8eab`. Constructor seeds now derive from
schema metadata: `TaskRun.issue_id` and `CommentThread.issue_id` use encoded
`_issue_id`, while `Autopilot.triggers` and `Autopilot.subscribers` use their
encoded seed fields. Detached, rebound, and presence-aware relation tests
remain green. All legacy field declarations were removed from concrete
entities and `_base.py`; a source-boundary contract rejects their
reintroduction and metaclass/registry replacements.

The focused 5.7 verification selected 218 tests covering bound entities,
entity relocation, decoders, serialization, relation seeding, continuation
actions, and autopilot/issue relation behavior: all 218 passed.

| Gate | Pinned baseline | Phase 2 result |
| --- | --- | --- |
| OpenSpec validation | valid, 0 issues | `uv run openspec validate simplify-sdk-architecture --strict --json` — exit 0; valid, 0 issues |
| Ruff lint | exit 0 | `uv run ruff check .` — exit 0 |
| Ruff format | exit 0 | `uv run ruff format --check .` — exit 0; 162 files formatted |
| Source typing | 72 source files, exit 0 | `uv run mypy src` — exit 0; 70 source files |
| Test typing | 79 source files, exit 0 | `uv run mypy tests` — exit 0; 79 source files |
| Offline tests | 1,856 passed, 6 deselected | `uv run pytest -m "not live"` — exit 0; 1,887 passed, 6 deselected, 55.00s |
| Offline collection | 1,862 collected; 1,856 selected; no `tests/live/*` nodes | `uv run pytest -m "not live" --collect-only -q` — exit 0; 1,893 collected; 1,887 selected; 6 live-marked nodes deselected; no `tests/live/*` nodes |
| Approved contract validation | exit 0 against pinned checkout | `uv run python scripts/upstream_contract.py validate --approved contracts/sdk-contract.json --source-checkout /Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/upstream-multica-v0.4.20` — exit 0 |
| Approved contract check | exit 0 | `uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json` — exit 0 |
| Diff whitespace | exit 0 | `git diff --check` — exit 0 |
| Public discovery | 1 passed | `uv run pytest tests/unit/resources/test_operations.py::test_discovered_public_methods` — 1 passed |

The Phase 2 changes and this evidence are committed as one recoverable
checkpoint descendant of `559900f`; the checkpoint is pushed to
`feat/simplify-sdk-architecture`.

## Phase 3 gate and baseline comparison

Phase 3 tasks 6.1–6.7 ran from the Phase 2 checkpoint
`cfd2d993850d56793e3a0b40f67c23d2f23f72b0`, a descendant of planning commit
`2ff0fd954851b9125ea3adba39696c00a57e8eab`. `LazyCollection` and
`LazyMapping` now delegate their common transition, generation waiter/outcome,
retry, refresh restoration, and blocking invalidation protocol to one private
generic `_GenerationState[R]`. Collection normalization remains in
`_RelationLoad` with `RelationMetadata`; mappings retain immutable
`MappingProxyType` snapshots.

The focused Phase 3 verification selected 271 relation tests covering cached
hits, concurrent success/failure, retries, refresh and invalidation races,
mapping behavior, offset/cursor pagination, prefetch, and mutation
invalidation: all 271 passed. The generation cases use collection, mapping,
offset, and cursor variants and assert one loader call per coalesced generation
plus generation-specific waiter outcomes.

| Gate | Pinned baseline | Phase 3 result |
| --- | --- | --- |
| OpenSpec validation | valid, 0 issues | `uv run openspec validate simplify-sdk-architecture --strict --json` — exit 0; valid, 0 issues |
| Ruff lint | exit 0 | `uv run ruff check .` — exit 0 |
| Ruff format | exit 0 | `uv run ruff format --check .` — exit 0; 162 files formatted |
| Source typing | 72 source files, exit 0 | `uv run mypy src` — exit 0; 70 source files |
| Test typing | 79 source files, exit 0 | `uv run mypy tests` — exit 0; 79 source files |
| Offline tests | 1,856 passed, 6 deselected | `uv run pytest -m "not live"` — exit 0; 1,887 passed, 6 deselected |
| Offline collection | 1,862 collected; 1,856 selected; no `tests/live/*` nodes | `uv run pytest -m "not live" --collect-only -q` — exit 0; 1,893 collected; 1,887 selected; 6 live-marked nodes deselected; no `tests/live/*` nodes |
| Live collection | not part of offline baseline | `uv run pytest -m live --collect-only -q` — exit 0; 6 selected, 1,887 deselected; six `tests/live/test_smoke.py` nodes |
| Approved contract validation | exit 0 against pinned checkout | `uv run python scripts/upstream_contract.py validate --approved contracts/sdk-contract.json --source-checkout /Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/upstream-multica-v0.4.20` — exit 0 |
| Approved contract check | exit 0 | `uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json` — exit 0 |
| Diff whitespace | exit 0 | `git diff --check` — exit 0 |
| Public discovery | 1 passed | `uv run pytest tests/unit/resources/test_operations.py::test_discovered_public_methods` — 1 passed |

The Phase 3 changes and this evidence are committed as one recoverable
checkpoint descendant of `cfd2d993850d56793e3a0b40f67c23d2f23f72b0`; the
checkpoint is pushed to `feat/simplify-sdk-architecture`.

## Phase 4.1 focused evidence

Phase 4 tasks 7.1–7.3 ran from the Phase 3 checkpoint
`80c83d80707dc88479fd1a835a19fb9d8ba8f482`, a descendant of planning commit
`2ff0fd954851b9125ea3adba39696c00a57e8eab`. `_internal.commands` now owns
private cached-result, coalesced-run, single-step alias, result-field
reference, and sequential-template transformations. The public command
surface remains only `Command`; `_CommandPlan`, `_Step`, and `_StepRef` stay
private, with no retry/parallel/rollback or public plan API. `LazyCollection`
and `LazyMapping` use the cached/coalesced transformations while retaining
their effective config/semaphore snapshots and zero-I/O cached execution.

The focused Phase 4.1 verification selected 352 tests across command options,
command previews, relation cache/coalescing, pagination, mapping, prefetch,
mutation invalidation, redaction, and subprocess-count behavior: all 352
passed. New transformation tests cover no-step cached values, coalesced
overrides, single-step aliasing, existing/inserted result-field references,
sequential templates, unsupported shapes, snapshot/semaphore retention, and
zero-I/O execution.

The Phase 4.1 tasks intentionally stop before 7.4; offset/cursor ownership
and the Phase 4 gate remain for the next accepted block. This focused block is
committed as one recoverable checkpoint descendant of `80c83d8` and pushed to
`feat/simplify-sdk-architecture`.

## Phase 4.2 focused evidence

Task 7.4 migrates only offset pagination composition. `OffsetLazyCollection`
now builds its continuation template through the private command transformations
for single-step aliasing, an existing `--offset` result-field reference, and
sequential continuation construction. The relation retains offset calculation,
default page limit, page/item budgets, repeated-offset and empty-page guards,
page aggregation, and `RelationMetadata(total=...)`. Empty source commands still
use the relation loader through the coalesced command wrapper, and a missing
offset argument remains a construction error before I/O. Cursor pagination and
the command/relations boundary test remain deferred to tasks 7.5+.

Focused discovery selected 261 tests across command options, offset/cursor
relation previews and guards, relation generation/cache behavior, issue
relations, and squad/agent/workspace pagination consumers; all 261 passed.
The command transformation tests also verify the command-owned template shape,
while existing pagination tests verify exact preview argv, runtime offset
resolution, aggregation, metadata, progress guards, and bounded execution.
This task is recorded as a separate recoverable checkpoint descendant of the
accepted Phase 4.1 commit `1cf6bde97270e0d360e5cfce7f80b91b71b44d58`.

## Phase 4.3 focused evidence

Task 7.5 migrates only cursor pagination composition. `CursorLazyCollection`
now builds its continuation through command-owned aliasing, result-field
references, and sequential continuation transformations. Applying the two
references independently preserves both cases required by the wire shape:
existing `--before`/`--before-id` arguments are replaced, and either missing
argument is inserted before `--output`; the continuation always carries the
complete pair. Cursor repeated/no-progress guards, page/item limits,
aggregation, metadata ownership, and cache installation remain in
`models/relations.py`.

Focused discovery selected 262 tests across command options, offset/cursor
relation previews and guards, relation generation/cache behavior, issue
relations, and squad/agent/workspace pagination consumers; all 262 passed.
The added mixed-pair test covers replacement of an existing `--before` and
insertion of a missing `--before-id`, exact preview rendering, and runtime
resolution of both cursor fields. Tasks 7.6–7.8 remain deferred.

## Phase 4.4 focused evidence

Task 7.6 removes the remaining command-plan internals from
`models/relations.py`; relation code now imports only the narrow private
transformations and the public `Command` wrapper. The focused AST/import
boundary test rejects `_plan` attribute access and `_CommandPlan`, `_Step`,
`_StepRef`, or `_replace_plan` names/imports in the relation module, preserving
command-module ownership without constraining unrelated command tests.

The focused boundary node was collected and passed. Tasks 7.7–7.8 remain
deferred; no full Phase-4 gate was run.

## Phase 4.5 focused evidence

Task 7.7's focused discovery selected 252 tests covering command options and
snapshot retention, command preview and operation preview vectors, CLI and
transport redaction across preview/result/error surfaces, offset and cursor
pagination previews and runtime guards, cached mapping/collection execution,
no-progress and repeated-cursor handling, relation invalidation/coalescing,
consumer pagination, and bounded transport call counts. The exact selected
set ran successfully: **252 passed**.

The focused run intentionally did not invoke task 7.8 or the complete Phase-4
gate. No implementation scope beyond the already accepted 7.1–7.6 command
composition and ownership work was changed in this checkpoint.

## Phase 4.6 full gate evidence

Task 7.8 ran the complete gate at the accepted Phase 4 tip
`50b3e4013799fe7c4d4183bb8ab46b5591e1b8d8`, a descendant of planning commit
`2ff0fd954851b9125ea3adba39696c00a57e8eab`. Every gate command completed
successfully before this evidence-only checkpoint was created.

| Gate | Pinned baseline | Phase 4 result |
| --- | --- | --- |
| OpenSpec validation | valid, 0 issues | `uv run openspec validate simplify-sdk-architecture --strict --json` — exit 0; valid, 0 issues |
| Ruff lint | exit 0 | `uv run ruff check .` — exit 0 |
| Ruff format | exit 0 | `uv run ruff format --check .` — exit 0; 162 files already formatted |
| Source typing | 72 source files, exit 0 | `uv run mypy src` — exit 0; 70 source files |
| Test typing | 79 source files, exit 0 | `uv run mypy tests` — exit 0; 79 source files |
| Offline tests | 1,856 passed, 6 deselected | `uv run pytest -m "not live"` — exit 0; 1,892 passed, 6 deselected |
| Offline collection | 1,862 collected; 1,856 selected; no `tests/live/*` nodes | `uv run pytest -m "not live" --collect-only -q` — exit 0; 1,898 collected; 1,892 selected; 6 deselected; no `tests/live/*` nodes |
| Approved contract validation | exit 0 against pinned checkout | `uv run python scripts/upstream_contract.py validate --approved contracts/sdk-contract.json --source-checkout /Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/upstream-multica-v0.4.20` — exit 0 |
| Approved contract check | exit 0 | `uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json` — exit 0 |
| Diff whitespace | exit 0 | `git diff --check` — exit 0 |

Compared with the pinned baseline, the gate retained zero failures and zero
live nodes in the offline collection while the current descendant contains 36
additional selected tests (1,892 versus 1,856). The approved upstream source
checkout and all baseline/planning revisions remain the absolute pinned paths
and IDs recorded above.

The Phase 4 gate and this evidence are committed as one recoverable checkpoint
descendant of `50b3e4013799fe7c4d4183bb8ab46b5591e1b8d8` and pushed to
`feat/simplify-sdk-architecture`; the lifecycle measurement was deferred to
the separate Phase 4.7 checkpoint below.

## Phase 4.7 lifecycle remeasurement and decision

Task 8.1 remeasured the completed Phase 4 tip against the immutable baseline.
The representative complex relation is `Issue.comments`: it combines an
entity accessor, cursor pagination, resource-owned command adapters, runtime
relation installation, mutation invalidation, and focused relation tests. The
ownership-symbol metric is deliberately closed and reproducible: it counts
distinct names from `_GenerationState`, `_RelationLoad`, `RelationMetadata`,
`LazyCollection`, `CursorLazyCollection`, `Command`, `command_loader`,
`page_command_loader`, `_set_runtime`, `_invalidate_comments`, and
`_comments_relation_command` in the six implementation/test files listed by the
raw command below.

```sh
BASE=/Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/baseline-sdk-architecture
for label in baseline final; do
  if [ "$label" = baseline ]; then root="$BASE"; else root="."; fi
  printf '%s private_entity_to_resource_calls=' "$label"
  rg -o '\.[A-Za-z][A-Za-z0-9_]*\._[A-Za-z0-9_]*\(' "$root/src/multica_py/entities" | wc -l
  printf '%s production_set_runtime=' "$label"
  rg -o '_set_runtime' "$root/src" | wc -l
  printf '%s invalidation_callbacks=' "$label"
  rg -c '^\s*def _invalidate' "$root/src/multica_py/entities" \
    | awk -F: '{n+=$2} END {print n+0}'
  printf '%s representative_relation_ownership_concepts=' "$label"
  rg -o '\b(_GenerationState|_RelationLoad|RelationMetadata|LazyCollection|CursorLazyCollection|Command|command_loader|page_command_loader|_set_runtime|_invalidate_comments|_comments_relation_command)\b' \
    "$root/src/multica_py/entities/issues.py" \
    "$root/src/multica_py/entities/comments.py" \
    "$root/src/multica_py/resources/issues.py" \
    "$root/src/multica_py/resources/issue_comments.py" \
    "$root/src/multica_py/models/relations.py" \
    "$root/tests/unit/resources/test_issue_relations.py" 2>/dev/null \
    | sed 's/.*://' | sort -u | wc -l
  printf '%s representative_relation_files=' "$label"
  rg -l '(_comments_relation_command|_invalidate_comments|class CommentThread|class Issue|CursorLazyCollection|_thread_page_command)' \
    "$root/src/multica_py/entities/issues.py" \
    "$root/src/multica_py/entities/comments.py" \
    "$root/src/multica_py/resources/issues.py" \
    "$root/src/multica_py/resources/issue_comments.py" \
    "$root/src/multica_py/models/relations.py" \
    "$root/tests/unit/resources/test_issue_relations.py" \
    | wc -l
done
```

The command reports the following baseline/final comparison:

| Measurement | Pinned baseline | Phase 4 final | Delta |
| --- | ---: | ---: | ---: |
| Private entity-to-resource calls | 47 | 47 | 0 |
| Production `_set_runtime` uses | 40 | 40 | 0 |
| Private invalidation callbacks | 8 | 8 | 0 |
| Representative relation ownership concepts | 10 | 11 | +1 (`_GenerationState`) |
| Files required for `Issue.comments` relation surface | 6 | 6 | 0 |

The six files are `entities/issues.py`, `entities/comments.py`,
`resources/issues.py`, `resources/issue_comments.py`, `models/relations.py`,
and `tests/unit/resources/test_issue_relations.py`. The counts show that the
Phase 2–4 work reduced duplicated generation machinery but did not materially
remove the entity/resource lifecycle seam: private calls, runtime writes,
callbacks, and file surface are unchanged, while the shared state owner is one
additional named concept.

Task 8.2 decision: do not implement a lifecycle pilot in this change. Because
the measured seam remains material, a separate future OpenSpec proposal may
pilot exactly `Issue.comments`, but only if its plan names all of these deletion
criteria before implementation: remove at least one private entity-to-resource
call, remove at least one relation `_set_runtime` write, remove at least one
invalidation callback, and reduce either the closed ownership-concept count
from 11 or the six-file change surface, while preserving public behavior and
the full offline/contract gates. Until such a proposal is accepted, no
repository-wide lifecycle abstraction or pilot is authorized. Phase 5 and the
final integrated verification remain unstarted.

This measurement-only block is committed as one recoverable checkpoint
descendant of `d06844313cf599681adb9794b3a65d670696e08e` and pushed to
`feat/simplify-sdk-architecture`.

## Phase 5.1 generator pilot evidence

Tasks 9.1–9.2 add only a bounded generator projection. The approved contract
is the sole input, and the generator allowlist is exactly
`squads.members.list`, `squads.members.add`, and `squads.members.remove`.
Each descriptor is accepted only when its mappings are contiguous `pos:N`
arguments whose destinations are matching `path:<source>` values and its
validators are the matching `nonblank:<source>` definitions. The output is
three ordinary typed private functions in
`src/multica_py/_generated/approved_sdk.py`:

```text
_build_squad_members_add_argv(squad_id: str, member_id: str) -> tuple[str, ...]
_build_squad_members_list_argv(squad_id: str) -> tuple[str, ...]
_build_squad_members_remove_argv(squad_id: str, member_id: str) -> tuple[str, ...]
```

They call the generated `validate_nonblank` function before returning literal
command tuples. Unsupported mappings, non-contiguous positions, missing
validators, and non-`nonblank` validators raise `ContractError` during
generation. The generated functions are private and omitted from `__all__`;
there is no runtime registry, `python_path` reflection, evaluator, or generic
interpreter. No resource method or public signature changed in this block.

The independent focused tests cover exact builder names and signatures,
private export boundaries, exact list/add/remove argv, pre-I/O nonblank
validation, deterministic source generation, and fail-closed unsupported
mapping/validator mutations:

```sh
uv run pytest tests/contract/test_generator_pilot.py tests/contract/test_sdk_contract.py -q
# 8 passed
```

The approved-contract render and closed check both pass with these raw
commands (the temporary directory receives only untracked projections):

```sh
tmpdir=$(mktemp -d)
uv run python scripts/upstream_contract.py render \
  --approved contracts/sdk-contract.json \
  --runtime-output "$PWD/src/multica_py/_generated/approved_sdk.py" \
  --transient-output "$tmpdir"
uv run python scripts/upstream_contract.py check \
  --approved contracts/sdk-contract.json
rm -rf "$tmpdir"
```

Both commands exited 0. At this checkpoint, tasks 9.3+ were not started:
`SquadMemberResource`, runtime command wiring, resource tests, pilot LOC/stop-go
measurement, and the Phase 5 gate remained deferred.

This bounded generator block is committed as one recoverable checkpoint
descendant of `5e7e84f26f0acd185073b6c62c374835d825e39e` and pushed to
`feat/simplify-sdk-architecture`.

## Phase 5.2 resource delegation evidence

Tasks 9.3–9.4 route `SquadMemberResource.list_command`, `add_command`, and
`remove_command` through the three generated private typed builders. The
resource no longer imports the public binding marker constants or generated
`validate_nonblank`, performs marker-only casts, repeats validation, or assembles
literal argv. Its public eager and command signatures are unchanged, the eager
methods still delegate through `.run()`, and the existing page/action result
adapters remain in place.

The independent table-driven resource tests cover all three current operation
IDs and assert no transport I/O before `.run()`, exact argv snapshots, immutable
options profile/timeout snapshots, eager delegation, successful page/action
results, propagated transport exceptions, pre-I/O nonblank validation, public
signatures, and the literal current-ID payload fingerprints:

```sh
uv run pytest \
  tests/contract/test_squad_member_pilot.py \
  tests/contract/test_generator_pilot.py \
  tests/contract/test_sdk_contract.py -q
# 23 passed
uv run pytest tests/unit/resources/test_operations.py::test_discovered_public_methods -q
# 1 passed
uv run ruff check src/multica_py/resources/squad_members.py \
  tests/contract/test_squad_member_pilot.py
uv run ruff format --check src/multica_py/resources/squad_members.py \
  tests/contract/test_squad_member_pilot.py
uv run mypy src
uv run mypy tests
# all commands exited 0
```

The resource table's closed literal fingerprint fixture contains exactly:

| OperationCase.id | sha256 |
| --- | --- |
| `generated:squads.members.list:default:canonical` | `45b23de207a4f7923a921e164f8cbe049328856ad3356947aa0472e9c91d7a8f` |
| `manual:squads.members.add:canonical` | `b19cc79e2435f1646db4fef983539b182a683e0a067611ff171b5cbcdb5e01cd` |
| `manual:squads.members.remove:canonical` | `c41df2291c89fa5022fc98588ad27299fea6629b7db53c6d994b4649ab4726ef` |

No 9.6+ task, pilot stop/go measurement, or Phase 5 gate was started at the
resource delegation checkpoint. That checkpoint is a separate recoverable
descendant of the accepted generator tip
`e1381b36715c2daaa2d4a754d63eb2817a7a6b2f`.

## Phase 5.3 deterministic contract render evidence

Task 9.5 was run on the accepted resource checkpoint. The canonical generated
runtime output was backed up, rendered again from the approved contract, and
compared byte-for-byte before the closed contract check:

```sh
TMPDIR_95=$(mktemp -d)
cp src/multica_py/_generated/approved_sdk.py "$TMPDIR_95/before.py"
mkdir -p "$TMPDIR_95/transient"
uv run python scripts/upstream_contract.py render \
  --approved contracts/sdk-contract.json \
  --runtime-output "$PWD/src/multica_py/_generated/approved_sdk.py" \
  --transient-output "$TMPDIR_95/transient"
shasum -a 256 "$TMPDIR_95/before.py"
shasum -a 256 src/multica_py/_generated/approved_sdk.py
cmp -s "$TMPDIR_95/before.py" src/multica_py/_generated/approved_sdk.py
uv run python scripts/upstream_contract.py check \
  --approved contracts/sdk-contract.json
find "$TMPDIR_95/transient" -type f | wc -l
rm -rf "$TMPDIR_95"
```

Both SHA-256 values were
`ccb4126c08193216f308fb6c6accbe5ded9ea9f6ebc66899c8cae21cda8035b7`;
`cmp` reported no diff, so the expected generated-builder output was already
present and regeneration introduced no additional changes. The approved
contract check exited 0 and the transient render produced exactly 3 files.
No 9.6+ task was started.

## Phase 5.4 pilot stop/go evidence and rollback

Tasks 9.6–9.7 compare the bounded pilot with the accepted pre-pilot
checkpoint `5e7e84f26f0acd185073b6c62c374835d825e39e` and pilot tip
`9589e5a4f9ce8bf2ddb5c70f9710eef317bd7310`. The manifest is limited to the
three pilot production/generator files and the two pilot test modules; it does
not count unrelated Phase 0–4 changes:

| Scope | Pre-pilot files | Pre-pilot LOC | Pilot-tip files | Pilot-tip LOC | Delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| Production + generator (`approved_sdk.py`, `squad_members.py`, `generation.py`) | 3 | 2,256 | 3 | 2,349 | +93 |
| Pilot tests (`test_generator_pilot.py`, `test_squad_member_pilot.py`) | 0 | 0 | 2 | 305 | +305 |
| Combined pilot production + tests | 3 | 2,256 | 5 | 2,654 | +398 |

The raw counting command was:

```sh
PRE=5e7e84f26f0acd185073b6c62c374835d825e39e
FINAL=9589e5a4f9ce8bf2ddb5c70f9710eef317bd7310
for ref in "$PRE" "$FINAL"; do
  for path in \
    src/multica_py/_generated/approved_sdk.py \
    src/multica_py/resources/squad_members.py \
    tools/upstream_contract/generation.py \
    tests/contract/test_generator_pilot.py \
    tests/contract/test_squad_member_pilot.py; do
    git show "$ref:$path" 2>/dev/null | wc -l
  done
done
```

The closed source/concept inventory is also reproducible. At the pinned
baseline, `SquadMemberResource` had 6 public binding-marker references, 6
`validate_nonblank` references, 3 marker-only `cast("object", ...)` sites, and
3 literal command assemblies. At the accepted pilot tip these were all zero;
the pilot added 3 generated private builder entrypoints, 2 generator allowlist
constants (`_PILOT_OPERATION_IDS` and `_PILOT_COMMANDS), one generator
emission helper (`_pilot_builder_lines`), and 2 independent pilot test
modules. The raw token inventory command was:

```sh
for ref in e719de13442841c64ed96855c5227bbe5e173f10 9589e5a4f9ce8bf2ddb5c70f9710eef317bd7310; do
  git show "$ref:src/multica_py/resources/squad_members.py" \
    | rg -o 'SQUAD_MEMBERS_(ADD|LIST|REMOVE)_BINDING|validate_nonblank|cast\("object"|\("squad", "member"' \
    | sort | uniq -c
done
```

Parity at the accepted pilot tip was independently green: the resource,
generator, and contract matrix reported `23 passed`; public-method discovery
reported `1 passed`; Ruff check/format, `mypy src`, `mypy tests`, and diff
check exited 0; deterministic render/check had equal generated SHA-256
`ccb4126c08193216f308fb6c6accbe5ded9ea9f6ebc66899c8cae21cda8035b7` and
approved-contract check exit 0. After rollback, the retained manual surface
was checked with:

```sh
uv run pytest tests/unit/resources/test_operations.py::test_discovered_public_methods --collect-only -q
# 1 test collected
uv run pytest tests/contract/test_sdk_contract.py \
  tests/unit/resources/test_operations.py::test_discovered_public_methods \
  tests/unit/test_command_options.py -q
# 86 passed
```

Stop/go criteria:

| Criterion | Result | Evidence/decision |
| --- | --- | --- |
| Approved contract is the sole deterministic input and render/check is reproducible | PASS at pilot tip | 9.5 render/check, equal SHA-256, 3 transient files, check exit 0 |
| Public signatures, return types, eager delegation, validation timing, exact argv, results/exceptions remain unchanged | PASS at pilot tip | 23-case independent matrix and literal current-ID fingerprints; rollback retains the accepted manual implementation |
| Independent table-driven canonical vectors and expected-result guard | PASS at pilot tip | 15 resource cases, 3 literal current-ID hashes, 23-case matrix |
| Measurable net deletion across production plus tests | FAIL | `2,256→2,654` LOC, delta `+398`; production/generator delta `+93` and tests delta `+305` |
| No added implementation concepts | FAIL | 3 generated entrypoints, 2 allowlist constants, and 1 emission helper were added; removed manual sites do not offset the failed net-deletion criterion |
| Expansion to another family | STOP | No next family is eligible for planning review from this failed pilot; no family expansion was implemented |

Per the specification, a pilot that adds concepts or lacks measurable net
deletion is reverted. The rollback removes the generated builders, generator
pilot branch, `SquadMemberResource` delegation changes, and pilot-only test
modules, leaving the descriptor-only generator baseline and the manual
`squads.members` family. No new family is retained or proposed. This rollback
is committed separately for review.

## Phase 5.5 complete Phase 5 gate evidence

Task 9.8 ran the complete task-1.3 gate at rollback tip
`2aa6df99ff0afbb4015da4232dfd30dee5ccc725`, a descendant of planning commit
`2ff0fd954851b9125ea3adba39696c00a57e8eab`. The stop/go rollback decision
remains unchanged; this gate made no pilot, family, or runtime changes.

The exact gate commands and results were:

```sh
uv run openspec validate simplify-sdk-architecture --strict --json
# valid: true, issues: [], exit 0
uv run ruff check .
# All checks passed!; exit 0
uv run ruff format --check .
# 162 files already formatted; exit 0
uv run mypy src
# Success: no issues found in 70 source files; exit 0
uv run mypy tests
# Success: no issues found in 79 source files; exit 0
uv run pytest -m 'not live'
# 1892 passed, 6 deselected in 72.50s; exit 0
uv run pytest -m 'not live' --collect-only -q
# 1892/1898 selected/collected, 6 deselected; no tests/live node; exit 0
uv run python scripts/upstream_contract.py validate \
  --approved contracts/sdk-contract.json \
  --source-checkout /Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/upstream-multica-v0.4.20
# exit 0, validation against pinned upstream checkout
uv run python scripts/upstream_contract.py check \
  --approved contracts/sdk-contract.json
# exit 0
git diff --check
# exit 0
uv run pytest tests/unit/resources/test_operations.py::test_discovered_public_methods -q
# 1 passed; exit 0
```

Compared with the immutable baseline gate recorded above:

| Gate evidence | Immutable baseline | Phase 5 rollback tip | Comparison |
| --- | --- | --- | --- |
| Offline pytest | `1,856 passed, 6 deselected` | `1,892 passed, 6 deselected` | all baseline tests remain green; +36 accepted tests from prior phases |
| Offline collection | `1,862 collected; 1,856 selected` | `1,898 collected; 1,892 selected` | six deselected in both; no live nodes in either offline collection |
| Source typing | 72 source files, exit 0 | 70 source files, exit 0 | two dead modules removed in accepted Phase 0 |
| Test typing | 79 source files, exit 0 | 79 source files, exit 0 | unchanged |
| Ruff check/format | exit 0 / exit 0 | exit 0 / exit 0 | unchanged green |
| Pinned-source contract validation | exit 0 | exit 0 | unchanged green against `upstream-multica-v0.4.20` |
| Approved contract check | exit 0 | exit 0 | unchanged green |
| Diff whitespace | exit 0 | exit 0 | unchanged green |
| Public discovery | 1 passed | 1 passed | discovered public set unchanged |

The gate confirms the rollback is releasable and preserves the immutable
baseline behavior evidence. The generated-builder pilot remains reverted,
descriptor-only generation and the manual `squads.members` family remain, no
next family is eligible, and no 10.1+ task or final integrated verification was
started. This gated decision is committed as a recoverable checkpoint on the
SSH feature branch.

## Phase 6.1 task 10.1 OpenSpec consistency evidence

Task 10.1 was run at the accepted Phase 5.5 checkpoint
`0cd0e300ad34f9c741edbf2ac81b09f1667b6991`. The exact command was:

```sh
uv run openspec validate simplify-sdk-architecture --strict --json
```

The command returned exit 0 with this result: the `simplify-sdk-architecture`
change was `valid: true`, `issues: []`, and the summary was `1 passed / 0
failed`. Proposal, spec, design, and task artifacts therefore contain no
remaining OpenSpec consistency issues. No implementation, public API, pilot,
or family scope was changed while resolving task 10.1. Tasks 10.2+ and the
final integrated verification were not started.

## Phase 6.2 task 10.2 final public discovery evidence

Task 10.2 was run without changing implementation or public API files. The
focused inventory command was run from both the immutable baseline worktree
and the current tip:

```sh
uv run pytest tests/unit/resources/test_operations.py -k \
  'discovered_public_methods or discovered_cli_surface_has_normalized_options_parity or \
   changed_public_surface_is_explicit_and_command_parity or \
   approved_symbols_signatures_and_canonical_vectors_are_complete' -q
```

It selected the same nine inventory/parity tests in each checkout: baseline
`9 passed, 336 deselected` from 345 collected; current tip `9 passed, 337
deselected` from 346 collected. The one extra collected test is a previously
accepted phase test and does not change the selected public inventory.

The exact discovery comparison command was the following inline Python
projection, run once from each checkout (the command emits counts and stable
SHA-256 digests of the sorted/discovered and ordered rows):

```sh
uv run python - <<'PY'
import hashlib, inspect, json, pathlib, typing
import multica_py
from tests.cases.operations import OPERATION_CASES, discover_public_methods
from tests.unit.resources.test_operations import _case_class
from tools.upstream_contract.contract import validate_contract

contract = validate_contract(pathlib.Path("contracts/sdk-contract.json"))
canonical = tuple(c for c in OPERATION_CASES if c.is_canonical)
def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
def signatures(fn):
    return tuple(str(inspect.signature(f).replace(return_annotation=inspect.Signature.empty))
                 for f in (typing.get_overloads(fn) or (fn,)))
def returns(fn):
    return tuple(repr(typing.get_type_hints(f).get("return"))
                 for f in (typing.get_overloads(fn) or (fn,)))
pairs = [(c.sdk_method, signatures(getattr(_case_class(c), c.method)),
          signatures(getattr(_case_class(c), c.method + "_command"))) for c in canonical]
annotations = [(c.sdk_method, returns(getattr(_case_class(c), c.method)),
                returns(getattr(_case_class(c), c.method + "_command"))) for c in canonical]
rows = [(c.id, c.sdk_method, c.method, c.contract_operation_id, c.expected_category,
         c.expected_response_id, c.expected_typed_input_id, c.expected_input_mode,
         c.presence_policy_ids) for c in canonical]
entrypoints = [(o.operation_id, e.entrypoint_id, e.public_symbol, e.command_symbol,
                e.signature_id, e.category, e.response_id, e.typed_input_id,
                e.input_mode, e.presence_policy_ids)
               for o in contract.operations for e in o.entrypoints]
print(json.dumps({
  "discovered": (len(discover_public_methods()), digest(sorted(discover_public_methods()))),
  "canonical_rows": (len(rows), digest(rows)),
  "normalized_signatures": (len(pairs), digest(pairs)),
  "return_annotations": (len(annotations), digest(annotations)),
  "generated_entrypoints": (len(entrypoints), digest(entrypoints)),
  "root_exports": (len(multica_py.__all__), digest(sorted(multica_py.__all__))),
  "operation_cases": len(OPERATION_CASES),
}, sort_keys=True))
PY
```

The baseline and current outputs were byte-for-byte equal for every recorded
inventory:

| Public discovery inventory | Baseline | Current tip | Comparison |
| --- | --- | --- | --- |
| Eager/command discovered methods | 163; `0cc4fe3de710419c1e867e2cfb0e4802353a8aac5e11f128b54ef96c50b46aef` | 163; `0cc4fe3de710419c1e867e2cfb0e4802353a8aac5e11f128b54ef96c50b46aef` | identical |
| Canonical operation rows | 163; `634c27c3bf0e99746095a82b120b5e5e32bef547ba88c431d40057b9d7b7a3ae` | 163; `634c27c3bf0e99746095a82b120b5e5e32bef547ba88c431d40057b9d7b7a3ae` | identical |
| Normalized eager/command signatures | 163; `356daed2d9f3e3c0b26a2aa58e194ec5a984d41fbe059a8190ebb05810bbacde` | 163; `356daed2d9f3e3c0b26a2aa58e194ec5a984d41fbe059a8190ebb05810bbacde` | identical |
| Return annotations | 163; `6749521bd1b00a4a1c24c0086ba519049450c227ef3db076c09f7eb247cded91` | 163; `6749521bd1b00a4a1c24c0086ba519049450c227ef3db076c09f7eb247cded91` | identical |
| Approved generated entrypoints | 142; `a899966dcdf375f17c2ff6a95112942e764efaec8df428b824c3a1235407428f` | 142; `a899966dcdf375f17c2ff6a95112942e764efaec8df428b824c3a1235407428f` | identical |
| Root `multica_py.__all__` exports | 49; `bd96454d5136c32b749d3f78f3735d0869972132c747fe84a51bef26a336a629` | 49; `bd96454d5136c32b749d3f78f3735d0869972132c747fe84a51bef26a336a629` | identical |
| Canonical/total operation rows | 163 / 289 | 163 / 289 | identical |

The approved contract has 139 operation IDs and 142 generated entrypoints in
both projections. Thus final public discovery, canonical rows, normalized
signatures, return annotations, generated entrypoints, and root exports are
closed against the recorded immutable baseline. Tasks 10.3+ and the final
gate were not started.

## Phase 6.3 task 10.3 focused public-behavior evidence

Task 10.3 ran only focused public-behavior matrices at the accepted discovery
tip. Collection was verified before execution with these exact commands:

```sh
uv run pytest tests/unit/resources/test_bound_entity.py \
  tests/contract/test_bound_public_surface.py \
  tests/contract/test_entity_relocation.py --collect-only -q
# 223 tests collected
uv run pytest tests/unit/resources/test_agent_skill_squad_relations.py \
  tests/unit/resources/test_autopilot_relations.py \
  tests/unit/resources/test_issue_relations.py \
  tests/unit/resources/test_project_relations.py \
  tests/unit/resources/test_relations.py \
  tests/unit/resources/test_workspace_relations.py \
  tests/unit/resources/test_workspace_relations_extra.py --collect-only -q
# 279 tests collected
uv run pytest tests/unit/test_command_options.py tests/unit/test_transport.py \
  --collect-only -q
# 144 tests collected
uv run pytest tests/unit/resources/test_attachments.py \
  -k 'temporary or temp or cleanup' --collect-only -q
# 9/53 tests collected (44 deselected)
uv run pytest tests/unit/test_process_lifecycle.py --collect-only -q
# 33 tests collected
uv run pytest tests/contract/test_sdk_contract.py \
  tests/unit/test_upstream_contract.py tests/unit/resources/test_operations.py \
  -k 'sdk_contract or render_is_independent or \
      public_conventions_and_response_catalog_are_typed_and_closed or \
      generated_runtime_tracks_target_and_copy_search_descriptors or \
      current_payload_fingerprint or discovered_public_methods or \
      approved_symbols_signatures_and_canonical_vectors_are_complete' \
  --collect-only -q
# 10/423 tests collected (413 deselected)
```

The same focused commands then ran in one fail-fast sequence:

```sh
uv run pytest tests/unit/resources/test_bound_entity.py \
  tests/contract/test_bound_public_surface.py \
  tests/contract/test_entity_relocation.py -q
# 223 passed in 14.05s
uv run pytest tests/unit/resources/test_agent_skill_squad_relations.py \
  tests/unit/resources/test_autopilot_relations.py \
  tests/unit/resources/test_issue_relations.py \
  tests/unit/resources/test_project_relations.py \
  tests/unit/resources/test_relations.py \
  tests/unit/resources/test_workspace_relations.py \
  tests/unit/resources/test_workspace_relations_extra.py -q
# 279 passed in 2.31s
uv run pytest tests/unit/test_command_options.py tests/unit/test_transport.py -q
# 144 passed in 1.52s
uv run pytest tests/unit/resources/test_attachments.py \
  -k 'temporary or temp or cleanup' -q
# 9 passed, 44 deselected in 0.17s
uv run pytest tests/unit/test_process_lifecycle.py -q
# 33 passed in 2.62s
uv run pytest tests/contract/test_sdk_contract.py \
  tests/unit/test_upstream_contract.py tests/unit/resources/test_operations.py \
  -k 'sdk_contract or render_is_independent or \
      public_conventions_and_response_catalog_are_typed_and_closed or \
      generated_runtime_tracks_target_and_copy_search_descriptors or \
      current_payload_fingerprint or discovered_public_methods or \
      approved_symbols_signatures_and_canonical_vectors_are_complete' -q
# 10 passed, 413 deselected in 1.05s
```

The entity matrix covers schema-derived field policy, serialization,
immutability, equality/hash/repr, detach/rebind, and public boundaries. The
relation matrix covers lazy/cache/coalescing, invalidation, concurrency,
offset and cursor pagination, no-progress and budget guards, metadata, and
detached behavior. Command/options/transport covers immutable option
snapshots, preview/execution identity, zero-I/O transformations, redaction,
transport error mapping, timeout, and spawn/execution failures. The
attachment subset covers temporary-file cleanup on success and failure. The
process matrix covers cancellation, timeout, pipe cleanup, streaming,
finalization, retry, close, and result lifecycle.

The final contract/fingerprint matrix passed the retained/reverted pilot
decision checks: approved contract/runtime projection remained valid,
deterministic render remained independent of evidence, current-ID
fingerprints and canonical discovery remained closed, and no generated pilot
runtime changes were introduced after rollback checkpoint
`2aa6df99ff0afbb4015da4232dfd30dee5ccc725`. No public API or implementation
file changed in task 10.3; tasks 10.4+ and the final gate were not started.

## Phase 6.4 task 10.4 final complete gate evidence

Task 10.4 ran the complete task-1.3 gate at implementation tip
`9ea828a37c6330f55a50e5879358de9c3781d41b`, which is a descendant of the
planning commit. The immutable baseline remained
`e719de13442841c64ed96855c5227bbe5e173f10`; `HEAD` was not reset to it. The
exact commands and results were:

```sh
uv run openspec validate simplify-sdk-architecture --strict --json
# valid: true, issues: [], summary 1 passed / 0 failed, exit 0
uv run ruff check .
# All checks passed!; exit 0
uv run ruff format --check .
# 162 files already formatted; exit 0
uv run mypy src
# Success: no issues found in 70 source files; exit 0
uv run mypy tests
# Success: no issues found in 79 source files; exit 0
uv run pytest -m 'not live'
# 1892 passed, 6 deselected in 72.57s (0:01:12); exit 0
uv run pytest -m 'not live' --collect-only -q
# 1892/1898 tests collected (6 deselected); no tests/live/* nodes; exit 0
uv run python scripts/upstream_contract.py validate \
  --approved contracts/sdk-contract.json \
  --source-checkout /Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/upstream-multica-v0.4.20
# exit 0 against exact pinned upstream source checkout
uv run python scripts/upstream_contract.py check \
  --approved contracts/sdk-contract.json
# exit 0
git diff --check
# exit 0
uv run pytest tests/unit/resources/test_operations.py::test_discovered_public_methods -q
# 1 passed in 0.41s; exit 0
```

The collection command wrote its output to a temporary log and explicitly
searched for `tests/live/`; the search found no live nodes (`live_nodes=0`).
The gate was fail-fast and every command exited successfully.

Compared with the immutable baseline gate recorded in the baseline section:

| Gate evidence | Immutable baseline | Final implementation tip | Comparison |
| --- | --- | --- | --- |
| Ruff check | exit 0 | `All checks passed!`, exit 0 | green |
| Ruff format | exit 0 | `162 files already formatted`, exit 0 | green |
| Source typing | 72 files, exit 0 | 70 files, exit 0 | two accepted Phase 0 dead modules remain removed |
| Test typing | 79 files, exit 0 | 79 files, exit 0 | unchanged |
| Offline pytest | `1856 passed, 6 deselected` | `1892 passed, 6 deselected` | +36 accepted tests, zero failures |
| Offline collection | `1862 collected, 1856 selected, 6 deselected` | `1898 collected, 1892 selected, 6 deselected` | six deselected in both; zero live nodes in final |
| Pinned-source contract validation | exit 0 against pinned checkout | exit 0 against `/Users/admin/multica_workspaces_codex-2/c64973be-7715-492a-8c84-c6263cb8163a/4dd3d699/upstream-multica-v0.4.20` | unchanged green |
| Approved contract check | exit 0 | exit 0 | unchanged green |
| Diff whitespace | exit 0 | exit 0 | unchanged green |
| Public discovery guard | `1 passed` | `1 passed` | unchanged |

The final gate preserves the recorded baseline behavior and the retained
stop/go decision: the generated-builder pilot remains reverted, descriptor-only
generation and the manual `squads.members` family remain, and no new family or
public API was introduced. This task changed only `tasks.md` and
`pilot-evidence.md`; task 10.5 and no later implementation work were started.

## Phase 6.5 task 10.5 final outputs and handoff

Task 10.5 was completed from the accepted task 10.4 checkpoint
`990199fdc36b6ad2dc1f692b3f4afb80ead9dbd5`. The final outputs are the complete
task-1.3 gate recorded in Phase 6.4 and the focused public-behavior matrices
recorded in Phase 6.3. Their exact commands and results remain unchanged:

| Final output | Result | Baseline comparison |
| --- | --- | --- |
| Strict OpenSpec | `valid: true`, `issues: []`, `1 passed / 0 failed`, exit 0 | baseline and final valid with zero issues |
| Ruff lint/format | `All checks passed!`; `162 files already formatted`; exit 0 | unchanged green |
| Mypy | `src`: 70 files; `tests`: 79 files; no issues | baseline `72`/`79`; two accepted Phase 0 dead modules remain removed |
| Offline pytest | `1892 passed, 6 deselected` in 72.57s; exit 0 | baseline `1856 passed, 6 deselected`; +36 accepted tests, zero failures |
| Offline collection | `1898 collected`, `1892 selected`, `6 deselected`; `live_nodes=0`; exit 0 | baseline `1862/1856`; no live nodes in either offline gate |
| Pinned-source contract validation/check | both exit 0; validation used exact pinned upstream checkout | unchanged green |
| Public discovery | `1 passed`; focused matrices all green | discovered public set and inventories remain identical |

The complete final-gate command set is the one reproduced verbatim in the
Phase 6.4 section above. No additional final gate was run for task 10.5.

### Final LOC and diff totals

These totals use newline counts from the tracked files at the immutable
baseline and final implementation tip. They are reproducible with
`git ls-files` plus `wc -l` from the repository root:

| Scope | Immutable baseline | Final tip | Delta |
| --- | ---: | ---: | ---: |
| Production (`src`) | 73 files / 13,288 LOC | 70 files / 13,207 LOC | -3 files / -81 LOC |
| Tests (`tests`) | 84 files / 24,027 LOC | 77 files / 24,090 LOC | -7 files / +63 LOC |
| Production + tests | 157 files / 37,315 LOC | 147 files / 37,297 LOC | -10 files / -18 LOC |

The full tracked implementation diff from immutable baseline
`e719de13442841c64ed96855c5227bbe5e173f10` to the accepted task 10.4 tip
`990199fdc36b6ad2dc1f692b3f4afb80ead9dbd5` is `48 files changed, 2,747
insertions(+), 1,074 deletions(-)`, or `+1,673` net lines including the
OpenSpec, contract, generated, test, and evidence artifacts. The task 10.5
checkpoint adds only `tasks.md` and `pilot-evidence.md`; it adds no source,
test, dependency, or public-API files.

### Complete checkpoint ledger

The recoverable ancestry and phase tips are pinned as follows:

| Scope | Tasks / purpose | Checkpoint |
| --- | --- | --- |
| Immutable baseline | comparison reference | `e719de13442841c64ed96855c5227bbe5e173f10` |
| Planning | OpenSpec plan descendant | `2ff0fd954851b9125ea3adba39696c00a57e8eab` |
| Phase 0 guard | 2.1–2.5 current-ID fixture | `52634ea98e09c11eb1685a98e35611960ce32eb7` |
| Phase 0 cleanup gate | 3.1–3.5 | `c0110e671a7f1eb8c9c2e032bbbb425b9da57536` |
| Phase 1 | 4.1–4.5 option ownership | `7d764e522cf1dad83b7762aaf8eec141835fa276` |
| Phase 2 policy | 5.1–5.4 field policy | `559900f36008a052edac32b927a50212bb1f501f` |
| Phase 2 gate | 5.5–5.8 relation seeds and policy gate | `cfd2d993850d56793e3a0b40f67c23d2f23f72b0` |
| Phase 3 | 6.1–6.7 shared generation state | `80c83d80707dc88479fd1a835a19fb9d8ba8f482` |
| Phase 4 composition | 7.1–7.3 | `1cf6bde97270e0d360e5cfce7f80b91b71b44d58` |
| Phase 4 pagination/boundary | 7.4–7.6 | `1e23d9774e82574c1fbf58fe4387f41eb65ca312` |
| Phase 4 focused/gate | 7.7–7.8 | `d06844313cf599681adb9794b3a65d670696e08e` |
| Phase 4.7 measurement | 8.1–8.2 | `5e7e84f26f0acd185073b6c62c374835d825e39e` |
| Phase 5.1 | 9.1–9.2 bounded generator builders | `e1381b36715c2daaa2d4a754d63eb2817a7a6b2f` |
| Phase 5.2 | 9.3–9.4 resource delegation | `9589e5a4f9ce8bf2ddb5c70f9710eef317bd7310` |
| Phase 5.3 | 9.5 deterministic render/check | `cc1ab3cd8e9879025cf63d4176dc85f70583440b` |
| Phase 5.4 | 9.6–9.7 pilot rollback | `2aa6df99ff0afbb4015da4232dfd30dee5ccc725` |
| Phase 5.5 | 9.8 complete Phase-5 gate | `0cd0e300ad34f9c741edbf2ac81b09f1667b6991` |
| Phase 6.1 | 10.1 strict consistency validation | `91128aae35b87b05cfe137374a1efc9305ae1e38` |
| Phase 6.2 | 10.2 final public discovery | `8e80833ed65fe94cabab55861bdd318d177b79d0` |
| Phase 6.3 | 10.3 focused behavior matrices | `9ea828a37c6330f55a50e5879358de9c3781d41b` |
| Phase 6.4 | 10.4 complete final gate | `990199fdc36b6ad2dc1f692b3f4afb80ead9dbd5` |
| Phase 6.5 | 10.5 final handoff (this checkpoint) | recorded after commit |

### Deferred decisions and explicit scope closure

- The generated-builder pilot remains reverted under the stop/go rule because
  it added concepts and produced no measurable net deletion. Only the manual
  `squads.members` family remains; no next family is eligible or implemented.
- The lifecycle pilot remains deferred. A future, separate OpenSpec proposal
  may consider only `Issue.comments` and must first satisfy the named deletion
  criteria in the Phase 4.7 evidence; no lifecycle abstraction was added here.
- No new runtime or development dependency was added, and no public API,
  public signature, return annotation, root export, or canonical operation row
  was changed. The final public discovery and parity inventories remain
  byte-for-byte equal to the pinned baseline.
- No further pilot/family expansion, implementation change, or additional
  final gate was started in task 10.5.

## Comparison policy and handoff boundary

The pinned baseline worktree and revision above are the comparison reference
for all later inventories, fingerprints, LOC totals, and phase gates. Later
phase gates must run at the then-current phase tip, which must remain a
descendant of planning commit `2ff0fd954851b9125ea3adba39696c00a57e8eab`;
they must not reset `HEAD` to the baseline. Phase 0, Phase 1, Phase 2,
Phase 3, and Phase 4 (tasks 7.1–7.8) are complete; the measurement-only
Phase 4.7 (tasks 8.1–8.2) is complete; Phase 5.1 (tasks 9.1–9.2) and
Phase 5.2 (tasks 9.3–9.4), Phase 5.3 (task 9.5), and Phase 5.4
(tasks 9.6–9.7) are now complete. The pilot was reverted by the stop/go rule;
the Phase 5 gate (task 9.8) is complete on the rollback tip. Tasks 10.1 and
10.2 are complete with strict OpenSpec and public discovery evidence green;
task 10.3 is complete with all focused public-behavior matrices green; task
10.4 is complete with the final complete gate green and baseline comparison
recorded; task 10.5 is complete with final outputs, LOC/diff totals, the full
checkpoint ledger, and deferred decisions recorded above. No additional
implementation or public API work was started. Work stops here for Manager
acceptance of the task 10.5 checkpoint.
