# Phase 1 Data Model: Test Suite Optimization

These are **test-harness data structures** (not SDK runtime models). They live
under the `tests.*` mypy override and use only stdlib + typing. Field names below
are the contract. All case-table containers MUST be `@dataclass(frozen=True)`
(chosen once for the whole feature — several rows carry `Callable` fields such as
`check`/`sdk_call` that are incompatible with frozen `msgspec.Struct`, and a
single container type removes an implementation decision). Each field MUST be
concretely typed (no `Any`).

## ArgvCase (unit resources)

One row = one CLI operation's expected argv.

| Field | Type | Meaning |
| --- | --- | --- |
| `resource_attr` | `str` | Client attribute chain, e.g. `"agents"` (root of `sdk_method`). |
| `method` | `str` | Method name on the resource, e.g. `"list"`, `"create"`. |
| `args` | `tuple[object, ...]` | Positional args passed to the method. |
| `kwargs` | `Mapping[str, object]` | Keyword args (typed as concrete union in impl). |
| `stdout` | `bytes` | Fake transport stdout for the call. |
| `expected_argv` | `tuple[str, ...]` | Full expected CLI argv (exact, ordered). |
| `transport_method` | `Literal["run_bytes", "run_text"]` | Which transport call is asserted. |
| `stdin` | `bytes \| None` | Expected `stdin` kwarg for `run_bytes` (default `None`). |
| `timeout` | `float \| None` | Expected `timeout` kwarg for `run_bytes` (default `None`). |
| `sdk_method` | `str` | Dotted manifest id, e.g. `"agents.list"`; used as `pytest.param` id and for the completeness guard. |

**Rules**:

- `expected_argv` is asserted in full; optional-flag presence/absence is expressed
  by inclusion/omission in this tuple (replaces `in`/`not in`).
- **Assertion form MUST match the transport method** (see current
  `tests/unit/resources/test_agents.py`):
  - `run_bytes`: `transport.run_bytes.assert_called_once_with(expected_argv, stdin=stdin, timeout=timeout)`.
  - `run_text`: `transport.run_text.assert_called_once_with(expected_argv)` — no kwargs.
- `sdk_method` MUST equal `f"{resource_attr}.{method}"` unless the manifest maps
  differently; when they differ, the manifest value wins and the guard matches on
  the manifest `sdk_method`.
- For `run_text` operations, `stdout` MAY be empty; `stdin`/`timeout` are ignored.

## DecodeCase (unit resources)

One row = one JSON-stdout → decoded-model check.

| Field | Type | Meaning |
| --- | --- | --- |
| `resource_attr` | `str` | Client attribute, e.g. `"agents"`. |
| `method` | `str` | Method returning a decoded model/list. |
| `args` | `tuple[object, ...]` | Positional args for the call. |
| `stdout` | `bytes` | JSON payload the fake transport returns. |
| `check` | `Callable[[object], None]` | Assertion over the decoded result. |
| `id` | `str` | `pytest.param` id, e.g. `"agents.list.decode"`. |

## FakeCliCase (integration resources)

One row = one operation against the fake CLI binary, bound to a JSON fixture.

| Field | Type | Meaning |
| --- | --- | --- |
| `fixture` | `str` | Repo-relative path under `tests/fixtures/json/**`, referenced by the usage guard. |
| `sdk_call` | `Callable[[MulticaClient], object]` | Invocation, e.g. `lambda c: c.labels.list()`. |
| `check` | `Callable[[object], None]` | Assertion over the return value (incl. special cases like `set_status`, `deprioritize`). |
| `sdk_method` | `str` | Dotted manifest id exercised, e.g. `"labels.list"`; used by the operation-coverage guard. |
| `id` | `str` | `pytest.param` id. |

**Rules**:

- Every file matching `tests/fixtures/json/**/*.json` MUST appear as some row's
  `fixture` (usage guard, FR-008).
- Every guard-eligible manifest operation MUST be covered by some row's
  `sdk_method` or be listed in `KNOWN_FIXTURE_GAPS` (operation-coverage guard,
  FR-020).
- The client is obtained from the `fake_cli_client` fixture (no `os.environ`
  mutation).

## MutationSeverityCase (contract-diff)

One row = one baseline→mutation diff severity expectation.

| Field | Type | Meaning |
| --- | --- | --- |
| `mutation_file` | `str` | Filename under `fixtures/upstream_contract/mutations/`. |
| `must_contain` | `tuple[str, ...]` | Severities that MUST be present. |
| `must_not_contain` | `tuple[str, ...]` | Severities that MUST be absent. |
| `unresolved_breaking` | `bool \| None` | Expected `diff.unresolved_breaking`; `None` = not asserted. |
| `id` | `str` | `pytest.param` id. |

