# Test-Harness Contracts: Test Suite Optimization

This feature has no public SDK surface. Its "interfaces" are the internal
pytest test-harness contracts: fixtures, helpers, case tables, and guard tests
that other test modules depend on. Contracts are grouped by user story. Signatures
are Python-typed (satisfy the `tests.*` mypy override; no `Any`).

## US2 — Unit resource harness (`tests/unit/resources/`)

### Fixtures (`conftest.py`)

```python
@pytest.fixture
def mock_transport() -> MagicMock: ...        # MagicMock(spec=CliTransport)

@pytest.fixture
def raw_result() -> Callable[[bytes, int], RawCommandResult]: ...
# raw_result(stdout=b"", exit_code=0) -> RawCommandResult(
#     argv=(), exit_code=exit_code, stdout=stdout, stderr=b"",
#     duration=datetime.timedelta())
# (mirrors the existing _result() helper in tests/unit/resources/test_agents.py)
```

### Case tables (`cases.py`)

- `ARGV_CASES: tuple[ArgvCase, ...]` — one row per supported operation.
- `DECODE_CASES: tuple[DecodeCase, ...]` — one row per decode check.

### Tests (`test_operations.py`)

```python
@pytest.mark.parametrize("case", ARGV_CASES, ids=lambda c: c.sdk_method)
def test_command_argv(case: ArgvCase, mock_transport: MagicMock,
                      raw_result: Callable[[bytes, int], RawCommandResult]) -> None: ...

@pytest.mark.parametrize("case", DECODE_CASES, ids=lambda c: c.id)
def test_decode(case: DecodeCase, mock_transport: MagicMock,
               raw_result: Callable[[bytes, int], RawCommandResult]) -> None: ...

KNOWN_ARGV_GAPS: frozenset[str]   # guard-eligible sdk_methods not yet covered; goal: empty

def test_every_guard_eligible_operation_has_argv_case() -> None:
    """Guard: each guard-eligible manifest sdk_method has a row or is allowlisted."""
```

**Contract**:
- `test_command_argv` builds the resource from `mock_transport`, calls
  `getattr(resource, case.method)(*case.args, **case.kwargs)`, then asserts the
  transport call with the exact form for `case.transport_method`:
  - `run_bytes`: `mock_transport.run_bytes.assert_called_once_with(case.expected_argv, stdin=case.stdin, timeout=case.timeout)`.
  - `run_text`: `mock_transport.run_text.assert_called_once_with(case.expected_argv)` (no kwargs).
- Guard eligibility: `sdk_method` non-empty AND `status != "unsupported"` (there
  is no `supported` field). The guard FAILS if a guard-eligible operation is
  neither in the table nor in `KNOWN_ARGV_GAPS`, or if a `KNOWN_ARGV_GAPS` entry
  also has a row (stale). Failure message names the offending `sdk_method`s.

## US3 — Integration fake-CLI harness (`tests/integration/`)

### Fixture (`conftest.py`)

```python
@pytest.fixture
def fake_cli_client(monkeypatch: pytest.MonkeyPatch) -> MulticaClient:
    """Prepend tests/fixtures to PATH via monkeypatch; return fake-binary client."""
```

### Table + tests (`resources/test_fake_cli_operations.py`)

```python
FAKE_CLI_CASES: tuple[FakeCliCase, ...]              # each row carries fixture, sdk_call, check, sdk_method, id
KNOWN_FIXTURE_GAPS: frozenset[str]                   # guard-eligible ops with no fixture yet; goal: empty

@pytest.mark.parametrize("case", FAKE_CLI_CASES, ids=lambda c: c.id)
def test_fake_cli_operation(case: FakeCliCase, fake_cli_client: MulticaClient) -> None: ...

def test_every_json_fixture_is_referenced() -> None:
    """Guard (FR-008): each tests/fixtures/json/**/*.json is referenced by a row."""

def test_every_guard_eligible_operation_has_fixture_or_gap() -> None:
    """Guard (FR-020): each guard-eligible manifest op has a row or is allowlisted."""
```

**Contract**:
- No test mutates `os.environ` directly (parallel-safe).
- FR-008 guard globs `tests/fixtures/json/**/*.json` and fails naming
  unreferenced files.
