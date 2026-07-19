# Implementation Plan: Test Suite Optimization

**Branch**: `004-test-suite-optimization` | **Date**: 2026-07-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-test-suite-optimization/spec.md`

## Summary

Refactor the `tests/` tree (~11,170 lines, 493 collected tests) so mechanical
repetition collapses into shared, table-driven pytest parametrization while four
fail-on-gap completeness guards (three offline + one live-gated, plus one
non-guard extensibility outcome) turn the reduction into growing coverage. The work is purely
test/infrastructure code — no `src/multica_py` behavior changes. Approach:
(1) delete dead/tautological/duplicate tests, relocating the few genuine
assertions; (2) introduce shared fixtures + case tables for unit resource tests,
integration fake-CLI tests, and maintainer upstream-contract tests; (3)
parametrize contract-diff severity and the live suite (errors, presence, CRUD,
and full command execution); (4) consolidate test-infra unit tests; (5) enforce
coverage with three offline guards (manifest argv, JSON-fixture usage, integration
operation-coverage) and one live-gated guard (live command-execution, `-m live`
only). Only stdlib + pytest are used; no new dependency is added.

## Technical Context

**Language/Version**: Python 3.12 / 3.13 (repo targets `>=3.12`, mypy pinned to 3.12).

**Primary Dependencies**: runtime `msgspec` only; test group `pytest>=8`,
`pytest-cov>=5`, `httpx>=0.27` (all already present — no additions per FR-016).

**Storage**: N/A (test fixtures are JSON files under `tests/fixtures/json/`).

**Testing**: pytest with `-m "not live"` default selection, `--strict-markers`,
`filterwarnings=["error"]`; markers `live`, `live_smoke`, `live_extended`,
`destructive`, `serial`.

**Target Platform**: Linux and macOS CI (constitution SDK Constraints).

**Project Type**: Single-project Python SDK/library wrapping the Multica CLI.

**Performance Goals**: Non-live suite stays fast and deterministic; integration
suite must be safe under `pytest-xdist`-style parallel execution (no `os.environ`
mutation). CI runtime is a soft goal (no hard threshold): non-live wall-time
should not materially regress versus the pre-refactor baseline captured in
quickstart; it is not an acceptance gate.

**Constraints**: Offline-only default suite (Constitution IV); typed test helpers
must satisfy the relaxed-but-checked mypy override for `tests.*`; no third-party
test frameworks (FR-016); feature-002 security invariants preserved (FR-015).

**Scale/Scope**: ~2,800 line reduction across 8 targeted areas; migrate ~21 unit
resource files, 17 integration resource files, 10 contract model files, 6+
maintainer contract test modules, contract-diff tests, and 6 live/infra areas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Impact | Status |
| --- | --- | --- |
| I. Source-Driven CLI Contract | The new argv-completeness guard is driven by `load_manifest()` (the pinned-source-derived manifest); it strengthens source traceability rather than weakening it. | PASS |
| II. Thin Synchronous Wrapper | No SDK/runtime code changes; only tests. | PASS (N/A) |
| III. Typed Public Surface | Test helpers live under the `tests.*` mypy override (typed, `check_untyped_defs=true`); no `Any` leaks into `src`. Case-table structs use typed containers. | PASS |
| IV. Offline Testability and Provenance | Unit/integration/contract layers stay offline (mock transport, fake CLI, fixtures); the three offline guards bind fixtures/operations to the manifest. The live layer gains a command-execution guard (FR-021) that runs ONLY under `-m live`, so the default offline suite is unaffected and stays green without a backend. | PASS |
| V. Secure Packaging and Release | feature-002 security-invariant tests (secret redaction, argv-without-shell, `KEEP_ENV` ban, loopback-only URL) are explicitly out of scope for deletion (FR-015). | PASS |

**Quality Gates** (Development Workflow): Ruff format/check, strict mypy, unit,
contract, integration (fake exe), coverage audits must still pass after each user
story (FR-017). Each new guard test ships with the migration that introduces it.

**Result**: No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/004-test-suite-optimization/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── test-harness.md  # Fixture + case-table + guard contracts
├── checklists/
│   └── requirements.md  # From /speckit-specify
└── tasks.md             # Phase 2 output (/speckit-tasks - NOT created here)
```

### Source Code (repository root)

This feature only touches `tests/` and two config lines in `pyproject.toml`
(mypy overrides). `src/multica_py/**` is unchanged.

