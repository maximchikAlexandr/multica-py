# Contract: Historical-to-OpenSpec Migration Matrix

## Fixed grammar and verifier

Create exactly four files: `openspec/specs/sdk-surface/spec.md`,
`openspec/specs/subprocess-transport/spec.md`,
`openspec/specs/upstream-contract/spec.md`, and
`openspec/specs/verification-and-release/spec.md`. Do not create OpenSpec
configuration, changes, commands, dependencies, or agent instructions.

Each starts `## ADDED Requirements`. Each matrix row becomes exactly one
`### Requirement: <title>` followed by its exact normative sentence and one
`#### Scenario: <title>` with the stated `- **WHEN**` and `- **THEN**` lines.
Append the listed source IDs as an HTML comment to that requirement.

Create `tests/contract/test_baseline_specs.py`. It loads only these four paths
and asserts: matrix titles occur once; every title has its exact sentence and
WHEN/THEN pair; its provenance comment contains every listed source ID; and no
heading outside the stated grammar occurs. It does not read deleted folders.

## Retained matrix

| Destination | Source IDs | Title | Exact normative sentence | Scenario: WHEN / THEN |
| --- | --- | --- | --- | --- |
| sdk-surface | 001:FR-001,FR-002,FR-003,FR-004,FR-005 | Synchronous resource client | The SDK MUST expose one synchronous `MulticaClient` with stateless domain resources and immutable typed models. | WHEN a consumer calls a resource method / THEN no model performs hidden I/O or Active Record persistence. |
| sdk-surface | 001:FR-018–FR-031,005:FR-019–FR-025 | Public resource surface | The SDK MUST retain every public resource method present in the canonical operation table. | WHEN a public resource method exists / THEN one canonical operation row covers it. |
| sdk-surface | 001:FR-033–FR-039 | Closed public types | The SDK MUST use immutable `msgspec` models and closed public enums or primitive unions without public `Any`. | WHEN structured output is decoded / THEN it is a typed model or documented closed primitive. |
| sdk-surface | 001:FR-006A–FR-006D,FR-047–FR-050B | Distribution boundary | The distribution MUST remain `multica-py`, import as `multica_py`, include `py.typed`, and import without a CLI. | WHEN installed cleanly / THEN `import multica_py` succeeds before a CLI invocation. |
| subprocess-transport | 001:FR-006–FR-010,FR-015 | CLI-only transport | The SDK MUST invoke Multica through one shell-free controlled subprocess transport. | WHEN a resource runs a command / THEN exact argv, cwd, profile, workspace, environment, stdin, and timeout reach that transport. |
| subprocess-transport | 001:FR-016–FR-017B,005:FR-004–FR-006,006:FR-008–FR-010 | Managed process lifecycle | The SDK MUST expose managed processes with bounded concurrency, timeout cancellation, escalation, and descendant cleanup. | WHEN the timeout process case expires / THEN parent and descendant are absent. |
| subprocess-transport | 001:FR-011–FR-014,FR-040–FR-044 | Decode and diagnostics | The SDK MUST decode supported structured output, map reliable failures to typed errors, and redact secrets from diagnostics. | WHEN malformed output or nonzero exit occurs / THEN the diagnostic has redacted command context and the documented error type. |
| upstream-contract | 001:FR-032A–FR-032G,002:FR-001,FR-002,FR-027 | Pinned source authority | The approved contract MUST cite full pinned source commits and locations, while extraction records only declared declarative facts. | WHEN extraction sees an unknown pattern / THEN it emits a review item and changes no approved behavior. |
| upstream-contract | 002:FR-003,FR-004,FR-012,FR-023,FR-032 | Verified evidence | Evidence collection MUST record verified binary identity, release identity, ordered declarative facts, and review items outside version control. | WHEN collection succeeds / THEN its two files satisfy the schemas in `generation.md`. |
| upstream-contract | 002:FR-028,007:FR-009,FR-010 | Reviewed mapping semantics | Every approved mapping MUST state source evidence, destination, five-state presence, enum policy, and normalized constraints with positive and negative evidence. | WHEN a mapping is incomplete or unresolved / THEN validation fails. |
| upstream-contract | 002:FR-017,FR-018,007:FR-012–FR-014 | Deterministic generation | The approved contract MUST be the only generator input and MUST render one committed runtime module plus deterministic transient projections. | WHEN rendered twice / THEN all relative paths and bytes are identical. |
| upstream-contract | 002:FR-025,FR-033 | Generated compatibility | The generated runtime module MUST provide the tested CLI interval from the approved target version. | WHEN a client reads default policy / THEN it uses generated minimum and exclusive next-patch maximum versions. |
| upstream-contract | 002:FR-030,007:FR-011 | Git promotion | A reviewed Git merge changing the approved contract and runtime projection MUST be the only promotion action. | WHEN a PR is merged / THEN no candidate, supported, observer, or journal state is written. |
| verification-and-release | 001:FR-051–FR-059C,005:FR-011–FR-017 | Offline quality and release | CI MUST run Ruff, configured mypy, offline pytest, coverage, contract check, package validation, and approved release validation through `uv`. | WHEN a pull request runs / THEN job outcomes, not workflow-text tests, decide acceptance. |
| verification-and-release | 001:FR-060–FR-066,004:FR-004–FR-008,FR-017,006:FR-011–FR-013 | Canonical operation coverage | Every public SDK method MUST have exactly one canonical success operation row with complete transport behavior. | WHEN `discovered_public_methods` is compared to `{case.sdk_method for case in OPERATION_CASES if case.is_canonical}` / THEN the sets are equal, with 116 unique canonical methods, 137 unique case IDs, and 21 noncanonical variants. |
| verification-and-release | 004:FR-006,FR-015,FR-016,005:FR-002,FR-005,FR-006,006:FR-009 | Focused process and offline checks | Offline tests MUST use stdlib and pytest, keep exact argv assertions, and retain exactly three real-process cases. | WHEN the process module is collected / THEN IDs are `bytes-env`, `text-stdin`, and `timeout-tree-cleanup`. |
| verification-and-release | 003:FR-001,FR-002,FR-007,FR-014,FR-022,FR-029,FR-030 | Prepared-target live smoke | Live smoke MUST run separately against a prepared CLI/profile/workspace and clean uniquely named resources through the SDK. | WHEN live smoke is selected / THEN five fixed scenarios run without backend provisioning or direct HTTP. |
| verification-and-release | 001:FR-067–FR-075 | Maintainer documentation | Documentation MUST describe CLI installation/authentication, compatibility, and approved upstream review. | WHEN a maintainer follows it / THEN they validate, collect, render, and check without a promotion state machine. |

## Superseded source IDs

These are intentionally superseded, not retained: 002:FR-005–FR-011,FR-013–FR-016,FR-019–FR-022,FR-024,FR-026,FR-029,FR-031; 003:FR-003–FR-006,FR-008–FR-013,FR-015–FR-021,FR-023–FR-028; 004:FR-001–FR-003,FR-004a,FR-009–FR-014,FR-018–FR-021; 005:FR-001,FR-002a,FR-003,FR-007–FR-010,FR-018,FR-026–FR-063; 006:FR-001–FR-007,FR-014–FR-032.

## Reference replacement

Update `AGENTS.md`, `README.md`, `docs/cli-coverage.md`, `docs/releasing.md`, `docs/contributing.md`, `docs/compatibility.md`, `scripts/audit_source_links.py`, and feature-007 active-entrypoint text. Use this only deletion reference check:

```bash
git grep -nE 'specs/00[1-6]' -- ':!specs/008-reduce-nonprod-complexity/**'
```

Success is no output; the exclusion prevents this matrix from failing itself.