- FR-020 guard uses the same eligibility predicate as US2 (`sdk_method` non-empty
  AND `status != "unsupported"`). It fails if a guard-eligible operation is
  neither in `{FakeCliCase.sdk_method}` nor in `KNOWN_FIXTURE_GAPS`, or if a
  `KNOWN_FIXTURE_GAPS` entry has a row (stale). Failure message names the
  offending operations.

## US4 — Maintainer upstream-contract harness (`tests/contract/conftest.py`)

```python
@pytest.fixture
def fake_upstream_cli(tmp_path: pathlib.Path) -> pathlib.Path:
    """Migrated _fake_multica_with_exporter; returns executable path."""

@pytest.fixture
def contract_cli(fake_upstream_cli: pathlib.Path) -> ContractCliRunner:
    """runner.run(subcommand, *extra, binary=..., output=...) -> CompletedProcess[str]."""

@pytest.fixture(autouse=True)
def preserved_generated_state() -> Iterator[None]:
    """Backup/restore upstream_state.json; remove generated candidate contract."""
```

**Contract**:
- `contract_cli.run` fills default `--version/--tag/--commit/--asset-name/
  --sha256/--os/--arch/--version-output/--repo-root`; callers override only
  differing flags.
- `preserved_generated_state` replaces every per-test `try/finally` state backup.
- Rewritten modules: `collect`, `check`, `prepare_upgrade`, `promotion`,
  `quickstart`, `apply_suggestions`. The specific tests to convert to
  parametrized output-path rows are `test_candidate_collection_is_deterministic`
  (deterministic A/B) and `test_collect_persists_in_repo_output_outside_generated`
  (canonical vs custom output) in `test_upstream_contract_collect.py`.

## US5 — Contract-diff severity (`tests/unit/` + `tests/contract/`)

```python
MUTATION_SEVERITY_CASES: tuple[MutationSeverityCase, ...]

@pytest.mark.parametrize("case", MUTATION_SEVERITY_CASES, ids=lambda c: c.id)
def test_mutation_severity(case: MutationSeverityCase) -> None: ...
```

**Contract**: decode baseline + mutation, `diff_contracts`, assert
`must_contain`/`must_not_contain` severities and (when set) `unresolved_breaking`.
Seed table = exactly five file-mutation rows (`required-flag-added`,
`help-text-changed` [severities ⊆ {`doc_only`,`provenance_only`}], `command-added`,
`command-removed`, `optional-flag-added`). The `command-renamed` rename-heuristic
test, in-code `SemanticCLIContract` tests, and summary-reconciliation tests remain
separate. Applies to whichever of these file-mutation tests exist in each of the
unit and contract diff modules.

## US6 — Live harness (`tests/live/`)

```python
# crud_descriptors.py
CRUD_DESCRIPTORS: tuple[CrudDescriptor, ...]        # seeds: labels, projects

# test_crud.py
# Markers do NOT inherit in this repo — set a module-level pytestmark on EVERY new
# live module so `-m "not live"` never collects it (FR-017 / Constitution IV).
pytestmark = [pytest.mark.live, pytest.mark.live_extended]

@pytest.mark.parametrize("descriptor", CRUD_DESCRIPTORS, ids=lambda d: d.id)
def test_crud_round_trip(descriptor: CrudDescriptor, live_ctx: LiveContext) -> None:
    # name via descriptor.name_builder(live_ctx.identity); no separate resource_name fixture
    ...

# live_operations.py  (FR-021)
LIVE_OPERATIONS: tuple[LiveOperation, ...]                   # NON-CRUD ops only
LIVE_EXEC_EXCEPTIONS: Mapping[str, LiveExecReason]          # unrunnable ops -> reason code
KNOWN_LIVE_GAPS: frozenset[str]                             # runnable, not-yet-automated; goal: empty

LiveExecReason = Literal[
    "destructive-irrecoverable", "requires-external-infra",
    "interactive-or-foreground", "process-or-daemon-control",
]

# tests/live/conftest.py
@pytest.fixture
def live_ctx(live_client: MulticaClient, api_oracle: DirectApiOracle,
             register_resource: Callable[..., None],
             test_identity: TestIdentity) -> LiveContext: ...

# test_live_command_coverage.py
pytestmark = [pytest.mark.live]  # base marker; per-test subtag below (markers don't inherit)

@pytest.mark.live_extended  # needs backend
@pytest.mark.parametrize("op", LIVE_OPERATIONS, ids=lambda o: o.id)
def test_live_operation_executes(op: LiveOperation, live_ctx: LiveContext) -> None:
    op.invoke(live_ctx)

@pytest.mark.live_smoke  # pure set math, no backend
def test_every_guard_eligible_operation_runs_live() -> None:
    """Guard (FR-021): each guard-eligible op is covered, allowlisted, or a known gap."""

# test_errors.py
ERROR_CASES: tuple[ErrorMappingCase, ...]
@pytest.mark.parametrize("case", ERROR_CASES, ids=lambda c: c.id)
def test_error_mapping(case: ErrorMappingCase, request: pytest.FixtureRequest,
                      test_identity: TestIdentity) -> None: ...

# test_projects.py
PRESENCE_CASES: tuple[PresenceCase, ...]            # P-OMIT, P-EMPTY, P-SET
@pytest.mark.parametrize("case", PRESENCE_CASES, ids=lambda c: c.id)
def test_project_presence(case: PresenceCase, live_client: MulticaClient,
                         api_oracle: DirectApiOracle, ...) -> None: ...
```

