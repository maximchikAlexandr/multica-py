<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
`specs/004-test-suite-optimization/plan.md`
<!-- SPECKIT END -->

## Multica Upstream Contract Review Rules

When updating the SDK from upstream `multica-ai/multica`, treat the pinned
upstream CLI source and verified release binary as evidence, not as automatic
approval for public SDK changes.

Extractor scripts may automatically record only declarative facts from known,
versioned patterns:

- Cobra command literals such as `cobra.Command{Use, Aliases, Hidden, Deprecated}`.
- `AddCommand(...)` command-tree relationships.
- Known `Flags()` and `PersistentFlags()` registration calls.
- Known Cobra argument validators and declarative flag constraints.
- Source file, symbol, and line-range provenance.

Everything else must fail closed into a review item. Unknown source patterns,
unresolved helpers, dynamic enum construction, imperative validation, or
presence-sensitive code must never change the public SDK automatically.

For every new or changed command, the reviewer must trace each positional
argument and flag through `RunE` and called helpers, then record where each
value lands: path, query, JSON body, header, multipart body, or local process
control. Do not treat matching names as proof of mapping; `--project` and
`project_id` still require source evidence.

For update/patch-style parameters, explicitly document presence semantics:

- omitted value;
- `null` / `None`;
- empty string;
- zero or `false` when accepted by the type.

Use an explicit unset sentinel in the SDK when `None` has a meaning different
from "not provided".

Enum values found by scripts are candidates only. A reviewer must approve the
public enum name, strict/open policy, aliases, deprecated values, and operation
scope before they enter the approved SDK contract.

Declarative Cobra constraints may be extracted automatically. Imperative
constraints found in conditionals, `Flags().Changed(...)`, helper calls, or
custom validation must be normalized by review as `requires`, `conflicts_with`,
`exactly_one`, `at_least_one`, `required_together`, conditional enum/range, or
a named custom validator. Each approved constraint needs positive and negative
tests.

Generated evidence, manifest suggestions, and upgrade bundles are not coverage
decisions. Only an approved SDK contract with operation IDs, source references,
input/output contracts, coverage level, and test references can promote a
candidate upstream contract to supported SDK coverage.

Keep the upstream-update pipeline split into two active layers in feature 002:

- `sdk-contract.json`: the human/agent-approved SDK contract with operation
  IDs, mappings, overrides, policy decisions, and source references.
- `generator/`: deterministic generation of Python signatures, enums,
  validators, docs, fixtures, and tests from the approved contract.

`source_evidence/` extractors were removed in the 002 cleanup and return in
feature 003 when wired to landing zones. Do not treat source evidence as an
active layer until 003 lands.

The approved SDK contract is the only valid production generator input.
Evidence files, heuristic rename suggestions, and generated upgrade bundles
must never directly generate or modify public SDK behavior.

Maintainer upgrade entrypoint:

```bash
uv run python scripts/upstream_contract.py upgrade --tag ... --version ... \
  --commit ... --release-id ... --binary ... --asset-name ... --sha256 ... \
  --os ... --arch ... --version-output ... --output-dir ...
```

Or `./scripts/upstream_upgrade.sh` with `TAG`, `COMMIT`, `RELEASE_ID`, `BINARY`,
`ASSET_NAME`, `SHA256`, and `VERSION_OUTPUT` set. Verified collect/export paths:
`tools/upstream-cli-contract/README.md` and `upstream_contract.py collect`.

## Writing Tests

These rules are binding for every new or changed test (established by feature
004). The goal: growing coverage without growing test code. Reuse before you add;
add data rows before you add functions; add functions before you add files.

### Table-driven first

- Express repeated "call → assert" and "decode → check" tests as
  `@pytest.mark.parametrize` over a case table, not as many near-identical
  functions. Adding coverage MUST be one new row, not a new test or file.
