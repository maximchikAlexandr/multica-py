# Implementation Plan: Reduce Non-Production Complexity

**Branch**: `008-reduce-nonprod-complexity` | **Date**: 2026-07-25 |
**Spec**: [spec.md](./spec.md)

**Input**: Feature specification from
`/specs/008-reduce-nonprod-complexity/spec.md`

## Summary

Remove at least 20,000 tracked physical non-production lines by replacing historical
Spec Kit records, test-architecture governance, duplicate operation catalogs,
the SDK-owned backend sandbox, and the upstream promotion state machine with
four small boundaries:

1. four OpenSpec-compatible baseline specifications containing active
   requirements from features 001–006;
2. `contracts/sdk-contract.json` as the sole approved input to deterministic
   SDK generation;
3. one committed runtime projection plus exactly three transient render
   projections (docs, compatibility report, provenance report); evidence is
   collect output and operation cases exist only in memory;
4. one canonical offline operation table, three real-process cases, and five
   live smoke scenarios against an externally prepared target.

Git review and merge is the only promotion action. No candidate/supported
state, promotion/recovery journal, upgrade bundle, rename suggestion, observer
state, full-output golden snapshot, or CI-workflow text test remains.

## Technical Context

**Language/Version**: Python 3.12 and 3.13; GitHub Actions YAML; Markdown
requirements.

**Primary Dependencies**: Runtime `msgspec>=0.19,<2`; development `pytest`,
`pytest-cov`, `pytest-xdist`, `pytest-timeout`, Ruff, and mypy. Remove the test
dependency `httpx`; add no dependency.

**Storage**: Reviewed JSON contract, one committed generated Python module,
OpenSpec-compatible Markdown baselines, transient evidence/output directories,
and Git history.

**Testing**: One parametrized unit executor over the canonical operation table;
focused decoder/validation/error tests; exactly three fake-executable process
cases; package tests; five manual live smoke scenarios; ordinary coverage
thresholds.

**Target Platform**: Offline checks on Linux and macOS with Python 3.12/3.13.
Live smoke runs manually on a self-hosted runner labelled `multica-live` whose
CLI, authenticated profile, server, and workspace already exist.

**Project Type**: Single-package synchronous Python SDK plus repository-local
maintainer tooling.

**Performance Goals**: Default offline verification requires no network and
does not execute the same complete operation through two mocked success
harnesses. Generator output is byte-identical across two clean renders. Live
smoke has five collected tests and a 10-minute workflow timeout.

**Constraints**:

- Public SDK behavior, supported platforms, and runtime dependencies do not
  regress.
- The approved contract is the only generator decision input.
- Unknown extraction patterns become review items and cannot update public
  code.
- Runtime generated code is one committed module. Every other generated
  projection is transient.
- Source evidence, credentials, review reports, and build outputs are ignored
  by Git.
- OpenSpec is not installed or initialized in this feature.
- Mutation policy, package-install matrix, mypy scope, and cache cleanup are
  unchanged.

**Scale/Scope**: Six historical feature directories; 16 approved-contract
operation IDs; 135 preserved offline argv rows (111 canonical public-method
rows plus 24 noncanonical rows; 30 generated vectors = 19 entrypoint-base
vectors plus 11 entrypoint variants, and 105 manual rows = 95 canonical public
methods plus 10 variants); five live
smoke tests; three process cases; at least 20,000 tracked physical
non-production lines removed.

## Constitution Check

*GATE: evaluated before research and re-evaluated after Phase 1 design.*

| Principle | Required design response | Pre-research | Post-design |
| --- | --- | --- | --- |
| I. Source-Driven CLI Contract | Retain pinned source refs, declarative extraction, fail-closed review items, approved mappings, presence semantics, and contract validation. | PASS | PASS |
| II. Thin Synchronous Wrapper | Delete direct backend HTTP clients and control-plane orchestration; live smoke uses only public SDK calls plus the CLI version probe. | PASS | PASS |
| III. Typed Public Surface | Generate typed bindings/enums/validators into one module; keep handwritten decoding and multi-step workflows; expose no `Any`. | PASS | PASS |
| IV. Offline Testability and Provenance | Keep the default suite offline, one complete argv record per public operation, decoder/error/process/package tests, and source refs in the approved contract. | PASS | PASS |
| V. Secure Packaging and Release | Keep package/release gates and redaction tests; remove `httpx`; compare the committed runtime projection during build validation. | PASS | PASS |