**Seed rows** (exactly five file-mutation rows):
`required-flag-added → must_contain={"breaking"}, unresolved_breaking=True`;
`help-text-changed → severities ⊆ {"doc_only", "provenance_only"}`;
`command-added → must_contain={"additive"}`;
`command-removed → must_contain={"breaking"}`;
`optional-flag-added → must_contain={"additive"}, must_not_contain={"breaking"}`.

**Not in the table (stay separate tests)**: `command-renamed` (rename heuristic
asserts `suggested_action`/`affected_operations`, not severity), summary-
reconciliation tests, and in-code `SemanticCLIContract`-assembly tests. Rule: a
test stays separate when its assertions cannot be expressed as
`(mutation_file → severities present/absent [+ unresolved_breaking])`.

## ContractCliInvocation (maintainer harness)

Shared helper (`contract_cli.run`) parameters.

| Field | Type | Meaning |
| --- | --- | --- |
| `subcommand` | `str` | e.g. `"collect"`, `"promote"`, `"check"`. |
| `extra` | `tuple[str, ...]` | Additional argv appended after defaults. |
| `binary` | `pathlib.Path` | Fake upstream CLI path (default from `fake_upstream_cli`). |
| `output` | `pathlib.Path \| None` | `--output` path override. |
| (returns) | `subprocess.CompletedProcess[str]` | Result for assertions. |

**Defaults filled by the helper**: `--version 0.4.3`, `--tag v0.4.3`,
`--commit <40-hex>`, `--asset-name`, `--sha256 <of binary>`, `--os linux`,
`--arch amd64`, `--version-output "multica 0.4.3"`, `--repo-root <ROOT>`.
Per-test overrides replace only differing values.

## CrudDescriptor (live)

One descriptor = one resource's generic CRUD round-trip.

| Field | Type | Meaning |
| --- | --- | --- |
| `create` | `Callable[[MulticaClient, str], object]` | Create via SDK, returns created model. |
| `get` | `Callable[[MulticaClient, str], object]` | Fetch by id via SDK. |
| `update` | `Callable[[MulticaClient, str], object]` | Update via SDK. |
| `delete` | `Callable[[MulticaClient, str], None]` | Delete via SDK. |
| `oracle_path` | `Callable[[str], str]` | Backend path builder, e.g. `lambda i: f"/api/labels/{i}"`. |
| `name_builder` | `Callable[[str], str]` | Produces the resource name (Unicode/emoji variant is just another builder). |
| `id` | `str` | `pytest.param` id, e.g. `"labels"`, `"projects"`. |

**Seed descriptors**: `labels`, `projects`. Each additional resource = one
descriptor (~10 lines), no new file (SC-004c).

## LiveContext (US6 / FR-021)

Passed to every `LiveOperation.invoke`; built by a `live_ctx` fixture in
`tests/live/conftest.py` from existing live infrastructure.

| Field | Type | Meaning |
| --- | --- | --- |
| `client` | `MulticaClient` | Live SDK client. |
| `oracle` | `DirectApiOracle` | Direct-API verification helper. |
| `register_resource` | `Callable[..., None]` | Registers created resources for teardown. |
| `identity` | `TestIdentity` | Unique-naming/identity helper for the run. |

## LiveOperation (live command execution, US6 / FR-021)

One entry = one NON-CRUD guard-eligible manifest operation executed against the
real backend. CRUD operations are covered separately through `CrudDescriptor`
(executed by `test_crud_round_trip`); they are NOT duplicated here.

| Field | Type | Meaning |
| --- | --- | --- |
| `sdk_method` | `str` | Dotted manifest id executed, e.g. `"agents.archive"`. |
| `invoke` | `Callable[[LiveContext], None]` | Sets up prerequisites (e.g. create a parent resource, registered via `ctx.register_resource`) and calls the SDK method against the live backend. |
| `id` | `str` | `pytest.param` id. |

**`LIVE_EXEC_EXCEPTIONS`**: `Mapping[str, LiveExecReason]` — guard-eligible
`sdk_method`s that CANNOT run in the test env, each with a reason code, where
`LiveExecReason = Literal["destructive-irrecoverable", "requires-external-infra",
"interactive-or-foreground", "process-or-daemon-control"]` (FR-021). Permanent;
goal = smallest possible.

**`KNOWN_LIVE_GAPS`**: `frozenset[str]` — runnable `sdk_method`s not yet automated
(mirrors `KNOWN_ARGV_GAPS`); goal `frozenset()` at completion (SC-008).

**`crud_sdk_methods(CRUD_DESCRIPTORS)`**: expands each descriptor into its four
manifest ids (`{descriptor.id}.create/get/update/delete`, per Appendix C).

**Rules**:

- Markers: `test_live_operation_executes` and `test_crud_round_trip` →
  `live_extended` (needs backend); the guard → `live_smoke` (pure set math, no
  backend). All are `-m live`-gated and NOT in the offline suite.
- Recoverable destructive operations run with restore (marked both `destructive`
  and `serial`); only irrecoverable ones go in `LIVE_EXEC_EXCEPTIONS`.