**Contract**:
- `test_crud_round_trip` runs create→oracle-check→get→list→update→delete→
  `assert_absent` generically; Unicode/emoji is a `name_builder` variant.
- `test_error_mapping` resolves `case.client_fixture_name` via
  `request.getfixturevalue` and asserts secret-free messages.
- Destructive, diagnostic-bundle, synthetic-wrapper, and P-NULL-HTTP tests stay
  separate. Every live module keeps its existing module-level `pytestmark`
  (base `pytest.mark.live` plus the appropriate `live_smoke`/`live_extended`
  subtag); markers do not inherit, so new modules must set it explicitly.
- Coverage set `T_live = {LiveOperation.sdk_method} ∪
  crud_sdk_methods(CRUD_DESCRIPTORS)`. `LIVE_OPERATIONS` holds NON-CRUD ops only
  (executed by `test_live_operation_executes`); CRUD ops are executed by
  `test_crud_round_trip` and contribute their four manifest ids — no op runs twice.
  Coverage from `test_error_mapping`/presence tests does NOT count toward `T_live`.
- The FR-021 guard FAILS if `E - T_live - set(LIVE_EXEC_EXCEPTIONS) -
  KNOWN_LIVE_GAPS` is non-empty, if `T_live ∩ (set(LIVE_EXEC_EXCEPTIONS) ∪
  KNOWN_LIVE_GAPS)` is non-empty (stale), if `set(LIVE_EXEC_EXCEPTIONS) ∩
  KNOWN_LIVE_GAPS` is non-empty (both buckets), or if a `LIVE_EXEC_EXCEPTIONS`
  value is not a `LiveExecReason`. `KNOWN_LIVE_GAPS` (goal: empty) keeps the guard
  green during incremental development, exactly like `KNOWN_ARGV_GAPS`.
- Recoverable destructive ops run with restore (marked both `destructive` and
  `serial`); irrecoverable ones go in `LIVE_EXEC_EXCEPTIONS`. The guard is
  `live_smoke` (no backend); execution is `live_extended`; nothing is in the
  offline suite.

## US7 — Test-infra consolidation (`tests/unit/`)

```python
# tests/unit/conftest.py
def make_target(**overrides: object) -> LiveTarget: ...
def make_settings(tmp_path: pathlib.Path, **overrides: object) -> LiveSettings: ...

# tests/unit/test_transport.py
TRANSPORT_ERROR_CASES: tuple[TransportErrorCase, ...]
@pytest.mark.parametrize("case", TRANSPORT_ERROR_CASES, ids=lambda c: c.id)
def test_exit_code_maps_to_exception(case: TransportErrorCase) -> None: ...
```

**Contract**:
- `make_target`/`make_settings` replace all local `_target()`/`_settings()`
  copies.
- `test_live_naming.py` → `test_live_settings.py`; `test_live_resource_registry.py`
  → `test_live_bootstrap.py`; `test_transport_errors.py` → `test_transport.py`.
- Every feature-002 security-invariant test (secret redaction, argv without
  shell, `KEEP_ENV` forbidden in CI, loopback-only URL) MUST still run.

## Cross-cutting invariants

- No third-party test dependency added (FR-016).
- After each user story, `uv run pytest -m "not live"` is green and Ruff + strict
  mypy pass (FR-017).
- `pyproject.toml` mypy overrides drop `tests.typing.*` and
  `tests.contract.models.*` once those packages are removed.
