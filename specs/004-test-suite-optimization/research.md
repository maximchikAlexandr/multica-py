# Phase 0 Research: Test Suite Optimization

No `NEEDS CLARIFICATION` markers remained in the Technical Context. Research here
records the design decisions that shape the refactor, each grounded in the
current test code.

## R1. Table-driven parametrization vs per-file tests

- **Decision**: Express repeated "call → assert argv" and "decode → check" tests
  as `pytest.mark.parametrize` rows over typed case objects defined in a shared
  `cases.py`, one `pytest.param(..., id="agents.list")` per operation.
- **Rationale**: `tests/unit/resources/test_agents.py` shows the pattern
  duplicated per method with copy-pasted `_make_transport()`/`_result()` helpers
  across ~19 files; a table collapses ceremony to one data row and gives stable
  test IDs for diffing coverage.
- **Alternatives considered**: keep per-file classes (status quo — high
  duplication, invisible gaps); a metaclass/test generator (more magic, worse mypy
  ergonomics under the `tests.*` override). Rejected.

## R2. Exact `expected_argv` vs partial `in`/`not in` assertions

- **Decision**: Verify optional-flag presence/absence by asserting the complete
  expected argv tuple, not membership checks.
- **Rationale**: current tests mix `assert_called_once_with((...))` (exact) with
  `assert "--description" in args` / `assert "--name" not in args` (partial). Exact
  argv catches ordering and adjacent-flag regressions the partial form misses.
- **Alternatives considered**: keep membership checks (weaker). Rejected.

## R3. Manifest-driven argv completeness guard

- **Decision**: Add a guard test asserting every `ManifestEntry` with a non-empty
  `sdk_method` and `status != "unsupported"` has at least one `ArgvCase` row,
  failing with the list of missing `sdk_method` values.
- **Rationale**: mirrors the existing `test_every_command_has_sdk_mapping` and
  `test_every_sdk_method_resolves_on_client` guards in
  `tests/contract/test_full_cli_coverage.py`, reusing `load_manifest()` and the
  `sdk_method`/`status` fields. This converts code reduction into enforced growth
  (SC-003). Newly added operations must add a row, not a file.
