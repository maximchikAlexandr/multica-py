# Research: Reduce Non-Production Complexity

## Decision 1 — Preserve history as four baseline capabilities

**Decision**: Create four files under `openspec/specs`: `sdk-surface`,
`subprocess-transport`, `upstream-contract`, and `verification-and-release`.
Each file uses `### Requirement: <name>`, normative `MUST`/`SHALL`, and one or
more `#### Scenario:` blocks with `- **WHEN**` and `- **THEN**`. Do not create
OpenSpec configuration or change artifacts.

**Rationale**: OpenSpec baseline specs are capability-oriented and plain
Markdown. Four capabilities retain active product knowledge without copying
six generations of planning, research, tasks, and process history.

**Alternatives considered**:

- ADRs: rejected because they do not encode verifiable requirements and
  scenarios.
- One large baseline file: rejected because unrelated SDK, transport,
  upstream, and release requirements would remain coupled.
- Full OpenSpec initialization: rejected because migration is the next
  feature.

## Decision 2 — One hybrid generated runtime projection

**Decision**: Commit only
`src/multica_py/_generated/approved_sdk.py`. It contains generated compatibility
constants, enums, binding descriptors, and validators. Render test cases,
documentation, compatibility, provenance, and evidence only in memory or below
a caller-supplied ignored output root.

**Rationale**: Runtime generated code is shipped and deserves a visible PR
diff. Committing other pure projections creates multiple authorities and
golden copies. One module also eliminates partial materialization of bindings,
enums, and validators.

**Alternatives considered**:

- Build-time generation only: rejected because editable installs, IDEs, and
  review of the public API become harder.
- Commit every generated projection: rejected because contract, outputs, and
  goldens repeat the same facts.
- Keep separate generated runtime modules: rejected because they permit
  partial drift and are not independently owned.

## Decision 3 — Git merge is promotion

**Decision**: Remove candidate/supported/observed state, promotion decisions,
lock/journal/backup recovery, rename suggestions, upgrade bundles, and
scheduled observers. A reviewed change to the approved contract and its one
runtime projection becomes active when merged.

**Rationale**: Automation is forbidden from approving evidence, so the second
state machine cannot remove the human decision. Git already supplies review,
atomic repository history, conflict handling, rollback, and authorship.

**Alternatives considered**:

- Keep state but remove recovery: rejected because candidate/supported remains
  a second promotion authority.
- Keep observer workflows: rejected because they create persisted state and
  suggestions that cannot approve coverage.
- Automatic evidence-to-contract promotion: rejected by the upstream contract
  review rules.

## Decision 4 — Keep a narrow fail-closed extractor

**Decision**: Keep binary/source collection only for known declarative Cobra
patterns, source provenance, checksums, and unresolved review items. `collect`
writes solely under the explicit output directory and has no code path that
writes `contracts/sdk-contract.json` or `src/multica_py`.

**Rationale**: Evidence accelerates upstream migration without turning
heuristics into public SDK decisions. A hard filesystem boundary makes the
fail-closed rule testable.

**Alternatives considered**:

- Delete extraction: rejected because it would make migrations more manual.
- Preserve semantic diff/impact/rename machinery: rejected because those
  candidate interpretations still require complete human review and dominate
  maintenance cost.

## Decision 5 — Canonical operation table lives in tests

**Decision**: `tests/cases/operations.py::OPERATION_CASES` is the only complete
success-operation registry. It stores SDK method, arguments, full transport
method/argv/stdin/timeout, fake output, result assertion, and stable case ID.
Public resource methods are introspected in one completeness test and compared
to the table.

**Rationale**: The table is executable proof. A production CLI manifest,
behavioral coverage JSON, live policy map, component table, and generated
golden do not add independent evidence when they restate the same SDK call.

**Alternatives considered**:

- Keep `cli_manifest.json` as authority: rejected because it is another
  generated catalog and does not execute the public method.
- Derive all 111 rows from the 16-operation approved contract: rejected
  because the current approved migration scope does not govern all public
  operations.
- Keep unit and mocked component executors: rejected because both use the same
  mocked transport boundary.

## Decision 6 — Three real-process cases

**Decision**: Retain exactly three rows in
`tests/component/test_process_contract.py`:

1. `bytes-env` verifies argv, JSON bytes, stderr capture, and environment
   allowlisting;
2. `text-stdin` verifies text decoding and exact stdin;
3. `timeout-tree-cleanup` verifies timeout, termination escalation, and no
   surviving descendant.

