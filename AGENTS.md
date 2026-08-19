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

Maintainer upstream-contract flow:

```bash
uv run python scripts/upstream_contract.py collect \
  --source-checkout /absolute/pinned/source \
  --binary /absolute/verified/multica \
  --tag ... --version ... --commit ... --release-id ... \
  --asset-name ... --sha256 ... --os ... --arch ... \
  --version-output /absolute/version.json --output-dir /absolute/evidence
uv run python scripts/upstream_contract.py validate --approved contracts/sdk-contract.json \
  --source-checkout /absolute/pinned/source
uv run python scripts/upstream_contract.py render --approved contracts/sdk-contract.json \
  --runtime-output src/multica_py/_generated/approved_sdk.py \
  --transient-output /absolute/ignored/output
uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json
```

Evidence is review-only. Only the approved contract may change public generated
behaviour; all transient output belongs outside tracked directories.

## Zeroshot Development Workflow

After an OpenSpec change is approved and ready for implementation, start the
worker and independent validators through the repository launcher:

```sh
./tools/zeroshot/run-change <openspec-change-id>
```

OpenSpec remains authoritative for requirements and architecture. The launcher
passes its artifacts to Zeroshot verbatim and uses an isolated Git worktree.
Use `--pr` only when the run should also create a pull request:

```sh
./tools/zeroshot/run-change --pr <openspec-change-id>
```

Bootstrap the pinned development-only Zeroshot version with
`./tools/zeroshot/bootstrap`. Repository verification is invoked through the
root `Makefile`; `tools/verify` is its internal implementation. GitHub CI
remains the final merge authority. The repository pins Codex as the workflow
provider and `make pr` as the required
command proof. Use `--ship` only when an approved run should create and merge a
pull request, `--background` for a detached run, and `zeroshot resume <run-id>`
to continue a stopped or failed run. Validators MUST NOT run until the worker
publishes `canValidate=true`; `canValidate=false` continues through
`WORKER_PROGRESS`.

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
  - live smoke: public SDK calls in `tests/live/test_smoke.py`.
- Keep genuinely distinct logic (rename heuristics, summary reconciliation,
  destructive/diagnostic-bundle flows, `P-NULL-HTTP`) as separate tests — do NOT
  force them into a table.

### Reuse shared code, don't duplicate

- Use the shared fixtures and factories (`make_target`, `make_settings`,
  `mock_transport`, the fake-CLI client fixture, `register_resource`,
  `test_identity`). Do NOT re-copy `_target()`/`_settings()` style local helpers
  into a test module.
- Never mutate `os.environ` directly in component tests; use the provided
  fixture-scoped environment control (keeps the suite parallel-safe).

### Assert precisely

- Verify optional-flag presence/absence with a complete `expected_argv` value,
  not partial `in`/`not in` checks. Match the transport method exactly
  (`run_bytes` including `stdin`/`timeout`, `run_text`).
- No tautological, dead, or duplicate tests. Do not add comments that narrate the
  code.

### Completeness assertion

`tests/unit/resources/test_operations.py::test_discovered_public_methods`
asserts `discovered_public_methods == {case.sdk_method for case in
OPERATION_CASES if case.is_canonical}` with 193 unique canonical methods,
320 unique case IDs (193 canonical rows), 127 noncanonical variants, 89 generated rows, and 231 manual rows; 148 legacy payload rows are a migration subset. No allowlist is accepted.

### Layers and markers

- Default suite is offline: `uv run pytest -m "not live"` MUST stay green and MUST
  need no backend/network. Unit, contract, component, and packaging layers stay
  offline.
- Path prefixes auto-apply layer markers (`unit`, `contract`, `component`,
  `packaging`, `live`) via `tests/conftest.py`; see
  `openspec/specs/verification-and-release/spec.md`.
- `tests/component/test_process_contract.py` carries `@pytest.mark.process` and
  `@pytest.mark.serial`; all other offline tests MUST NOT use `serial`.
- Live tests are gated. Markers do NOT inherit in this repo: every
  `tests/live/*` test module sets `pytestmark = [pytest.mark.live,
  pytest.mark.live_smoke, pytest.mark.serial]`. Verify with
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