- Case-table containers are `@dataclass(frozen=True)`. Reuse the existing types
  and follow their layer:
  - unit CLI argv: `ArgvCase` (+ `DecodeCase` for model decoding) in
    `tests/unit/resources/`;
  - component fake CLI: `CommandCase` in `tests/component/resources/cases.py`
    (PR-03 migration from legacy `FakeCliCase` rows);
  - contract-diff severity: `MutationSeverityCase` in `tests/unit/`/`tests/contract/`;
  - live CRUD: `CrudDescriptor`; live non-CRUD command: `LiveOperation` in
    `tests/live/`.
- Keep genuinely distinct logic (rename heuristics, summary reconciliation,
  destructive/diagnostic-bundle flows, `P-NULL-HTTP`) as separate tests — do NOT
  force them into a table.

### Reuse shared code, don't duplicate

- Use the shared fixtures and factories (`make_target`, `make_settings`,
  `mock_transport`, the fake-CLI client fixture, `DirectApiOracle`, `live_ctx`,
  `register_resource`, `test_identity`). Do NOT re-copy `_target()`/`_settings()`
  style local helpers into a test module.
- Never mutate `os.environ` directly in component tests; use the provided
  fixture-scoped environment control (keeps the suite parallel-safe).

### Assert precisely

- Verify optional-flag presence/absence with a complete `expected_argv` value,
  not partial `in`/`not in` checks. Match the transport method exactly
  (`run_bytes` including `stdin`/`timeout`, `run_text`).
- No tautological, dead, or duplicate tests. Do not add comments that narrate the
  code.

### Respect the completeness guards

Coverage is enforced by manifest-driven guards. When you add or change a command,
keep the matching guard green by adding real coverage — the allowlists are a
temporary bridge, not a dumping ground:

- unit argv: `KNOWN_ARGV_GAPS`;
- component fake CLI: `KNOWN_FIXTURE_GAPS` (until each legacy `FakeCliCase.id`
  migrates to `CommandCase` in PR-03);
- live command execution: `KNOWN_LIVE_GAPS` (runnable, not-yet-automated; goal
  empty) and `LIVE_EXEC_EXCEPTIONS` (permanently unrunnable, with a valid
  `LiveExecReason` code).

An allowlist entry MUST carry a short inline reason and MUST be removed the moment
real coverage exists (the guards fail on stale entries). Prefer writing the
`ArgvCase`/`CommandCase`/`LiveOperation`/`CrudDescriptor` over allowlisting.

### Layers and markers

- Default suite is offline: `uv run pytest -m "not live"` MUST stay green and MUST
  need no backend/network. Unit, contract, component, and packaging layers stay
  offline.
- Path prefixes auto-apply layer markers (`unit`, `contract`, `component`,
  `packaging`, `live`) via `tests/conftest.py`; see
  `specs/005-test-suite-agent-sandbox/contracts/marker-profiles.md`.
- `tests/component/test_process_contract.py` carries `@pytest.mark.process` and
  `@pytest.mark.serial`; all other offline tests MUST NOT use `serial`.
- Live tests are gated. Markers do NOT inherit in this repo: every
  `tests/live/*` module sets a module-level `pytestmark` including base
  `pytest.mark.live`, exactly one profile among `live_smoke`, `live_extended`, or
  `live_opencode_canary`, and `pytest.mark.serial`. Verify with
  `uv run pytest -m "not live" --collect-only` that no `tests/live/*` node is
  collected.

### Tooling gates

Both `uv run mypy src` and `uv run mypy tests` MUST pass; test helpers live under
the typed `tests.*` mypy override — no `Any` leaks. Use only stdlib + pytest; do
NOT add third-party test frameworks or UI-automation patterns (Screenplay, Page
Object, pytest-bdd, hypothesis, snapshot libraries).

## Commit Messages

Use Conventional Commits for all repository commits:

```text
<type>[optional scope]: <description>
```

Allowed types: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `build`, `ci`,
`chore`, `style`, `revert`.

The repository enforces this with `.githooks/commit-msg`. Pre-commit also runs
Ruff (`check` + `format --check`) and mypy on `src` via `.githooks/pre-commit`.
Enable hooks locally with:

```sh
git config core.hooksPath .githooks
```