**Governance transition**: current test-architecture and deletion-ledger rules
are the feature's removal target, not retained product requirements. The first
implementation change MUST atomically remove those rules from `AGENTS.md`,
`README.md`, and CI together with their scripts, ledgers, and tests. Git
preserves the removed node history; no new entry is added to a ledger deleted
by that same change.

**Gate result**: PASS. No constitution exception is required.

## Project Structure

### Documentation (this feature)

```text
specs/008-reduce-nonprod-complexity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
├── contracts/
│   ├── generation.md
│   ├── historical-baseline.md
│   ├── reduction-map.md
│   └── verification.md
└── tasks.md                       # created by /speckit-tasks
```

### Resulting Repository Layout

```text
openspec/
└── specs/
    ├── sdk-surface/spec.md
    ├── subprocess-transport/spec.md
    ├── upstream-contract/spec.md
    └── verification-and-release/spec.md

contracts/
└── sdk-contract.json              # sole approved generator input

src/multica_py/
├── _generated/
│   └── approved_sdk.py            # sole committed runtime projection
├── _internal/
│   ├── compat.py                  # reads generated version constants
│   └── transport.py
├── resources/
├── models/
└── enums.py                       # re-exports generated enums

tools/upstream_contract/
├── __init__.py
├── cli.py                         # validate, collect, render, check
├── contract.py                    # closed schema + validation
├── evidence.py                    # declarative extraction + review items
└── generation.py                  # runtime and transient renderers

scripts/
└── upstream_contract.py           # thin repository entrypoint

tests/
├── cases/
│   ├── operations.py              # sole success operation table
│   └── errors.py                  # distinct negative/error rows
├── unit/
│   ├── resources/test_operations.py
│   ├── test_upstream_contract.py
│   └── focused model/transport/error tests
├── component/
│   └── test_process_contract.py   # exactly three process cases
├── contract/
├── packaging/
└── live/
    ├── README.md
    ├── conftest.py
    └── test_smoke.py              # exactly five scenarios

.github/workflows/
├── ci.yml                         # offline product checks
├── live-smoke.yml                 # manual prepared-target check
├── mutation.yml                   # unchanged by this feature
├── package-test.yml               # unchanged in scope
└── release.yml
```

**Structure Decision**: Move maintainer-only upstream tooling out of the
installed package into `tools/upstream_contract`. Keep generated runtime code
inside the package as one reviewable module. Use `openspec/specs` only for
baseline Markdown; do not create OpenSpec configuration, changes, commands, or
agent integration.

## Binding Decisions

### Generated artifacts

`contracts/sdk-contract.json` is the only reviewed generator input.
`src/multica_py/_generated/approved_sdk.py` is the only committed generated
output and exports, in stable order:

- `TARGET_VERSION`, `MIN_CLI_VERSION`, `MAX_CLI_VERSION`;
- generated enums;
- immutable binding descriptors;
- validator functions.

The generator materializes operation cases only in memory and renders exactly
`docs/approved-sdk.md`, `reports/compatibility.json`, and
`reports/provenance.json` into a caller-supplied temporary directory. Tests
consume these bytes from memory or that directory; none is committed. `check`
fails when the committed runtime module is missing
or differs by one byte. Two render calls in separate temporary directories
must have identical relative paths and bytes.

### Upstream review workflow

The only maintainer sequence is:

1. `collect` reads a pinned source checkout and verified binary and writes
   declarative evidence plus review items under a caller-supplied ignored
   directory.
2. A maintainer edits `contracts/sdk-contract.json` in a PR.
3. `validate` checks the closed contract, source refs, mappings, presence,
   enums, constraints, and unresolved markers.