- **Alternatives considered**: manual coverage tracking (drifts); coverage
  percentage thresholds only (don't map to specific operations). Rejected.

## R4. Integration `PATH` handling: fixture vs `os.environ` mutation

- **Decision**: Provide a `fake_cli_client` fixture in
  `tests/integration/conftest.py` that uses `monkeypatch.setenv("PATH", ...)` and
  builds `MulticaClient(ClientConfig(executable="fake_multica.py"))`.
- **Rationale**: all 17 `tests/integration/resources/*` files directly mutate
  `os.environ["PATH"]` in a `try/finally`, which leaks across threads and is
  unsafe under parallel execution (SC-005). `monkeypatch` scopes teardown to the
  test automatically.
- **Alternatives considered**: shared helper that still mutates `os.environ`
  (still unsafe); passing an absolute executable path per call (loses the PATH
  resolution coverage the fake binary exercises). Rejected.

## R5. Integration coverage guards (fixture-usage + operation-coverage)

- **Decision**: Drive integration operations from one table with one row per
  existing `tests/fixtures/json/**/*.json` file, plus TWO guard tests: (1)
  fixture-usage (FR-008) — fails when any fixture file is not referenced by a row;
  (2) operation-coverage (FR-020) — fails when a guard-eligible manifest operation
  is neither exercised by a `FakeCliCase.sdk_method` nor listed in a
  `KNOWN_FIXTURE_GAPS` allowlist. This mirrors the unit `KNOWN_ARGV_GAPS`
  mechanism (R3) exactly, so it stays green while making command gaps explicit at
  the integration (fake-CLI) layer.
- **Rationale**: 23 fixtures exist, some unused; the manifest lists >100
  operations. The usage guard makes dead fixtures fail loudly; the
  operation-coverage guard makes missing end-to-end (execute + decode) coverage
  explicit and turns "add a fixture" into "close a tracked gap" (SC-003). The
  guard applies to the offline integration layer; live command-level completeness
  is enforced separately by the FR-021 live command-execution guard (R8). Here it is
  resource/CRUD-oriented and backend-gated, so command-level completeness is not
  enforced there.
- **Alternatives considered**: leave fixtures unreferenced (dead weight);
  auto-discovering fixtures without asserting usage (silent gaps). Rejected.

## R6. Shared upstream-contract test harness

- **Decision**: Add `tests/contract/conftest.py` with (a) a `fake_upstream_cli`
  fixture migrating the duplicated `_fake_multica_with_exporter`, (b) a
  `contract_cli` helper `run(subcommand, *extra, binary=..., output=...)` that
  assembles the full `upstream_contract.py` argv with default
  `--version/--tag/--commit/--sha256/--os/--arch/--version-output/--repo-root`
  and returns a `CompletedProcess`, and (c) an autouse `preserved_generated_state`
  fixture that backs up/restores `upstream_state.json` and removes the generated
  candidate contract.
- **Rationale**: `test_upstream_contract_collect.py` repeats the ~30-line argv
  block 4× and manual `try/finally` state backup 3×; the same block recurs in
  check/prepare_upgrade/promotion/quickstart/apply_suggestions. Centralizing
  leaves only the meaningful assertions per test.
- **Alternatives considered**: module-level helper functions (still repeated
  imports and manual teardown); parametrizing whole subprocess invocations (hides
  per-test assertions). Fixture + helper chosen for clarity and automatic
  teardown.

## R7. Contract-diff severity parametrization

- **Decision**: Replace the six near-identical file-mutation diff tests with one
  parametrized test over `(mutation_file, must_contain, must_not_contain,
  unresolved_breaking)`; keep tests with distinct logic (summary reconciliation,
  in-code `SemanticCLIContract` assembly) separate. Apply to both the unit and
  contract diff modules.
- **Rationale**: `tests/unit/test_upstream_contract_diff.py` shows six bodies that
  differ only by mutation filename and expected severity; the in-code struct tests
  (required-arg, deprecation, enum-widening, default-change, alias) are genuinely
  distinct and stay.
- **Alternatives considered**: leave as-is (duplication). Rejected.

## R8. Live suite: descriptor-driven CRUD + parametrized errors/presence + full command execution

- **Decision**: Introduce `tests/live/crud_descriptors.py` with a resource
  descriptor `(create, get, update, delete, oracle_path, name_builder)` and one
  parametrized `test_crud_round_trip` in `test_crud.py` seeded with labels and
  projects; fold the Unicode/emoji case into a `name_builder` parameter.
  Parametrize `test_errors.py` on `(client_fixture_name, operation, expected_exc)`
  resolving fixtures via `request.getfixturevalue`; parametrize `test_projects.py`
  presence cases (P-OMIT/P-EMPTY/P-SET), keeping destructive, diagnostic-bundle,
  synthetic-wrapper, and P-NULL-HTTP tests separate. Additionally introduce
  `tests/live/live_operations.py` with a `LIVE_OPERATIONS` registry (one
  `(sdk_method, invoke)` per NON-CRUD guard-eligible operation; CRUD ops come from
  `CRUD_DESCRIPTORS` so nothing runs twice) plus two disjoint allowlists —
  `KNOWN_LIVE_GAPS: frozenset[str]` (runnable, not-yet-automated; goal empty,
  mirrors `KNOWN_ARGV_GAPS`) and `LIVE_EXEC_EXCEPTIONS: Mapping[str, LiveExecReason]`
  (permanently unrunnable, with a closed-set reason code). The `-m live_smoke`
  command-execution guard (FR-021, pure set math, no backend) mirrors the offline
  `KNOWN_*_GAPS` mechanism (R3/R5), while `-m live_extended` actually executes
  every operation against the real backend (SC-008).
- **Rationale**: `test_labels.py`, `test_errors.py`, and `test_projects.py` share
  skeletons already; `DirectApiOracle` exposes generic `get/delete/assert_absent`
  plus `delete_callback`, so a descriptor table cheaply extends coverage
  (SC-004c). Reusing the manifest-driven guard pattern for the live layer makes
  "every command executed live" a mechanical, allowlist-tracked invariant rather
  than a manual checklist, without touching the offline suite (the guard is
  `-m live` only). Existing live infrastructure is reused as-is.
- **Trade-off**: the guard itself is pure set math and needs no backend (runs in
  the blocking `-m live_smoke` job); only actual execution (`-m live_extended`)
  requires a running backend and per-operation setup. Runnable-but-not-yet-automated
  operations sit in `KNOWN_LIVE_GAPS` (goal empty, keeps the guard green
  incrementally, seeded mechanically per Appendix E); unrunnable operations
  (irrecoverable destructive, external-infra, interactive, daemon/process control)
  are tracked in `LIVE_EXEC_EXCEPTIONS` with a closed set of reason codes.
- **Alternatives considered**: a Page Object / Screenplay layer (rejected in
  ticket #9 / FR-016 — the fixtures + oracle + fake binary already play that
  role). Rejected.

## R9. Test-infra consolidation and shared factories

- **Decision**: Move `make_target()`/`make_settings(tmp_path, **overrides)` into
  `tests/unit/conftest.py`; merge `test_live_naming.py` into
  `test_live_settings.py` and `test_live_resource_registry.py` into
  `test_live_bootstrap.py`; fold `test_transport_errors.py` into `test_transport.py`
  as a `(exit_code, stderr, expected_exc)` table; keep all feature-002
  security-invariant tests intact.
- **Rationale**: `_target()`/`_settings()` factories are copied across live-infra
  modules and tiny modules multiply files without value. Security invariants
  (FR-015) are explicitly excluded from deletion.
- **Alternatives considered**: leave duplication (maintenance cost). Rejected.

## R10. Dependency and framework policy

- **Decision**: Use only stdlib + pytest (parametrization, fixtures,
  `request.getfixturevalue`, case tables, guard tests). Add no third-party test
  dependency.
- **Rationale**: FR-016 and ticket #9 record this decision (Screenplay, Page
  Object, pytest-bdd, hypothesis, syrupy all rejected as overhead for a
  fail-closed SDK repo). Constitution SDK Constraints also forbid growing runtime
  deps; test deps already cover the need.
- **Alternatives considered**: hypothesis for `_truncate_with_hash`/redaction
  (nondeterministic CI time, new dep). Rejected.

## Open Risks

- **Coverage parity**: migrating cases must not drop assertions. Mitigation: the
  argv/decoder guards plus running the full non-live suite after each story
  (FR-017, SC-002).
- **mypy under `tests.*` override**: new typed case structs and fixtures must pass
  `check_untyped_defs`. Mitigation: keep case containers as simple typed
  `msgspec.Struct`/`dataclass`/`NamedTuple` with concrete types.
- **Live layer verification**: US6 requires a real backend run. Mitigation:
  sequenced last; non-live gates unaffected.