- Coverage from `test_error_mapping`/presence tests does NOT count toward `T_live`;
  such operations still need a `LIVE_OPERATIONS`/`CRUD_DESCRIPTORS` entry or an
  allowlist listing.
- `crud_sdk_methods` assumes the four standard verbs; if a resource's manifest ids
  differ (e.g. no `update`), the missing/extra ids go to `KNOWN_LIVE_GAPS` until a
  matching `LiveOperation` is written.
- Every new `tests/live/*` module sets a module-level `pytestmark` including base
  `pytest.mark.live` (markers do not inherit).

## ErrorMappingCase (live)

One row = one client operation → expected exception.

| Field | Type | Meaning |
| --- | --- | --- |
| `client_fixture_name` | `str` | Fixture resolved via `request.getfixturevalue`, e.g. `"invalid_pat_client"`. |
| `operation` | `Callable[[MulticaClient], object]` | The failing call. |
| `expected_exc` | `type[Exception]` | Expected public exception. |
| `id` | `str` | `pytest.param` id. |

**Rule**: message must exclude secrets (`_assert_safe_message`). Destructive,
diagnostic-bundle, and synthetic-wrapper tests stay separate.

## PresenceCase (live projects)

One row = one update-request presence variant.

| Field | Type | Meaning |
| --- | --- | --- |
| `update_request` | `ProjectUpdateRequest` | The SDK update payload. |
| `expected_title` | `str` | Expected title after update. |
| `expected_description` | `str \| None` | Expected description after update. |
| `id` | `str` | `pytest.param` id: `P-OMIT`, `P-EMPTY`, `P-SET`. |

**Rule**: `P-NULL-HTTP` bypasses the SDK and stays a separate test.

## TransportErrorCase (unit transport)

One row = exit-code → exception mapping (folds `test_transport_errors.py`).

| Field | Type | Meaning |
| --- | --- | --- |
| `exit_code` | `int` | Process exit code. |
| `stderr` | `bytes \| str` | Captured stderr. |
| `expected_exc` | `type[Exception]` | Expected public exception. |
| `id` | `str` | `pytest.param` id. |

## Shared factories (unit conftest)

- `make_target(**overrides) -> <LiveTarget>`: builds a live target with default
  sha256/fields; overrides replace specific fields.
- `make_settings(tmp_path, **overrides) -> <LiveSettings>`: builds settings for
  live-infra tests. Replaces per-module `_target()`/`_settings()` copies.

## Completeness Guards (relationships)

- **Argv guard**: let `E = {entry.sdk_method for entry in load_manifest() if
  entry.sdk_method and entry.status != "unsupported"}` (guard-eligible; there is
  no boolean `supported` field). Let `T = {ArgvCase.sdk_method}` and
  `G = KNOWN_ARGV_GAPS`. The guard FAILS if `E - T - G` is non-empty (names the
  missing operations) OR if `T ∩ G` is non-empty (stale allowlist entries). Goal:
  `G == frozenset()`; each `G` entry carries an inline reason comment.
- **`KNOWN_ARGV_GAPS`**: `frozenset[str]` seeded with exactly the guard-eligible
  `sdk_method` values that have no unit argv coverage after all 21 resource files
  are migrated; keeps the suite green (FR-017) while making gaps explicit.
- **Fixture guard**: `{tests/fixtures/json/**/*.json}` ⊆ `{FakeCliCase.fixture}`.
  Failure lists the unused fixtures.
- **Integration operation-coverage guard**: with `E` as above (guard-eligible
  manifest operations), `T_int = {FakeCliCase.sdk_method}`, and
  `G_int = KNOWN_FIXTURE_GAPS`: FAILS if `E - T_int - G_int` is non-empty (names
  uncovered operations) OR if `T_int ∩ G_int` is non-empty (stale). Goal:
  `G_int == frozenset()`; each entry carries an inline reason. Closing a gap means
  adding a JSON fixture + `FakeCliCase` row. Applies to the offline integration
  (fake-CLI) layer.
- **Live command-execution guard** (`live_smoke`-marked, no backend): with `E` as
  above,
  `T_live = {LiveOperation.sdk_method} ∪ crud_sdk_methods(CRUD_DESCRIPTORS)`,
  `G_exec = set(LIVE_EXEC_EXCEPTIONS)`, and `G_gap = KNOWN_LIVE_GAPS`: FAILS if
  `E - T_live - G_exec - G_gap` is non-empty (names uncovered, untracked
  operations), OR if `T_live ∩ (G_exec ∪ G_gap)` is non-empty (stale allowlist
  entry), OR if `G_exec ∩ G_gap` is non-empty (operation in both buckets), OR if
  any `LIVE_EXEC_EXCEPTIONS` value is not in `LiveExecReason` (invalid reason code).
  Goal: `G_gap == frozenset()` at completion; smallest possible `G_exec`.