4. `render` updates the one runtime module and writes exactly
   `docs/approved-sdk.md`, `reports/compatibility.json`, and
   `reports/provenance.json` to its required ignored output directory.
5. `check` validates the contract, rerenders twice, compares the committed
   runtime projection, compiles Python projections, validates JSON/Markdown
   projections, and checks package import.
6. PR review and merge promotes the contract. There is no other promotion
   state or action.

### Verification ownership

`tests/cases/operations.py::OPERATION_CASES` contains every supported public
operation and every variant needed for argv/presence/transport behavior.
`tests/unit/resources/test_operations.py::test_operation` is its only generic
success executor and asserts the complete transport call, including method,
argv, stdin, and timeout. Decoder rows exist only for distinct response shapes.
Component coverage is limited to the three process boundaries defined in
[verification.md](./contracts/verification.md).

The live workflow never provisions Docker, downloads/builds the CLI, creates a
workspace, calls the backend directly, or runs an agent sandbox. It validates
the five scenarios in [verification.md](./contracts/verification.md) against a
prepared authenticated profile.

## Implementation Sequence

The order below is mandatory because every deletion follows an installed
replacement.

### Phase A — Retain active knowledge

1. Create the four baseline specifications defined in
   [historical-baseline.md](./contracts/historical-baseline.md).
2. Add the source-to-baseline trace table and prove every active item listed in
   that contract has one destination requirement and scenario.
3. Replace all live references to `specs/001-*` through `specs/006-*` in
   `AGENTS.md`, `README.md`, `docs/cli-coverage.md`, `docs/releasing.md`, and
   `scripts/audit_source_links.py`.
4. Delete the six historical directories. Do not delete feature 007 or 008.

**Gate A**: the exact `git grep` command in `historical-baseline.md` returns no tracked match; all four baseline
specs satisfy the required heading/scenario grammar; default offline tests
pass.

### Phase B — Install canonical operation replacement

5. Convert `ArgvSpec` into the frozen `OperationCase` in
   `tests/cases/operations.py`, preserving every existing argv variant and
   stable pytest ID. Move only distinct error rows to `tests/cases/errors.py`.
6. Make `tests/unit/resources/test_operations.py` the sole generic success
   executor. Remove the mock component round-trip and live policy catalog.
7. Reduce `tests/component/test_process_contract.py` to the three exact
   process rows, then delete fake-OpenCode and fake-CLI self-tests not used by
   those rows.

**Gate B**: `discovered_public_methods == {case.sdk_method for case in
OPERATION_CASES if case.is_canonical}`; there are 111 unique canonical public
methods, 135 unique case IDs, and 24 noncanonical variants; every row asserts
a full transport call; decoder/presence/error tests pass; exactly three process
case IDs collect.

### Phase C — Retire test meta-governance

8. In one change, remove the test-architecture, LOC-budget, baseline,
   historical-node, registry-count, and duplicate-removal rules and all exact
   files listed under group B in
   [reduction-map.md](./contracts/reduction-map.md).
9. Replace them with one completeness assertion:
   `discovered_public_methods == {case.sdk_method for case in OPERATION_CASES
   if case.is_canonical}`. It also asserts 111 unique canonical public methods,
   135 unique case IDs, and 24 noncanonical variants; retain existing zonal
   coverage thresholds and standard pytest marker selection.
10. Remove five-stage invocations from `.github/workflows/ci.yml`; run the
   offline suite once in the parallel pass and once for the existing serial
   process marker as required by current coverage collection.

**Gate C**: the deleted filenames have no tracked references; `pytest
--collect-only -m "not live"` collects zero `tests/live` nodes; Ruff, mypy,
coverage, and offline pytest pass.

### Phase D — Simplify upstream generation

11. Create `tools/upstream_contract` and copy only closed contract validation,
    declarative evidence extraction, deterministic rendering, and the four
    commands into it. Tests must be green before deleting the old package.