**Rationale**: These are distinct OS-process boundaries. Running every
resource through a fake executable does not add evidence beyond the canonical
argv executor.

**Alternatives considered**:

- No subprocess tests: rejected because mock transport cannot prove lifecycle
  cleanup.
- One process test per SDK operation: rejected because command semantics are
  already proved by the unit table.
- Five separate process functions: rejected because one table supports new
  boundary cases without new harnesses.

## Decision 7 — Prepared-target live smoke

**Decision**: Run exactly five public-SDK scenarios on a manually dispatched
self-hosted `multica-live` runner: release identity, project CRUD, comment
list decoding, not-found mapping, and project-update presence semantics. Require
an existing executable, authenticated profile, HTTPS/loopback server URL, and
workspace. Clean created resources through one `contextlib.ExitStack`.

**Rationale**: These cases prove the SDK/CLI/backend boundary without owning
backend deployment, account creation, direct HTTP truth, daemon lifecycle, or
agent execution.

**Alternatives considered**:

- Continue Docker/bootstrap/sandbox in SDK CI: rejected because it tests a
  second backend client and control plane.
- No live tests: rejected because package-to-real-CLI compatibility still
  needs a release smoke signal.
- Scheduled extended live runs: rejected because upstream owns broad backend
  acceptance and the prepared environment is explicitly manual.

## Decision 8 — Remove `httpx`

**Decision**: Delete direct live HTTP clients and their tests, then remove
`httpx` from the test dependency group and lockfile.

**Rationale**: Production is a CLI wrapper. After the direct oracle and
backend bootstrap are removed, no in-scope test requires an HTTP client.
Offline-network tests can prohibit stdlib socket creation without importing
`httpx`.

**Alternatives considered**:

- Retain `httpx` for an oracle: rejected because the oracle duplicates an
  undocumented server API.
- Replace it with `urllib`: rejected because the direct API boundary itself is
  out of scope.

## Decision 9 — Product outcomes replace meta-gates

**Decision**: Delete five-stage architecture/baseline checks, LOC caps,
registry/file-count rules, historical node fingerprints, and the
duplicate-removal ledger. Retain Ruff, mypy, pytest, zonal coverage, package
checks, operation completeness, and marker selection.

**Rationale**: Product outcomes catch public regressions. The removed gates
freeze test organization and already tolerate violated budgets through known
gaps.

**Alternatives considered**:

- Collapse five stages into one script: rejected because most checks still
  govern internal layout rather than behavior.
- Keep the duplicate ledger: rejected because each deletion permanently grows
  the repository.
- Replace permanent LOC gates with a new baseline: rejected because line
  reduction is a feature acceptance measurement, not a runtime invariant.

## Decision 10 — CI configuration is tested by CI

**Decision**: Delete pytest modules and functions that parse, regex-match, or
assert literal workflow YAML. Keep the workflows themselves, pinned actions,
required commands, and external branch-protection settings.

**Rationale**: Text tests reject semantically equivalent workflow edits and do
not execute the platform behavior they claim to prove.

**Alternatives considered**:

- Add a YAML parser: rejected because it still tests configuration shape.
- Add `actionlint`: rejected for this feature because a new tool is unnecessary
  to remove brittle repository tests.

## Decision 11 — Compatibility constants come from the approved contract

**Decision**: Render `TARGET_VERSION`, `MIN_CLI_VERSION`, and
`MAX_CLI_VERSION` into `approved_sdk.py`. The minimum equals
`target.version`; the maximum is its next patch version. `compat.py` imports
these constants and stops reading `upstream_state.json`.

**Rationale**: Runtime compatibility needs one small approved projection, not
the removed supported-state model.

**Alternatives considered**:

- Read `sdk-contract.json` at runtime: rejected because package consumers need
  no repository contract file.
- Keep `upstream_state.json`: rejected because it preserves the parallel
  supported state.

## Decision 12 — Deletion and verification sequence

**Decision**: Install each replacement before deleting its source. The fixed
order is baseline specs, meta-gates, operation table, upstream pipeline, live
suite, workflow-text tests, final reference/LOC audit.

**Rationale**: Each phase has an executable gate and can be reviewed without
temporarily losing a product guarantee.

**Alternatives considered**:

- One unstructured mass deletion: rejected because failures cannot be
  attributed or safely corrected.
- Preserve compatibility shims for deleted test registries: rejected because
  aliases retain the complexity this feature removes.