```text
tests/
├── conftest.py                       # unchanged (root)
├── contract/
│   ├── conftest.py                   # NEW: fake_upstream_cli, contract_cli, preserved_generated_state (US4)
│   ├── models/                       # DELETE entire dir (US1)
│   ├── test_upstream_contract_*.py   # REWRITE onto contract conftest (US4)
│   └── test_upstream_contract_diff.py# PARAMETRIZE severity table (US5)
├── integration/
│   ├── conftest.py                   # ADD fake_cli_client fixture (US3)
│   └── resources/
│       ├── test_fake_cli_operations.py  # NEW table module + fixture-usage & operation-coverage guards (US3)
│       └── test_*.py (17 files)         # DELETE after migration (US3)
├── unit/
│   ├── conftest.py                   # ADD make_target/make_settings factories (US7)
│   ├── resources/
│   │   ├── conftest.py               # NEW: mock_transport fixture + raw_result factory (US2)
│   │   ├── cases.py                  # NEW: ArgvCase / DecodeCase tables (US2)
│   │   ├── test_operations.py        # NEW: test_command_argv, test_decode, argv-completeness guard (US2)
│   │   ├── test_issues.py            # KEEP: absorb relocated mutually-exclusive assertions (US1)
│   │   ├── test_mutually_exclusive.py# DELETE after relocation (US1)
│   │   ├── test_labels.py            # DELETE tautological model default test (US1)
│   │   └── test_*.py (remaining)     # DELETE after case migration (US2)
│   ├── test_live_*.py                # MERGE tiny modules, share factories (US7)
│   ├── test_transport.py             # ABSORB test_transport_errors as table (US7)
│   ├── test_transport_errors.py      # DELETE after merge (US7)
│   └── test_upstream_contract_diff.py# PARAMETRIZE severity table (US5)
├── typing/                           # DELETE entire package (US1)
└── live/
    ├── crud_descriptors.py           # NEW: CRUD descriptor table (US6)
    ├── test_crud.py                  # NEW: parametrized round-trip (labels, projects) (US6)
    ├── live_operations.py            # NEW: live invocation registry + LIVE_EXEC_EXCEPTIONS (US6/FR-021)
    ├── test_live_command_coverage.py # NEW: execute every op live + FR-021 guard (-m live) (US6)
    ├── test_errors.py                # PARAMETRIZE error-mapping table (US6)
    ├── test_projects.py             # PARAMETRIZE presence semantics (US6)
    └── test_labels.py                # FOLD into crud_descriptors / test_crud (US6)
```

**Structure Decision**: Single-project layout is retained. All changes are
confined to `tests/` plus a two-line `pyproject.toml` mypy-override edit
(removing `tests.typing.*` and `tests.contract.models.*`). The manifest at
`src/multica_py/_generated/cli_manifest.json` and the fixtures at
`tests/fixtures/json/**` are read-only inputs to the new guards.

## Implementation Sequencing

The authoritative implementation order is the numeric user-story order
**US1 → US2 → US3 → US4 → US5 → US6 → US7** (this matches spec.md Assumptions).
The source ticket suggested a different order (`1 → 2 → 4 → 3 → 6 → 8 → 5 → 7`);
that ticket order is historical context only and is NOT binding — where they
differ, the US order above wins. Each user story leaves the non-live suite green
(FR-017) and is independently mergeable. The four fail-on-gap coverage guards
ship with their tables: unit argv-completeness (FR-005) with US2, both the
JSON-fixture-usage (FR-008) and integration operation-coverage (FR-020) guards
with US3, and the live command-execution guard (FR-021) with US6. The three
offline guards use `KNOWN_ARGV_GAPS` / `KNOWN_FIXTURE_GAPS` allowlists to stay
green while coverage grows; the live guard uses `KNOWN_LIVE_GAPS` (not-yet-automated,
goal empty) plus `LIVE_EXEC_EXCEPTIONS` (permanently unrunnable, with reason codes),
runs the guard under `-m live_smoke` and full execution under `-m live_extended`,
so it never affects the offline suite. `KNOWN_LIVE_GAPS` is seeded mechanically per
spec.md Appendix E; every new `tests/live/*` module MUST set a module-level
`pytestmark` including base `pytest.mark.live` (markers do not inherit in this repo).

## Complexity Tracking

No constitution violations; table intentionally omitted.