12. Render `approved_sdk.py`; change `enums.py`, `compat.py`, and governed
    resources to import it. The compatibility interval is exact
    `[TARGET_VERSION, next_patch(TARGET_VERSION))`, rendered as constants.
13. Update `.gitignore`: unignore `approved_sdk.py`; ignore
    `.devlocal/upstream-contract/**`; remove obsolete generated-output rules.
14. Delete state/promotion/diff/observer/suggestion/upgrade/reporting artifacts,
    commands, workflows, fixtures, and tests listed under group D.
15. Delete full generated goldens and replace their assertions with
    determinism, compilation, semantic-invariant, drift, and built-wheel import
    checks.

**Gate D**: only `contracts/sdk-contract.json` can drive rendering; `collect`
cannot write it; `check` fails for a missing or changed runtime projection;
two clean renders match; all transient outputs are untracked; built wheel
imports generated enums/bindings/validators and compatibility constants.

### Phase E — Replace live ownership

16. Add the prepared-target fixture and five tests first.
17. Add manual `.github/workflows/live-smoke.yml` using runner labels
    `[self-hosted, multica-live]`, the exact required environment contract, and
    a 10-minute timeout.
18. Delete direct HTTP/backend/compose/sandbox/oracle/diagnostics orchestration,
    their unit tests, extended/canary workflows, and the `httpx` test
    dependency.
19. Remove every test that parses or regex-checks workflow YAML. Keep workflow
    correctness observable through actual jobs and branch protection, not
    repository pytest.

**Gate E**: default suite is network-free; `uv lock --check` and offline gates
pass without `httpx`; exactly five live tests collect under `live_smoke`.
There is no automated assertion about workflow YAML content. The manual CI-008
evidence record in [verification.md](./contracts/verification.md) is required
for review. Updating `specs/007-upstream-v0-4-9-migration/` removes only its
references to retired commands and flows; it does not alter a product requirement.

### Phase F — Final reduction proof

20. Record baseline/final tracked physical-line counts using the exact Git-object command
    in the PR description; do not add a permanent LOC
    script or checked-in baseline.
21. Run the quickstart verbatim and remove all stale documentation references.

**Gate F**: tracked non-production physical lines fall by at least 20,000;
public API comparison, offline verification, package verification, generator
check, and manual live collection all pass.

## Complexity Tracking

No constitution violations or retained complexity exceptions.

## Review-closed execution rules

The source baseline is immutable tree `b3a299b36d1ad5bc386b5e4517d2a348d53db31c`; the final object is the staged tree returned by `git write-tree` after `git add -A`. For each tree `TREE`, count tracked physical lines with `git ls-tree -r --name-only "$TREE" -- tests scripts tools .github specs contracts openspec | rg '\.(py|md|json|toml|ya?ml|sh)$' | while IFS= read -r path; do git show "$TREE:$path"; done | wc -l`. The identical roots deliberately include absent baseline `openspec` as zero. Exclude lockfiles and binaries by the extension filter. The final total must be at least 20,000 below baseline.

CI disposition is fixed: `ci.yml` retains jobs `lint`, `types`, `quality`, and `compatibility`; its `upstream-check` becomes `contract-check`; its `live-smoke` job is deleted. Workflows `mutation.yml`, `package-test.yml`, and `release.yml` remain; workflows `live-extended.yml`, `live-opencode-canary.yml`, `upstream-contract-observer.yml`, and `upstream-drift.yml` are deleted; manual `live-smoke.yml` is added. `quality` retains its current mutation step because mutation policy is out of scope. The only remaining custom pytest markers are `unit`, `contract`, `component`, `packaging`, `process`, `compat`, `serial`, `live`, and `live_smoke`; remove `live_extended`, `live_opencode_canary`, `destructive`, and the architecture marker/path validator. `tests/conftest.py` assigns only the first four layer markers by path; process/live modules declare their complete module-level marker lists.

Every phase uses the one deletion reference command in `historical-baseline.md`; no gate invokes broad `rg` over feature-008 artifacts. Phase D also runs the wheel test in `verification.md`; Phase E uses reviewer checklist `CI-008`, not an automated YAML parser.
